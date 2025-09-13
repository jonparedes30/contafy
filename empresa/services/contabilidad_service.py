from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from empresa.models import CuentaContable, MovimientoContable
import uuid
import logging

logger = logging.getLogger(__name__)

class ContabilidadService:
    """
    Servicio centralizado para garantizar integridad contable.
    Todas las transacciones contables deben pasar por este servicio.
    """
    
    @staticmethod
    @transaction.atomic
    def crear_transaccion_contable(empresa, asientos, descripcion_general=""):
        """
        Crea una transacción contable completa y balanceada.
        
        Args:
            empresa: Instancia de Empresa
            asientos: Lista de diccionarios con estructura:
                [
                    {
                        'cuenta': 'Nombre de la cuenta',
                        'tipo_cuenta': 'activo|pasivo|capital|ingreso|gasto',
                        'tipo_movimiento': 'debito|credito',
                        'monto': Decimal('100.00'),
                        'descripcion': 'Descripción específica'
                    }
                ]
            descripcion_general: Descripción general de la transacción
        
        Returns:
            str: ID de la transacción creada
            
        Raises:
            ValidationError: Si la transacción no está balanceada
        """
        
        # Generar ID único para la transacción
        transaccion_id = str(uuid.uuid4())[:12]
        
        # Convertir todos los montos a Decimal para precisión
        for asiento in asientos:
            if not isinstance(asiento['monto'], Decimal):
                asiento['monto'] = Decimal(str(asiento['monto']))
        
        # Validar que la transacción esté balanceada
        total_debitos = sum(
            asiento['monto'] for asiento in asientos 
            if asiento['tipo_movimiento'] == 'debito'
        )
        total_creditos = sum(
            asiento['monto'] for asiento in asientos 
            if asiento['tipo_movimiento'] == 'credito'
        )
        
        if abs(total_debitos - total_creditos) > Decimal('0.01'):
            raise ValidationError(
                f"Transacción desbalanceada: Débitos={total_debitos}, Créditos={total_creditos}"
            )
        
        # Validar que hay al menos un débito y un crédito
        tiene_debito = any(a['tipo_movimiento'] == 'debito' for a in asientos)
        tiene_credito = any(a['tipo_movimiento'] == 'credito' for a in asientos)
        
        if not (tiene_debito and tiene_credito):
            raise ValidationError("La transacción debe tener al menos un débito y un crédito")
        
        # Crear los movimientos contables
        movimientos_creados = []
        
        try:
            for asiento in asientos:
                # Obtener o crear la cuenta contable
                cuenta, created = CuentaContable.objects.get_or_create(
                    empresa=empresa,
                    nombre=asiento['cuenta'],
                    defaults={'tipo': asiento['tipo_cuenta']}
                )
                
                # Crear el movimiento contable
                movimiento = MovimientoContable.objects.create(
                    empresa=empresa,
                    cuenta_fk=cuenta,
                    cuenta_text=asiento['cuenta'],
                    tipo=asiento['tipo_movimiento'],
                    monto=asiento['monto'],
                    descripcion=asiento['descripcion'],
                    transaccion_id=transaccion_id
                )
                
                movimientos_creados.append(movimiento)
                
                logger.info(
                    f"Movimiento creado: {cuenta.nombre} - {asiento['tipo_movimiento']} - ${asiento['monto']}"
                )
            
            logger.info(
                f"Transacción {transaccion_id} creada exitosamente: "
                f"Débitos=${total_debitos}, Créditos=${total_creditos}"
            )
            
            return transaccion_id
            
        except Exception as e:
            logger.error(f"Error creando transacción contable: {str(e)}")
            raise
    
    @staticmethod
    def crear_asientos_venta(empresa, venta):
        """Crea asientos contables para una venta"""
        asientos = []
        
        # 1. Débito: Caja o Cuentas por Cobrar
        cuenta_debito = 'Caja' if venta.tipo_pago == 'contado' else 'Cuentas por Cobrar'
        asientos.append({
            'cuenta': cuenta_debito,
            'tipo_cuenta': 'activo',
            'tipo_movimiento': 'debito',
            'monto': venta.monto,
            'descripcion': f'Venta {venta.tipo_pago} {venta.producto.nombre} - {venta.cantidad} unidades'
        })
        
        # 2. Crédito: IVA por Pagar (si aplica)
        if venta.iva > 0:
            asientos.append({
                'cuenta': 'IVA por Pagar',
                'tipo_cuenta': 'pasivo',
                'tipo_movimiento': 'credito',
                'monto': venta.iva,
                'descripcion': f'IVA venta {venta.producto.nombre} - {venta.tasa_iva}%'
            })
        
        # 3. Crédito: Ventas
        asientos.append({
            'cuenta': 'Ventas',
            'tipo_cuenta': 'ingreso',
            'tipo_movimiento': 'credito',
            'monto': venta.monto_neto,
            'descripcion': f'Venta {venta.producto.nombre} - {venta.cantidad} unidades'
        })
        
        # 4. Costo de Ventas (si aplica)
        costo_unitario = venta.obtener_costo_peps()
        costo_total = venta.cantidad * costo_unitario
        
        if costo_total > 0:
            asientos.extend([
                {
                    'cuenta': 'Costo de Ventas',
                    'tipo_cuenta': 'gasto',
                    'tipo_movimiento': 'debito',
                    'monto': costo_total,
                    'descripcion': f'Costo venta {venta.producto.nombre} - {venta.cantidad} unidades'
                },
                {
                    'cuenta': 'Inventario',
                    'tipo_cuenta': 'activo',
                    'tipo_movimiento': 'credito',
                    'monto': costo_total,
                    'descripcion': f'Salida inventario {venta.producto.nombre} - {venta.cantidad} unidades'
                }
            ])
        
        return ContabilidadService.crear_transaccion_contable(
            empresa, asientos, f"Venta #{venta.id}"
        )
    
    @staticmethod
    def crear_asientos_compra(empresa, compra):
        """Crea asientos contables para una compra"""
        asientos = []
        
        # 1. Débito: Inventario
        asientos.append({
            'cuenta': 'Inventario',
            'tipo_cuenta': 'activo',
            'tipo_movimiento': 'debito',
            'monto': compra.monto_neto,
            'descripcion': f'Compra {compra.producto.nombre} - {compra.cantidad} unidades'
        })
        
        # 2. Débito: IVA Crédito Fiscal (si aplica)
        if compra.iva > 0:
            asientos.append({
                'cuenta': 'IVA Crédito Fiscal',
                'tipo_cuenta': 'activo',
                'tipo_movimiento': 'debito',
                'monto': compra.iva,
                'descripcion': f'IVA compra {compra.producto.nombre} - {compra.tasa_iva}%'
            })
        
        # 3. Crédito: Caja o Cuentas por Pagar
        cuenta_credito = 'Caja' if compra.tipo_pago == 'contado' else 'Cuentas por Pagar'
        asientos.append({
            'cuenta': cuenta_credito,
            'tipo_cuenta': 'activo' if compra.tipo_pago == 'contado' else 'pasivo',
            'tipo_movimiento': 'credito',
            'monto': compra.monto,
            'descripcion': f'Pago compra {compra.producto.nombre}'
        })
        
        return ContabilidadService.crear_transaccion_contable(
            empresa, asientos, f"Compra #{compra.id}"
        )
    
    @staticmethod
    def crear_asientos_gasto(empresa, gasto):
        """Crea asientos contables para un gasto"""
        asientos = []
        
        # 1. Débito: Gastos
        asientos.append({
            'cuenta': 'Gastos',
            'tipo_cuenta': 'gasto',
            'tipo_movimiento': 'debito',
            'monto': gasto.monto,
            'descripcion': gasto.descripcion
        })
        
        # 2. Crédito: Caja o Cuentas por Pagar
        cuenta_credito = 'Caja' if gasto.tipo_pago == 'contado' else 'Cuentas por Pagar'
        asientos.append({
            'cuenta': cuenta_credito,
            'tipo_cuenta': 'activo' if gasto.tipo_pago == 'contado' else 'pasivo',
            'tipo_movimiento': 'credito',
            'monto': gasto.monto,
            'descripcion': f"{gasto.descripcion} - {gasto.get_tipo_pago_display()}"
        })
        
        return ContabilidadService.crear_transaccion_contable(
            empresa, asientos, f"Gasto #{gasto.id}"
        )
    
    @staticmethod
    def verificar_integridad_empresa(empresa):
        """
        Verifica la integridad contable de una empresa.
        Retorna un reporte con desbalances encontrados.
        """
        from collections import defaultdict
        
        movimientos = MovimientoContable.objects.filter(empresa=empresa)
        
        # Agrupar por transaccion_id
        transacciones = defaultdict(lambda: {'debitos': Decimal('0'), 'creditos': Decimal('0')})
        
        for mov in movimientos:
            tid = mov.transaccion_id or mov.descripcion  # Fallback para datos antiguos
            if mov.tipo == 'debito':
                transacciones[tid]['debitos'] += mov.monto
            else:
                transacciones[tid]['creditos'] += mov.monto
        
        # Encontrar desbalances
        desbalances = []
        for tid, totales in transacciones.items():
            diferencia = abs(totales['debitos'] - totales['creditos'])
            if diferencia > Decimal('0.01'):
                desbalances.append({
                    'transaccion_id': tid,
                    'debitos': totales['debitos'],
                    'creditos': totales['creditos'],
                    'diferencia': diferencia
                })
        
        return {
            'empresa': empresa.nombre,
            'total_transacciones': len(transacciones),
            'desbalances': desbalances,
            'integridad_ok': len(desbalances) == 0
        }