from django.http import JsonResponse
from empresa.models import Producto

def obtener_info_producto(request):
    """Devuelve información del producto al escanear el código."""
    codigo = request.GET.get('codigo')
    producto = Producto.objects.filter(codigo=codigo).first()
    if producto:
        data = {
            'id': producto.id,
            'nombre': producto.nombre,
            'precio_unitario': float(producto.precio_unitario),
            'stock': producto.stock,
        }
    else:
        data = {'error': 'Producto no encontrado'}
    return JsonResponse(data)
