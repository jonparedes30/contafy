from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from empresa.services.ml_service import MLService
from empresa.services.predicciones_service import PrediccionesAvanzadas
from empresa.services.automation_service import AutomatizacionCompleta
from empresa.services.conversational_ai import ConversationalAI
import json

@login_required
def dashboard_ia_avanzado(request):
    """Dashboard con todas las funcionalidades avanzadas de IA"""
    empresa = request.user.empresa
    
    # Obtener datos de ML
    ml_service = MLService(empresa)
    predicciones_ml = ml_service.predecir_ventas_mes_siguiente()
    patrones_ml = ml_service.detectar_patrones_ventas()
    
    # Obtener predicciones avanzadas
    predicciones_service = PrediccionesAvanzadas(empresa)
    flujo_caja = predicciones_service.predecir_flujo_caja(3)
    riesgo_quiebra = predicciones_service.detectar_riesgo_quiebra()
    
    # Obtener estado de automatización
    automation = AutomatizacionCompleta(empresa)
    analisis_automatico = automation.proceso_analisis_financiero_automatico()
    
    context = {
        'empresa': empresa,
        'predicciones_ml': predicciones_ml,
        'patrones_ml': patrones_ml,
        'flujo_caja': flujo_caja,
        'riesgo_quiebra': riesgo_quiebra,
        'analisis_automatico': analisis_automatico,
        'funcionalidades_disponibles': {
            'comandos_voz': True,
            'api_movil': True,
            'ml_local': True,
            'automatizacion': True,
            'predicciones': True,
            'conversacional': True
        }
    }
    
    return render(request, 'empresa/dashboard_ia_avanzado.html', context)

@login_required
def api_estado_ia(request):
    """API para obtener estado de todas las funcionalidades de IA"""
    try:
        empresa = request.user.empresa
        
        # Estado de ML
        ml_service = MLService(empresa)
        estado_ml = ml_service.entrenar_modelo_ventas()
        
        # Estado de predicciones
        predicciones_service = PrediccionesAvanzadas(empresa)
        estado_predicciones = predicciones_service.predecir_flujo_caja(1)
        
        return JsonResponse({
            'success': True,
            'estado_ml': estado_ml,
            'estado_predicciones': estado_predicciones.get('success', False),
            'funcionalidades_activas': {
                'comandos_voz': True,
                'api_movil': True,
                'ml_local': estado_ml.get('success', False),
                'automatizacion': True,
                'predicciones': estado_predicciones.get('success', False),
                'conversacional': True
            },
            'timestamp': request.user.last_login.isoformat() if request.user.last_login else None
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error obteniendo estado de IA: {str(e)}'
        })