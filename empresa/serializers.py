from rest_framework import serializers
from .models import Producto, Empresa

class ProductoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Producto"""
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    
    class Meta:
        model = Producto
        fields = ['id', 'codigo', 'nombre', 'descripcion', 'precio_unitario', 'stock', 'empresa_nombre']
        read_only_fields = ['id']
    
    def validate_codigo(self, value):
        """Validar que el código sea único por empresa"""
        empresa = self.context['request'].user.empresa
        if Producto.objects.filter(empresa=empresa, codigo=value).exists():
            if self.instance and self.instance.codigo == value:
                return value
            raise serializers.ValidationError("Ya existe un producto con este código en tu empresa.")
        return value
    
    def create(self, validated_data):
        """Asignar automáticamente la empresa del usuario"""
        validated_data['empresa'] = self.context['request'].user.empresa
        return super().create(validated_data)

class ProductoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar productos"""
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    
    class Meta:
        model = Producto
        fields = ['id', 'codigo', 'nombre', 'precio_unitario', 'stock', 'empresa_nombre'] 