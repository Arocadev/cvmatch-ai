from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from cryptography.fernet import Fernet
import base64


def _fernet():
    key = settings.ENCRYPTION_KEY
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    foto = models.BinaryField(blank=True, null=True)
    foto_mime = models.CharField(max_length=20, blank=True, default='image/jpeg')
    groq_token_cifrado = models.BinaryField(blank=True, null=True)

    # ── Token Groq ────────────────────────────────────────────────────────────
    def set_groq_token(self, token_plano: str):
        """Cifra y guarda el token. Llama a save() después."""
        if token_plano:
            self.groq_token_cifrado = _fernet().encrypt(token_plano.strip().encode())
        else:
            self.groq_token_cifrado = None

    def get_groq_token(self) -> str | None:
        """Devuelve el token descifrado, o None si no existe."""
        if not self.groq_token_cifrado:
            return None
        try:
            raw = bytes(self.groq_token_cifrado)
            return _fernet().decrypt(raw).decode()
        except Exception:
            return None

    @property
    def tiene_groq_token(self) -> bool:
        return bool(self.groq_token_cifrado)

    # ── Foto ──────────────────────────────────────────────────────────────────
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
    resumen_ia = models.TextField(blank=True, null=True)  # cache del resumen IA

    def __str__(self):
        return f"{self.titulo} - {self.empresa}"