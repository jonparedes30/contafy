from django.contrib import admin
from .models import (
    Usuario, Empresa, Venta, Gasto, Producto, CuentaContable,
    Capital, Compra, MateriaPrima, ProductoManufacturado, 
    OrdenProduccion, TipoServicio, Proveedor, Cliente,
    CuentaPorCobrar, CuentaPorPagar, MetaFinanciera
)
from .models_aprendizaje import (
    ModuloAprendizaje, Leccion, ProgresoUsuario, PerfilAprendizaje, PasoCompletado
)
from .models_simulaciones import (
    TipoSimulacion, SimulacionUsuario, EscenarioSimulacion
)
from .models_audit import AsientoAudit
from empresa.services.accounting_setup import ensure_contrapartidas_for_account

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

# === ACADEMIA - MODELOS DE APRENDIZAJE ===

class LeccionInline(admin.TabularInline):
    model = Leccion
    extra = 0
    fields = ['titulo', 'slug', 'tipo', 'orden', 'puntos_xp', 'tiempo_estimado', 'dificultad', 'visible', 'activa']
    prepopulated_fields = {'slug': ('titulo',)}

@admin.register(ModuloAprendizaje)
class ModuloAprendizajeAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'slug', 'tipo_empresa', 'nivel', 'orden', 'visible', 'activo']
    list_filter = ['tipo_empresa', 'nivel', 'visible', 'activo']
    search_fields = ['nombre', 'slug']
    prepopulated_fields = {'slug': ('nombre',)}
    readonly_fields = ['creado_en', 'actualizado_en']
    inlines = [LeccionInline]
    actions = ['publicar_modulos', 'despublicar_modulos']
    
    def publicar_modulos(self, request, queryset):
        updated = queryset.update(visible=True)
        self.message_user(request, f'{updated} módulos publicados')
    publicar_modulos.short_description = 'Publicar módulos seleccionados'
    
    def despublicar_modulos(self, request, queryset):
        updated = queryset.update(visible=False)
        self.message_user(request, f'{updated} módulos despublicados')
    despublicar_modulos.short_description = 'Despublicar módulos seleccionados'

@admin.register(Leccion)
class LeccionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'slug', 'modulo', 'tipo', 'dificultad', 'puntos_xp', 'tiempo_estimado', 'visible', 'activa']
    list_filter = ['tipo', 'dificultad', 'visible', 'activa', 'modulo__tipo_empresa']
    search_fields = ['titulo', 'slug', 'contenido']
    prepopulated_fields = {'slug': ('titulo',)}
    readonly_fields = ['creado_en', 'actualizado_en']
    actions = ['publicar_lecciones', 'despublicar_lecciones']
    
    def publicar_lecciones(self, request, queryset):
        updated = queryset.update(visible=True)
        self.message_user(request, f'{updated} lecciones publicadas')
    publicar_lecciones.short_description = 'Publicar lecciones seleccionadas'
    
    def despublicar_lecciones(self, request, queryset):
        updated = queryset.update(visible=False)
        self.message_user(request, f'{updated} lecciones despublicadas')
    despublicar_lecciones.short_description = 'Despublicar lecciones seleccionadas'

class EscenarioSimulacionInline(admin.TabularInline):
    model = EscenarioSimulacion
    extra = 0
    fields = ['nombre', 'dificultad', 'puntos_max', 'activo']

@admin.register(TipoSimulacion)
class TipoSimulacionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'activo']
    list_filter = ['categoria', 'activo']
    search_fields = ['nombre']
    inlines = [EscenarioSimulacionInline]

@admin.register(EscenarioSimulacion)
class EscenarioSimulacionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_simulacion', 'dificultad', 'puntos_max', 'activo']
    list_filter = ['dificultad', 'activo', 'tipo_simulacion__categoria']
    search_fields = ['nombre', 'descripcion']

@admin.register(SimulacionUsuario)
class SimulacionUsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo_simulacion', 'estado', 'puntuacion', 'fecha_inicio', 'es_sandbox']
    list_filter = ['estado', 'es_sandbox', 'tipo_simulacion__categoria']
    search_fields = ['usuario__username']
    readonly_fields = ['fecha_inicio', 'fecha_completado']

@admin.register(ProgresoUsuario)
class ProgresoUsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'leccion', 'completada', 'puntuacion', 'intentos', 'tiempo_completado']
    list_filter = ['completada', 'leccion__modulo__tipo_empresa']
    search_fields = ['usuario__username', 'leccion__titulo']

@admin.register(PerfilAprendizaje)
class PerfilAprendizajeAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'nivel', 'xp_total', 'racha_dias', 'ultima_actividad']
    search_fields = ['usuario__username']
    readonly_fields = ['xp_para_siguiente_nivel', 'xp_porcentaje']

@admin.register(AsientoAudit)
class AsientoAuditAdmin(admin.ModelAdmin):
    list_display = ['simulacion', 'cuenta', 'tipo_movimiento', 'monto', 'creado_en']
    list_filter = ['tipo_movimiento', 'tipo_cuenta', 'creado_en']
    search_fields = ['cuenta', 'descripcion', 'transaccion_id']
    readonly_fields = ['creado_en']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('simulacion__usuario')

# Configuración del sitio admin
admin.site.site_header = 'CONTAFY - Administración'
admin.site.site_title = 'CONTAFY Admin'
admin.site.index_title = 'Panel de Administración CONTAFY'