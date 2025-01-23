from django.contrib import admin
from django.urls import path, include
from users.views import auth, two_factor_auth, logout

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', auth),
    path('2fa/', two_factor_auth),
    path('logout/', logout),
    # path('account/', include('two_factor.urls')),
]
