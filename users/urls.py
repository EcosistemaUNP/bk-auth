from django.urls import path
from rest_framework import routers
from .views import auth, two_factor_auth, refresh_token, get_data, logout, validate

app_name = 'usuario'
routers = routers.DefaultRouter()

urlpatterns = [
    path('auth/', auth),
    path('2fa/', two_factor_auth),
    path('refresh/', refresh_token),
    path('data/', get_data),
    path('logout/', logout),
    path('validate/', validate),
]
