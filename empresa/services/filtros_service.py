"""Servicio para manejar filtros de fecha y consultas optimizadas"""
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Q
from ..models import Venta, Gasto, Compra, MovimientoContable, CuentaContable


class FiltrosFechaService:
    """Servicio para aplicar filtros de fecha consistentes"""
    
    @staticmethod
    def obtener_rango_fechas(request):
        """Obtiene el rango de fechas desde los parámetros GET"""
        hoy = timezone.now().date()
        
        fecha_inicio_str = request.GET.get('fecha_inicio')
        fecha_fin_str = request.GET.get('fecha_fin')
        
        # Fecha de fin
        if fecha_fin_str:
            try:
                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            except ValueError:
                fecha_fin = hoy
        else:
            fecha_fin = hoy

        # Fecha de inicio
        if fecha_inicio_str:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            except ValueError:
                # Default: 3 meses atrás
                fecha_inicio = (fecha_fin.replace(day=1) - timedelta(days=60)).replace(day=1)
        else:
            # LÓGICA INTELIGENTE: Si no se especifican fechas, buscar dónde hay datos
            if not fecha_fin_str and hasattr(request, 'user') and hasattr(request.user, 'empresa'):
                try:
                    ultima_venta = Venta.objects.filter(empresa=request.user.empresa).order_by('-fecha').first()
                    if ultima_venta:
                        # Si hay datos, usar la fecha de la última venta como referencia
                        fecha_ultima_venta = ultima_venta.fecha.date()
                        # Si la última venta es muy antigua (más de 3 meses del default "hoy"), ajustar
                        if fecha_ultima_venta < (hoy - timedelta(days=90)) or fecha_ultima_venta > hoy:
                            fecha_fin = fecha_ultima_venta
                            # Ajustar inicio para cubrir 3 meses terminando en esta fecha
                            fecha_inicio = (fecha_fin.replace(day=1) - timedelta(days=60)).replace(day=1)
                            return fecha_inicio, fecha_fin
                except Exception:
                    pass # Fallback al default silenciando error
            
            # Default normal: 3 meses atrás desde hoy/fecha_fin
            fecha_inicio = (fecha_fin.replace(day=1) - timedelta(days=60)).replace(day=1)

        return fecha_inicio, fecha_fin
    
    @staticmethod
    def obtener_ventas_por_periodo(empresa, fecha_inicio, fecha_fin):
        """Obtiene ventas filtradas por período"""
        return Venta.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        ).aggregate(
            total=Sum('total'),
            cantidad=Sum('cantidad')
        )
    
    @staticmethod
    def obtener_gastos_por_periodo(empresa, fecha_inicio, fecha_fin):
        """Obtiene gastos filtrados por período"""
        return Gasto.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        ).aggregate(
            total=Sum('monto')
        )
    
    @staticmethod
    def obtener_compras_por_periodo(empresa, fecha_inicio, fecha_fin):
        """Obtiene compras filtradas por período"""
        return Compra.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        ).aggregate(
            total=Sum('total')
        )
    
    @staticmethod
    def obtener_movimientos_contables_por_periodo(empresa, cuenta_nombre, tipo, fecha_inicio, fecha_fin):
        """Obtiene movimientos contables filtrados por período"""
        try:
            cuenta = CuentaContable.objects.get(empresa=empresa, nombre__iexact=cuenta_nombre)
            return MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk=cuenta,
                tipo=tipo,
                fecha__date__gte=fecha_inicio,
                fecha__date__lte=fecha_fin
            ).aggregate(total=Sum('monto'))['total'] or 0
        except CuentaContable.DoesNotExist:
            return 0
    
    @staticmethod
    def obtener_datos_mensuales(empresa, fecha_inicio, fecha_fin):
        """Obtiene datos agrupados por mes en el rango especificado"""
        datos_mensuales = []
        
        # Generar lista de meses en el rango
        fecha_actual = fecha_inicio.replace(day=1)
        while fecha_actual <= fecha_fin:
            # Calcular último día del mes
            if fecha_actual.month == 12:
                ultimo_dia = fecha_actual.replace(year=fecha_actual.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                ultimo_dia = fecha_actual.replace(month=fecha_actual.month + 1, day=1) - timedelta(days=1)
            
            # Ajustar si el último día excede fecha_fin
            if ultimo_dia > fecha_fin:
                ultimo_dia = fecha_fin
            
            # Obtener datos del mes
            ventas_mes = FiltrosFechaService.obtener_ventas_por_periodo(
                empresa, fecha_actual, ultimo_dia
            )['total'] or 0
            
            gastos_mes = FiltrosFechaService.obtener_gastos_por_periodo(
                empresa, fecha_actual, ultimo_dia
            )['total'] or 0
            
            compras_mes = FiltrosFechaService.obtener_compras_por_periodo(
                empresa, fecha_actual, ultimo_dia
            )['total'] or 0
            
            datos_mensuales.append({
                'mes': fecha_actual.strftime('%b %Y'),
                'fecha_inicio': fecha_actual,
                'fecha_fin': ultimo_dia,
                'ventas': float(ventas_mes),
                'gastos': float(gastos_mes),
                'compras': float(compras_mes),
                'utilidad': float(ventas_mes - gastos_mes - compras_mes)
            })
            
            # Avanzar al siguiente mes
            if fecha_actual.month == 12:
                fecha_actual = fecha_actual.replace(year=fecha_actual.year + 1, month=1)
            else:
                fecha_actual = fecha_actual.replace(month=fecha_actual.month + 1)
        
        return datos_mensuales
    
    @staticmethod
    def validar_fechas(fecha_inicio, fecha_fin):
        """Valida que las fechas sean coherentes"""
        errores = []
        
        if fecha_inicio > fecha_fin:
            errores.append("La fecha de inicio no puede ser posterior a la fecha de fin")
        
        if fecha_fin > timezone.now().date():
            errores.append("La fecha de fin no puede ser futura")
        
        # Validar que el rango no sea excesivamente largo (más de 2 años)
        if (fecha_fin - fecha_inicio).days > 730:
            errores.append("El rango de fechas no puede exceder 2 años")
        
        return errores