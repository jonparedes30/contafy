from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('empresa', '0008_add_pasos_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='PasoCompletado',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('paso_index', models.IntegerField()),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('leccion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empresa.leccion')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Paso Completado',
                'verbose_name_plural': 'Pasos Completados',
                'unique_together': {('usuario', 'leccion', 'paso_index')},
            },
        ),
    ]
