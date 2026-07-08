from django.db import models
from django.contrib.auth.models import User
import base64

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    foto = models.BinaryField(blank=True, null=True)
    foto_mime = models.CharField(max_length=20, blank=True, default='image/jpeg')

    def foto_base64(self):
        if self.foto:
            return base64.b64encode(bytes(self.foto)).decode('utf-8')
        return None

    def __str__(self):
        return f"Perfil de {self.user.username}"

class CVUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cvs')
    nombre = models.CharField(max_length=100)
    texto = models.TextField()
    fecha_subida = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} — {self.usuario.username}"

class Oferta(models.Model):
    ESTADOS = [
        ('nueva', 'Nueva'),
        ('vista', 'Vista'),
        ('guardada', 'Guardada'),
        ('descartada', 'Descartada'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ofertas')
    titulo = models.CharField(max_length=255)
    empresa = models.CharField(max_length=255)
    ubicacion = models.CharField(max_length=255, blank=True)
    descripcion = models.TextField(blank=True)
    url_original = models.URLField()
    fecha_publicacion = models.DateField(null=True, blank=True)
    fecha_guardada = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='nueva')
    fuente = models.CharField(max_length=50, default='adzuna')

    def __str__(self):
        return f"{self.titulo} - {self.empresa}"