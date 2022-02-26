from datetime import datetime
from django.conf import settings
from .settings import rest_microservice_settings
from django.middleware import csrf
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenViewBase

from .serializers import LogInTokenObtainPairSerializer, CustomTokenRefreshSerializer, \
    SocialLogInTokenExchangeSerializer


class RefreshTokenUsingCookieMixin:
    """
    Provides function to handle refresh token that comes from cookie
    """

    def set_cookie_header_in_response(self, response, refresh_token, refresh_expiry):
        expires = datetime.fromtimestamp(refresh_expiry)
        # set matching pair of csrf token in cookie and in response body
        csrf_token = self.get_csrf_token()
        response.data.update({"CSRF_token": csrf_token})
        response.set_signed_cookie(key='CSRF_token',
                                   value=csrf_token,
                                   salt=rest_microservice_settings.COOKIE_SALT,
                                   expires=expires,
                                   httponly=True,
                                   samesite='strict',
                                   secure=not settings.DEBUG,
                                   path=rest_microservice_settings.REFRESH_COOKIE_PATH)
        # set refresh token
        response.set_signed_cookie(key=rest_microservice_settings.REFRESH_COOKIE_NAME,
                                   value=refresh_token,
                                   salt=rest_microservice_settings.COOKIE_SALT,
                                   expires=expires,
                                   httponly=True, samesite='strict', secure=not settings.DEBUG,
                                   path=rest_microservice_settings.REFRESH_COOKIE_PATH)
        return response

    @staticmethod
    def get_token_from_cookie(request):
        try:
            csrf_from_cookie = request.get_signed_cookie('CSRF_token', salt=rest_microservice_settings.COOKIE_SALT)
            csrf_from_body = request.data.get('CSRF_token')
            token = request.get_signed_cookie(rest_microservice_settings.REFRESH_COOKIE_NAME,
                                              salt=rest_microservice_settings.COOKIE_SALT)
        except KeyError:
            raise InvalidToken()

        if csrf_from_cookie is None or csrf_from_body is None:
            raise InvalidToken()

        if csrf._does_token_match(csrf_from_cookie, csrf_from_body) is False:
            raise InvalidToken()

        return token

    @staticmethod
    def get_delete_cookie_response(status_code=status.HTTP_401_UNAUTHORIZED):
        response = Response(status=status_code)
        response.delete_cookie('CSRF_token', path=rest_microservice_settings.REFRESH_COOKIE_PATH)
        response.delete_cookie(key=rest_microservice_settings.REFRESH_COOKIE_NAME,
                               path=rest_microservice_settings.REFRESH_COOKIE_PATH)
        return response

    @staticmethod
    def get_csrf_token():
        """Returns a csrf token."""
        return csrf._mask_cipher_secret(csrf._get_new_csrf_string())


class TokenLogIn(TokenObtainPairView, RefreshTokenUsingCookieMixin):
    """
    Log in using username and password, returns access token in body, refresh token in httpOnly cookie.
    """

    serializer_class = LogInTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        refresh_token = serializer.validated_data['refresh']
        refresh_expiry = serializer.validated_data['refresh_expiry']
        response = serializer.make_auth_response()

        return self.set_cookie_header_in_response(response, refresh_token, refresh_expiry)


class RefreshTokenUsingCookie(TokenViewBase, RefreshTokenUsingCookieMixin):
    """
    Provides an access token when called with a refresh token in header cookie.
    """
    serializer_class = CustomTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        jwt = self.get_token_from_cookie(request)
        serializer = self.get_serializer(data={'refresh': jwt})

        if not serializer.is_valid():
            return self.get_delete_cookie_response()

        response = serializer.make_auth_response()
        return response


class BlacklistRefreshToken(TokenViewBase, RefreshTokenUsingCookieMixin):
    """
    Blacklist's refresh token received in header cookie. Used for logging off.
    """

    def post(self, request, *args, **kwargs):
        jwt = self.get_token_from_cookie(request)
        token = RefreshToken(jwt)
        token.blacklist()
        return self.get_delete_cookie_response(status_code=status.HTTP_200_OK)


class SocialLogInExchangeTokens(APIView, RefreshTokenUsingCookieMixin):
    """
    Used when front-end authenticates directly with auth provider using OAuth2 Code grant with PKCE.
    This end point allows frontend to exchange auth provider JWT for backend-signed tokens.
    """
    permission_classes = ()
    authentication_classes = ()

    def post(self, request, *args, **kwargs):
        serializer = SocialLogInTokenExchangeSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data['refresh']
        refresh_expiry = serializer.validated_data['refresh_expiry']
        response = serializer.make_auth_response()

        return self.set_cookie_header_in_response(response, refresh_token, refresh_expiry)
