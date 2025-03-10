import json
import requests
import datetime
import uuid
import jwt
import pyotp
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.decorators import api_view
from decouple import config
from django.contrib.auth.models import User
from django_otp.plugins.otp_totp.models import TOTPDevice
from custom_auth.models.models_global import Session, TwoFactorAuth, Recaptcha, Token, RefreshToken, Blacklist
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

        user_instance = User.objects.get(username=username)

        existe_session = Session.objects.filter(
            user=user_instance, is_active=True).exists()
        if existe_session:
            return JsonResponse({'message': 'Session active in other device'}, status=status.HTTP_400_BAD_REQUEST)

        # * Validate Code and Generate JWT
        try:
            totp_device = TOTPDevice.objects.get(
                user_id=user_instance, confirmed=True)
            totp = pyotp.TOTP(totp_device.key)

            if not totp.verify(code):
                return JsonResponse({'message': 'Invalid code'}, status=status.HTTP_400_BAD_REQUEST)

            access_token = generate_jwt_token(data={'username': username, 'address': request.META.get(
                'REMOTE_ADDR'), 'type': 'access', 'user_type': 'external'}, exp_minutes=60)

            response = JsonResponse(
                {'message': 'Login Success'}, status=status.HTTP_200_OK)

            response.set_cookie(
                key='access_token',
                value=access_token,
                max_age=60 * 60,
                expires=1,
                secure=False,
                httponly=True,
                samesite='Lax',
                path='/'
            )

            save_session(user_instance)

            return response

        except TOTPDevice.DoesNotExist:
            return JsonResponse({'message': 'User has no device'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return JsonResponse({'message': f'Internal Server Error: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JsonResponse({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
def microsoft_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        access_token = data.get('access_token')

        response = JsonResponse(
        {'message': 'Login Success'}, status=status.HTTP_200_OK)

        response.set_cookie(
            key='access_token',
            value=access_token,
            max_age=60 * 60,
            expires=1,
            secure=False,
            httponly=True,
            samesite='Lax',
            path='/'
        )
        
        return response

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
def validate(request):
    if request.method == 'POST':
        try:
            user_info = request.user
            if user_info:
                return JsonResponse({'message': 'JWT validated'}, status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
@jwt_required
def logout(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')

        if not username:
            return JsonResponse({'message': 'Code or user is required'}, status=status.HTTP_400_BAD_REQUEST)

        user_instance = User.objects.get(username=username)

        existe_session = Session.objects.filter(
            user=user_instance, is_active=True).exists()
        if existe_session:
            session_instance = Session.objects.filter(
                user=user_instance, is_active=True)
            session_instance.is_active = False
            session_instance.save()

        response = JsonResponse(
            {'message': 'Logout Success'}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        return response

    return JsonResponse({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

# * Metohds to be implemented


def generate_2fa_device(user: User) -> str:
    try:
        user = User.objects.get(id=user.id)
    except user.DoesNotExist:
        return None

    secret = pyotp.random_base32()

    totp_device = TOTPDevice.objects.create(
        user=user, name='auth device', key=secret)
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
    response = requests.post(config('RECAPTCHA_API'), data={
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


def save_session(user: User) -> bool:
    try:
        session = Session.objects.create(user=user)
        session.save()
        return True
    except:
        return False
