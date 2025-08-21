# ADMIN BÁSICO FUNCIONAL
from .admin_minimal import *

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'ruc', 'categoria', 'tipo_negocio', 'provincia', 'ciudad']
    search_fields = ['nombre', 'ruc', 'tipo_negocio', 'ciudad']
    list_filter = ['categoria', 'provincia', 'tipo_negocio']

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'empresa', 'is_superuser', 'is_active', 'date_joined']
    list_filter = ['is_superuser', 'is_active', 'empresa', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'precio_unitario', 'stock', 'empresa']
    list_filter = ['empresa', 'precio_unitario']
    search_fields = ['codigo', 'nombre', 'descripcion']
    ordering = ['codigo']

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['producto', 'cantidad', 'precio_unitario', 'monto', 'fecha', 'empresa']
    list_filter = ['empresa', 'fecha', 'producto']
    search_fields = ['producto__nombre', 'producto__codigo']
    ordering = ['-fecha']
    readonly_fields = ['monto']

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ['producto', 'cantidad', 'monto', 'fecha', 'empresa']
    list_filter = ['empresa', 'fecha', 'producto']
    search_fields = ['producto__nombre', 'producto__codigo']
    ordering = ['-fecha']

@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'monto', 'fecha', 'empresa']
    list_filter = ['empresa', 'fecha']
    search_fields = ['descripcion']
    ordering = ['-fecha']

@admin.register(CuentaContable)
class CuentaContableAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'empresa']
    list_filter = ['tipo', 'empresa']
    search_fields = ['nombre']
    ordering = ['nombre']

@admin.register(MovimientoContable)
class MovimientoContableAdmin(admin.ModelAdmin):
    list_display = ['cuenta_text', 'tipo', 'monto', 'fecha', 'empresa']
    list_filter = ['tipo', 'empresa', 'fecha']
    search_fields = ['cuenta_text', 'descripcion']
    ordering = ['-fecha']

@admin.register(Capital)
class CapitalAdmin(admin.ModelAdmin):
    list_display = ['monto', 'fecha', 'empresa']
    list_filter = ['empresa', 'fecha']
    ordering = ['-fecha']

@admin.register(CategoriaGastoKeyword)
class CategoriaGastoKeywordAdmin(admin.ModelAdmin):
    list_display = ('palabra', 'categoria', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('palabra',)


# === ADMIN PARA MANUFACTURA ===

@admin.register(MateriaPrima)
class MateriaPrimaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'unidad_medida', 'precio_unitario', 'stock_actual', 'stock_minimo', 'empresa']
    list_filter = ['empresa', 'unidad_medida', 'proveedor_principal']
    search_fields = ['codigo', 'nombre', 'descripcion']
    ordering = ['codigo']
    readonly_fields = ['creado_en', 'modificado_en', 'creado_por', 'modificado_por']


@admin.register(ProductoManufacturado)
class ProductoManufacturadoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'precio_venta', 'stock_actual', 'stock_minimo', 'activo', 'empresa']
    list_filter = ['empresa', 'activo']
    search_fields = ['codigo', 'nombre', 'descripcion']
    ordering = ['codigo']
    readonly_fields = ['creado_en', 'modificado_en', 'creado_por', 'modificado_por']


class RecetaProduccionInline(admin.TabularInline):
    model = RecetaProduccion
    extra = 1
    fields = ['materia_prima', 'cantidad_necesaria']


@admin.register(RecetaProduccion)
class RecetaProduccionAdmin(admin.ModelAdmin):
    list_display = ['producto', 'materia_prima', 'cantidad_necesaria']
    list_filter = ['producto__empresa']
    search_fields = ['producto__nombre', 'materia_prima__nombre']


@admin.register(OrdenProduccion)
class OrdenProduccionAdmin(admin.ModelAdmin):
    list_display = ['numero_orden', 'producto', 'cantidad_solicitada', 'cantidad_producida', 'estado', 'fecha_inicio', 'empresa']
    list_filter = ['empresa', 'estado', 'fecha_inicio']
    search_fields = ['numero_orden', 'producto__nombre']
    ordering = ['-creado_en']
    readonly_fields = ['creado_en', 'modificado_en', 'creado_por', 'modificado_por']


@admin.register(ConsumoMateriaPrima)
class ConsumoMateriaPrimaAdmin(admin.ModelAdmin):
    list_display = ['orden_produccion', 'materia_prima', 'cantidad_consumida', 'costo_unitario', 'costo_total', 'fecha_consumo']
    list_filter = ['empresa', 'fecha_consumo', 'orden_produccion__estado']
    search_fields = ['orden_produccion__numero_orden', 'materia_prima__nombre']
    ordering = ['-fecha_consumo']
    readonly_fields = ['costo_total', 'creado_en', 'modificado_en', 'creado_por', 'modificado_por']

# === MODELOS CRÍTICOS FALTANTES ===

@admin.register(CodigoInvitacion)
class CodigoInvitacionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'usado', 'usado_por', 'fecha_creacion']
    list_filter = ['usado', 'fecha_creacion']
    search_fields = ['codigo']
    ordering = ['-fecha_creacion']

@admin.register(MetaFinanciera)
class MetaFinancieraAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'objetivo_mensual', 'mes', 'anio', 'empresa']
    list_filter = ['tipo', 'empresa', 'anio', 'mes']
    ordering = ['-anio', '-mes']

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'numero_documento', 'telefono', 'email', 'empresa']
    list_filter = ['empresa', 'tipo_documento']
    search_fields = ['nombre', 'numero_documento', 'email']

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'ruc', 'telefono', 'email', 'empresa']
    list_filter = ['empresa']
    search_fields = ['nombre', 'ruc', 'email']

@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'activa', 'empresa']
    list_filter = ['activa', 'empresa']
    search_fields = ['nombre']

@admin.register(SolicitudAyuda)
class SolicitudAyudaAdmin(admin.ModelAdmin):
    list_display = ['asunto', 'tipo', 'estado', 'usuario', 'empresa', 'fecha_creacion']
    list_filter = ['tipo', 'estado', 'empresa']
    search_fields = ['asunto', 'mensaje']
    ordering = ['-fecha_creacion']

@admin.register(TipoServicio)
class TipoServicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio_base', 'tiempo_estimado', 'activo', 'empresa']
    list_filter = ['activo', 'empresa']
    search_fields = ['nombre', 'descripcion']

# === MODELOS DE APRENDIZAJE ===

@admin.register(ModuloAprendizaje)
class ModuloAprendizajeAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_empresa', 'orden', 'activo']
    list_filter = ['tipo_empresa', 'activo']
    search_fields = ['nombre', 'descripcion']
    ordering = ['orden']

@admin.register(Leccion)
class LeccionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'modulo', 'tipo', 'orden', 'activa']
    list_filter = ['modulo', 'tipo', 'activa']
    search_fields = ['titulo', 'descripcion']
    ordering = ['modulo', 'orden']

@admin.register(ProgresoUsuario)
class ProgresoUsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'leccion', 'completada', 'puntuacion', 'tiempo_completado']
    list_filter = ['completada', 'leccion__modulo']
    search_fields = ['usuario__username', 'leccion__titulo']
    ordering = ['-tiempo_completado']

@admin.register(PerfilAprendizaje)
class PerfilAprendizajeAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'nivel', 'xp_total', 'racha_dias']
    list_filter = ['nivel']
    search_fields = ['usuario__username']
    ordering = ['-xp_total']

@admin.register(PasoCompletado)
class PasoCompletadoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'leccion', 'paso_index', 'creado_en']
    list_filter = ['leccion__modulo']
    search_fields = ['usuario__username', 'leccion__nombre']
    ordering = ['-creado_en']

# Configuración del sitio admin
admin.site.site_header = "Contafy - Panel de Administración"
admin.site.site_title = "Contafy Admin"
admin.site.index_title = "Bienvenido al Panel de Administración de Contafy"
