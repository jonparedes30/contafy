import os
import sys
import django
from datetime import timedelta
from decimal import Decimal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
os.environ.setdefault('SECRET_KEY', 'dev_demo_secret')

django.setup()

from django.utils import timezone
from empresa.models import Usuario, Empresa, Venta, Gasto, CuentaContable, MovimientoContable

def crear_empresas_benchmarking():
    """Crea empresas adicionales para benchmarking"""
    
    categorias = ['comercial', 'manufactura', 'servicios']
    now = timezone.now()
    
    for i, categoria in enumerate(categorias):
        for j in range(5):  # 5 empresas por categoría
            username = f'bench_{categoria}_{j+1}'
            
            # Verificar si ya existe
            if Usuario.objects.filter(username=username).exists():
                print(f'Usuario {username} ya existe, saltando...')
                continue
            
            # Crear usuario
            user = Usuario.objects.create_user(
                username=username,
                email=f'{username}@benchmark.com',
                password='benchmark123',
                nombre=f'Benchmark {categoria.title()} {j+1}',
                apellido='Demo'
            )
            
            # Crear empresa
            empresa = Empresa.objects.create(
                nombre=f'Empresa Benchmark {categoria.title()} {j+1}',
                ruc=f'999999999{i}{j:03d}',
                categoria=categoria,
                tipo_negocio=categoria,
                ciudad='Quito',
                provincia='Pichincha',
                pais='Ecuador',
                propietario=user
            )
            
            user.empresa = empresa
            user.save()
            
            # Crear cuentas contables
            cuenta_ventas = CuentaContable.objects.create(
                empresa=empresa,
                nombre='Ventas',
                tipo='ingreso',
                codigo='4.1.01'
            )
            
            cuenta_gastos = CuentaContable.objects.create(
                empresa=empresa,
                nombre='Gastos',
                tipo='gasto',
                codigo='5.1.01'
            )
            
            # Generar datos de los últimos 3 meses
            for mes_offset in range(3):
                fecha = now - timedelta(days=30 * mes_offset)
                
                # Ventas variables por empresa
                base_ventas = Decimal('5000') + (Decimal('1000') * j)
                ventas_mes = base_ventas * Decimal(str(1 + (mes_offset * 0.1)))
                
                # Gastos (60-80% de ventas)
                ratio_gastos = Decimal('0.6') + (Decimal('0.05') * j)
                gastos_mes = ventas_mes * ratio_gastos
                
                # Crear movimientos de ventas
                MovimientoContable.objects.create(
                    empresa=empresa,
                    cuenta_fk=cuenta_ventas,
                    tipo='credito',
                    monto=ventas_mes,
                    descripcion=f'Ventas mes {fecha.month}/{fecha.year}',
                    fecha=fecha
                )
                
                # Crear movimientos de gastos
                MovimientoContable.objects.create(
                    empresa=empresa,
                    cuenta_fk=cuenta_gastos,
                    tipo='debito',
                    monto=gastos_mes,
                    descripcion=f'Gastos mes {fecha.month}/{fecha.year}',
                    fecha=fecha
                )
            
            print(f'✓ Creada empresa benchmark: {empresa.nombre}')
    
    print('\n=== Resumen ===')
    for categoria in categorias:
        count = Empresa.objects.filter(categoria=categoria).count()
        print(f'{categoria.title()}: {count} empresas')

if __name__ == '__main__':
    crear_empresas_benchmarking()
    print('\n¡Empresas de benchmarking creadas exitosamente!')
