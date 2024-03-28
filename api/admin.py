from .models import *
from django.contrib import admin

# Register your models here.
class FotoPredeterminadaAdmin(admin.ModelAdmin):
    list_display = ['id', 'foto', 'registro']

class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['id', 'foto', 'nombre', 'correo', 'password', 'racha', 'estado', 'registro', 'administrador']

class LenguajeAdmin(admin.ModelAdmin):
    list_display = ['id', 'logo', 'urlDocumentation', 'colorHexadecimal', 'nombre', 'estado', 'registro']

class NivelAdmin(admin.ModelAdmin):
    list_display = ['id', 'lenguaje', 'nombre', 'explanation', 'totalPreguntas', 'estado', 'registro']

class PreguntaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nivel', 'explanation', 'pregunta', 'respuesta', 'estado', 'registro']

class ProgresoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'lenguaje', 'progresoLenguaje', 'puntos', 'nivelesPermitidos', 'registro']

admin.site.register(FotoPredeterminada, FotoPredeterminadaAdmin)
admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Lenguaje, LenguajeAdmin)
admin.site.register(Nivel, NivelAdmin)
admin.site.register(Pregunta, PreguntaAdmin)
admin.site.register(Progreso, ProgresoAdmin)