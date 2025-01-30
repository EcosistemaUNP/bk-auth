import uuid
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import User
from users.models.models_static import Pais, Departamento, Municipio, ZonaUbicacion, TipoIdentificacion, TipoSexo, TipoGenero, TipoOrientacionSexual, GpRh, EstadoCivil, FondoPensiones, Eps, TipoVinculacion, Dependencia, Grupo, Rol
from decouple import config
from cryptography.fernet import Fernet

# * Modelos de usuarios

class TelefonoCelularContactoUsuario(models.Model):
    id_ctelefono = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    celular_uno = models.CharField(max_length=15, blank=True, null=True)
    celular_dos = models.CharField(max_length=15, blank=True, null=True)
    celular_emergencia = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        db_table = 'eco_usr_ctelefono'
        verbose_name_plural = 'Datos de contacto'

    def __str__(self):
        return str(self.id_ctelefono)

class CorreoElectronicoContactoUsuario(models.Model):
    id_ccelectronico = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    correo_electronico = models.EmailField(max_length=100)

    class Meta:
        db_table = 'eco_usr_ccelectronico'
        verbose_name_plural = 'Datos de contacto'

    def __str__(self):
        return str(self.id_ccelectronico)

class DatosContactoUsuario(models.Model):
    id_contacto = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_ctelefono = models.ForeignKey(TelefonoCelularContactoUsuario, to_field='id_ctelefono', on_delete=models.CASCADE)
    id_ccelectronico = models.ForeignKey(CorreoElectronicoContactoUsuario, to_field='id_ccelectronico', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True, null=True)
    object_id = models.CharField(blank=True, null=True, max_length=50)

    class Meta:
        db_table = 'eco_usr_contacto'
        verbose_name_plural = 'Datos de contacto'

    def __str__(self):
        return str(self.id_contacto)

class DatosUbicacionUsuario(models.Model):
    id_ubicacion = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pais = models.ForeignKey(Pais, to_field='id_pais',on_delete=models.CASCADE)
    departamento = models.ForeignKey(Departamento, to_field='id_departamento', on_delete=models.CASCADE)
    municipio = models.ForeignKey(Municipio, to_field='id_municipio', on_delete=models.CASCADE)
    zona = models.ForeignKey(ZonaUbicacion, to_field='id_zubicacion', on_delete=models.CASCADE)
    direccion = models.CharField(max_length=160, blank=True, null=True)
    indicacion = models.CharField(max_length=160, blank=True, null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True, null=True)
    object_id = models.CharField(blank=True, null=True, max_length=50)

    class Meta:
        db_table = 'eco_usr_ubicacion'
        verbose_name_plural = 'Datos de ubicación'

    def __str__(self):
        return str(self.id_ubicacion)

class UbicacionRural(DatosUbicacionUsuario):
    corregimiento = models.CharField(max_length=150, null=True, blank=True)
    centro_poblado = models.CharField(max_length=150, null=True, blank=True)
    vereda = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return self.direccion

    class Meta:
        db_table = 'eco_usr_direccionrural'
        verbose_name_plural = 'Dirección rural'

class UbicacionUrbana(DatosUbicacionUsuario):
    nombre_barrio = models.CharField(max_length=100, null=True, blank=True)
    tipo_viaprincipal = models.CharField(max_length=20, null=True, blank=True)
    numero_viaprincipal = models.IntegerField(null=True, blank=True)
    letra_principal = models.CharField(max_length=10, null=True, blank=True)
    es_bis = models.BooleanField(null=True)
    cuadrante_principal = models.CharField( max_length=10, null=True, blank=True)
    numero_viasecundaria = models.IntegerField(null=True, blank=True)
    letra_secundaria = models.CharField(max_length=10, null=True, blank=True)
    cuadrante_secundario = models.CharField(max_length=10, null=True, blank=True)
    numero_placa = models.IntegerField(null=True, blank=True)
    complemento = models.CharField(max_length=60, null=True, blank=True)

    def __str__(self):
        fields = [
            self.tipo_viaprincipal, self.numero_viaprincipal, self.letra_principal,
            self.cuadrante_principal, self.numero_viasecundaria, self.letra_secundaria, self.numero_placa,
            self.cuadrante_secundario, self.complemento]

        fields = [str(field) for field in fields if field]
        return " ".join(fields)

    class Meta:
        db_table = 'eco_usr_direccionurbana'
        verbose_name_plural = 'Dirección urbana'
        
class IdentificacionUsuario(models.Model):
    id_iusuario = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_identificacion = models.CharField(max_length=20, null=False, blank=True)
    fecha_expedicion = models.DateField()
    tipo_identificacion = models.ForeignKey(TipoIdentificacion, to_field='id_tidentificacion', on_delete=models.CASCADE)

    class Meta:
        db_table = 'eco_usr_iusuario'
        verbose_name_plural = 'Datos de la identificación del usuario'

    def __str__(self):
        return str(self.numero_identificacion) + str(self.fecha_expedicion)

class NombrePersonaUsuario(models.Model):
    id_npersona = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    primer_nombre = models.CharField(max_length=20, null=False, blank=False)
    segundo_nombre = models.CharField(max_length=50, null=True, blank=True)
    primer_apellido = models.CharField(max_length=50, null=False, blank=False)
    segundo_apellido = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'eco_usr_nombrepersona'
        verbose_name_plural = 'Nombres y apellidos de las personas'

    def __str__(self):
        return str(self.id_npersona) + str(self.primer_nombre)

class DatosBasicosUsuario(models.Model):
    id_busuario = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identificacion_usuario = models.ForeignKey(IdentificacionUsuario, to_field='id_iusuario', on_delete=models.CASCADE)
    nombre_persona = models.ForeignKey(NombrePersonaUsuario, to_field='id_npersona',  on_delete=models.CASCADE)
    sexo_persona = models.ForeignKey(TipoSexo, to_field='id_tsexo', on_delete=models.CASCADE, null=True)
    genero_persona = models.ForeignKey(TipoGenero, to_field='id_tgenero', on_delete=models.CASCADE, null=True)
    orientacion_persona = models.ForeignKey(TipoOrientacionSexual, to_field='id_torientacion', on_delete=models.CASCADE, null=True)
    gp_rh = models.ForeignKey(GpRh, to_field='id_grh',on_delete=models.CASCADE, null=True)
    ubicacion_persona = GenericRelation(DatosUbicacionUsuario)
    contacto_persona = GenericRelation(DatosContactoUsuario)

    class Meta:
        db_table = 'eco_usr_basicosusuario'
        verbose_name_plural = 'Datos básicos del usuario'

    def __str__(self):
        return str(self.id_busuario)

class DatosComplementariosUsuario(models.Model):
    id_cusuario = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    estado_civil = models.ForeignKey(EstadoCivil, to_field='id_ecivil', on_delete=models.CASCADE, null=True)
    fondo_pensiones = models.ForeignKey(FondoPensiones, to_field='id_fpensiones', on_delete=models.CASCADE, null=True)
    eps = models.ForeignKey(Eps, to_field='id_eps', on_delete=models.CASCADE, null=True)
    tipo_vinculacion = models.ForeignKey(TipoVinculacion, to_field='id_tvinculacion', on_delete=models.CASCADE, null=True, blank=True)
    acepto_politicas = models.BooleanField(default=False)
    basicos_usuario = models.ForeignKey(DatosBasicosUsuario, to_field='id_busuario', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        db_table = 'eco_usr_complementariosusuario'
        verbose_name_plural = 'Datos básicos del usuario'

    def __str__(self):
        return str(self.id_cusuario)

class ContratoContratista(models.Model):
    id_contrato = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_contrato = models.CharField(max_length=10, blank=True, null=True)
    fecha_iniciocontrato = models.DateField(blank=True, null=True)
    fecha_fincontrato = models.DateField(blank=True, null=True)
    complementario_usuario = models.ForeignKey(DatosComplementariosUsuario, to_field='id_cusuario', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = 'eco_usr_datoscontrato'
        verbose_name_plural = 'Datos básicos del contrato'

    def __str__(self):
        return str(self.id_contrato)

class ResolucionFuncionario(models.Model):
    id_resolucion = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_resolucion = models.CharField(max_length=30, blank=True, null=True)
    complementario_usuario = models.ForeignKey(DatosComplementariosUsuario, to_field='id_cusuario', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = 'eco_usr_datosresolucion'
        verbose_name_plural = 'Datos básicos de la resolucion del contratista'

    def __str__(self):
        return str(self.id_resolucion)
    
class PerfilUsuario(models.Model):
    id_pusuario = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.CharField(max_length=100, unique=True)
    dependencia = models.ForeignKey(Dependencia, to_field='id_dependencia', on_delete=models.CASCADE, null=True)
    grupo = models.ForeignKey(Grupo, to_field='id_grupo', on_delete=models.CASCADE, null=True)
    rol = models.ForeignKey(Rol, to_field='id_rol', on_delete=models.CASCADE, null=True)
    basicos_usuario = models.ForeignKey(DatosBasicosUsuario, to_field='id_busuario', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = 'eco_usr_perfilusuario'
        verbose_name_plural = 'perfil del usuario'

    def __str__(self):
        return str(self.id_pusuario)

# * Modelos de autenticación

class Session(models.Model):
    id_session = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'eco_auth_session'
        verbose_name_plural = 'sesiones del usuario'

    def __str__(self):
        return str(self.id_session)


class TwoFactorAuth(models.Model):
    id_tfactor = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    id_recaptcha = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    id_token = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    id_rtoken = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    id_blist = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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