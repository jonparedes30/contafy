"""Servicio para operaciones contables"""
import logging
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from ..models import CuentaContable, MovimientoContable, Venta, Gasto

logger = logging.getLogger(__name__)


class ContabilidadService:
    """Servicio para manejar operaciones contables"""
    
    @staticmethod
    @transaction.atomic
    def registrar_venta(venta):
        """Registra asientos contables para una venta"""
        try:
            empresa = venta.empresa
            
            # Débito: Caja (Activo)
            cuenta_caja, _ = CuentaContable.objects.get_or_create(
                empresa=empresa,
                nombre="Caja",
                defaults={'tipo': 'activo'}
            )
            
            # Crédito: Ventas (Ingreso)
            cuenta_ventas, _ = CuentaContable.objects.get_or_create(
                empresa=empresa,
                nombre="Ventas",
                defaults={'tipo': 'ingreso'}
            )
            
            # Crear movimientos
            MovimientoContable.objects.bulk_create([
                MovimientoContable(
                    empresa=empresa,
                    cuenta_fk=cuenta_caja,
                    cuenta_text=cuenta_caja.nombre,
                    tipo='debito',
                    monto=venta.total,
                    descripcion=f"Venta {venta.producto.nombre}"
                ),
                MovimientoContable(
                    empresa=empresa,
                    cuenta_fk=cuenta_ventas,
                    cuenta_text=cuenta_ventas.nombre,
                    tipo='credito',
                    monto=venta.total,
                    descripcion=f"Venta {venta.producto.nombre}"
                )
            ])
            
            logger.info(f"Venta registrada contablemente: {venta.id}")
            
        except Exception as e:
            logger.error(f"Error registrando venta {venta.id}: {str(e)}")
            raise
    
    @staticmethod
    @transaction.atomic
    def registrar_gasto(gasto):
        """Registra asientos contables para un gasto"""
        try:
            empresa = gasto.empresa
            
            # Débito: Gastos
            cuenta_gastos, _ = CuentaContable.objects.get_or_create(
                empresa=empresa,
                nombre="Gastos Operacionales",
                defaults={'tipo': 'gasto'}
            )
            
            # Crédito: Caja
            cuenta_caja, _ = CuentaContable.objects.get_or_create(
                empresa=empresa,
                nombre="Caja",
                defaults={'tipo': 'activo'}
            )
            
            MovimientoContable.objects.bulk_create([
                MovimientoContable(
                    empresa=empresa,
                    cuenta_fk=cuenta_gastos,
                    cuenta_text=cuenta_gastos.nombre,
                    tipo='debito',
                    monto=gasto.monto,
                    descripcion=gasto.descripcion
                ),
                MovimientoContable(
                    empresa=empresa,
                    cuenta_fk=cuenta_caja,
                    cuenta_text=cuenta_caja.nombre,
                    tipo='credito',
                    monto=gasto.monto,
                    descripcion=gasto.descripcion
                )
            ])
            
            logger.info(f"Gasto registrado contablemente: {gasto.id}")
            
        except Exception as e:
            logger.error(f"Error registrando gasto {gasto.id}: {str(e)}")
            raise
    
    @staticmethod
    def calcular_balance_general(empresa):
        """Calcula balance general optimizado"""
        cuentas = CuentaContable.objects.filter(empresa=empresa).prefetch_related('movimientos')
        
        balance = {
            'activos': {},
            'pasivos': {},
            'capital': {},
            'total_activos': Decimal('0'),
            'total_pasivos': Decimal('0'),
            'total_capital': Decimal('0')
        }
        
        for cuenta in cuentas:
            valor = cuenta.valor
            if cuenta.tipo == 'activo':
                balance['activos'][cuenta.nombre] = valor
                balance['total_activos'] += valor
            elif cuenta.tipo == 'pasivo':
                balance['pasivos'][cuenta.nombre] = valor
                balance['total_pasivos'] += valor
            elif cuenta.tipo == 'capital':
                balance['capital'][cuenta.nombre] = valor
                balance['total_capital'] += valor
        
        return balance