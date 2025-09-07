from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime

@login_required
def estado_resultados_simple(request):
    from django.http import HttpResponse
    
    debug_info = []
    debug_info.append(f"DEBUG: Usuario autenticado: {request.user.is_authenticated}")
    debug_info.append(f"DEBUG: Username: {request.user.username}")
    debug_info.append(f"DEBUG: User ID: {request.user.id}")
    
    try:
        empresa = getattr(request.user, 'empresa', None)
        debug_info.append(f"DEBUG: Empresa: {empresa}")
        debug_info.append(f"DEBUG: Tiene empresa: {empresa is not None}")
        
        if empresa:
            debug_info.append(f"DEBUG: Empresa ID: {empresa.id}")
            debug_info.append(f"DEBUG: Empresa nombre: {empresa.nombre}")
        
        debug_info.append("DEBUG: Creando context...")
        
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
        
        debug_info.append(f"DEBUG: Context creado: {context}")
        debug_info.append("DEBUG: Intentando renderizar template...")
        
        # Intentar renderizar
        response = render(request, 'empresa/estado_resultado.html', context)
        debug_info.append("DEBUG: Template renderizado exitosamente!")
        return response
        
    except Exception as e:
        debug_info.append(f"ERROR: {str(e)}")
        debug_info.append(f"ERROR Tipo: {type(e).__name__}")
        import traceback
        debug_info.append(f"ERROR Traceback: {traceback.format_exc()}")
        
        # Retornar debug info como HTML
        debug_html = "<h1>DEBUG Estado Resultados</h1><pre>" + "\n".join(debug_info) + "</pre>"
        return HttpResponse(debug_html, content_type="text/html")