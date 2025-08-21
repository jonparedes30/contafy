from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('empresa', '0010_add_gamificacion_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoSimulacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('categoria', models.CharField(max_length=20)),
                ('descripcion', models.TextField()),
                ('icono', models.CharField(max_length=50, default='fas fa-play-circle')),
                ('configuracion', models.JSONField(default=dict)),
                ('activo', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='SimulacionUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(default='iniciada', max_length=20)),
                ('datos_entrada', models.JSONField(default=dict)),
                ('resultado', models.JSONField(default=dict)),
                ('puntuacion', models.IntegerField(default=0)),
                ('tiempo_completado', models.IntegerField(default=0)),
                ('fecha_inicio', models.DateTimeField(auto_now_add=True)),
                ('fecha_completado', models.DateTimeField(null=True, blank=True)),
                ('tipo_simulacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empresa.tiposimulacion')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empresa.usuario', related_name='simulaciones')),
                ('leccion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empresa.leccion', null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='EscenarioSimulacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField()),
                ('datos_iniciales', models.JSONField(default=dict)),
                ('solucion_esperada', models.JSONField(default=dict)),
                ('dificultad', models.IntegerField(default=1)),
                ('puntos_max', models.IntegerField(default=100)),
                ('activo', models.BooleanField(default=True)),
                ('tipo_simulacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empresa.tiposimulacion', related_name='escenarios')),
            ],
        ),
    ]
