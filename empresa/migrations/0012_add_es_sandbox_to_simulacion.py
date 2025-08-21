from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresa', '0011_simulaciones_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='simulacionusuario',
            name='es_sandbox',
            field=models.BooleanField(default=False, help_text='Indica si la simulación se ejecutó en modo sandbox'),
        ),
    ]
