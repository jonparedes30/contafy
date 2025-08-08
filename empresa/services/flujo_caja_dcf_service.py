"""
Servicio de Flujo de Caja con DCF y Proyecciones
Integra: flujo actual + DCF + proyecciones futuras
"""
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta, datetime
from empresa.models import MovimientoContable, CuentaContable
from decimal import Decimal

class FlujoCajaDCFService:
    
    @staticmethod
    def calcular_flujo_completo(empresa):
        """Calcula flujo de caja completo con DCF y proyecciones"""
        
        # Flujo histórico (últimos 12 meses)
        flujo_historico = FlujoCajaDCFService._calcular_flujo_historico(empresa)
        
        # Flujo actual (mes actual)
        flujo_actual = FlujoCajaDCFService._calcular_flujo_actual(empresa)
        
        # Proyecciones futuras (12 meses)
        proyecciones = FlujoCajaDCFService._calcular_proyecciones(empresa, flujo_historico)
        
        # DCF (Flujo de Caja Descontado)
        dcf_analysis = FlujoCajaDCFService._calcular_dcf(proyecciones)
        
        return {
            'flujo_historico': flujo_historico,
            'flujo_actual': flujo_actual,
            'proyecciones': proyecciones,
            'dcf_analysis': dcf_analysis,
            'resumen': FlujoCajaDCFService._generar_resumen(flujo_actual, proyecciones, dcf_analysis)
        }
    
    @staticmethod
    def _calcular_flujo_historico(empresa):
        """Calcula flujo de caja histórico por meses"""
        hoy = timezone.now()
        flujos_mensuales = []
        
        for i in range(12, 0, -1):  # Últimos 12 meses
            fecha_inicio = (hoy - timedelta(days=30*i)).replace(day=1)
            fecha_fin = (hoy - timedelta(days=30*(i-1))).replace(day=1)
            
            # Ingresos del mes
            try:
                cuenta_ventas = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Ventas')
                ingresos = MovimientoContable.objects.filter(
                    empresa=empresa, cuenta_fk=cuenta_ventas, tipo='credito',
                    fecha__gte=fecha_inicio, fecha__lt=fecha_fin
                ).aggregate(total=Sum('monto'))['total'] or 0
            except CuentaContable.DoesNotExist:
                ingresos = 0
            
            # Egresos del mes
            try:
                cuenta_gastos = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Gastos')
                egresos = MovimientoContable.objects.filter(
                    empresa=empresa, cuenta_fk=cuenta_gastos, tipo='debito',
                    fecha__gte=fecha_inicio, fecha__lt=fecha_fin
                ).aggregate(total=Sum('monto'))['total'] or 0
            except CuentaContable.DoesNotExist:
                egresos = 0
            
            # Compras/Inventario
            try:
                cuentas_inventario = CuentaContable.objects.filter(
                    empresa=empresa, 
                    nombre__in=['Inventario', 'Inventario de Materias Primas', 'Costo de Ventas']
                )
                compras = MovimientoContable.objects.filter(
                    empresa=empresa, cuenta_fk__in=cuentas_inventario, tipo='debito',
                    fecha__gte=fecha_inicio, fecha__lt=fecha_fin
                ).aggregate(total=Sum('monto'))['total'] or 0
            except:
                compras = 0
            
            flujo_neto = ingresos - egresos - compras
            
            flujos_mensuales.append({
                'mes': fecha_inicio.strftime('%Y-%m'),
                'mes_nombre': fecha_inicio.strftime('%B %Y'),
                'ingresos': float(ingresos),
                'egresos': float(egresos),
                'compras': float(compras),
                'flujo_neto': float(flujo_neto)
            })
        
        return flujos_mensuales
    
    @staticmethod
    def _calcular_flujo_actual(empresa):
        """Calcula flujo de caja del mes actual"""
        hoy = timezone.now()
        inicio_mes = hoy.replace(day=1)
        
        # Ingresos del mes actual
        try:
            cuenta_ventas = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Ventas')
            ingresos = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_ventas, tipo='credito',
                fecha__gte=inicio_mes
            ).aggregate(total=Sum('monto'))['total'] or 0
        except CuentaContable.DoesNotExist:
            ingresos = 0
        
        # Egresos del mes actual
        try:
            cuenta_gastos = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Gastos')
            egresos = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk=cuenta_gastos, tipo='debito',
                fecha__gte=inicio_mes
            ).aggregate(total=Sum('monto'))['total'] or 0
        except CuentaContable.DoesNotExist:
            egresos = 0
        
        # Compras del mes actual
        try:
            cuentas_inventario = CuentaContable.objects.filter(
                empresa=empresa, 
                nombre__in=['Inventario', 'Inventario de Materias Primas', 'Costo de Ventas']
            )
            compras = MovimientoContable.objects.filter(
                empresa=empresa, cuenta_fk__in=cuentas_inventario, tipo='debito',
                fecha__gte=inicio_mes
            ).aggregate(total=Sum('monto'))['total'] or 0
        except:
            compras = 0
        
        # Saldo de caja actual
        try:
            cuenta_caja = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Caja/Banco')
            saldo_caja = cuenta_caja.valor
        except CuentaContable.DoesNotExist:
            saldo_caja = 0
        
        flujo_neto = ingresos - egresos - compras
        
        return {
            'ingresos': float(ingresos),
            'egresos': float(egresos),
            'compras': float(compras),
            'flujo_neto': float(flujo_neto),
            'saldo_caja': float(saldo_caja),
            'dias_transcurridos': hoy.day,
            'proyeccion_mes': float(flujo_neto) * (30 / hoy.day) if hoy.day > 0 else 0
        }
    
    @staticmethod
    def _calcular_proyecciones(empresa, flujo_historico):
        """Calcula proyecciones de flujo de caja futuro"""
        if not flujo_historico:
            return []
        
        # Calcular promedios y tendencias
        ingresos_promedio = sum(f['ingresos'] for f in flujo_historico[-6:]) / 6  # Últimos 6 meses
        egresos_promedio = sum(f['egresos'] for f in flujo_historico[-6:]) / 6
        compras_promedio = sum(f['compras'] for f in flujo_historico[-6:]) / 6
        
        # Calcular tendencia de crecimiento
        if len(flujo_historico) >= 6:
            ingresos_recientes = sum(f['ingresos'] for f in flujo_historico[-3:]) / 3
            ingresos_anteriores = sum(f['ingresos'] for f in flujo_historico[-6:-3]) / 3
            tasa_crecimiento = ((ingresos_recientes - ingresos_anteriores) / ingresos_anteriores) if ingresos_anteriores > 0 else 0
        else:
            tasa_crecimiento = 0.02  # 2% por defecto
        
        # Limitar crecimiento entre -10% y +20%
        tasa_crecimiento = max(-0.10, min(0.20, tasa_crecimiento))
        
        proyecciones = []
        hoy = timezone.now()
        
        for i in range(1, 13):  # Próximos 12 meses
            fecha_proyeccion = hoy + timedelta(days=30*i)
            factor_crecimiento = (1 + tasa_crecimiento) ** i
            
            ingresos_proyectados = ingresos_promedio * factor_crecimiento
            egresos_proyectados = egresos_promedio * 1.02 ** i  # Inflación 2%
            compras_proyectadas = compras_promedio * factor_crecimiento * 0.7  # Proporcional a ventas
            
            flujo_neto_proyectado = ingresos_proyectados - egresos_proyectados - compras_proyectadas
            
            proyecciones.append({
                'mes': fecha_proyeccion.strftime('%Y-%m'),
                'mes_nombre': fecha_proyeccion.strftime('%B %Y'),
                'ingresos_proyectados': ingresos_proyectados,
                'egresos_proyectados': egresos_proyectados,
                'compras_proyectadas': compras_proyectadas,
                'flujo_neto_proyectado': flujo_neto_proyectado,
                'factor_crecimiento': factor_crecimiento
            })
        
        return proyecciones
    
    @staticmethod
    def _calcular_dcf(proyecciones):
        """Calcula el Flujo de Caja Descontado (DCF)"""
        if not proyecciones:
            return {'valor_presente_neto': 0, 'tasa_descuento': 0.15}
        
        tasa_descuento = 0.15  # 15% anual para PyMEs
        tasa_mensual = tasa_descuento / 12
        
        valor_presente_total = 0
        flujos_descontados = []
        
        for i, proyeccion in enumerate(proyecciones, 1):
            flujo_futuro = proyeccion['flujo_neto_proyectado']
            factor_descuento = (1 + tasa_mensual) ** i
            valor_presente = flujo_futuro / factor_descuento
            
            valor_presente_total += valor_presente
            
            flujos_descontados.append({
                'mes': proyeccion['mes_nombre'],
                'flujo_futuro': flujo_futuro,
                'factor_descuento': factor_descuento,
                'valor_presente': valor_presente
            })
        
        # Valor terminal (crecimiento perpetuo del 2%)
        if proyecciones:
            ultimo_flujo = proyecciones[-1]['flujo_neto_proyectado']
            crecimiento_terminal = 0.02
            valor_terminal = (ultimo_flujo * (1 + crecimiento_terminal)) / (tasa_descuento - crecimiento_terminal)
            valor_terminal_presente = valor_terminal / ((1 + tasa_descuento) ** 1)  # Descontado a 1 año
            
            valor_presente_total += valor_terminal_presente
        else:
            valor_terminal_presente = 0
        
        return {
            'valor_presente_neto': valor_presente_total,
            'valor_terminal': valor_terminal_presente,
            'tasa_descuento': tasa_descuento,
            'flujos_descontados': flujos_descontados,
            'interpretacion': FlujoCajaDCFService._interpretar_dcf(valor_presente_total)
        }
    
    @staticmethod
    def _interpretar_dcf(vpn):
        """Interpreta el resultado del DCF"""
        if vpn > 50000:
            return {
                'nivel': 'Excelente',
                'color': 'success',
                'descripcion': 'Empresa genera valor significativo'
            }
        elif vpn > 10000:
            return {
                'nivel': 'Bueno',
                'color': 'primary',
                'descripcion': 'Empresa genera valor positivo'
            }
        elif vpn > 0:
            return {
                'nivel': 'Aceptable',
                'color': 'info',
                'descripcion': 'Empresa genera valor marginal'
            }
        else:
            return {
                'nivel': 'Preocupante',
                'color': 'danger',
                'descripcion': 'Empresa destruye valor'
            }
    
    @staticmethod
    def _generar_resumen(flujo_actual, proyecciones, dcf_analysis):
        """Genera resumen ejecutivo del análisis"""
        if not proyecciones:
            return {}
        
        # Flujo promedio proyectado
        flujo_promedio_futuro = sum(p['flujo_neto_proyectado'] for p in proyecciones) / len(proyecciones)
        
        # Comparar con flujo actual
        if flujo_actual['flujo_neto'] != 0:
            mejora_esperada = ((flujo_promedio_futuro - flujo_actual['flujo_neto']) / abs(flujo_actual['flujo_neto'])) * 100
        else:
            mejora_esperada = 0
        
        # Meses con flujo positivo proyectado
        meses_positivos = sum(1 for p in proyecciones if p['flujo_neto_proyectado'] > 0)
        
        return {
            'flujo_actual_mensual': flujo_actual['flujo_neto'],
            'flujo_promedio_futuro': flujo_promedio_futuro,
            'mejora_esperada_porcentaje': mejora_esperada,
            'meses_flujo_positivo': meses_positivos,
            'total_meses_proyectados': len(proyecciones),
            'valor_presente_neto': dcf_analysis['valor_presente_neto'],
            'recomendacion': FlujoCajaDCFService._generar_recomendacion(flujo_actual, flujo_promedio_futuro, dcf_analysis)
        }
    
    @staticmethod
    def _generar_recomendacion(flujo_actual, flujo_promedio_futuro, dcf_analysis):
        """Genera recomendación basada en el análisis"""
        vpn = dcf_analysis['valor_presente_neto']
        flujo_actual_neto = flujo_actual['flujo_neto']
        
        if vpn > 10000 and flujo_actual_neto > 0:
            return {
                'tipo': 'success',
                'mensaje': 'Excelente gestión de flujo de caja. Considera inversiones para acelerar crecimiento.',
                'accion': 'Evaluar oportunidades de expansión'
            }
        elif vpn > 0 and flujo_promedio_futuro > flujo_actual_neto:
            return {
                'tipo': 'info',
                'mensaje': 'Tendencia positiva en flujo de caja. Mantén la estrategia actual.',
                'accion': 'Monitorear cumplimiento de proyecciones'
            }
        elif flujo_actual_neto < 0:
            return {
                'tipo': 'warning',
                'mensaje': 'Flujo de caja negativo requiere atención inmediata.',
                'accion': 'Revisar gastos y acelerar cobranzas'
            }
        else:
            return {
                'tipo': 'info',
                'mensaje': 'Flujo de caja estable. Busca oportunidades de optimización.',
                'accion': 'Analizar eficiencia operativa'
            }