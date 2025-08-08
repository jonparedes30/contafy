from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from empresa.services.ai_agent_service import ContafyAIAgent
from empresa.services.ai_comandos_service import procesar_comando_ia
from empresa.models import Venta, Gasto, Producto, MetaFinanciera
from django.db.models import Sum
from datetime import datetime, date
import json

@login_required
@csrf_exempt
def chat_movil(request):
    """Chat optimizado para apps móviles"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pregunta = data.get('pregunta', '').strip()
            
            if not pregunta:
                return JsonResponse({
                    'success': False,
                    'error': 'Pregunta vacía'
                })
            
            empresa = request.user.empresa
            agente = ContafyAIAgent()
            
            # Respuesta optimizada para móvil
            respuesta = agente.chat_con_usuario(empresa, pregunta)
            
            # Generar acciones sugeridas
            acciones_sugeridas = generar_acciones_movil(pregunta, empresa)
            
            return JsonResponse({
                'success': True,
                'respuesta': respuesta[:300],  # Respuesta corta para móvil
                'respuesta_completa': respuesta,
                'acciones_sugeridas': acciones_sugeridas,
                'notificaciones_push': True,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error en chat móvil: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def dashboard_movil(request):
    """Dashboard optimizado para móviles"""
    try:
        empresa = request.user.empresa
        hoy = date.today()
        
        # Datos esenciales para móvil
        ventas_hoy = Venta.objects.filter(
            empresa=empresa,
            fecha__date=hoy
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        gastos_hoy = Gasto.objects.filter(
            empresa=empresa,
            fecha__date=hoy
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        productos_bajo_stock = Producto.objects.filter(
            empresa=empresa,
            stock__lte=5
        ).count()
        
        # Metas del mes
        metas_mes = MetaFinanciera.objects.filter(
            empresa=empresa,
            mes=hoy.month,
            anio=hoy.year
        ).first()
        
        progreso_meta = 0
        if metas_mes:
            progreso_meta = metas_mes.progreso_actual
        
        return JsonResponse({
            'success': True,
            'dashboard': {
                'ventas_hoy': float(ventas_hoy),
                'gastos_hoy': float(gastos_hoy),
                'utilidad_hoy': float(ventas_hoy - gastos_hoy),
                'productos_bajo_stock': productos_bajo_stock,
                'progreso_meta': float(progreso_meta),
                'fecha': hoy.isoformat()
            },
            'alertas': generar_alertas_movil(empresa),
            'acciones_rapidas': [
                {'accion': 'nueva_venta', 'icono': 'cart-plus', 'texto': 'Nueva Venta'},
                {'accion': 'nuevo_gasto', 'icono': 'receipt', 'texto': 'Nuevo Gasto'},
                {'accion': 'ver_stock', 'icono': 'boxes', 'texto': 'Ver Stock'},
                {'accion': 'chat_ia', 'icono': 'robot', 'texto': 'Consultar IA'}
            ]
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error en dashboard móvil: {str(e)}'
        })

@login_required
@csrf_exempt
def comando_rapido_movil(request):
    """Comandos rápidos optimizados para móvil"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            comando = data.get('comando', '').strip()
            
            # Procesar comando
            resultado = procesar_comando_ia(request.user.empresa, request.user, comando)
            
            return JsonResponse({
                'success': resultado.get('success', False),
                'mensaje_corto': resultado.get('mensaje', '')[:100],
                'mensaje_completo': resultado.get('mensaje', ''),
                'datos': resultado.get('datos', {}),
                'requiere_confirmacion': resultado.get('requiere_confirmacion', False),
                'vibrar': resultado.get('success', False)  # Vibración en móvil
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error en comando móvil: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

def generar_acciones_movil(pregunta, empresa):
    """Genera acciones sugeridas para móvil"""
    pregunta_lower = pregunta.lower()
    
    if 'venta' in pregunta_lower:
        return [
            {'accion': 'crear_venta', 'texto': 'Registrar Venta'},
            {'accion': 'ver_ventas', 'texto': 'Ver Ventas Hoy'},
            {'accion': 'productos_populares', 'texto': 'Productos Populares'}
        ]
    elif 'gasto' in pregunta_lower:
        return [
            {'accion': 'crear_gasto', 'texto': 'Registrar Gasto'},
            {'accion': 'ver_gastos', 'texto': 'Ver Gastos Hoy'},
            {'accion': 'categorias_gastos', 'texto': 'Categorías'}
        ]
    elif 'stock' in pregunta_lower:
        return [
            {'accion': 'ver_stock_bajo', 'texto': 'Stock Bajo'},
            {'accion': 'crear_producto', 'texto': 'Nuevo Producto'},
            {'accion': 'actualizar_stock', 'texto': 'Actualizar Stock'}
        ]
    else:
        return [
            {'accion': 'resumen_dia', 'texto': 'Resumen del Día'},
            {'accion': 'metas_mes', 'texto': 'Metas del Mes'},
            {'accion': 'ayuda', 'texto': 'Ayuda'}
        ]

def generar_alertas_movil(empresa):
    """Genera alertas importantes para móvil"""
    alertas = []
    
    # Stock bajo
    productos_bajo = Producto.objects.filter(
        empresa=empresa,
        stock__lte=5
    ).count()
    
    if productos_bajo > 0:
        alertas.append({
            'tipo': 'warning',
            'mensaje': f'{productos_bajo} productos con stock bajo',
            'accion': 'ver_stock_bajo'
        })
    
    # Metas del mes
    hoy = date.today()
    meta = MetaFinanciera.objects.filter(
        empresa=empresa,
        mes=hoy.month,
        anio=hoy.year,
        tipo='ventas'
    ).first()
    
    if meta and meta.progreso_actual < 50 and hoy.day > 15:
        alertas.append({
            'tipo': 'danger',
            'mensaje': f'Meta de ventas en riesgo: {meta.progreso_actual:.1f}%',
            'accion': 'ver_metas'
        })
    
    return alertas