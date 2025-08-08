from django.core.management.base import BaseCommand
from django.db import transaction
from empresa.models import Venta, Compra, Gasto, Producto, MovimientoContable, Capital, Usuario


class Command(BaseCommand):
    help = 'Asigna usuarios a registros existentes que tienen creado_por como None'

    def add_arguments(self, parser):
        parser.add_argument(
            '--usuario',
            type=str,
            help='Username del usuario a asignar (opcional, si no se especifica se usará el primer usuario de cada empresa)'
        )
        parser.add_argument(
            '--empresa',
            type=int,
            help='ID de la empresa específica (opcional)'
        )

    def handle(self, *args, **options):
        usuario_especifico = options.get('usuario')
        empresa_id = options.get('empresa')
        
        self.stdout.write(self.style.SUCCESS('Iniciando asignación de usuarios a registros existentes...'))
        
        # Obtener todas las empresas o una específica
        if empresa_id:
            empresas = [Usuario.objects.get(id=empresa_id).empresa]
        else:
            empresas = set()
            for usuario in Usuario.objects.filter(empresa__isnull=False):
                empresas.add(usuario.empresa)
        
        total_actualizados = 0
        
        for empresa in empresas:
            self.stdout.write(f'Procesando empresa: {empresa.nombre}')
            
            # Determinar usuario para esta empresa
            if usuario_especifico:
                try:
                    usuario = Usuario.objects.get(username=usuario_especifico, empresa=empresa)
                except Usuario.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Usuario {usuario_especifico} no encontrado en empresa {empresa.nombre}'))
                    continue
            else:
                # Usar el primer usuario de la empresa
                usuario = Usuario.objects.filter(empresa=empresa).first()
                if not usuario:
                    self.stdout.write(self.style.WARNING(f'No se encontraron usuarios en empresa {empresa.nombre}'))
                    continue
            
            self.stdout.write(f'  Usando usuario: {usuario.username}')
            
            # Actualizar registros por modelo
            modelos = [
                (Venta, 'Ventas'),
                (Compra, 'Compras'),
                (Gasto, 'Gastos'),
                (Producto, 'Productos'),
                (MovimientoContable, 'Movimientos Contables'),
                (Capital, 'Capital')
            ]
            
            for modelo, nombre in modelos:
                registros_sin_usuario = modelo.objects.filter(
                    empresa=empresa,
                    creado_por__isnull=True
                )
                
                if registros_sin_usuario.exists():
                    count = registros_sin_usuario.count()
                    registros_sin_usuario.update(creado_por=usuario)
                    self.stdout.write(f'    {nombre}: {count} registros actualizados')
                    total_actualizados += count
                else:
                    self.stdout.write(f'    {nombre}: 0 registros actualizados')
        
        self.stdout.write(self.style.SUCCESS(f'Proceso completado. Total de registros actualizados: {total_actualizados}')) 