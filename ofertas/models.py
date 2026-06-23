from django.db import models

class Oferta(models.Model):
    titulo = models.CharField(max_length=255)
    empresa = models.CharField(max_length=255)
    ubicacion = models.CharField(max_length=255, blank=True)
    descripcion = models.TextField(blank=True)
    url_original = models.URLField()
    fecha_publicacion = models.DateField(null=True, blank=True)
    fecha_guardada = models.DateTimeField(auto_now_add=True)
    vista = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.titulo} - {self.empresa}"