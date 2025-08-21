from django.contrib import admin
from .models import (
    Empresa, Usuario, CodigoInvitacion, Producto, Venta, Compra, 
    Gasto, CuentaContable, Capital
)

# Solo registrar modelos básicos y estables
@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'ruc', 'categoria', 'ciudad']
    search_fields = ['nombre', 'ruc']
    list_filter = ['categoria']

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'empresa', 'is_active', 'date_joined']
    list_filter = ['is_active', 'empresa']
    search_fields = ['username', 'email']
    ordering = ['-date_joined']

@admin.register(CodigoInvitacion)
class CodigoInvitacionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'usado', 'usado_por', 'fecha_creacion']
    list_filter = ['usado']
    search_fields = ['codigo']
    ordering = ['-fecha_creacion']

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'precio_unitario', 'stock', 'empresa']
    list_filter = ['empresa']
    search_fields = ['codigo', 'nombre']

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['producto', 'cantidad', 'monto', 'fecha', 'empresa']
    list_filter = ['empresa', 'fecha']
    ordering = ['-fecha']

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ['producto', 'cantidad', 'monto', 'fecha', 'empresa']
    list_filter = ['empresa', 'fecha']
    ordering = ['-fecha']

@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'monto', 'fecha', 'empresa']
    list_filter = ['empresa', 'fecha']
    ordering = ['-fecha']

@admin.register(CuentaContable)
class CuentaContableAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'empresa']
    list_filter = ['tipo', 'empresa']

@admin.register(Capital)
class CapitalAdmin(admin.ModelAdmin):
    list_display = ['monto', 'tipo', 'fecha', 'empresa']
    list_filter = ['tipo', 'empresa']
    ordering = ['-fecha']

# Configuración del sitio admin
admin.site.site_header = "Contafy - Admin Básico"
admin.site.site_title = "Contafy Admin"
admin.site.index_title = "Panel de Administración Básico"