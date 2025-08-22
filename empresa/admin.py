# Temporalmente deshabilitado para verificar modelos
pass

# from django.contrib import admin
# from .models import (
#     Usuario, Empresa, Venta, Gasto, Producto, CuentaContable,
#     Capital, Compra, DetalleVenta, DetalleCompra, Meta,
#     MateriaPrima, ProductoManufacturado, OrdenProduccion,
#     TipoServicio, Proveedor
# )

# TODO: Habilitar después de verificar modelos
# 
# # Configuración del admin para Usuario
# @admin.register(Usuario)
# class UsuarioAdmin(admin.ModelAdmin):
#     list_display = ['username', 'email', 'empresa', 'is_superuser', 'is_active', 'date_joined']
#     list_filter = ['is_superuser', 'is_active', 'empresa']
#     search_fields = ['username', 'email']
#     readonly_fields = ['date_joined', 'last_login']
# 
# # Configuración del admin para Empresa
# @admin.register(Empresa)
# class EmpresaAdmin(admin.ModelAdmin):
#     list_display = ['nombre', 'categoria', 'propietario', 'fecha_creacion']
#     list_filter = ['categoria', 'fecha_creacion']
#     search_fields = ['nombre', 'propietario__username']
# 
# # Configuración del admin para Venta
# @admin.register(Venta)
# class VentaAdmin(admin.ModelAdmin):
#     list_display = ['id', 'empresa', 'total', 'fecha', 'usuario']
#     list_filter = ['fecha', 'empresa']
#     search_fields = ['empresa__nombre']
#     date_hierarchy = 'fecha'
# 
# # Configuración del admin para Gasto
# @admin.register(Gasto)
# class GastoAdmin(admin.ModelAdmin):
#     list_display = ['descripcion', 'monto', 'fecha', 'empresa', 'usuario']
#     list_filter = ['fecha', 'empresa']
#     search_fields = ['descripcion', 'empresa__nombre']
#     date_hierarchy = 'fecha'
# 
# # Configuración del admin para Producto
# @admin.register(Producto)
# class ProductoAdmin(admin.ModelAdmin):
#     list_display = ['nombre', 'precio', 'stock', 'empresa']
#     list_filter = ['empresa']
#     search_fields = ['nombre', 'empresa__nombre']
# 
# # Configuración del admin para CuentaContable
# @admin.register(CuentaContable)
# class CuentaContableAdmin(admin.ModelAdmin):
#     list_display = ['codigo', 'nombre', 'tipo', 'empresa']
#     list_filter = ['tipo', 'empresa']
#     search_fields = ['codigo', 'nombre']
# 
# # Registrar otros modelos con configuración básica
# admin.site.register(Capital)
# admin.site.register(Compra)
# admin.site.register(DetalleVenta)
# admin.site.register(DetalleCompra)
# admin.site.register(Meta)
# admin.site.register(MateriaPrima)
# admin.site.register(ProductoManufacturado)
# admin.site.register(OrdenProduccion)
# admin.site.register(TipoServicio)
# admin.site.register(Proveedor)
# 
# # Configuración del sitio admin
# admin.site.site_header = 'CONTAFY - Administración'
# admin.site.site_title = 'CONTAFY Admin'
# admin.site.index_title = 'Panel de Administración CONTAFY'