from rest_framework.exceptions import APIException
from rest_framework import status
from django.utils.translation import gettext_lazy as _


class ModelAttributeError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Model instance attribute error.')
    default_code = 'authentication_failed'


class TokenExpired(APIException):
    status_code = status.HTTP_410_GONE
    default_detail = _('Token expired.')
    default_code = 'authentication_failed'


class InvalidToken(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _('Invalid token.')
    default_code = 'authentication_failed'


class SubscriptionExpired(APIException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = _('Subscription expired.')
    default_code = 'error'


class UserAgreementExpired(APIException):
    status_code = status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS
    default_detail = _('User agreement expired.')
    default_code = 'error'
