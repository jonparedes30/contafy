# Generated migration for social features (Phase 5)

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('empresa', '0012_add_es_sandbox_to_simulacion'),
    ]

    operations = [
        migrations.CreateModel(
            name='Liga',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('fecha_inicio', models.DateTimeField()),
                ('fecha_fin', models.DateTimeField()),
                ('activa', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['-fecha_inicio'],
            },
        ),
        migrations.CreateModel(
            name='Reto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('lecciones', 'Completar Lecciones'), ('xp', 'Ganar XP'), ('simulaciones', 'Completar Simulaciones')], max_length=20)),
                ('objetivo', models.IntegerField()),
                ('fecha_limite', models.DateTimeField()),
                ('completado_creador', models.BooleanField(default=False)),
                ('completado_retado', models.BooleanField(default=False)),
                ('activo', models.BooleanField(default=True)),
                ('creador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='retos_creados', to=settings.AUTH_USER_MODEL)),
                ('ganador', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('retado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='retos_recibidos', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ParticipanteLiga',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('xp_inicial', models.IntegerField(default=0)),
                ('xp_ganada', models.IntegerField(default=0)),
                ('posicion', models.IntegerField(blank=True, null=True)),
                ('liga', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participantes', to='empresa.liga')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('liga', 'usuario')},
            },
        ),
        migrations.CreateModel(
            name='LogroCompartido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mensaje', models.TextField(blank=True)),
                ('fecha_compartido', models.DateTimeField(auto_now_add=True)),
                ('likes', models.ManyToManyField(blank=True, related_name='likes_logros', to=settings.AUTH_USER_MODEL)),
                ('logro_usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empresa.logrousuario')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-fecha_compartido'],
            },
        ),
    ]