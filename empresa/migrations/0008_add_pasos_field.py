from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresa', '0007_learning_system'),
    ]

    operations = [
        migrations.AddField(
            model_name='leccion',
            name='pasos',
            field=models.TextField(blank=True, null=True, help_text='JSON con pasos si JSONField no disponible'),
        ),
    ]
