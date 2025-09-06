# Generated migration for NIIF Phase 1 implementation

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('empresa', '0015_auto_20250822_1526'),
    ]

    operations = [
        # Add deterioro_esperado field to CuentaPorCobrar
        migrations.AddField(
            model_name='cuentaporcobrar',
            name='deterioro_esperado',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        
        # Create MovimientoInventario model
        migrations.CreateModel(
            name='MovimientoInventario',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado_en', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('modificado_en', models.DateTimeField(auto_now=True, verbose_name='Fecha de modificación')),
                ('tipo', models.CharField(choices=[('entrada', 'Entrada'), ('salida', 'Salida'), ('ajuste', 'Ajuste')], max_length=10)),
                ('cantidad', models.DecimalField(decimal_places=2, max_digits=10)),
                ('costo_unitario', models.DecimalField(decimal_places=2, max_digits=10)),
                ('costo_total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('referencia', models.CharField(blank=True, max_length=100)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='movimientoinventario_creadas', to='empresa.usuario', verbose_name='Creado por')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empresa.empresa')),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='movimientoinventario_modificadas', to='empresa.usuario', verbose_name='Modificado por')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empresa.producto')),
            ],
            options={
                'ordering': ['fecha'],
            },
        ),
        
        # Add indexes for MovimientoInventario
        migrations.AddIndex(
            model_name='movimientoinventario',
            index=models.Index(fields=['empresa', 'producto', 'fecha'], name='empresa_mov_empresa_b8c123_idx'),
        ),
        migrations.AddIndex(
            model_name='movimientoinventario',
            index=models.Index(fields=['tipo', 'fecha'], name='empresa_mov_tipo_4a5678_idx'),
        ),
    ]