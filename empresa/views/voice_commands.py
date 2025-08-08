from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from empresa.services.ai_comandos_service import procesar_comando_ia
import json

@login_required
@csrf_exempt
def procesar_comando_voz(request):
    """Procesa comandos de voz y genera respuesta hablada"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            comando = data.get('comando', '').strip().lower()
            
            if not comando:
                return JsonResponse({
                    'success': False,
                    'error': 'Comando vacío'
                })
            
            # Procesar comando con IA
            resultado = procesar_comando_ia(request.user.empresa, request.user, comando)
            
            # Generar respuesta de voz optimizada
            respuesta_voz = generar_respuesta_voz(resultado, comando)
            
            return JsonResponse({
                'success': resultado.get('success', False),
                'mensaje': resultado.get('mensaje', 'Comando procesado'),
                'respuesta_voz': respuesta_voz,
                'actualizar_pagina': resultado.get('success', False),
                'datos': resultado.get('datos', {})
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error procesando comando de voz: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

def generar_respuesta_voz(resultado, comando_original):
    """Genera respuesta optimizada para síntesis de voz"""
    
    if not resultado.get('success'):
        return f"No pude ejecutar el comando. {resultado.get('error', '')}"
    
    # Respuestas específicas por tipo de comando
    if 'producto' in comando_original and 'crear' in comando_original:
        if resultado.get('requiere_confirmacion'):
            return "¿Confirmas crear este producto? Di sí para continuar."
        else:
            producto = resultado.get('datos', {}).get('nombre', 'producto')
            return f"Producto {producto} creado exitosamente."
    
    elif 'vender' in comando_original or 'venta' in comando_original:
        datos = resultado.get('datos', {})
        producto = datos.get('producto', 'producto')
        cantidad = datos.get('cantidad', 1)
        total = datos.get('total', 0)
        return f"Venta registrada: {cantidad} {producto} por {total} dólares."
    
    elif 'gasto' in comando_original:
        datos = resultado.get('datos', {})
        monto = datos.get('monto', 0)
        return f"Gasto de {monto} dólares registrado correctamente."
    
    elif 'reporte' in comando_original:
        return "Reporte generado. Revisa tu pantalla para ver los detalles."
    
    else:
        # Respuesta genérica
        mensaje = resultado.get('mensaje', '')
        mensaje_limpio = limpiar_para_voz(mensaje)
        return mensaje_limpio

def limpiar_para_voz(texto):
    """Limpia texto para síntesis de voz"""
    import re
    
    # Remover emojis y símbolos especiales
    texto = re.sub(r'[🤖📊💰✅❌🔍⚠️📈💡🎯🚀]', '', texto)
    texto = re.sub(r'\[.*?\]', '', texto)
    texto = texto.replace('$', 'dólares ')
    texto = texto.replace('%', ' por ciento')
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    return texto[:200]