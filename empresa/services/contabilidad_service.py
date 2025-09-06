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
    def registrar_venta_niif(venta):
        """Registra venta según NIIF 15 y NIC 2"""
        from ..models import MovimientoInventario
        
        try:
            # Crear movimiento de inventario (salida)
            MovimientoInventario.objects.create(
                empresa=venta.empresa,
                producto=venta.producto,
                tipo='salida',
                cantidad=venta.cantidad,
                costo_unitario=venta.obtener_costo_peps(),
                referencia=f'Venta #{venta.id}'
            )
            
            # Actualizar deterioro de cuentas por cobrar si es crédito
            if venta.tipo_pago == 'credito':
                from ..models import CuentaPorCobrar
                try:
                    cuenta = CuentaPorCobrar.objects.get(venta=venta)
                    cuenta.actualizar_deterioro()
                except CuentaPorCobrar.DoesNotExist:
                    pass
            
            logger.info(f"Venta NIIF registrada: {venta.id}")
            
        except Exception as e:
            logger.error(f"Error registrando venta NIIF {venta.id}: {str(e)}")
            raise
    
    @staticmethod
    def actualizar_deterioro_masivo(empresa):
        """Actualiza deterioro de todas las cuentas por cobrar"""
        from ..models import CuentaPorCobrar
        
        cuentas = CuentaPorCobrar.objects.filter(
            empresa=empresa,
            estado='pendiente'
        )
        
        actualizadas = 0
        for cuenta in cuentas:
            deterioro_anterior = cuenta.deterioro_esperado
            cuenta.actualizar_deterioro()
            
            if cuenta.deterioro_esperado != deterioro_anterior:
                actualizadas += 1
        
        logger.info(f"Deterioro actualizado para {actualizadas} cuentas")
        return actualizadas
    
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