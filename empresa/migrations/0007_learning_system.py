# Generated migration for learning system
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('empresa', '0006_codigoinvitacion_tiposervicio_materialservicio'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModuloAprendizaje',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('tipo_empresa', models.CharField(choices=[('comercial', 'Comercial'), ('manufactura', 'Manufactura'), ('servicios', 'Servicios')], max_length=20)),
                ('nivel', models.IntegerField(default=1)),
                ('descripcion', models.TextField()),
                ('icono', models.CharField(default='fas fa-book', max_length=50)),
                ('orden', models.IntegerField(default=1)),
                ('activo', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Leccion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200)),
                ('tipo', models.CharField(choices=[('teoria', 'Teoría'), ('practica', 'Práctica'), ('simulacion', 'Simulación'), ('quiz', 'Quiz')], default='teoria', max_length=20)),
                ('contenido', models.TextField()),
                ('puntos_xp', models.IntegerField(default=10)),
                ('tiempo_estimado', models.IntegerField(default=5)),
                ('orden', models.IntegerField(default=1)),
                ('activa', models.BooleanField(default=True)),
                ('modulo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lecciones', to='empresa.moduloaprendizaje')),
            ],
        ),
        migrations.CreateModel(
            name='PerfilAprendizaje',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nivel', models.IntegerField(default=1)),
                ('xp_total', models.IntegerField(default=0)),
                ('racha_dias', models.IntegerField(default=0)),
                ('ultima_actividad', models.DateField(auto_now=True)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil_aprendizaje', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ProgresoUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completada', models.BooleanField(default=False)),
                ('puntuacion', models.IntegerField(default=0)),
                ('intentos', models.IntegerField(default=0)),
                ('tiempo_completado', models.DateTimeField(blank=True, null=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('leccion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empresa.leccion')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='progresousuario',
            unique_together={('usuario', 'leccion')},
        ),
    ]