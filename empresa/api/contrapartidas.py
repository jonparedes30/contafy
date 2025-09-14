from rest_framework.decorators import api_view
from rest_framework.response import Response
from empresa.services.accounting_setup import DEFAULT_CONTRAPARTIDAS

@api_view(['GET'])
def sugerencias_contrapartidas(request):
    """API para obtener sugerencias de contrapartidas"""
    nombre_cuenta = request.GET.get('nombre', 'Nueva Cuenta')
    
    sugerencias = []
    for conf in DEFAULT_CONTRAPARTIDAS:
        sugerencias.append({
            'nombre': conf["nombre_tpl"].format(base_nombre=nombre_cuenta),
            'tipo': conf['tipo'],
            'codigo': conf['codigo_suffix']
        })
    
    return Response({'sugerencias': sugerencias})