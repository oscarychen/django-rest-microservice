from operator import attrgetter
from django.conf import settings
from .settings import rest_microservice_settings
from rest_framework import serializers
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.serializers import TokenObtainSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings
from django.utils.module_loading import import_string
from .exceptions import InvalidToken, TokenExpired
from django.contrib.auth.models import update_last_login
from django.contrib.auth import get_user_model
from jwt import ExpiredSignatureError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from .social_auth.aws_cognito import decode_token
from .models import Idp

def add_custom_token_claims(token, user):
    """Append custom token claims specified using settings."""
    for attr in rest_microservice_settings.CUSTOM_TOKEN_USER_ATTRIBUTES:
        token[attr] = getattr(user, attr, None)

    for attr in rest_microservice_settings.CUSTOM_TOKEN_CALLABLE_ATTRIBUTES:
        attr_name = attr["attr_name"]
        attr_getter = import_string(attr["attr_getter"])
        token[attr_name] = attr_getter(user)

    return token


class SerializerResponseMixin:
    def make_auth_response(self):
        access_token = self.validated_data['access']
        access_expiry = self.validated_data['access_expiry']
        response_data = {'access_token': access_token, 'expires': access_expiry}

        user_serializer = rest_microservice_settings.USER_SERIALIZER_CLASS
        if user_serializer:
            user = self.validated_data['user']
            response_data['user'] = user_serializer(user).data

        return Response(response_data, status=status.HTTP_200_OK)


class LogInTokenObtainPairSerializer(TokenObtainSerializer, SerializerResponseMixin):
    """
    Validates user, returns dictionary containing refresh token, access token,
    expiry time of access token, user dictionary.
    This is similar to the rest_framework_simplejwt.serializers.TokenObtainPairSerializer.
    """

    @classmethod
    def get_token(cls, user):
        # TODO: simple-jwt future release
        # token = cls.token_class.for_user(user)
        token = RefreshToken.for_user(user)
        add_custom_token_claims(token, user)

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        # putting a few things from JWT directly into the response to make it easier for web frontend to use
        data['refresh_expiry'] = refresh.payload['exp']
        data['access_expiry'] = refresh.access_token['exp']
        data['user'] = self.user

        update_last_login(None, self.user)

        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer, SerializerResponseMixin):
    """
    Validates refresh token string, returns dictionary containing access token,
    expiry time of access token, user dictionary.
    """

    def validate(self, attrs):
        try:
            refresh = RefreshToken(attrs['refresh'])
            user = self.get_user(refresh)
            # copying custom attributes from user instance to TokenUser in case any attributes have been changed
            add_custom_token_claims(refresh, user)

        # only intercept errors that we do not want to see in Django error reporting here
        except ExpiredSignatureError:
            raise TokenExpired()
        except ObjectDoesNotExist:
            raise InvalidToken()

        data = {'access': str(refresh.access_token), 'access_expiry': refresh.access_token['exp'], 'user': user}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    # Attempt to blacklist the given refresh token
                    refresh.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will not be present
                    pass

            refresh.set_jti()
            refresh.set_exp()

            data['refresh_token'] = str(refresh)

        return data

    @staticmethod
    def get_user(refresh_token):
        user_model = get_user_model()
        return user_model.objects.get(id=refresh_token.get("user_id"))


class SocialLogInTokenExchangeSerializer(serializers.Serializer, SerializerResponseMixin):
    """
    Validates AWS Cognito id token, returns dictionary containing internally-signed
    refresh token, access token, expiry time of access token, and user dictionary.
    """
    id_token = serializers.CharField()
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()

    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        try:
            id_token = decode_token(attrs['id_token'], rest_microservice_settings.IDP['CLIENT_ID'])

        # only intercept errors that we do not want to see in Django error report here
        except ExpiredSignatureError:
            raise TokenExpired()

        if id_token.get('email_verified') is False:
            raise APIException("Email not verified.")

        user_defaults = {
            "username": id_token["cognito:username"],
            "first_name": id_token.get("given_name"),
            "last_name": id_token.get("family_name"),
        }

        if rest_microservice_settings.USER_MODEL_UUID_FIELD is not None:
            user_defaults[rest_microservice_settings.USER_MODEL_UUID_FIELD] = id_token['sub']

        user, created = get_user_model().objects.get_or_create(email=id_token["email"], defaults=user_defaults)

        if rest_microservice_settings.USER_MODEL_UUID_FIELD is None:
            Idp.objects.update_or_create(user=user, defaults={"uuid": id_token['sub']})

        refresh = self.get_token(user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'refresh_expiry': refresh.payload['exp'],
            'access_expiry': refresh.access_token['exp'],
            'user': user
        }

        update_last_login(None, user)

        return data
