from django.core.management.base import BaseCommand
from empresa.models import Empresa, Usuario, CuentaContable, Producto, Venta, Gasto, MetaFinanciera, Compra
from empresa.views.contabilidad import registrar_movimiento_contable
from django.utils import timezone
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Genera datos históricos completos para la empresa "prueba1" y usuario "jona30" (ventas, compras, gastos, movimientos, metas) mes a mes desde el año pasado.'

    def handle(self, *args, **options):
        try:
            empresa = Empresa.objects.get(nombre='prueba1')
            usuario = Usuario.objects.get(username='jona30')
        except Empresa.DoesNotExist:
            self.stdout.write(self.style.ERROR('Empresa "prueba1" no encontrada.'))
            return
        except Usuario.DoesNotExist:
            self.stdout.write(self.style.ERROR('Usuario "jona30" no encontrado.'))
            return

        # Crear cuentas contables básicas
        cuentas = [
            ('Ventas', 'ingreso'),
            ('Caja/Banco', 'activo'),
            ('Inventario', 'activo'),
            ('Gastos', 'gasto'),
            ('Capital Social', 'capital'),
        ]
        cuentas_objs = {}
        for nombre, tipo in cuentas:
            cuenta, _ = CuentaContable.objects.get_or_create(
                nombre=nombre, tipo=tipo, empresa=empresa
            )
            cuentas_objs[nombre] = cuenta

        # Crear productos demo
        productos = [
            ('Producto A', 'A', 10.0),
            ('Producto B', 'B', 20.0),
            ('Producto C', 'C', 15.5),
        ]
        productos_objs = []
        for nombre, codigo, precio in productos:
            prod, _ = Producto.objects.get_or_create(
                nombre=nombre, codigo=codigo, precio_unitario=precio, empresa=empresa
            )
            productos_objs.append(prod)

        # Borrar datos previos demo
        Venta.objects.filter(empresa=empresa).delete()
        Gasto.objects.filter(empresa=empresa).delete()
        MetaFinanciera.objects.filter(empresa=empresa).delete()
        from empresa.models import MovimientoContable
        MovimientoContable.objects.filter(empresa=empresa).delete()

        # Capital inicial (ANTES de generar movimientos)
        registrar_movimiento_contable(
            empresa=empresa,
            cuenta_debito_nombre='Caja/Banco',
            cuenta_credito_nombre='Capital Social',
            monto=500000,
            descripcion='Aporte inicial de capital para demo'
        )

        hoy = timezone.now().date()
        primer_mes = (hoy.replace(day=1) - timedelta(days=365)).replace(day=1)
        meses = []
        fecha = primer_mes
        while fecha <= hoy:
            meses.append((fecha.year, fecha.month))
            if fecha.month == 12:
                fecha = fecha.replace(year=fecha.year+1, month=1)
            else:
                fecha = fecha.replace(month=fecha.month+1)

        for anio, mes in meses:
            # Ventas
            for _ in range(random.randint(2, 5)):
                producto = random.choice(productos_objs)
                cantidad = random.randint(1, 5)
                precio = producto.precio_unitario
                total = precio * cantidad
                fecha_venta = datetime(anio, mes, random.randint(1, 28))
                venta = Venta.objects.create(
                    empresa=empresa,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    total=total,
                    fecha=fecha_venta
                )
                # Movimiento contable de venta (doble partida)
                registrar_movimiento_contable(
                    empresa=empresa,
                    cuenta_debito_nombre='Caja/Banco',
                    cuenta_credito_nombre='Ventas',
                    monto=total,
                    descripcion=f"Venta de {producto.nombre} (x{cantidad}) - {fecha_venta.strftime('%d/%m/%Y')}"
                )

            # Crear compras demo
            inicio = datetime(anio, mes, 1)
            for mes_compra in range(12):
                fecha_compra = inicio + timedelta(days=mes_compra*30+10)
                producto = random.choice(productos_objs)
                cantidad = random.randint(1, 8)
                precio = producto.precio_unitario
                total = precio * cantidad
                compra = Compra.objects.create(
                    empresa=empresa,
                    producto=producto,
                    cantidad=cantidad,
                    total=total,
                    fecha=fecha_compra
                )
                # Movimiento contable de la compra
                registrar_movimiento_contable(
                    empresa=empresa,
                    cuenta_debito_nombre='Inventario',
                    cuenta_credito_nombre='Caja/Banco',
                    monto=total,
                    descripcion=f"Compra demo de {producto.nombre} (x{cantidad}) en {fecha_compra.strftime('%B %Y')}"
                )

            # Crear gastos demo
            for mes_gasto in range(12):
                fecha_gasto = inicio + timedelta(days=mes_gasto*30+20)
                monto = random.randint(50, 300)
                descripcion = f"Gasto demo mes {fecha_gasto.strftime('%B %Y')}"
                categoria = random.choice(['Fijo', 'Variable'])
                gasto = Gasto.objects.create(
                    empresa=empresa,
                    descripcion=descripcion,
                    monto=monto,
                    fecha=fecha_gasto,
                    categoria=categoria
                )
                # Movimiento contable del gasto
                registrar_movimiento_contable(
                    empresa=empresa,
                    cuenta_debito_nombre='Gastos',
                    cuenta_credito_nombre='Caja/Banco',
                    monto=monto,
                    descripcion=descripcion
                )

            # Metas financieras (algunas cumplidas, otras no)
            objetivo_ventas = random.randint(800, 1500)
            objetivo_gastos = random.randint(400, 700)
            MetaFinanciera.objects.create(
                empresa=empresa,
                tipo='ventas',
                objetivo_mensual=objetivo_ventas,
                mes=mes,
                anio=anio
            )
            MetaFinanciera.objects.create(
                empresa=empresa,
                tipo='gastos',
                objetivo_mensual=objetivo_gastos,
                mes=mes,
                anio=anio
            )

        self.stdout.write(self.style.SUCCESS('Datos históricos completos generados para empresa "prueba1" y usuario "jona30".')) 