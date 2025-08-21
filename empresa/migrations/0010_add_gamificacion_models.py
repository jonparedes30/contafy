from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('empresa', '0009_paso_completado'),
    ]

    operations = [
        migrations.CreateModel(
            name='Logro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField()),
                ('icono', models.CharField(default='fas fa-trophy', max_length=50)),
                ('tipo', models.CharField(choices=[('completar_modulo', 'Completar Módulo'), ('racha_dias', 'Racha de Días'), ('puntos_xp', 'Puntos XP'), ('primera_vez', 'Primera Vez'), ('maestria', 'Maestría')], max_length=20)),
                ('condicion_valor', models.IntegerField(help_text='Valor necesario para desbloquear')),
                ('puntos_xp_premio', models.IntegerField(default=50)),
                ('activo', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Logro',
                'verbose_name_plural': 'Logros',
            },
        ),
        migrations.CreateModel(
            name='LogroUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('desbloqueado_en', models.DateTimeField(auto_now_add=True)),
                ('notificado', models.BooleanField(default=False)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logros_obtenidos', to=settings.AUTH_USER_MODEL)),
                ('logro', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empresa.logro')),
            ],
            options={
                'unique_together': {('usuario', 'logro')},
                'verbose_name': 'Logro de Usuario',
                'verbose_name_plural': 'Logros de Usuarios',
            },
        ),
        migrations.CreateModel(
            name='ActividadDiaria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('lecciones_completadas', models.IntegerField(default=0)),
                ('xp_ganada', models.IntegerField(default=0)),
                ('tiempo_estudiado', models.IntegerField(default=0)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actividades_diarias', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('usuario', 'fecha')},
                'verbose_name': 'Actividad Diaria',
                'verbose_name_plural': 'Actividades Diarias',
            },
        ),
        migrations.CreateModel(
            name='Insignia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField()),
                ('icono', models.CharField(default='fas fa-medal', max_length=50)),
                ('categoria', models.CharField(choices=[('comercial', 'Comercial'), ('manufactura', 'Manufactura'), ('servicios', 'Servicios'), ('general', 'General')], default='general', max_length=20)),
                ('color', models.CharField(default='#FFD700', help_text='Color hex de la insignia', max_length=7)),
                ('requisito_xp', models.IntegerField(default=100)),
                ('activa', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Insignia',
                'verbose_name_plural': 'Insignias',
            },
        ),
        migrations.CreateModel(
            name='InsigniaUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('obtenida_en', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='insignias_obtenidas', to=settings.AUTH_USER_MODEL)),
                ('insignia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empresa.insignia')),
            ],
            options={
                'unique_together': {('usuario', 'insignia')},
                'verbose_name': 'Insignia de Usuario',
                'verbose_name_plural': 'Insignias de Usuarios',
            },
        ),
    ]
