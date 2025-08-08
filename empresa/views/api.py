from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from ..models import Producto
from ..serializers import ProductoSerializer, ProductoListSerializer

class ProductoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la API de productos
    Permite CRUD completo de productos con autenticación por token
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProductoSerializer
    
    def get_queryset(self):
        """Filtrar productos por empresa del usuario autenticado"""
        return Producto.objects.filter(empresa=self.request.user.empresa)
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listar"""
        if self.action == 'list':
            return ProductoListSerializer
        return ProductoSerializer
    
    def perform_create(self, serializer):
        """Asignar empresa automáticamente"""
        serializer.save(empresa=self.request.user.empresa)
    
    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """
        Buscar productos por código o nombre
        GET /api/productos/buscar/?q=termino
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Parámetro "q" requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        productos = self.get_queryset().filter(
            Q(codigo__icontains=query) | Q(nombre__icontains=query)
        )[:10]  # Limitar a 10 resultados
        
        serializer = ProductoListSerializer(productos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stock_bajo(self, request):
        """
        Obtener productos con stock bajo (menos de 10 unidades)
        GET /api/productos/stock_bajo/
        """
        productos = self.get_queryset().filter(stock__lt=10)
        serializer = ProductoListSerializer(productos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def actualizar_stock(self, request, pk=None):
        """
        Actualizar stock de un producto
        PATCH /api/productos/{id}/actualizar_stock/
        """
        producto = self.get_object()
        nuevo_stock = request.data.get('stock')
        
        if nuevo_stock is None:
            return Response({'error': 'Campo "stock" requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            nuevo_stock = int(nuevo_stock)
            if nuevo_stock < 0:
                return Response({'error': 'El stock no puede ser negativo'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': 'El stock debe ser un número entero'}, status=status.HTTP_400_BAD_REQUEST)
        
        producto.stock = nuevo_stock
        producto.save()
        
        serializer = ProductoSerializer(producto)
        return Response(serializer.data) 