# Generated migration for NIIF Phase 2 implementation

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('empresa', '0016_niif_fase1'),
    ]

    operations = [
        # Create ContratoVenta model
        migrations.CreateModel(
            name='ContratoVenta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado_en', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('modificado_en', models.DateTimeField(auto_now=True, verbose_name='Fecha de modificación')),
                ('numero_contrato', models.CharField(max_length=50, unique=True)),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin', models.DateField(blank=True, null=True)),
                ('precio_total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('estado', models.CharField(choices=[('borrador', 'Borrador'), ('activo', 'Activo'), ('completado', 'Completado'), ('cancelado', 'Cancelado')], default='borrador', max_length=15)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empresa.cliente')),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='contratoventa_creadas', to='empresa.usuario', verbose_name='Creado por')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empresa.empresa')),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='contratoventa_modificadas', to='empresa.usuario', verbose_name='Modificado por')),
            ],
            options={
                'abstract': False,
            },
        ),
        
        # Create ObligacionDesempeno model
        migrations.CreateModel(
            name='ObligacionDesempeno',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado_en', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('modificado_en', models.DateTimeField(auto_now=True, verbose_name='Fecha de modificación')),
                ('descripcion', models.CharField(max_length=200)),
                ('precio_asignado', models.DecimalField(decimal_places=2, max_digits=12)),
                ('porcentaje_completado', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('fecha_satisfaccion', models.DateField(blank=True, null=True)),
                ('satisfecha', models.BooleanField(default=False)),
                ('contrato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='obligaciones', to='empresa.contratoventa')),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='obligaciondesempeno_creadas', to='empresa.usuario', verbose_name='Creado por')),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='obligaciondesempeno_modificadas', to='empresa.usuario', verbose_name='Modificado por')),
            ],
            options={
                'abstract': False,
            },
        ),
        
        # Create InstrumentoFinanciero model
        migrations.CreateModel(
            name='InstrumentoFinanciero',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado_en', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('modificado_en', models.DateTimeField(auto_now=True, verbose_name='Fecha de modificación')),
                ('nombre', models.CharField(max_length=100)),
                ('tipo', models.CharField(choices=[('activo_financiero', 'Activo Financiero'), ('pasivo_financiero', 'Pasivo Financiero'), ('patrimonio', 'Instrumento de Patrimonio')], max_length=20)),
                ('categoria', models.CharField(choices=[('costo_amortizado', 'Costo Amortizado'), ('valor_razonable_ori', 'Valor Razonable con cambios en ORI'), ('valor_razonable_resultado', 'Valor Razonable con cambios en Resultado')], max_length=30)),
                ('valor_nominal', models.DecimalField(decimal_places=2, max_digits=12)),
                ('valor_razonable', models.DecimalField(decimal_places=2, max_digits=12)),
                ('fecha_adquisicion', models.DateField()),
                ('fecha_vencimiento', models.DateField(blank=True, null=True)),
                ('tasa_interes', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='instrumentofinanciero_creadas', to='empresa.usuario', verbose_name='Creado por')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empresa.empresa')),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='instrumentofinanciero_modificadas', to='empresa.usuario', verbose_name='Modificado por')),
            ],
            options={
                'abstract': False,
            },
        ),
        
        # Create RevaluacionActivo model
        migrations.CreateModel(
            name='RevaluacionActivo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado_en', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('modificado_en', models.DateTimeField(auto_now=True, verbose_name='Fecha de modificación')),
                ('activo_descripcion', models.CharField(max_length=200)),
                ('valor_anterior', models.DecimalField(decimal_places=2, max_digits=12)),
                ('valor_revaluado', models.DecimalField(decimal_places=2, max_digits=12)),
                ('fecha_revaluacion', models.DateField()),
                ('metodo_valuacion', models.CharField(max_length=100)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='revaluacionactivo_creadas', to='empresa.usuario', verbose_name='Creado por')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empresa.empresa')),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='revaluacionactivo_modificadas', to='empresa.usuario', verbose_name='Modificado por')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]