from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from empresa.models import Venta, Gasto, Producto, MetaFinanciera
from empresa.services.ai_agent_service import ContafyAIAgent
from empresa.services.ai_comandos_service import procesar_comando_ia
from datetime import datetime, date
import json

@login_required
@csrf_exempt
def dashboard_movil(request):
    """Dashboard optimizado para móviles"""
    empresa = request.user.empresa
    hoy = date.today()
    
    # Datos del día
    ventas_hoy = Venta.objects.filter(
        empresa=empresa,
        fecha__date=hoy
    ).aggregate(total=Sum('monto'))['total'] or 0
    
    gastos_hoy = Gasto.objects.filter(
        empresa=empresa,
        fecha__date=hoy
    ).aggregate(total=Sum('monto'))['total'] or 0
    
    # Productos con stock bajo
    productos_stock_bajo = Producto.objects.filter(
        empresa=empresa,
        stock__lte=5
    ).count()
    
    # Meta del mes
    meta_mes = MetaFinanciera.objects.filter(
        empresa=empresa,
        mes=hoy.month,
        anio=hoy.year,
        tipo='ventas'
    ).first()
    
    progreso_meta = 0
    if meta_mes:
        progreso_meta = meta_mes.progreso_actual
    
    return JsonResponse({
        'success': True,
        'dashboard': {
            'ventas_hoy': float(ventas_hoy),
            'gastos_hoy': float(gastos_hoy),
            'utilidad_hoy': float(ventas_hoy - gastos_hoy),
            'productos_stock_bajo': productos_stock_bajo,
            'progreso_meta': round(progreso_meta, 1),
            'fecha': hoy.strftime('%Y-%m-%d')
        },
        'acciones_rapidas': [
            {'id': 'nueva_venta', 'titulo': 'Nueva Venta', 'icono': 'cart-plus'},
            {'id': 'nuevo_gasto', 'titulo': 'Nuevo Gasto', 'icono': 'receipt'},
            {'id': 'ver_stock', 'titulo': 'Ver Stock', 'icono': 'boxes'},
            {'id': 'chat_ia', 'titulo': 'Chat IA', 'icono': 'robot'}
        ]
    })

@login_required
@csrf_exempt
def chat_movil(request):
    """Chat IA optimizado para móviles"""
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
            
            # Detectar si es comando ejecutable
            es_comando = any(word in pregunta.lower() for word in [
                'crear', 'vender', 'registrar', 'gasto', 'producto'
            ])
            
            if es_comando:
                resultado = procesar_comando_ia(empresa, request.user, pregunta)
                
                return JsonResponse({
                    'success': resultado.get('success', False),
                    'respuesta': resultado.get('mensaje', ''),
                    'respuesta_corta': resultado.get('mensaje', '')[:100] + '...',
                    'tipo': 'comando',
                    'requiere_confirmacion': resultado.get('requiere_confirmacion', False),
                    'acciones_sugeridas': generar_acciones_sugeridas(resultado),
                    'datos': resultado.get('datos', {})
                })
            else:
                # Chat normal
                respuesta = agente.chat_con_usuario(empresa, pregunta)
                
                return JsonResponse({
                    'success': True,
                    'respuesta': respuesta,
                    'respuesta_corta': respuesta[:150] + '...' if len(respuesta) > 150 else respuesta,
                    'tipo': 'chat',
                    'acciones_sugeridas': generar_acciones_contextuales(pregunta)
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
@csrf_exempt
def venta_rapida_movil(request):
    """Registro rápido de venta desde móvil"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Buscar producto por código o nombre
            producto_query = data.get('producto', '')
            cantidad = int(data.get('cantidad', 1))
            
            producto = Producto.objects.filter(
                empresa=request.user.empresa
            ).filter(
                models.Q(codigo__icontains=producto_query) |
                models.Q(nombre__icontains=producto_query)
            ).first()
            
            if not producto:
                return JsonResponse({
                    'success': False,
                    'error': 'Producto no encontrado'
                })
            
            if producto.stock < cantidad:
                return JsonResponse({
                    'success': False,
                    'error': f'Stock insuficiente. Disponible: {producto.stock}'
                })
            
            # Crear venta
            venta = Venta.objects.create(
                empresa=request.user.empresa,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.pvp,
                monto=producto.pvp * cantidad,
                cliente_nombre='Cliente Móvil',
                tipo_pago='contado'
            )
            
            # Actualizar stock
            producto.stock -= cantidad
            producto.save()
            
            return JsonResponse({
                'success': True,
                'mensaje': f'Venta registrada: {cantidad}x {producto.nombre}',
                'venta': {
                    'id': venta.id,
                    'producto': producto.nombre,
                    'cantidad': cantidad,
                    'total': float(venta.monto),
                    'stock_restante': producto.stock
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error registrando venta: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def productos_movil(request):
    """Lista de productos optimizada para móvil"""
    productos = Producto.objects.filter(
        empresa=request.user.empresa
    ).order_by('nombre')[:50]  # Limitar para móvil
    
    productos_data = []
    for p in productos:
        productos_data.append({
            'id': p.id,
            'codigo': p.codigo,
            'nombre': p.nombre,
            'precio': float(p.pvp),
            'stock': p.stock,
            'stock_bajo': p.stock <= p.stock_minimo,
            'disponible': p.stock > 0
        })
    
    return JsonResponse({
        'success': True,
        'productos': productos_data,
        'total': len(productos_data)
    })

def generar_acciones_sugeridas(resultado):
    """Genera acciones sugeridas basadas en el resultado"""
    acciones = []
    
    if resultado.get('success'):
        if 'producto' in resultado.get('mensaje', '').lower():
            acciones.append({'accion': 'ver_productos', 'titulo': 'Ver Productos'})
        if 'venta' in resultado.get('mensaje', '').lower():
            acciones.append({'accion': 'ver_ventas', 'titulo': 'Ver Ventas'})
    else:
        acciones.append({'accion': 'ayuda', 'titulo': 'Ver Ayuda'})
    
    return acciones

def generar_acciones_contextuales(pregunta):
    """Genera acciones contextuales basadas en la pregunta"""
    acciones = []
    
    if 'venta' in pregunta.lower():
        acciones.append({'accion': 'nueva_venta', 'titulo': 'Nueva Venta'})
    if 'gasto' in pregunta.lower():
        acciones.append({'accion': 'nuevo_gasto', 'titulo': 'Nuevo Gasto'})
    if 'producto' in pregunta.lower():
        acciones.append({'accion': 'ver_productos', 'titulo': 'Ver Productos'})
    
    return acciones