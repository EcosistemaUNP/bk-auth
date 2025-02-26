# DOCUMENTACIÓN DEL MODULO DE AUTENTICACIÓN

## Introducción

Este módulo de **autenticación** en Django permite la creación y validación de tokens JWT para usuarios externos, así como la validación de tokens JWT de Microsoft para usuarios internos. Utiliza Django REST Framework y SimpleJWT para la gestión de tokens.

## Tecnologias utilizadas

•	Django 5.1.6

•	Django REST Framework 3.15.2

•	SimpleJWT 5.4.0

•	PyJWT 2.10.1

•	PostgreSQL (psycopg2 2.9.10)

•	django-cors-headers 4.7.0 (para habilitar CORS)

•	django-otp 1.5.4 y django-two-factor-auth 1.17.0 (para autenticación en dos factores)

•	qrcode 8.0 (para generar códigos QR en autenticación en dos pasos)

## Instalación

Para instalar las dependencias necesarias, ejecute:
``` npm
pip install -r requirements.txt
```

## Variables de entorno utilizadas
``` env
#Conexion BD local
DATABASE_NAME='bk-auth'
DATABASE_USER='postgres'
DATABASE_PASSWORD='Jsol2303.'
DATABASE_HOST='localhost'
DATABASE_PORT='5432'

RECAPTCHA_SECRET_KEY='6Ld_aKAqAAAAADNjf0R9YO6SSFeE8_zpeq800mhP'
FERNET_SECRET_KEY='x6VEWxff5-KfBQa1TB6yQV6UqvhS5O4J4iy6vm97P1A='
TOKEN_SECRET_KEY='2255f4356abf8fefb56d36f9bd2c823915f7a088b00388d4d65e5fda17bfed064f95eb109e8474159be45dfff0d73d0f19f20562ef4309b56566f9f0669e4a7267e313ee420750dad9d400aa232a59e2796cfabbc9069d51fec3bf8f8abe37c22e689c6554c845033dbb93fe278e8d2c8f9385e99a99f3b9ad7de4a5e91778415ccec366372821bf5a2e35fdbcbfcd6499fd2cae725b1f98337822223a9ef9f2d4511d1ef4f4f2cc3c1152d8e8a9f6ceed236891619d9f1406b28a9d9bc13b7566a007a1774203662233b8a8d66fa3ba30bcda093515a797c6191ab860de45ba314a4baea26aa90ee8507f8a3ce836cf8c2f19bdb89a2adad9f54753b321024e'

MICROSOFT_TENANT='58ec5e61-0ed7-4021-a4f8-c2e2b3b9f5ff'
MICROSOFT_CLIENT_ID='e0ade322-98b9-46ba-9ac4-22c18724363d'
```

## Endpoints

**Ruta:** ```/api/auth/```  
**Método:** ```POST```  
**Parámetros:**
```json
{
    "username": string,
    "password": string,
    "recaptcha": string
}
```  
**Respuestas:**  
```json
{
    "message": "User has no device",
    "qr_code": "",
    "twoFARequired": True
}
{
    "message": "Login Success",
    "twoFARequired": True
}
```  
**Ruta:** ```/api/auth/2fa/```  
**Método:** ```POST```  
**Parámetros:**
```json
{
    "code2fa": string,
    "username": string
}
```  
**Respuestas:**  
```json
{
    "message": "Login Success"
}
```  
**Ruta:** ```/api/auth/microsoft_login/```  
**Método:** ```POST```
**Parámetros:**
```json
{
    "access_token": string
}
```  
**Respuestas:**  
```json
{
    "message": "Login Success"
}
``` 
**Ruta:** ```/api/auth/logout/```  
**Método:** ```POST```  
**Parámetros:**
```json
{
    "username": string
}
``` 
**Respuestas:**  
```json
{
    "message": "Logout Success"
}
``` 
**Ruta:** ```/api/auth/validate/```  
**Método:** ```POST```
**Respuestas:**  
```json
{
    "message": "JWT validated",
}
```  
**Ruta:** ```/api/users/data/```  
**Método:** ```POST```
**Respuestas:**  
```json
{
    "message": "Required basic data",
    "BdRequired": True
}
{
    "message": "Data retrieved",
}
```
## Formato de los JWT (Enviados por cookies)
**access_token**
```json
{
    "username": string,
    "address": string,
    "type": string("access"),
    "user_type":string("external | internal"),
    "token_id": uuid,
    "iat": datetime,
    "exp": datetime
}
```
**user_token**
```json
{
    "username": string,
    "datos_basicos": {
        "dependencia": string,
        "grupo": string,
        "rol": string[],
        "rutas": string[]
    },
    "address": string,
    "type": string("data"),
    "user_type": string("external | internal"),
    "token_id": uuid,
    "iat": datetime,
    "exp": datetime
}
```


## Codigo usado en el decorador **jwt_required**
```py
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

```  

## Conclusión
Este módulo proporciona una solución completa para la autenticación basada en JWT en Django, permitiendo la validación tanto de tokens propios como de Microsoft. Además, se ha integrado la autenticación en dos factores y soporte para CORS.