from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ofertas', '0005_userprofile_foto_mime_alter_userprofile_foto'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='groq_token_cifrado',
            field=models.BinaryField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='oferta',
            name='resumen_ia',
            field=models.TextField(blank=True, null=True),
        ),
    ]