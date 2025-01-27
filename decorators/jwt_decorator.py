import jwt
from functools import wraps
from django.http import JsonResponse
from rest_framework import status
from decouple import config


def jwt_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization", None)

        if not auth_header:
            return JsonResponse({"error": "Token no proporcionado"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            token = auth_header.split(" ")[1]

            payload = jwt.decode(token, config(
                'TOKEN_SECRET_KEY'), algorithms=["HS256"])

            request.user = payload
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token expirado"}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Token inválido"}, status=status.HTTP_401_UNAUTHORIZED)

        return view_func(request, *args, **kwargs)

    return wrapped_view
