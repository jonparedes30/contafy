from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from empresa.services.ai_agent_service import ContafyAIAgent
from empresa.services.notificaciones_service import NotificacionesService
from empresa.services.ai_comandos_service import procesar_comando_ia
import json

@login_required
def agente_ia(request):
    """Vista principal del agente de IA"""
    empresa = request.user.empresa
    agente = ContafyAIAgent()
    
    # Obtener análisis inicial
    try:
        analisis = agente.analizar_empresa(empresa)
    except Exception as e:
        analisis = {
            "resumen": "Error al generar análisis. Usando datos básicos.",
            "fortalezas": ["Empresa activa en el sistema"],
            "debilidades": ["Necesita más datos para análisis completo"],
            "oportunidades": ["Registrar más transacciones", "Configurar metas financieras"],
            "acciones_inmediatas": ["Completar información empresarial"],
            "prediccion_proximo_mes": "Depende de la actividad registrada",
            "recomendacion_principal": "Mantener registros actualizados para mejores insights"
        }
    
    return render(request, 'empresa/agente_ia.html', {
        'analisis': analisis,
        'empresa': empresa
    })

@login_required
def chat_ia(request):
    """Endpoint para chat con IA"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pregunta = data.get('pregunta', '').strip()
            
            print(f"DEBUG CHAT: Pregunta recibida: {pregunta}")
            
            if not pregunta:
                return JsonResponse({
                    'success': False,
                    'error': 'Pregunta vacía'
                })
            
            empresa = request.user.empresa
            
            # Primero intentar procesar como comando de IA
            if any(word in pregunta.lower() for word in ['crear', 'añadir', 'agregar', 'vender', 'registrar', 'gasto', 'reporte', 'meta', 'cuanto', 'automatizar']):
                resultado_comando = procesar_comando_ia(empresa, request.user, pregunta)
                
                if resultado_comando.get('success'):
                    respuesta = f"✅ {resultado_comando['mensaje']}"
                    
                    # Agregar datos adicionales si existen
                    if 'datos' in resultado_comando:
                        respuesta += "\n\nDetalles:"
                        for key, value in resultado_comando['datos'].items():
                            respuesta += f"\n• {key}: {value}"
                    
                    return JsonResponse({
                        'success': True,
                        'respuesta': respuesta,
                        'tipo': 'comando'
                    })
                else:
                    # Si falla el comando, continuar con chat normal
                    pass
            
            # Si no es comando o falló, usar chat normal
            agente = ContafyAIAgent()
            
            print(f"DEBUG CHAT: Empresa: {empresa.nombre}")
            print(f"DEBUG CHAT: Provider del agente: {agente.provider}")
            
            respuesta = agente.chat_con_usuario(empresa, pregunta)
            
            print(f"DEBUG CHAT: Respuesta generada: {respuesta[:100]}...")
            
            return JsonResponse({
                'success': True,
                'respuesta': respuesta,
                'tipo': 'chat'
            })
            
        except Exception as e:
            print(f"DEBUG CHAT: Error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Error procesando pregunta: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def generar_reporte_ia(request):
    """Genera y envía reporte de IA por email"""
    try:
        empresa = request.user.empresa
        agente = ContafyAIAgent()
        
        # Generar análisis completo
        analisis = agente.analizar_empresa(empresa)
        
        # Crear reporte en formato email
        reporte_email = f"""
🤖 REPORTE INTELIGENTE CONTAFY - {empresa.nombre}

📊 RESUMEN EJECUTIVO:
{analisis['resumen']}

💪 FORTALEZAS IDENTIFICADAS:
{chr(10).join([f"• {f}" for f in analisis['fortalezas']])}

⚠️ ÁREAS DE MEJORA:
{chr(10).join([f"• {d}" for d in analisis['debilidades']])}

🚀 OPORTUNIDADES:
{chr(10).join([f"• {o}" for o in analisis['oportunidades']])}

🎯 ACCIONES INMEDIATAS:
{chr(10).join([f"• {a}" for a in analisis['acciones_inmediatas']])}

🔮 PREDICCIÓN PRÓXIMO MES:
{analisis['prediccion_proximo_mes']}

💡 RECOMENDACIÓN PRINCIPAL:
{analisis['recomendacion_principal']}

---
Reporte generado automáticamente por CONTAFY AI
{request.build_absolute_uri('/empresa/agente-ia/')}
        """.strip()
        
        # Enviar por email
        for usuario in empresa.usuarios.all():
            if usuario.email:
                NotificacionesService.enviar_email(
                    usuario.email,
                    f'Reporte Inteligente - {empresa.nombre}',
                    reporte_email,
                    empresa
                )
        
        # Enviar por WhatsApp si está configurado
        if empresa.telefono_whatsapp:
            whatsapp_mensaje = f"""
🤖 REPORTE IA - {empresa.nombre}

{analisis['resumen']}

💡 RECOMENDACIÓN CLAVE:
{analisis['recomendacion_principal']}

📧 Revisa tu email para el reporte completo.
            """.strip()
            
            NotificacionesService.enviar_whatsapp(
                empresa.telefono_whatsapp,
                whatsapp_mensaje,
                empresa
            )
        
        messages.success(request, 'Reporte inteligente enviado por email y WhatsApp')
        
    except Exception as e:
        messages.error(request, f'Error generando reporte: {str(e)}')
    
    return JsonResponse({'success': True})

@login_required
def actualizar_analisis(request):
    """Actualiza el análisis de IA"""
    try:
        empresa = request.user.empresa
        agente = ContafyAIAgent()
        
        analisis = agente.analizar_empresa(empresa)
        
        return JsonResponse({
            'success': True,
            'analisis': analisis
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error actualizando análisis: {str(e)}'
        })