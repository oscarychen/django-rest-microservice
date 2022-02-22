from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenVerifyView

urlpatterns = [
    path('sign-in/', TokenLogIn.as_view()),
    path('social-exchange/', SocialLogInExchangeTokens.as_view()),
    path('refresh/', RefreshTokenUsingCookie.as_view()),
    path('verify/', TokenVerifyView.as_view()),
    path('logoff/', BlacklistRefreshToken.as_view()),
]
