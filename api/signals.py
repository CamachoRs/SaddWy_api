from .models import *
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender = Pregunta)
@receiver(post_delete, sender = Pregunta)
def actualizarCantidadNiveles(sender, instance, **kwargs):
    instancePregunta = instance.nivel
    instancePregunta.totalPreguntas = Pregunta.objects.filter(nivel = instancePregunta, estado = True).count()
    instancePregunta.save()