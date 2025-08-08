from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
import json
from empresa.services.ai_comandos_service import procesar_comando_ia

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class AIComandosView(View):
    """Vista para procesar comandos de IA por texto natural"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            comando = data.get('comando', '').strip()
            
            if not comando:
                return JsonResponse({
                    'error': 'Comando vacío. Escribe algo como: "crear producto camiseta precio $15"'
                })
            
            # Procesar comando con IA
            resultado = procesar_comando_ia(
                empresa=request.user.empresa,
                usuario=request.user,
                comando=comando
            )
            
            return JsonResponse(resultado)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'})
        except Exception as e:
            return JsonResponse({'error': f'Error procesando comando: {str(e)}'})

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def procesar_comando_rapido(request):
    """Endpoint rápido para comandos de IA"""
    try:
        comando = request.POST.get('comando', '').strip()
        
        if not comando:
            return JsonResponse({'error': 'Comando requerido'})
        
        resultado = procesar_comando_ia(
            empresa=request.user.empresa,
            usuario=request.user,
            comando=comando
        )
        
        return JsonResponse(resultado)
        
    except Exception as e:
        return JsonResponse({'error': str(e)})

@login_required
def ayuda_comandos(request):
    """Devuelve ayuda sobre comandos disponibles"""
    comandos_disponibles = {
        "productos": [
            "crear producto 'Camiseta Azul' precio $15 stock 100",
            "añadir producto 'Laptop HP' precio $800 categoria 'Electrónicos'",
            "agregar producto 'Pan Integral' precio $2.50 codigo PAN001"
        ],
        "categorias": [
            "crear categoria 'Ropa Deportiva'",
            "añadir categoria 'Tecnología'"
        ],
        "clientes": [
            "crear cliente 'Juan Pérez' cedula 1234567890 telefono 0987654321",
            "añadir cliente 'Empresa ABC' ruc 1791234567001"
        ],
        "ventas": [
            "vender producto 'Camiseta' cantidad 2 cliente 'Juan'",
            "registrar venta 'Laptop' cantidad 1"
        ],
        "gastos": [
            "registrar gasto 'Alquiler oficina' $500",
            "pagar gasto 'Servicios básicos' $120"
        ],
        "reportes": [
            "generar reporte de ventas",
            "mostrar reporte de gastos",
            "crear balance general"
        ],
        "metas": [
            "crear meta de ventas $5000",
            "establecer objetivo de gastos $2000"
        ],
        "consultas": [
            "cuánto stock tengo",
            "ventas de hoy",
            "cuántos clientes tengo"
        ],
        "automatizacion": [
            "automatizar alertas de stock bajo",
            "activar recordatorios de cobros",
            "proceso de reportes mensuales"
        ]
    }
    
    return JsonResponse({
        'success': True,
        'comandos': comandos_disponibles,
        'mensaje': '🤖 Comandos disponibles para IA'
    })

@login_required
def ejemplos_comandos(request):
    """Devuelve ejemplos prácticos de comandos"""
    ejemplos = [
        {
            "comando": "crear producto 'iPhone 14' precio $999 stock 5 categoria 'Electrónicos'",
            "descripcion": "Crea un producto con todos los detalles"
        },
        {
            "comando": "vender 'Camiseta' cantidad 3 cliente 'María'",
            "descripcion": "Registra una venta específica"
        },
        {
            "comando": "gasto 'Internet' $45",
            "descripcion": "Registra un gasto rápido"
        },
        {
            "comando": "reporte de ventas",
            "descripcion": "Genera reporte del mes actual"
        },
        {
            "comando": "cuánto vendí hoy",
            "descripcion": "Consulta ventas del día"
        },
        {
            "comando": "meta de ventas $8000",
            "descripcion": "Establece meta mensual"
        },
        {
            "comando": "automatizar stock bajo",
            "descripcion": "Activa alertas automáticas"
        }
    ]
    
    return JsonResponse({
        'success': True,
        'ejemplos': ejemplos,
        'mensaje': '💡 Ejemplos de comandos de IA'
    })