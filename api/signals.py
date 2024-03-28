from .models import *
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender = Pregunta)
@receiver(post_delete, sender = Pregunta)
def actualizarCantidadNiveles(sender, instance, **kwargs):
    instancePregunta = instance.nivel
    instancePregunta.totalPreguntas = Pregunta.objects.filter(nivel = instancePregunta, estado = True).count()
    instancePregunta.save()

@receiver(post_save, sender = Nivel)
def nivelesPermitidos(sender, instance, created, **kwargs):
    if created:
        for usuario in Usuario.objects.all():
            if Progreso.objects.filter(usuario = usuario, lenguaje = instance.lenguaje).exists():
                progreso = Progreso.objects.get(usuario = usuario, lenguaje = instance.lenguaje)
                nivelesPermitidos = progreso.nivelesPermitidos
                nivelesPermitidos[instance.nombre] = False
                progreso.nivelesPermitidos = nivelesPermitidos
                progreso.save()