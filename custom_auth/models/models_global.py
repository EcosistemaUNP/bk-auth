import uuid
from django.db import models
from django.contrib.auth.models import User
from decouple import config
from cryptography.fernet import Fernet

# * Modelos de autenticación


class Session(models.Model):
    id_session = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'eco_auth_session'
        verbose_name_plural = 'sesiones del usuario'

    def __str__(self):
        return str(self.id_session)


class TwoFactorAuth(models.Model):
    id_tfactor = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    secret = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'eco_auth_two_factor_auth'
        verbose_name_plural = 'dos factores de autenticación'

    def __str__(self):
        return str(self.id_tfactor)


class Recaptcha(models.Model):
    id_recaptcha = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.BinaryField()
    is_valid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'eco_auth_recaptcha'
        verbose_name_plural = 'recaptcha'

    def set_encrypted_token(self, token):
        fernet = Fernet(config('FERNET_SECRET_KEY'))
        encrypted_token = fernet.encrypt(token.encode())
        self.token = encrypted_token

    def get_decrypted_token(self):
        fernet = Fernet(config('FERNET_SECRET_KEY'))
        decrypted_token = fernet.decrypt(self.token)
        return decrypted_token.decode()

    def __str__(self):
        return str(self.id_recaptcha)


class Token(models.Model):
    id_token = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.BinaryField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'eco_auth_token'
        verbose_name_plural = 'token'

    def set_encrypted_token(self, token):
        fernet = Fernet(config('FERNET_SECRET_KEY'))
        encrypted_token = fernet.encrypt(token.encode())
        self.token = encrypted_token

    def get_decrypted_token(self):
        fernet = Fernet(config('FERNET_SECRET_KEY'))
        decrypted_token = fernet.decrypt(self.token)
        return decrypted_token.decode()

    def __str__(self):
        return str(self.id_token)


class RefreshToken(models.Model):
    id_rtoken = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.BinaryField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'eco_auth_refresh_token'
        verbose_name_plural = 'token de refresco'

    def set_encrypted_token(self, token):
        fernet = Fernet(config('FERNET_SECRET_KEY'))
        encrypted_token = fernet.encrypt(token.encode())
        self.token = encrypted_token

    def get_decrypted_token(self):
        fernet = Fernet(config('FERNET_SECRET_KEY'))
        decrypted_token = fernet.decrypt(self.token)
        return decrypted_token.decode()

    def __str__(self):
        return str(self.id_rtoken)


class Blacklist(models.Model):
    id_blist = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    token = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'eco_auth_blacklist'
        verbose_name_plural = 'lista negra'

    def set_encrypted_token(self, token):
        fernet = Fernet(config('FERNET_SECRET_KEY'))
        encrypted_token = fernet.encrypt(token.encode())
        self.token = encrypted_token

    def get_decrypted_token(self):
        fernet = Fernet(config('FERNET_SECRET_KEY'))
        decrypted_token = fernet.decrypt(self.token)
        return decrypted_token.decode()

    def __str__(self):
        return str(self.id_blist)
