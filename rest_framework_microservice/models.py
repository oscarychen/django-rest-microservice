from rest_framework_simplejwt.models import TokenUser
from django.db import models
from django.contrib.auth import get_user_model


class CustomTokenUser(TokenUser):
    """
    Extend TokenUser and adds custom attributes to be pulled from TokenUser.
    This class should be specified in Django settings SIMPLE_JWT.TOKEN_USER_CLASS
    """

    # TODO: No longer needed in newer version of djangorestframework-simplejwt
    # See: https://github.com/jazzband/djangorestframework-simplejwt/pull/528
    def __getattr__(self, attr_name):
        return self.token.get(attr_name, None)


class Idp(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name="idp")
    uuid = models.UUIDField()

    class Meta:
        indexes = [models.Index(fields=['uuid'])]