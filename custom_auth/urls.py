from django.urls import path
from rest_framework import routers
from custom_auth.views import auth, two_factor_auth, refresh_token, logout, validate

app_name = 'auth'
routers = routers.DefaultRouter()

urlpatterns = [
    path('', auth),
    path('2fa/', two_factor_auth),
    path('refresh/', refresh_token),
    path('logout/', logout),
    path('validate/', validate),
]
