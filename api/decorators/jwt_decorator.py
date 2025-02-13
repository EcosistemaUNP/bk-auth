import jwt
import base64
import json
from functools import wraps
from django.http import JsonResponse
from rest_framework import status
from decouple import config
from jwt import PyJWKClient
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, InvalidAudienceError, InvalidIssuerError


def identificar_tipo_token(token):
    try:
        header_encoded = token.split(".")[0]
        header_decoded = base64.urlsafe_b64decode(
            header_encoded + "==").decode("utf-8")
        header = json.loads(header_decoded)

        if header.get("alg") == "RS256":
            return "microsoft"
        elif header.get("alg") == "HS256":
            return "propio"
        else:
            return "desconocido"
    except Exception as e:
        return "desconocido"


def validate_microsoft_token(token):
    jwks_url = f"https://login.microsoftonline.com/{config('MICROSOFT_TENANT')}/discovery/v2.0/keys"
    issuer_url = f"https://login.microsoftonline.com/{config('MICROSOFT_TENANT')}/v2.0"
    audience = config('MICROSOFT_CLIENT_ID')

    try:
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        decoded_token = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer_url
        )

        return decoded_token
    except ExpiredSignatureError:
        raise InvalidTokenError("Token expirado")
    except InvalidAudienceError as e:
        raise InvalidTokenError(f"Audiencia del token inválida: {e}")
    except InvalidIssuerError as e:
        raise InvalidTokenError(f"Emisor del token inválido: {e}")
    except jwt.InvalidAlgorithmError as e:
        raise InvalidTokenError(f"Algoritmo de firma no soportado: {e}")
    except jwt.DecodeError as e:
        raise InvalidTokenError(f"Token malformado o firma inválida: {e}")
    except Exception as e:
        raise InvalidTokenError(f"Error al validar el token: {str(e)}")


def jwt_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        token = None

        # 1. Primero buscar el token en las cookies (para JWT propio)
        token = request.COOKIES.get('access_token')  # Nombre de la cookie

        # 2. Si no está en cookies, buscar en el header (para Microsoft)
        if not token:
            auth_header = request.headers.get("Authorization", None)
            if not auth_header:
                return JsonResponse({"error": "Token no proporcionado"}, status=status.HTTP_401_UNAUTHORIZED)
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return JsonResponse({"error": "Formato de token inválido"}, status=status.HTTP_401_UNAUTHORIZED)

        # 3. Identificar tipo de token
        token_type = identificar_tipo_token(token)

        try:
            if token_type == 'microsoft':
                payload = validate_microsoft_token(token)
                payload["token_type"] = "microsoft"
                request.user = payload
            elif token_type == "propio":
                payload = jwt.decode(token, config(
                    'TOKEN_SECRET_KEY'), algorithms=["HS256"])
                payload["token_type"] = "propio"
                request.user = payload
            else:
                return JsonResponse({"error": "Tipo de token no soportado"}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.ExpiredSignatureError:
            return JsonResponse(
                {"error": "Token expirado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except jwt.InvalidTokenError as e:
            return JsonResponse(
                {"error": f"Token inválido: {str(e)}"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return JsonResponse(
                {"error": f"Error de autenticación: {str(e)}"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        return view_func(request, *args, **kwargs)

    return wrapped_view
