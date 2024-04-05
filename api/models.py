from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

# Create your models here.
class UsuarioManager(BaseUserManager):
    def create_user(self, correo, nombre, password, foto = None):
        usuario = self.model(
            nombre = nombre, 
            correo = self.normalize_email(correo)
        )
        usuario.set_password(password)
        usuario.save()
        return usuario

    def create_superuser(self, nombre, correo, password, foto = None):
        usuario = self.create_user(
            correo,
            nombre = nombre,
            password = password
        )
        usuario.administrador = True
        usuario.save()
        return usuario

class Usuario(AbstractBaseUser):
    foto = models.ImageField(upload_to = 'usuario/')
    nombre = models.CharField(max_length = 50)
    correo = models.EmailField(unique = True)
    racha = models.JSONField(default = {
        'Lunes': False, 'Martes': False,
        'Miercoles': False, 'Jueves': False,
        'Viernes': False, 'Sábado': False,
        'Domingo': False
    })
    estado = models.BooleanField(default = False)
    registro = models.DateField(auto_now_add = True)
    administrador = models.BooleanField(default = False)
    objects = UsuarioManager()
    USERNAME_FIELD = 'correo'
    REQUIRED_FIELDS = ['nombre', 'password']

    def str(self):
        return self.correo
    
    def has_perm(self, perm, obj = None):
        return True
    
    def has_module_perms(self, api_label):
        return True
    
    @property
    def is_staff(self):
        return self.administrador

class Lenguaje(models.Model):
    logo = models.ImageField(upload_to = 'lenguaje/')
    urlDocumentation = models.URLField(max_length = 2083)
    color = models.JSONField()
    nombre = models.CharField(max_length = 50, unique = True)
    estado = models.BooleanField(default = False)
    registro = models.DateField(auto_now_add = True)

class Nivel(models.Model):
    lenguaje = models.ForeignKey(Lenguaje, on_delete = models.CASCADE, limit_choices_to = {'estado': True})
    nombre = models.CharField(max_length = 50, unique = True)
    explanation = models.TextField()
    totalPreguntas = models.PositiveIntegerField(default = 0)
    estado = models.BooleanField(default = False)
    registro = models.DateField(auto_now_add = True)

class Pregunta(models.Model):
    nivel = models.ForeignKey(Nivel, on_delete = models.CASCADE, limit_choices_to = {'estado': True})
    explanation = models.TextField()
    pregunta = models.TextField()
    respuesta = models.JSONField()
    estado = models.BooleanField(default = False)
    registro = models.DateField(auto_now_add = True)

class Progreso(models.Model):
    usuario =  models.ForeignKey(Usuario, on_delete = models.CASCADE, limit_choices_to = {'estado': True})
    lenguaje = models.ForeignKey(Lenguaje, on_delete = models.CASCADE, limit_choices_to = {'estado': True})
    progresoLenguaje = models.FloatField(default = 0)
    puntos = models.PositiveIntegerField(default = 0)
    nivelesPermitidos = models.JSONField()
    registro = models.DateTimeField(auto_now = True)
    
class FotoPredeterminada(models.Model):
    foto = models.ImageField(upload_to = 'predeterminado/')
    registro = models.DateTimeField(auto_now_add = True)