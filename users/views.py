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
import qrcode
from io import BytesIO
from django.contrib.auth.models import User
from django_otp.plugins.otp_totp.models import TOTPDevice

# Create your views here.
@api_view(['POST'])
def auth(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # * Validate Recaptcha
        token = data.get('recaptcha')
        if not token:
            return JsonResponse({'message': 'Recaptcha token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        isValidate = validate_recaptcha(token)
        if not isValidate:
            return JsonResponse({'message': 'Recaptcha validation failed'}, status=status.HTTP_400_BAD_REQUEST)
        
        # * Validate User and Password
        user = data.get('user')
        password = data.get('password')
        
        if not user or not password:
            return JsonResponse({'message': 'User and Password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        result = authenticate(username=user, password=password)
        if not result:
            return JsonResponse({'message': 'Invalid User or Password'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # TODO: Validate or generate 2FA Device
        is_2fa_required = validate_2fa_device(result)
        if not is_2fa_required:
            qr_code = generate_2fa_code(result)
        
        return JsonResponse({'message': 'Login Success', 'twoFARequired': True, 'qr_code': qr_code}, status=status.HTTP_200_OK)
        
    return JsonResponse({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
def two_factor_auth(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        code = data.get('code2fa')
        
        if not code:
            return JsonResponse({'message': 'Code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # TODO: Implement 2FA validation
        
        
        # * Generate JWT Token
        access_token = generate_jwt_token(data={'user': 'user'}, exp_minutes = 60)
        
        return JsonResponse({'message': 'Login Success', 'access_token': access_token}, status=status.HTTP_200_OK)
    
    return JsonResponse({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
def external_logout(request):
    if request.method == 'POST':
        return JsonResponse({'message': 'Logout Success'}, status=status.HTTP_200_OK)
    
    return JsonResponse({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

# * Metohds to be implemented

def generate_2fa_code(user: User) -> str:
    try:
        user = User.objects.get(id=user.id)
    except user.DoesNotExist:
        return None
    
    totp_device = TOTPDevice.objects.create(user=user, name='auth device')
    totp_device.save()
    secret = totp_device.secret
    totp = pyotp.TOTP(secret)
    opt_uri = totp.provisioning_uri(name=user.username, issuer_name='auth')
    
    img = qrcode.make(opt_uri)
    img_io = BytesIO()
    img.save(img_io)
    img_io.seek(0)
    
    return JsonResponse({'message': 'QR Code generated', 'qr_code': img_io}, status=status.HTTP_200_OK)

def validate_2fa_device(user: User) -> bool:
    # TODO: Retorn device if exists
    try:
        totp_device = TOTPDevice.objects.get(user=user, confirmed=False)
        if totp_device:
            return True
    except TOTPDevice.DoesNotExist:
        return False

def validate_recaptcha(token):
    response = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
        'secret': config('RECAPTCHA_SECRET_KEY'),
        'response': token
    })
    response_json = response.json()
    if response_json.get('success'):
        return True
    else:
        return False
    
def generate_jwt_token(data: dict, exp_minutes: int = 60) -> str:
    issued_at = datetime.datetime.utcnow()
    expiration_time = issued_at + datetime.timedelta(minutes=exp_minutes)
    payload = {
        **data,
        'id_token': str(uuid.uuid4()),
        'iat': issued_at,
        'exp': expiration_time
    }
    token = jwt.encode(payload, config('TOKEN_SECRET_KEY'), algorithm='HS256')
    return token