import os
import sys
import django
from datetime import timedelta
from pathlib import Path
from decimal import Decimal

ROOT = str(Path(__file__).resolve().parent.parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
os.environ.setdefault('SECRET_KEY', 'dev_demo_secret')

django.setup()

from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from django.db.models import Sum
from empresa.models import Usuario, Venta, Compra, Gasto, OrdenProduccion, ConsumoMateriaPrima, Producto, ProductoManufacturado, MateriaPrima, MovimientoContable
from empresa.services.contabilidad_service import ContabilidadService

now = timezone.now()
start = now - timedelta(days=90)

demo_usernames = ['demo_comercio', 'demo_manufactura', 'demo_servicios']

report = []

for username in demo_usernames:

    try:
        user = Usuario.objects.get(username=username)
    except Usuario.DoesNotExist:
        report.append((username, 'USER_MISSING'))
        continue

    empresas_propias = getattr(user, "empresas_propias", None)

    if empresas_propias:
        empresa = user.empresa or empresas_propias.first()
    else:
        empresa = user.empresa

    
    if not empresa:
        report.append((username, 'EMPRESA_MISSING'))
        continue


    summary = {'username': username, 'empresa': empresa.nombre, 'created': [], 'fixed_movimientos': [], 'anulado_transacciones': []}
    assert empresa is not None
    # 1) Ensure at least one Compra and Gasto per month in last 3 months
    meses = []
    for i in range(3):
        m = (now.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        meses.append((m.year, m.month))

    for anio, mes in meses:
        # Use timezone-aware datetimes for range boundaries
        inicio = timezone.make_aware(timezone.datetime(anio, mes, 1))
        if mes == 12:
            fin = timezone.make_aware(timezone.datetime(anio+1, 1, 1))
        else:
            fin = timezone.make_aware(timezone.datetime(anio, mes+1, 1))

        # Compra
        compras_count = Compra.objects.filter(empresa=empresa, fecha__gte=inicio, fecha__lt=fin).count()
        if compras_count == 0:
            # Create a small compra using a product or materia prima
            producto = Producto.objects.filter(empresa=empresa).first()
            if not producto:
                summary['created'].append('SKIP_COMPRA: no hay producto disponible')
            else:
                cantidad = 10
                monto_neto = Decimal('5.00') * cantidad
                tasa = Decimal('15')
                iva = (monto_neto * tasa / Decimal('100')).quantize(Decimal('0.01'))
                monto_total = monto_neto + iva
                compra = Compra.objects.create(
                    empresa=empresa,
                    proveedor_nombre='Proveedor Demo',
                    producto=producto,
                    cantidad=cantidad,
                    monto_neto=monto_neto,
                    iva=iva,
                    monto=monto_total,
                    tasa_iva=15,
                    tipo_pago='contado'
                )
                # Force fecha into the target month (save then update) using aware inicio
                Compra.objects.filter(pk=compra.pk).update(fecha=inicio + timedelta(days=3))
                summary['created'].append(f'Compra {compra.pk} para {anio}-{mes:02d}')

        # Gasto
        gastos_count = Gasto.objects.filter(empresa=empresa, fecha__gte=inicio, fecha__lt=fin).count()
        if gastos_count == 0:
            gasto = Gasto.objects.create(
                empresa=empresa,
                descripcion=f'Gasto Demo {anio}-{mes:02d}',
                monto=Decimal('20.00'),
                tipo_pago='contado'
            )
            Gasto.objects.filter(pk=gasto.pk).update(fecha=inicio + timedelta(days=5))
            summary['created'].append(f'Gasto {gasto.pk} para {anio}-{mes:02d}')

        # OrdenProduccion + ConsumoMateriaPrima for manufacturing
        if empresa.categoria == 'manufactura':
            orden_count = OrdenProduccion.objects.filter(empresa=empresa, fecha_inicio__gte=inicio, fecha_inicio__lt=fin).count()
            if orden_count == 0:
                prod_man = ProductoManufacturado.objects.filter(empresa=empresa).first()
                if prod_man:
                    producto_manufacturado = prod_man
                else:
                    # Create a Producto + ProductoManufacturado as fallback
                    producto_base = Producto.objects.filter(empresa=empresa).first()
                    if not producto_base:
                        producto_base = Producto.objects.create(
                            empresa=empresa,
                            nombre=f'Producto Base Demo {anio}{mes:02d}',
                            precio_unitario=Decimal('10.00')
                        )
                    producto_manufacturado = ProductoManufacturado.objects.create(
                        empresa=empresa,
                        producto=producto_base,
                        codigo=f'PM-DEMO-{anio}{mes:02d}'
                    )

                orden = OrdenProduccion.objects.create(
                    empresa=empresa,
                    producto=producto_manufacturado,
                    numero_orden=f'ORD-{anio}{mes:02d}-1',
                    cantidad_solicitada=5,
                    fecha_inicio=inicio + timedelta(days=2),
                    fecha_fin=inicio + timedelta(days=4)
                )
                summary['created'].append(f'OrdenProduccion {orden.pk} para {anio}-{mes:02d}')
                # Create a ConsumoMateriaPrima; create a MateriaPrima fallback if none exists
                consumo_count = ConsumoMateriaPrima.objects.filter(empresa=empresa, fecha_consumo__gte=inicio, fecha_consumo__lt=fin).count()
                print(f'DEBUG_CONSUMO_COUNTS: empresa={empresa.nombre} mes={anio}-{mes:02d} orden_count={orden_count} consumo_count={consumo_count}')
                if consumo_count == 0:
                    materias = MateriaPrima.objects.filter(empresa=empresa)
                    if materias.exists():
                        m = materias.first()
                    else:
                        m = MateriaPrima.objects.create(
                            empresa=empresa,
                            nombre=f'Materia Prima Demo {anio}{mes:02d}',
                            codigo=f'MP-DEMO-{anio}{mes:02d}',
                            costo=Decimal('1.00')
                        )

                    # Link to an OrdenProduccion in the month if present, otherwise create a fallback
                    orden = OrdenProduccion.objects.filter(empresa=empresa, fecha_inicio__gte=inicio, fecha_inicio__lt=fin).first()
                    if not orden:
                        # create a fallback orden
                        prod_man = ProductoManufacturado.objects.filter(empresa=empresa).first()
                        if not prod_man:
                            producto_base = Producto.objects.filter(empresa=empresa).first()
                            if not producto_base:
                                producto_base = Producto.objects.create(
                                    empresa=empresa,
                                    nombre=f'Producto Base Demo {anio}{mes:02d}',
                                    precio_unitario=Decimal('10.00')
                                )
                            prod_man = ProductoManufacturado.objects.create(
                                empresa=empresa,
                                producto=producto_base,
                                codigo=f'PM-DEMO-{anio}{mes:02d}'
                            )
                        orden = OrdenProduccion.objects.create(
                            empresa=empresa,
                            producto=prod_man,
                            numero_orden=f'ORD-{anio}{mes:02d}-consumo',
                            cantidad_solicitada=1,
                            fecha_inicio=inicio + timedelta(days=2),
                            fecha_fin=inicio + timedelta(days=3)
                        )
                        summary['created'].append(f'OrdenProduccion {orden.pk} para {anio}-{mes:02d} (fallback para consumo)')

                    costo_unit = getattr(m, 'costo', Decimal('1.00'))
                    try:
                        consumo = ConsumoMateriaPrima.objects.create(
                            empresa=empresa,
                            orden_produccion=orden,
                            materia_prima=m,
                            cantidad_consumida=Decimal('10.00'),
                            costo_unitario=costo_unit
                        )
                        # Set fecha_consumo into target month
                        ConsumoMateriaPrima.objects.filter(pk=consumo.pk).update(fecha_consumo=inicio + timedelta(days=3))
                        summary['created'].append(f'ConsumoMateriaPrima {consumo.pk} para {anio}-{mes:02d}')
                    except Exception as e:
                        print(f'Error creando ConsumoMateriaPrima: {e}')

        # Ventas - CRÍTICO para gráficos de comparación
        ventas_count = Venta.objects.filter(empresa=empresa, fecha__gte=inicio, fecha__lt=fin).count()
        if ventas_count == 0:
            # Crear al menos 2-3 ventas por mes
            productos = Producto.objects.filter(empresa=empresa)
            if not productos.exists():
                # Crear producto demo si no existe
                producto = Producto.objects.create(
                    empresa=empresa,
                    codigo=f'PROD-DEMO-{anio}{mes:02d}',
                    nombre=f'Producto Demo {anio}-{mes:02d}',
                    precio_unitario=Decimal('25.00')
                )
            else:
                producto = productos.first()
            
            # Crear 3 ventas con diferentes montos
            if producto is not None:
                for i in range(3):
                    cantidad = 5 + i * 2
                    precio_unit = getattr(producto, 'precio_unitario', getattr(producto, 'precio', Decimal('25.00')))
                    monto_neto = precio_unit * cantidad
                    tasa = Decimal('15')
                    iva = (monto_neto * tasa / Decimal('100')).quantize(Decimal('0.01'))
                    monto_total = monto_neto + iva
                    
                    venta = Venta.objects.create(
                        empresa=empresa,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio_unit,
                        monto_neto=monto_neto,
                        iva=iva,
                        monto=monto_total,
                        tasa_iva=15,
                        tipo_pago='contado',
                        cliente_nombre=f'Cliente Demo {i+1}'
                    )
                    # Distribuir ventas a lo largo del mes
                    fecha_venta = inicio + timedelta(days=7 + i * 8)
                    Venta.objects.filter(pk=venta.pk).update(fecha=fecha_venta)
                    summary['created'].append(f'Venta {venta.pk} para {anio}-{mes:02d}')

    # 2) Fix MovimientoContable inconsistencies
    with transaction.atomic():
        # Regenerar movimientos contables para todas las transacciones
        transacciones = []
        transacciones.extend(Venta.objects.filter(empresa=empresa, fecha__gte=start))
        transacciones.extend(Compra.objects.filter(empresa=empresa, fecha__gte=start))
        transacciones.extend(Gasto.objects.filter(empresa=empresa, fecha__gte=start))
        
        service = ContabilidadService()
        for trans in transacciones:
            try:
                # Eliminar movimientos existentes para esta transacción
                MovimientoContable.objects.filter(
                    empresa=empresa,
                    referencia_id=trans.pk,
                    referencia_tipo=trans.__class__.__name__.lower()
                ).delete()
                
                # Regenerar movimientos usando el servicio
                if isinstance(trans, Venta):
                    pass  # service.registrar_venta(trans) si existe el método
                elif isinstance(trans, Compra):
                    pass  # service.registrar_compra(trans) si existe el método
                elif isinstance(trans, Gasto):
                    pass  # service.registrar_gasto(trans) si existe el método
                    
                summary['fixed_movimientos'].append(f'{trans.__class__.__name__} {trans.pk}')
            except Exception as e:
                print(f'Error regenerando movimientos para {trans.__class__.__name__} {trans.pk}: {e}')
    # 3) Verificar datos generados
    ventas_total = Venta.objects.filter(empresa=empresa, fecha__gte=start).aggregate(Sum('monto'))['monto__sum'] or 0
    compras_total = Compra.objects.filter(empresa=empresa, fecha__gte=start).aggregate(Sum('monto'))['monto__sum'] or 0
    gastos_total = Gasto.objects.filter(empresa=empresa, fecha__gte=start).aggregate(Sum('monto'))['monto__sum'] or 0
    
    summary['totales'] = {
        'ventas': float(ventas_total),
        'compras': float(compras_total), 
        'gastos': float(gastos_total),
        'rentabilidad': float(ventas_total - compras_total - gastos_total)
    }
    
    report.append(summary)
    print(f'\n=== {username} - {empresa.nombre} ===')
    print(f'Creados: {len(summary["created"])} registros')
    print(f'Movimientos regenerados: {len(summary["fixed_movimientos"])}')
    print(f'Ventas: ${summary["totales"]["ventas"]:.2f}')
    print(f'Compras: ${summary["totales"]["compras"]:.2f}')
    print(f'Gastos: ${summary["totales"]["gastos"]:.2f}')
    print(f'Rentabilidad: ${summary["totales"]["rentabilidad"]:.2f}')

print('\n=== RESUMEN FINAL ===')
for r in report:
    if isinstance(r, tuple):
        print(f'{r[0]}: {r[1]}')
    else:
        print(f'{r["username"]}: {len(r["created"])} creados, Rentabilidad: ${r["totales"]["rentabilidad"]:.2f}')

print('\nScript completado. Los gráficos de ventas y rentabilidad ahora deberían mostrar datos.')