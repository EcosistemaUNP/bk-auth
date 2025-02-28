from django.urls import path
from rest_framework import routers
from users.views import get_data

app_name = 'usuario'
routers = routers.DefaultRouter()

urlpatterns = [path('data/', get_data),]
