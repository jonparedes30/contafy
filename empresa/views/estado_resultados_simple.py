from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@login_required
def estado_resultados_simple(request):
    try:
        logger.info(f"Estado resultados - Usuario: {request.user.username}")
        logger.info(f"Estado resultados - Empresa: {getattr(request.user, 'empresa', 'No tiene')}")
        
        context = {
            'ventas': 2500.00,
            'costos': 1200.00,
            'gastos': 600.00,
            'utilidad_bruta': 1300.00,
            'utilidad_operativa': 700.00,
            'utilidad_neta': 700.00,
            'fecha_inicio': datetime.now().replace(day=1).date(),
            'fecha_fin': datetime.now().date(),
            'formato_niif': False,
        }
        
        logger.info(f"Estado resultados - Context: {context}")
        logger.info("Estado resultados - Renderizando template")
        
        return render(request, 'empresa/estado_resultado.html', context)
        
    except Exception as e:
        logger.error(f"Error en estado_resultados_simple: {str(e)}")
        logger.error(f"Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise