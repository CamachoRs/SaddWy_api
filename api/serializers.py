from django.conf import settings
from .models import *
from rest_framework import serializers

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['foto', 'nombre', 'correo', 'password', 'racha', 'registro', 'administrador']

class ProgresoSerializer(serializers.ModelSerializer):
    lenguajeLogo = serializers.SerializerMethodField()
    lenguajeNombre = serializers.SerializerMethodField()
    
    def get_lenguajeLogo(self, obj):
        return f'http://127.0.0.1:8000{obj.lenguaje.logo.url}'
    
    def get_lenguajeNombre(self, obj):
        return obj.lenguaje.nombre
    
    class Meta:
        model = Progreso
        fields = ['lenguajeLogo', 'lenguajeNombre', 'progresoLenguaje']
    
class LenguajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lenguaje
        fields = ['logo', 'urlDocumentation', 'color', 'nombre']

class NivelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nivel
        fields = ['id', 'nombre', 'explanation']

class PreguntaSerializer(serializers.ModelSerializer):
    nivel = serializers.SerializerMethodField()
   
    def get_nivel(self, obj):
        return {'nombre': obj.nivel.nombre, 'detalle': obj.nivel.explanation, 'preguntas': obj.nivel.totalPreguntas}

    class Meta:
        model = Pregunta
        fields = ['nivel', 'explanation', 'pregunta', 'respuesta']

class CartaSerializer(serializers.ModelSerializer):
    niveles = NivelSerializer(many = True, read_only = True, source = 'nivel_set')
    
    class Meta:
        model = Lenguaje
        fields = ['logo', 'urlDocumentation', 'color', 'nombre', 'niveles']
    
class ContactarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contactar
        fields = '__all__'

class UsuarioSerializerAdmin(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'

class LenguajeSerializerAdmin(serializers.ModelSerializer):
    class Meta:
        model = Lenguaje
        fields = '__all__'

class NivelSerializerAdmin(serializers.ModelSerializer):
    lenguajeNombre = serializers.SerializerMethodField()
    
    def get_lenguajeNombre(self, obj):
        return obj.lenguaje.nombre

    class Meta:
        model = Nivel
        fields = ['id', 'nombre', 'explanation', 'totalPreguntas', 'estado', 'registro', 'lenguaje', 'lenguajeNombre']

class PreguntaSerializerAdmin(serializers.ModelSerializer):
    nivelNombre = serializers.SerializerMethodField()
    
    def get_nivelNombre(self, obj):
        return obj.nivel.nombre
    
    class Meta:
        model = Pregunta
        fields = ['id', 'explanation', 'pregunta', 'respuesta', 'estado', 'registro', 'nivel', 'nivelNombre']

class ProgresoSerializerAdmin(serializers.ModelSerializer):
    usuarioNombre = serializers.SerializerMethodField()
    lenguajeNombre = serializers.SerializerMethodField()

    def get_usuarioNombre(self, obj):
        return obj.usuario.nombre
    
    def get_lenguajeNombre(self, obj):
        return obj.lenguaje.nombre

    class Meta:
        model = Progreso
        fields = ['id', 'usuario', 'usuarioNombre', 'lenguaje', 'lenguajeNombre', 'progresoLenguaje', 'puntos', 'nivelesPermitidos', 'registro']

class FotoSerializerAdmin(serializers.ModelSerializer):
    class Meta:
        model = FotoPredeterminada
        fields = '__all__'