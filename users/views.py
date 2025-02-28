from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from users.models.models_global import PerfilUsuario
from api.decorators.jwt_decorator import jwt_required
from custom_auth.views import generate_jwt_token


@api_view(['POST'])
@jwt_required
def get_data(request):
    if request.method == 'POST':
        try:
            user_info = request.user
            username_field = 'preferred_username' if user_info.get(
                'token_type') == 'microsoft' else 'username'

            basicos_usuario = PerfilUsuario.objects.filter(
                usuario=user_info.get(username_field)).last()
            if not basicos_usuario:
                return JsonResponse({'message': 'Required basic data', 'BdRequired': True}, status=status.HTTP_200_OK)

            perfiles_usr = PerfilUsuario.objects.filter(
                basicos_usuario=basicos_usuario)
            
            urls_usuario = []
            for perfil_usr in perfiles_usr:
                url = f'{perfil_usr.dependencia.url}/{perfil_usr.grupo.url}/{perfil_usr.rol.url}'
                urls_usuario.append(url)

            datos_basicos = {
                "dependencia": basicos_usuario.dependencia.nombre_dependencia,
                "grupo": basicos_usuario.grupo.nombre_grupo,
                "rol": [perfil_usr.rol.nombre_rol for perfil_usr in perfiles_usr],
                "rutas": urls_usuario
            }

            user_token = generate_jwt_token(data={'datos_basicos': datos_basicos, 'address': request.META.get(
                'REMOTE_ADDR'), 'type': 'data', 'user_type': 'external'}, exp_minutes=60)

            response = JsonResponse(
                {'message': 'Data retrieved'}, status=status.HTTP_200_OK)

            response.set_cookie(
                key='user_token',
                value=user_token,
                max_age=60 * 60,
                expires=1,
                secure=False,
                httponly=True,
                samesite='Lax',
                path='/'
            )

            return response
        except Exception as e:
            return JsonResponse({'message': f'Error en la data {e}'}, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
