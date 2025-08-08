from datetime import date, timedelta
from django.db.models import Sum, Avg, F
from django.db import models
from django.conf import settings
from empresa.models import (
    Producto, CuentaPorCobrar, Venta, Gasto, Compra, 
    CuentaContable, MovimientoContable
)

class WorkflowIA:
    """Workflows automáticos basados en eventos"""
    
    def __init__(self, empresa):
        self.empresa = empresa
    
    def detectar_stock_bajo(self):
        """Detecta productos con stock bajo y genera alertas"""
        productos_bajo_stock = Producto.objects.filter(
            empresa=self.empresa,
            stock__lte=F('stock_minimo')
        )
        
        alertas = []
        for producto in productos_bajo_stock:
            # Generar orden de compra automática
            self.generar_orden_compra_automatica(producto)
            
            # Preparar alerta
            alertas.append({
                'producto': producto.nombre,
                'stock_actual': producto.stock,
                'stock_minimo': producto.stock_minimo,
                'accion': 'Orden de compra generada'
            })
        
        return alertas
    
    def generar_orden_compra_automatica(self, producto):
        """Genera orden de compra automática"""
        cantidad_sugerida = max(producto.stock_minimo * 3, 10)
        
        # Crear compra automática
        Compra.objects.create(
            empresa=self.empresa,
            producto=producto,
            cantidad=cantidad_sugerida,
            monto=producto.precio_unitario * cantidad_sugerida,
            proveedor_nombre="Proveedor Automático",
            tipo_pago='credito'
        )
        
        # Actualizar stock
        producto.stock += cantidad_sugerida
        producto.save()
    
    def cierre_mensual_automatico(self):
        """Genera reportes automáticos al cierre del mes"""
        mes_actual = date.today().month
        anio_actual = date.today().year
        
        # Calcular métricas del mes
        ventas_mes = Venta.objects.filter(
            empresa=self.empresa,
            fecha__month=mes_actual,
            fecha__year=anio_actual
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        gastos_mes = Gasto.objects.filter(
            empresa=self.empresa,
            fecha__month=mes_actual,
            fecha__year=anio_actual
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        utilidad_mes = ventas_mes - gastos_mes
        
        reporte = {
            'periodo': f"{mes_actual}/{anio_actual}",
            'ventas': float(ventas_mes),
            'gastos': float(gastos_mes),
            'utilidad': float(utilidad_mes),
            'margen': (utilidad_mes / ventas_mes * 100) if ventas_mes > 0 else 0
        }
        
        return reporte

class RecordatoriosIA:
    """Sistema de recordatorios inteligentes"""
    
    def __init__(self, empresa):
        self.empresa = empresa
    
    def recordatorios_cobros_vencidos(self):
        """Detecta cuentas por cobrar vencidas"""
        cuentas_vencidas = CuentaPorCobrar.objects.filter(
            empresa=self.empresa,
            fecha_vencimiento__lt=date.today(),
            estado='pendiente'
        )
        
        recordatorios = []
        for cuenta in cuentas_vencidas:
            dias_vencido = (date.today() - cuenta.fecha_vencimiento).days
            
            recordatorios.append({
                'cliente': cuenta.cliente.nombre,
                'monto': float(cuenta.monto_pendiente),
                'dias_vencido': dias_vencido,
                'telefono': cuenta.cliente.telefono,
                'mensaje': f"Recordatorio: Factura vencida hace {dias_vencido} días por ${cuenta.monto_pendiente}"
            })
        
        return recordatorios
    
    def alertas_metas_mensuales(self):
        """Verifica progreso de metas mensuales"""
        from empresa.models import MetaFinanciera
        
        mes_actual = date.today().month
        anio_actual = date.today().year
        
        metas = MetaFinanciera.objects.filter(
            empresa=self.empresa,
            mes=mes_actual,
            anio=anio_actual
        )
        
        alertas_metas = []
        for meta in metas:
            progreso = meta.progreso_actual
            
            if progreso < 50 and date.today().day > 15:  # Menos del 50% a mitad de mes
                alertas_metas.append({
                    'tipo': meta.tipo,
                    'objetivo': float(meta.objetivo_mensual),
                    'progreso': progreso,
                    'estado': 'critico',
                    'mensaje': f"Meta de {meta.tipo} en riesgo: {progreso:.1f}% completado"
                })
        
        return alertas_metas

class AlertasIA:
    """Sistema de alertas críticas"""
    
    def __init__(self, empresa):
        self.empresa = empresa
    
    def monitorear_flujo_caja(self):
        """Monitorea el flujo de caja en tiempo real"""
        # Calcular saldo actual
        cuenta_caja = CuentaContable.objects.filter(
            empresa=self.empresa,
            nombre__icontains='caja'
        ).first()
        
        if not cuenta_caja:
            return None
        
        saldo_actual = cuenta_caja.valor
        umbral_critico = 1000  # Configurable
        
        if saldo_actual < umbral_critico:
            return {
                'tipo': 'flujo_caja_critico',
                'saldo_actual': float(saldo_actual),
                'umbral': umbral_critico,
                'mensaje': f"ALERTA CRÍTICA: Flujo de caja bajo: ${saldo_actual}"
            }
        
        return None
    
    def detectar_anomalias_ventas(self):
        """Detecta anomalías en patrones de venta"""
        # Ventas de hoy
        ventas_hoy = Venta.objects.filter(
            empresa=self.empresa,
            fecha__date=date.today()
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        # Promedio últimos 7 días
        hace_7_dias = date.today() - timedelta(days=7)
        ventas_7_dias = Venta.objects.filter(
            empresa=self.empresa,
            fecha__date__gte=hace_7_dias,
            fecha__date__lt=date.today()
        )
        
        if ventas_7_dias.exists():
            total_7_dias = ventas_7_dias.aggregate(total=Sum('monto'))['total'] or 0
            promedio_7_dias = total_7_dias / 7
        else:
            promedio_7_dias = 0
        
        # Si ventas de hoy son 50% menores al promedio
        if ventas_hoy < (promedio_7_dias * 0.5):
            return {
                'tipo': 'ventas_bajas',
                'ventas_hoy': float(ventas_hoy),
                'promedio_7_dias': float(promedio_7_dias),
                'diferencia_porcentual': ((ventas_hoy - promedio_7_dias) / promedio_7_dias * 100) if promedio_7_dias > 0 else 0,
                'mensaje': f"Ventas inusualmente bajas: ${ventas_hoy} vs promedio ${promedio_7_dias:.2f}"
            }
        
        return None

class WhatsAppService:
    """Servicio para envío de WhatsApp (preparado para Twilio)"""
    
    @staticmethod
    def enviar_whatsapp_automatico(numero, mensaje):
        """Envía WhatsApp automático (requiere configuración Twilio)"""
        try:
            # from twilio.rest import Client
            # client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
            # client.messages.create(
            #     from_='whatsapp:+14155238886',
            #     body=mensaje,
            #     to=f'whatsapp:{numero}'
            # )
            
            # Por ahora solo simular
            print(f"WhatsApp a {numero}: {mensaje}")
            return True
        except Exception as e:
            print(f"Error enviando WhatsApp: {e}")
            return False

# Función principal para ejecutar todos los workflows
def ejecutar_workflows_automaticos(empresa):
    """Ejecuta todos los workflows automáticos para una empresa"""
    resultados = {
        'empresa': empresa.nombre,
        'fecha_ejecucion': date.today().isoformat(),
        'workflows': {}
    }
    
    # 1. Detectar stock bajo
    workflow_ia = WorkflowIA(empresa)
    stock_bajo = workflow_ia.detectar_stock_bajo()
    resultados['workflows']['stock_bajo'] = stock_bajo
    
    # 2. Recordatorios de cobros
    recordatorios_ia = RecordatoriosIA(empresa)
    cobros_vencidos = recordatorios_ia.recordatorios_cobros_vencidos()
    resultados['workflows']['cobros_vencidos'] = cobros_vencidos
    
    # 3. Alertas de metas
    alertas_metas = recordatorios_ia.alertas_metas_mensuales()
    resultados['workflows']['alertas_metas'] = alertas_metas
    
    # 4. Monitoreo flujo de caja
    alertas_ia = AlertasIA(empresa)
    flujo_caja = alertas_ia.monitorear_flujo_caja()
    if flujo_caja:
        resultados['workflows']['flujo_caja'] = flujo_caja
    
    # 5. Detectar anomalías ventas
    anomalias_ventas = alertas_ia.detectar_anomalias_ventas()
    if anomalias_ventas:
        resultados['workflows']['anomalias_ventas'] = anomalias_ventas
    
    # Enviar alertas críticas por WhatsApp
    if empresa.telefono_whatsapp:
        alertas_criticas = []
        
        if stock_bajo:
            alertas_criticas.append(f"Stock bajo en {len(stock_bajo)} productos")
        
        if cobros_vencidos:
            total_vencido = sum(c['monto'] for c in cobros_vencidos)
            alertas_criticas.append(f"${total_vencido:.2f} en cobros vencidos")
        
        if flujo_caja:
            alertas_criticas.append(flujo_caja['mensaje'])
        
        if alertas_criticas:
            mensaje_resumen = f"ALERTAS {empresa.nombre}:\n" + "\n".join(alertas_criticas)
            WhatsAppService.enviar_whatsapp_automatico(empresa.telefono_whatsapp, mensaje_resumen)
    
    return resultados