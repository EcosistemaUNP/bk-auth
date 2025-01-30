import json
import requests
import datetime
import uuid
import jwt
from django.http import JsonResponse
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.decorators import api_view
from decouple import config

import pyotp
from django.contrib.auth.models import User
from django_otp.plugins.otp_totp.models import TOTPDevice

from users.models.models_global import Session, TwoFactorAuth, Recaptcha, Token, RefreshToken, Blacklist, PerfilUsuario

from api.decorators.jwt_decorator import jwt_required

@api_view(['POST'])
def auth(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        user_instance = User.objects.get(username=username)

        # * Validate Recaptcha
        token = data.get('recaptcha')
        if not token:
            return JsonResponse({'message': 'Recaptcha token is required'}, status=status.HTTP_400_BAD_REQUEST)

        isValidate = validate_recaptcha(user=user_instance, token=token)
        if not isValidate:
            return JsonResponse({'message': 'Recaptcha validation failed'}, status=status.HTTP_400_BAD_REQUEST)

        # * Validate User and Password
        if not username or not password:
            return JsonResponse({'message': 'User and Password are required'}, status=status.HTTP_400_BAD_REQUEST)

        result = authenticate(username=username, password=password)
        if not result:
            return JsonResponse({'message': 'Invalid User or Password'}, status=status.HTTP_401_UNAUTHORIZED)

        totp_device = validate_2fa_device(result)
        if not totp_device:
            qr_code = generate_2fa_device(result)
            return JsonResponse({'message': 'User has no device', 'qr_code': qr_code, 'twoFARequired': True}, status=status.HTTP_200_OK)

        return JsonResponse({'message': 'Login Success', 'twoFARequired': True}, status=status.HTTP_200_OK)

    return JsonResponse({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
def two_factor_auth(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        code = data.get('code2fa')
        username = data.get('username')

        if not code or not username:
            return JsonResponse({'message': 'Code or user is required'}, status=status.HTTP_400_BAD_REQUEST)

        # * Validate Code and Generate JWT
        try:
            user_instance = User.objects.get(username=username)
            totp_device = TOTPDevice.objects.get(
                user_id=user_instance, confirmed=True)
            totp = pyotp.TOTP(totp_device.key)

            if not totp.verify(code):
                return JsonResponse({'message': 'Invalid code'}, status=status.HTTP_400_BAD_REQUEST)

            access_token = generate_jwt_token(data={'username': username, 'address': request.META.get('REMOTE_ADDR'), 'type': 'access', 'user_type': 'external'}, exp_minutes=60)

            return JsonResponse({'message': 'Login Success', 'access_token': access_token}, status=status.HTTP_200_OK)

        except TOTPDevice.DoesNotExist:
            return JsonResponse({'message': 'User has no device'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return JsonResponse({'message': f'Internal Server Error: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JsonResponse({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
@jwt_required
def refresh_token(request):
    if request.metodh == 'POST':
        refresh_token = request.headers.get('Authorization')
        if not refresh_token:
            return JsonResponse({'message': 'Refresh Token is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            payload = jwt.decode(
                refresh_token, config('REFRESH_TOKEN_SECRET_KEY'), algorithms=['HS256'])
            if payload.get('type') != 'refresh':
                return JsonResponse({'message': 'Invalid Token'}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(id=payload.get('user_id'))
            access_token = generate_jwt_token()
            refresh_token = generate_refresh_jwt_token()

            return JsonResponse({'message': 'Token Refreshed', 'access_token': access_token, 'refresh_token': refresh_token}, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse({'message': 'Invalid Token'}, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
@jwt_required
def get_data(request):
    if request.method == 'POST':
        try:
            user_info = request.user
            username_field = 'preferred_username' if user_info.get('token_type') == 'microsoft' else 'username'

            basicos_usuario = PerfilUsuario.objects.filter(usuario=user_info.get(username_field)).last()
            if not basicos_usuario:
                return JsonResponse({'message': 'Required basic data', 'BdRequired': True}, status=status.HTTP_200_OK)
  
            datos_basicos = {
                "dependencia": basicos_usuario.dependencia.nombre_dependencia,
                "grupo": basicos_usuario.grupo.nombre_grupo,
                "rol": basicos_usuario.rol.nombre_rol
            }

            user_token = generate_jwt_token(data={'datos_basicos': datos_basicos, 'address': request.META.get('REMOTE_ADDR'), 'type': 'data', 'user_type': 'external'}, exp_minutes=60)
            
            return JsonResponse({'message': 'Data retrieved', 'user_token': user_token}, status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({'message': f'Error en la data {e}'}, status=status.HTTP_400_BAD_REQUEST)
        
    return JsonResponse({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
@jwt_required
def logout(request):
    if request.method == 'POST':
        return JsonResponse({'message': 'Logout Success'}, status=status.HTTP_200_OK)

    return JsonResponse({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

# * Metohds to be implemented


def generate_2fa_device(user: User) -> str:
    try:
        user = User.objects.get(id=user.id)
    except user.DoesNotExist:
        return None

    secret = pyotp.random_base32()
    
    totp_device = TOTPDevice.objects.create(user=user, name='auth device', key=secret)
    totp_device.save()
    
    totp = pyotp.TOTP(secret)
    opt_uri = totp.provisioning_uri(name=user.username, issuer_name='ECO-UNP')

    # img = qrcode.make(opt_uri)
    # img_io = BytesIO()
    # img.save(img_io, 'PNG')
    # img_io.seek(0)
    # img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

    twoFactorAuth = TwoFactorAuth.objects.create(user=user, secret=secret)
    twoFactorAuth.save()
    
    return opt_uri


def validate_2fa_device(user: User) -> bool:
    try:
        totp_device = TOTPDevice.objects.get(user=user, confirmed=True)
        if totp_device:
            return True
    except TOTPDevice.DoesNotExist:
        return False


def validate_recaptcha(user: User, token):
    response = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
        'secret': config('RECAPTCHA_SECRET_KEY'),
        'response': token
    })
    response_json = response.json()
    
    recaptcha = Recaptcha(user=user)
    recaptcha.set_encrypted_token(token)
    
    if response_json.get('success'):
        recaptcha.is_valid = True
    else:
        recaptcha.is_valid = False
        
    recaptcha.save()
    return recaptcha.is_valid


def generate_jwt_token(data: dict, exp_minutes: int = 60) -> str:
    issued_at = datetime.datetime.utcnow()
    expiration_time = issued_at + datetime.timedelta(minutes=exp_minutes)
    payload = {
        **data,
        'token_id': str(uuid.uuid4()),
        'iat': issued_at,
        'exp': expiration_time
    }
    token = jwt.encode(payload, config('TOKEN_SECRET_KEY'), algorithm='HS256')
    user_instance = User.objects.get(username=data.get('username'))

    token_instance = Token(user=user_instance)
    token_instance.set_encrypted_token(token)

    token_instance.save()

    return token


def generate_refresh_jwt_token(data: dict, exp_minutes: int = 60) -> str:
    issued_at = datetime.datetime.utcnow()
    expiration_time = issued_at + datetime.timedelta(minutes=exp_minutes)
    payload = {
        **data,
        'id_token': str(uuid.uuid4()),
        'iat': issued_at,
        'exp': expiration_time,
        'type': 'refresh'
    }
    token = jwt.encode(payload, config(
        'REFRESH_TOKEN_SECRET_KEY'), algorithm='HS256')

    refresh_token_instance = RefreshToken(user=data.get('user'))
    refresh_token_instance.set_encrypted_token(token)
    refresh_token_instance.save()

    return token


def save_session(user: User, session_id: str) -> None:
    session = Session.objects.create(user=user, session_id=session_id)
    session.save()
