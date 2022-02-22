# django-rest-microservice

This package is built on the 
[djangorestframework-simplejwt](https://github.com/jazzband/djangorestframework-simplejwt) package, which provides
some JWT authentication mechanisms with [Django REST framework](https://github.com/encode/django-rest-framework).
This package offers the following features:
- Provides refresh cookie in HttpOnly cookie, and access token in response body, for better security 
when implemented properly with SPA.
- Provides an easier approach to customizing token claims than the standard mechanism described in 
djangorestframework-simplejwt documentation.
- Provides a mechanism for authentication with a third-party IDP, before issuing internal JWT to your users.
- Currently, supports authentication with AWS Cognito using OAuth 2 Code Grant with PKCE for best security practices.

Installation
============
Install package to environment:
```commandline
pip install django-rest-microservice
```
In the main urls.py, include the default package url routes:
```python
from django.urls import path, include

urlpatterns = [
    path("auth/", include("rest_framework_microservice.urls"))
]
```

In Django settings, include the following:
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTTokenUserAuthentication',
    )
}
```

Settings
========
Settings are specified in Django settings.py under `REST_FRAMEWORK_MICROSERVICE`, the defaults are
the following:
```python
REST_FRAMEWORK_MICROSERVICE = {
    "REFRESH_COOKIE_NAME": "refresh_cookie",
    "IDP": {
        "PROVIDER": "aws",
        "USER_POOL": "us-west-2_abcdefg",
        "CLIENT_ID": "abcdefg",
    },
    "CUSTOM_TOKEN_USER_ATTRIBUTES": [],
    "CUSTOM_TOKEN_CALLABLE_ATTRIBUTES": [],
    "COOKIE_SALT": "extra",
    "USER_SERIALIZER_CLASS": None,
}
```

``REFRESH_COOKIE_NAME``
-----------------------
Name of refresh cookie to set in HTTP header.

``IDP``
-----------------
A dictionary containing IDP attributes:
- ``PROVIDER``: a string identifying what IDP backend to use, defaults to `'aws'` 
(Currently only AWS Cognito is supported.)
- ``USER_POOL``: user pool identifier used with the IDP.
- ``CLIENT_ID``: IDP client id for your application.



``CUSTOM_TOKEN_USER_ATTRIBUTES``
--------------------------------

The list of Django user attributes to be copied to token as claims. i.e.: ``['is_active',]``.

``CUSTOM_TOKEN_CALLABLE_ATTRIBUTES``
------------------------------------

This is used to customize claims which cannot be done by simply using ``CUSTOM_TOKEN_USER_ATTRIBUTES`` setting.
This should be a list of dictionaries containing ``attr_name`` and ``attr_getter``.
i.e. : ``[{'attr_name': 'preferences', 'attr_getter': 'my_module.some_file.get_user_preferences'}, ...]``

The function specified in ``attr_getter`` should accept an argument of a Django user instance.

``COOKIE_SALT``
---------------
Salt to be used when signing cookie.

``USER_SERIALIZER_CLASS``
-------------------------
Defaults to None. If specified, the default view serializers will try to add a user object representing the user.
The content of the user object is defined by ``USER_SERIALIZER_CLASS``.

Customizing token claims
========================

You can include additional user attributes in the token claims by specifying them
in the ``CUSTOM_TOKEN_USER_ATTRIBUTES``.

You can also specify functions to return the value for custom claims by using
``CUSTOM_TOKEN_CALLABLE_ATTRIBUTES``.

```python
# settings.py
REST_FRAMEWORK_MICROSERVICE = {
  ...,
  'CUSTOM_TOKEN_CALLABLE_ATTRIBUTES': [
        {'attr_name': 'user_services',
         'attr_getter': 'my_module.token_claims.get_user_subscribed_services'
         }
    ]
}

# my_module.token_claims.py
def get_user_subscribed_services(user):
  return user.subscribed_services

```
If you are using `djangorestframework-simplejwt` version <= 5.0.0, you will also need to extend the 
`rest_framework_simplejwt.models.TokenUser` to include the additional claims. This is only applicable when using
[older versions](https://github.com/jazzband/djangorestframework-simplejwt/pull/528/).

```python
from functools import cached_property
from rest_framework_simplejwt.models import TokenUser

class CustomTokenUser(TokenUser):
    """
    Extend TokenUser and adds custom attributes to be pulled from TokenUser.
    This class should be specified in Django settings SIMPLE_JWT.TOKEN_USER_CLASS
    """

    @cached_property
    def first_name(self):
        return self.token.get('first_name', None)
```
and include the following Django setting:
```python
SIMPLE_JWT = {
    'TOKEN_USER_CLASS': 'microservice.models.CustomTokenUser'
}
```
