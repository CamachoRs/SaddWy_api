from .models import *
from rest_framework import serializers

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['foto', 'nombre', 'correo', 'password', 'racha', 'registro']

class ProgresoSerializer(serializers.ModelSerializer):
    lenguajeNombre = serializers.SerializerMethodField()
    
    def get_lenguajeNombre(self, obj):
        return obj.lenguaje.nombre
    
    class Meta:
        model = Progreso
        fields = ['lenguajeNombre', 'progresoLenguaje']
    
class LenguajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lenguaje
        fields = ['logo', 'urlDocumentation', 'colorHexadecimal', 'nombre']

class NivelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nivel
        fields = ['nombre', 'explanation']

class PreguntaSerializer(serializers.ModelSerializer):
    nivel = serializers.SerializerMethodField()
   
    def get_nivel(self, obj):
        return {'nombre': obj.nivel.nombre, 'detalle': obj.nivel.explanation, 'preguntas': obj.nivel.totalPreguntas}

    class Meta:
        model = Pregunta
        fields = ['nivel', 'explanation', 'pregunta', 'respuesta']

class CartaSerializer(serializers.ModelSerializer):
    niveles = serializers.SerializerMethodField()
  
    def get_niveles(self, obj):
        niveles = obj.nivel_set.filter(estado = True)
        nivelData = NivelSerializer(niveles, many = True).data
        usuario = self.context['request'].user
        nivelesPermitidos = Progreso.objects.get(usuario = usuario, lenguaje = obj).nivelesPermitidos

        for nivel in nivelData:
            nombre = nivel['nombre']
            nivel['permitido'] = nivelesPermitidos.get(nombre)

        if nivelData:
            nivelData[-1].pop('nivelesPermitidos', None)

        return nivelData
    
    class Meta:
        model = Lenguaje
        fields = ['logo', 'urlDocumentation', 'colorHexadecimal', 'nombre', 'niveles']