from django.contrib import admin
from .models import (
    Usuario, Empresa, Venta, Gasto, Producto, CuentaContable,
    Capital, Compra, MateriaPrima, ProductoManufacturado, 
    OrdenProduccion, TipoServicio, Proveedor, Cliente,
    CuentaPorCobrar, CuentaPorPagar, MetaFinanciera, CodigoInvitacion
)

from empresa.services.accounting_setup import ensure_contrapartidas_for_account

# Configuración básica del admin - solo campos seguros
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_superuser', 'is_active']
    list_filter = ['is_superuser', 'is_active']
    search_fields = ['username', 'email']

@admin.register(CodigoInvitacion)
class CodigoInvitacionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'usado', 'fecha_creacion', 'usado_por']
    list_filter = ['usado', 'fecha_creacion']
    search_fields = ['codigo', 'usado_por__username']
    readonly_fields = ['fecha_creacion']
    actions = ['marcar_como_no_usado']
    
    def marcar_como_no_usado(self, request, queryset):
        updated = queryset.update(usado=False, usado_por=None)
        self.message_user(request, f'{updated} códigos marcados como disponibles')
    marcar_como_no_usado.short_description = 'Marcar como no usado'

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
    list_display = ['nombre', 'empresa', 'tipo']
    list_filter = ['empresa', 'tipo']
    search_fields = ['nombre']
    actions = ['action_create_contrapartidas']

    def action_create_contrapartidas(self, request, queryset):
        total = 0
        for cuenta in queryset:
            created = ensure_contrapartidas_for_account(cuenta)
            total += len(created)
        self.message_user(request, f"Se crearon {total} contrapartidas para las cuentas seleccionadas")
    action_create_contrapartidas.short_description = "Crear contrapartidas recomendadas para la(s) cuenta(s)"

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