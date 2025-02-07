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

            datos_basicos = {
                "dependencia": basicos_usuario.dependencia.nombre_dependencia,
                "grupo": basicos_usuario.grupo.nombre_grupo,
                "rol": basicos_usuario.rol.nombre_rol
            }

            user_token = generate_jwt_token(data={'datos_basicos': datos_basicos, 'address': request.META.get(
                'REMOTE_ADDR'), 'type': 'data', 'user_type': 'external'}, exp_minutes=60)

            return JsonResponse({'message': 'Data retrieved', 'user_token': user_token}, status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({'message': f'Error en la data {e}'}, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
