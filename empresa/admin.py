from django.contrib import admin
from .models import (
    Usuario, Empresa, Venta, Gasto, Producto, CuentaContable,
    Capital, Compra, MateriaPrima, ProductoManufacturado, 
    OrdenProduccion, TipoServicio, Proveedor, Cliente,
    CuentaPorCobrar, CuentaPorPagar, MetaFinanciera
)

# Configuración básica del admin - solo campos seguros
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_superuser', 'is_active']
    list_filter = ['is_superuser', 'is_active']
    search_fields = ['username', 'email']

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria']
    list_filter = ['categoria']
    search_fields = ['nombre']

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'empresa', 'fecha']
    list_filter = ['fecha', 'empresa']
    date_hierarchy = 'fecha'

@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'monto', 'fecha', 'empresa']
    list_filter = ['fecha', 'empresa']
    search_fields = ['descripcion']
    date_hierarchy = 'fecha'

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'empresa']
    list_filter = ['empresa']
    search_fields = ['nombre']

@admin.register(CuentaContable)
class CuentaContableAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'empresa']
    list_filter = ['empresa']
    search_fields = ['nombre']

# Registrar otros modelos con configuración básica
admin.site.register(Capital)
admin.site.register(Compra)
admin.site.register(MateriaPrima)
admin.site.register(ProductoManufacturado)
admin.site.register(OrdenProduccion)
admin.site.register(TipoServicio)
admin.site.register(Proveedor)
admin.site.register(Cliente)
admin.site.register(CuentaPorCobrar)
admin.site.register(CuentaPorPagar)
admin.site.register(MetaFinanciera)

# Configuración del sitio admin
admin.site.site_header = 'CONTAFY - Administración'
admin.site.site_title = 'CONTAFY Admin'
admin.site.index_title = 'Panel de Administración CONTAFY'