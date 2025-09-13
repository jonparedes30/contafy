# Generated manually for Academia UX Duolingo

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('empresa', '0019_leccion_dificultad_leccion_visible_and_more'),
    ]

    operations = [
        # Add slug fields to ModuloAprendizaje
        migrations.AddField(
            model_name='moduloaprendizaje',
            name='slug',
            field=models.SlugField(max_length=120, unique=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='moduloaprendizaje',
            name='visible',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='moduloaprendizaje',
            name='creado_en',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='moduloaprendizaje',
            name='actualizado_en',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Add slug field to Leccion
        migrations.AddField(
            model_name='leccion',
            name='slug',
            field=models.SlugField(max_length=220, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='leccion',
            name='creado_en',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='leccion',
            name='actualizado_en',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Create AsientoAudit model
        migrations.CreateModel(
            name='AsientoAudit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cuenta', models.CharField(max_length=100)),
                ('tipo_cuenta', models.CharField(max_length=20)),
                ('tipo_movimiento', models.CharField(max_length=10)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=12)),
                ('descripcion', models.TextField()),
                ('transaccion_id', models.CharField(max_length=50)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('simulacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asientos_audit', to='empresa.simulacionusuario')),
            ],
            options={
                'verbose_name': 'Asiento Audit',
                'verbose_name_plural': 'Asientos Audit',
            },
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='moduloaprendizaje',
            index=models.Index(fields=['tipo_empresa', 'orden'], name='empresa_mod_tipo_em_b8c123_idx'),
        ),
        migrations.AddIndex(
            model_name='leccion',
            index=models.Index(fields=['modulo', 'orden'], name='empresa_lec_modulo__f0e590_idx'),
        ),
        migrations.AddIndex(
            model_name='leccion',
            index=models.Index(fields=['tipo', 'visible'], name='empresa_lec_tipo_vi_a1b2c3_idx'),
        ),
        migrations.AddIndex(
            model_name='asientoaudit',
            index=models.Index(fields=['simulacion', 'transaccion_id'], name='empresa_asi_simula_d4e5f6_idx'),
        ),
        
        # Add unique constraint
        migrations.AlterUniqueTogether(
            name='leccion',
            unique_together={('slug', 'modulo')},
        ),
    ]