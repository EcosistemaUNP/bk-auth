import jwt
from django.http import JsonResponse
from rest_framework import status
from decouple import config


class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get("Authorization", None)

        if auth_header:
            try:
                token = auth_header.split(" ")[1]

                payload = jwt.decode(token, config(
                    'TOKEN_SECRET_KEY'), algorithms=["HS256"])

                request.user = payload
            except jwt.ExpiredSignatureError:
                return JsonResponse({"error": "Token expirado"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return JsonResponse({"error": "Token inválido"}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            request.user = None

        response = self.get_response(request)
        return response
