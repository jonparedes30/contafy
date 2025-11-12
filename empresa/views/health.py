from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Health check endpoint para Render y monitoreo"""
    try:
        # Verificar conexión a base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }, status=503)
