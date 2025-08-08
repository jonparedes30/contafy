from django.core.management.base import BaseCommand
from empresa.models import Empresa, CuentaContable, MovimientoContable
from django.utils import timezone
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Pobla datos de prueba para benchmarking'

    def handle(self, *args, **options):
        self.stdout.write('Creando empresas de prueba para benchmarking...')
        
        # Datos de empresas de manufactura
        empresas_manufactura = [
            {'nombre': 'Panadería San Juan', 'ruc': '1234567890001', 'tipo_negocio': 'panaderia', 'ciudad': 'Quito', 'provincia': 'Pichincha'},
            {'nombre': 'Carpintería El Roble', 'ruc': '1234567890002', 'tipo_negocio': 'carpinteria', 'ciudad': 'Cuenca', 'provincia': 'Azuay'},
            {'nombre': 'Panadería La Espiga', 'ruc': '1234567890003', 'tipo_negocio': 'panaderia', 'ciudad': 'Guayaquil', 'provincia': 'Guayas'},
            {'nombre': 'Herrería Moderna', 'ruc': '1234567890004', 'tipo_negocio': 'herreria', 'ciudad': 'Ambato', 'provincia': 'Tungurahua'},
            {'nombre': 'Alimentos Andinos', 'ruc': '1234567890005', 'tipo_negocio': 'alimentos', 'ciudad': 'Quito', 'provincia': 'Pichincha'},
        ]
        
        # Datos de empresas comerciales
        empresas_comerciales = [
            {'nombre': 'Minimarket Central', 'ruc': '1234567890006', 'tipo_negocio': 'minimarket', 'ciudad': 'Quito', 'provincia': 'Pichincha'},
            {'nombre': 'Farmacia Salud', 'ruc': '1234567890007', 'tipo_negocio': 'farmacia', 'ciudad': 'Guayaquil', 'provincia': 'Guayas'},
            {'nombre': 'Ferretería El Martillo', 'ruc': '1234567890008', 'tipo_negocio': 'ferreteria', 'ciudad': 'Cuenca', 'provincia': 'Azuay'},
            {'nombre': 'Tienda La Esquina', 'ruc': '1234567890009', 'tipo_negocio': 'minimarket', 'ciudad': 'Ambato', 'provincia': 'Tungurahua'},
        ]
        
        todas_empresas = []
        
        # Crear empresas de manufactura
        for data in empresas_manufactura:
            empresa, created = Empresa.objects.get_or_create(
                ruc=data['ruc'],
                defaults={
                    'nombre': data['nombre'],
                    'direccion': 'Dirección de prueba',
                    'categoria': 'manufactura',
                    'tipo_negocio': data['tipo_negocio'],
                    'ciudad': data['ciudad'],
                    'provincia': data['provincia']
                }
            )
            if created:
                self.stdout.write(f'Creada empresa: {empresa.nombre}')
                todas_empresas.append(empresa)
        
        # Crear empresas comerciales
        for data in empresas_comerciales:
            empresa, created = Empresa.objects.get_or_create(
                ruc=data['ruc'],
                defaults={
                    'nombre': data['nombre'],
                    'direccion': 'Dirección de prueba',
                    'categoria': 'comercial',
                    'tipo_negocio': data['tipo_negocio'],
                    'ciudad': data['ciudad'],
                    'provincia': data['provincia']
                }
            )
            if created:
                self.stdout.write(f'Creada empresa: {empresa.nombre}')
                todas_empresas.append(empresa)
        
        # Crear cuentas contables y movimientos para cada empresa
        for empresa in todas_empresas:
            self.crear_cuentas_y_movimientos(empresa)
        
        self.stdout.write(self.style.SUCCESS(f'Proceso completado. Creadas {len(todas_empresas)} empresas con datos financieros.'))
    
    def crear_cuentas_y_movimientos(self, empresa):
        """Crea cuentas contables y movimientos de prueba"""
        
        # Crear cuentas contables básicas
        cuenta_ventas, _ = CuentaContable.objects.get_or_create(
            empresa=empresa,
            nombre='Ventas',
            defaults={'tipo': 'ingreso'}
        )
        
        cuenta_gastos, _ = CuentaContable.objects.get_or_create(
            empresa=empresa,
            nombre='Gastos',
            defaults={'tipo': 'gasto'}
        )
        
        cuenta_inventario, _ = CuentaContable.objects.get_or_create(
            empresa=empresa,
            nombre='Inventario',
            defaults={'tipo': 'activo'}
        )
        
        cuenta_caja, _ = CuentaContable.objects.get_or_create(
            empresa=empresa,
            nombre='Caja/Banco',
            defaults={'tipo': 'activo'}
        )
        
        # Generar movimientos del mes actual
        hoy = timezone.now()
        inicio_mes = hoy.replace(day=1)
        
        # Ventas aleatorias (entre 5,000 y 25,000)
        ventas_base = random.randint(5000, 25000)
        for i in range(random.randint(10, 30)):  # Entre 10 y 30 ventas
            MovimientoContable.objects.create(
                empresa=empresa,
                cuenta_fk=cuenta_ventas,
                tipo='credito',
                monto=Decimal(str(random.randint(100, 1000))),
                descripcion=f'Venta #{i+1}',
                fecha=inicio_mes
            )
        
        # Costos/Inventario (60-80% de las ventas)
        factor_costo = random.uniform(0.6, 0.8)
        costos_total = ventas_base * factor_costo
        MovimientoContable.objects.create(
            empresa=empresa,
            cuenta_fk=cuenta_inventario,
            tipo='debito',
            monto=Decimal(str(round(costos_total, 2))),
            descripcion='Compra de inventario',
            fecha=inicio_mes
        )
        
        # Gastos operativos (10-20% de las ventas)
        factor_gastos = random.uniform(0.1, 0.2)
        gastos_total = ventas_base * factor_gastos
        MovimientoContable.objects.create(
            empresa=empresa,
            cuenta_fk=cuenta_gastos,
            tipo='debito',
            monto=Decimal(str(round(gastos_total, 2))),
            descripcion='Gastos operativos',
            fecha=inicio_mes
        )
        
        # Movimiento en caja
        MovimientoContable.objects.create(
            empresa=empresa,
            cuenta_fk=cuenta_caja,
            tipo='debito',
            monto=Decimal(str(ventas_base)),
            descripcion='Ingresos por ventas',
            fecha=inicio_mes
        )
        
        self.stdout.write(f'  -> Datos financieros creados para {empresa.nombre} (Ventas: ${ventas_base})')