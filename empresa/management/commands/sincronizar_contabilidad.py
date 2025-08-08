from django.core.management.base import BaseCommand
from django.db import transaction
from empresa.models import Venta, Compra, Gasto, MovimientoContable
from empresa.views.contabilidad import registrar_movimiento_contable
from datetime import datetime

class Command(BaseCommand):
    help = 'Sincroniza registros históricos de ventas, compras y gastos con movimientos contables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa-id',
            type=int,
            help='ID de la empresa específica (opcional)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar en modo simulación sin hacer cambios',
        )

    def handle(self, *args, **options):
        empresa_id = options.get('empresa_id')
        dry_run = options.get('dry_run')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO SIMULACIÓN - No se harán cambios reales'))
        
        # Obtener empresas a procesar
        from empresa.models import Empresa
        if empresa_id:
            empresas = Empresa.objects.filter(id=empresa_id)
        else:
            empresas = Empresa.objects.all()
        
        if not empresas.exists():
            self.stdout.write(self.style.ERROR('No se encontraron empresas para procesar'))
            return
        
        total_ventas_procesadas = 0
        total_compras_procesadas = 0
        total_gastos_procesados = 0
        total_errores = 0
        
        for empresa in empresas:
            self.stdout.write(f'\nProcesando empresa: {empresa.nombre}')
            
            # Procesar ventas
            ventas_sin_movimientos = self._obtener_ventas_sin_movimientos(empresa)
            self.stdout.write(f'  - Ventas sin movimientos contables: {len(ventas_sin_movimientos)}')
            
            for venta in ventas_sin_movimientos:
                try:
                    if not dry_run:
                        registrar_movimiento_contable(
                            empresa=empresa,
                            cuenta_debito_nombre='Caja/Banco',
                            cuenta_credito_nombre='Ventas',
                            monto=venta.total,
                            descripcion=f"Venta de {venta.producto.nombre} (x{venta.cantidad}) - {venta.fecha.strftime('%d/%m/%Y')}"
                        )
                    total_ventas_procesadas += 1
                    self.stdout.write(f'    ✓ Venta {venta.id}: ${venta.total}')
                except Exception as e:
                    total_errores += 1
                    self.stdout.write(self.style.ERROR(f'    ✗ Error en venta {venta.id}: {e}'))
            
            # Procesar compras
            compras_sin_movimientos = self._obtener_compras_sin_movimientos(empresa)
            self.stdout.write(f'  - Compras sin movimientos contables: {len(compras_sin_movimientos)}')
            
            for compra in compras_sin_movimientos:
                try:
                    if not dry_run:
                        registrar_movimiento_contable(
                            empresa=empresa,
                            cuenta_debito_nombre='Inventario',
                            cuenta_credito_nombre='Caja/Banco',
                            monto=compra.total,
                            descripcion=f"Compra de {compra.producto.nombre} (x{compra.cantidad}) - {compra.fecha.strftime('%d/%m/%Y')}"
                        )
                    total_compras_procesadas += 1
                    self.stdout.write(f'    ✓ Compra {compra.id}: ${compra.total}')
                except Exception as e:
                    total_errores += 1
                    self.stdout.write(self.style.ERROR(f'    ✗ Error en compra {compra.id}: {e}'))
            
            # Procesar gastos
            gastos_sin_movimientos = self._obtener_gastos_sin_movimientos(empresa)
            self.stdout.write(f'  - Gastos sin movimientos contables: {len(gastos_sin_movimientos)}')
            
            for gasto in gastos_sin_movimientos:
                try:
                    if not dry_run:
                        registrar_movimiento_contable(
                            empresa=empresa,
                            cuenta_debito_nombre='Gastos',
                            cuenta_credito_nombre='Caja/Banco',
                            monto=gasto.monto,
                            descripcion=f"{gasto.descripcion} - {gasto.fecha.strftime('%d/%m/%Y')}"
                        )
                    total_gastos_procesados += 1
                    self.stdout.write(f'    ✓ Gasto {gasto.id}: ${gasto.monto}')
                except Exception as e:
                    total_errores += 1
                    self.stdout.write(self.style.ERROR(f'    ✗ Error en gasto {gasto.id}: {e}'))
        
        # Resumen final
        self.stdout.write('\n' + '='*50)
        self.stdout.write('RESUMEN DE SINCRONIZACIÓN')
        self.stdout.write('='*50)
        self.stdout.write(f'Ventas procesadas: {total_ventas_procesadas}')
        self.stdout.write(f'Compras procesadas: {total_compras_procesadas}')
        self.stdout.write(f'Gastos procesados: {total_gastos_procesados}')
        self.stdout.write(f'Errores: {total_errores}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nMODO SIMULACIÓN - Ejecuta sin --dry-run para aplicar los cambios'))
        else:
            self.stdout.write(self.style.SUCCESS('\nSincronización completada exitosamente'))
    
    def _obtener_ventas_sin_movimientos(self, empresa):
        """Obtiene ventas que no tienen movimientos contables asociados"""
        ventas_con_movimientos = MovimientoContable.objects.filter(
            empresa=empresa,
            descripcion__icontains='Venta de'
        ).values_list('descripcion', flat=True)
        
        # Filtrar ventas que no tienen movimientos contables
        ventas_sin_movimientos = []
        for venta in Venta.objects.filter(empresa=empresa):
            descripcion_esperada = f"Venta de {venta.producto.nombre} (x{venta.cantidad})"
            if not any(descripcion_esperada in desc for desc in ventas_con_movimientos):
                ventas_sin_movimientos.append(venta)
        
        return ventas_sin_movimientos
    
    def _obtener_compras_sin_movimientos(self, empresa):
        """Obtiene compras que no tienen movimientos contables asociados"""
        compras_con_movimientos = MovimientoContable.objects.filter(
            empresa=empresa,
            descripcion__icontains='Compra de'
        ).values_list('descripcion', flat=True)
        
        # Filtrar compras que no tienen movimientos contables
        compras_sin_movimientos = []
        for compra in Compra.objects.filter(empresa=empresa):
            descripcion_esperada = f"Compra de {compra.producto.nombre} (x{compra.cantidad})"
            if not any(descripcion_esperada in desc for desc in compras_con_movimientos):
                compras_sin_movimientos.append(compra)
        
        return compras_sin_movimientos
    
    def _obtener_gastos_sin_movimientos(self, empresa):
        """Obtiene gastos que no tienen movimientos contables asociados"""
        gastos_con_movimientos = MovimientoContable.objects.filter(
            empresa=empresa,
            cuenta_fk__nombre='Gastos'
        ).values_list('descripcion', flat=True)
        
        # Filtrar gastos que no tienen movimientos contables
        gastos_sin_movimientos = []
        for gasto in Gasto.objects.filter(empresa=empresa):
            if not any(gasto.descripcion in desc for desc in gastos_con_movimientos):
                gastos_sin_movimientos.append(gasto)
        
        return gastos_sin_movimientos 