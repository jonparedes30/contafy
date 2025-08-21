app_name = "empresa"
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.api import ProductoViewSet
from .views.api_comercio import (
    categorias_api, categoria_delete_api, clientes_api, 
    proveedores_api, cuentas_cobrar_api, cuentas_pagar_api
)

# Importar vistas específicas
from .views.autenticacion import login_usuario, logout_usuario, registrar_usuario
from .views.empresa import crear_empresa, listar_empresas, gestion_poderes_empleado, crear_empleado, home, eliminar_empleado
from .views.entrada_beta import entrada_beta
from .views.productos import crear_producto, listar_productos, editar_producto, eliminar_producto
from .views.ventas import crear_venta, listar_ventas
from .views.compras import crear_compra, listar_compras
from .views.gastos import crear_gasto, listar_gastos
from .views.capital import crear_capital, listar_capital
from .views.cuentas_contables import crear_cuenta_contable, listar_cuentas_contables
from .views.dashboard import dashboard
from .views.dashboards import dashboard_ventas, dashboard_inventario, dashboard_gastos, dashboard_productos, dashboard_metas, dashboard_basico
from .views.contabilidad import estado_resultados, balance_general, flujo_caja
from .views.resumen import resumen_financiero
from .views.exportaciones import exportar_excel_ventas, exportar_excel_compras, exportar_excel_gastos, exportar_excel_inventario, exportar_pdf, exportar_pdf_usuario, exportar_pdf_profesional, exportar_pdf_inventario, exportar_excel_completo, exportar_excel_iva, exportar_pdf_iva
from .views.metas import gestionar_metas, historial_meta, marcar_notificacion_leida
from .views.inventario import inventario, descargar_plantilla_inventario, subir_inventario_excel, saldos_iniciales, inventario_detallado_inicial
from .views.actividad import actividad_reciente, asignar_usuarios_auditoria
from .views.test_filtros import test_filtros_fecha, verificar_datos_fecha
from .views.barcode_api import buscar_por_codigo_barras, validar_codigo_barras, crear_categoria_api, materias_primas_api
from .views.manufactura import (
    dashboard_manufactura, listar_materias_primas, crear_materia_prima,
    listar_productos_manufacturados, crear_producto_manufacturado,
    editar_producto_manufacturado,
    listar_ordenes_produccion, crear_orden_produccion, detalle_orden_produccion,
    iniciar_produccion, completar_produccion, cambiar_estado_producto,
    crear_proveedor_ajax, editar_materia_prima
)
from .views.proveedores_simple import listar_proveedores_simple
from .views.ventas_manufactura import crear_venta_manufactura, listar_ventas_manufactura
from .views.asistente import asistente_ayuda, historial_solicitudes
from .views.exportaciones_mejoradas import (
    exportaciones_comercio, exportaciones_manufactura,
    exportar_excel_ventas_manufactura, exportar_pdf_comercio_bancario, exportar_pdf_comercio_interno,
    exportar_pdf_manufactura_bancario, exportar_pdf_manufactura_interno
)
from .views.exportaciones_manufactura import exportar_excel_materias_primas, exportar_excel_productos_manufacturados, exportar_excel_ordenes_produccion
from .views.gestion_deudas import gestion_deudas, registrar_pago_cobrar, registrar_pago_pagar, api_cuentas_cobrar, api_cuentas_pagar
from .views.servicios import listar_tipos_servicios, crear_tipo_servicio, editar_tipo_servicio, eliminar_tipo_servicio
from .views.voice_commands import procesar_comando_voz
from .views.mobile_api import chat_movil, dashboard_movil, comando_rapido_movil
from .views.ai_agent import agente_ia, chat_ia, generar_reporte_ia, actualizar_analisis
from .views.aprendizaje import dashboard_aprendizaje, modulo_detalle, leccion_detalle, perfil_usuario, simulacion_venta, simulacion_receta, simulacion_servicio, paso_completado
from .views import social
from .views.simulaciones_api import simulacion_tipos_api, simulacion_escenarios_api, simulacion_start_api, simulacion_step_api, simulacion_result_api
from .views.recomendaciones_api import obtener_recomendaciones_api, registrar_interaccion_api, obtener_siguiente_leccion_api
from .views.ranking_api import ranking_semanal_api, ligas_activas_api, inscribir_liga_api, retos_activos_api, ranking_view
from .views.admin_simple import admin_dashboard, crear_codigo_invitacion

# Configurar router para la API
router = DefaultRouter()
router.register(r'productos', ProductoViewSet, basename='producto')

urlpatterns = [
    # URL principal - Entrada beta
    path('', entrada_beta, name='entrada_beta'),
    path('home/', home, name='home'),
    
    # URLs de la API REST
    path('api/', include(router.urls)),
    
    # URLs de autenticación
    path('login/', login_usuario, name='login'),
    path('logout/', logout_usuario, name='logout'),
    path('registro/', registrar_usuario, name='registro'),
    
    # URLs de empresa
    path('crear/', crear_empresa, name='crear_empresa'),
    path('listar/', listar_empresas, name='listar_empresas'),
    path('crear_empleado/', crear_empleado, name='crear_empleado'),
    path('empresa/<int:empresa_id>/empleado/<int:empleado_id>/poderes/', gestion_poderes_empleado, name='gestion_poderes_empleado'),
    path('empleado/<int:empleado_id>/eliminar/', eliminar_empleado, name='eliminar_empleado'),
    
    # URLs de productos
    path('producto/crear/', crear_producto, name='crear_producto'),
    path('producto/listar/', listar_productos, name='listar_productos'),
    path('producto/<int:producto_id>/editar/', editar_producto, name='editar_producto'),
    path('producto/<int:producto_id>/eliminar/', eliminar_producto, name='eliminar_producto'),
    
    # URLs de ventas
    path('venta/crear/', crear_venta, name='crear_venta'),
    path('venta/listar/', listar_ventas, name='listar_ventas'),
    
    # URLs de compras
    path('compra/crear/', crear_compra, name='crear_compra'),
    path('compra/listar/', listar_compras, name='listar_compras'),
    
    # URLs de gastos
    path('gasto/crear/', crear_gasto, name='crear_gasto'),
    path('gasto/listar/', listar_gastos, name='listar_gastos'),
    
    # URLs de capital
    path('capital/registrar/', crear_capital, name='registrar_capital'),
    path('capital/listar/', listar_capital, name='listar_capital'),
    
    # URLs de cuentas contables
    path('cuentas/crear/', crear_cuenta_contable, name='crear_cuenta_contable'),
    path('cuentas/listar/', listar_cuentas_contables, name='listar_cuentas_contables'),
    
    # URLs de reportes
    path('dashboard/', dashboard, name='dashboard'),
    path('resumen/', resumen_financiero, name='resumen_financiero'),
    
    # URLs de dashboards rol-centrados
    path('dashboard/ventas/', dashboard_ventas, name='dashboard_ventas'),
    path('dashboard/inventario/', dashboard_inventario, name='dashboard_inventario'),
    path('dashboard/gastos/', dashboard_gastos, name='dashboard_gastos'),
    path('dashboard/productos/', dashboard_productos, name='dashboard_productos'),
    path('dashboard/metas/', dashboard_metas, name='dashboard_metas'),
    path('dashboard/basico/', dashboard_basico, name='dashboard_basico'),
    path('estado-resultados/', estado_resultados, name='estado_resultados'),
    path('balance-general/', balance_general, name='balance_general'),
    path('flujo-caja/', flujo_caja, name='flujo_caja'),
    
    # URLs de exportaciones
    path('exportar/excel/ventas/', exportar_excel_ventas, name='exportar_excel_ventas'),
    path('exportar/excel/compras/', exportar_excel_compras, name='exportar_excel_compras'),
    path('exportar/excel/gastos/', exportar_excel_gastos, name='exportar_excel_gastos'),
    path('exportar/excel/inventario/', exportar_excel_inventario, name='exportar_excel_inventario'),
    path('exportar/excel/completo/', exportar_excel_completo, name='exportar_excel_completo'),
    path('exportar/pdf/', exportar_pdf, name='exportar_pdf'),
    path('exportar/pdf/usuario/', exportar_pdf_usuario, name='exportar_pdf_usuario'),
    path('exportar/pdf/profesional/', exportar_pdf_profesional, name='exportar_pdf_profesional'),
    path('exportar/pdf/inventario/', exportar_pdf_inventario, name='exportar_pdf_inventario'),
    path('exportar/excel/iva/', exportar_excel_iva, name='exportar_excel_iva'),
    path('exportar/pdf/iva/', exportar_pdf_iva, name='exportar_pdf_iva'),
    
    # URLs de metas
    path('metas/', gestionar_metas, name='gestionar_metas'),
    path('metas/historial/<int:meta_id>/', historial_meta, name='historial_meta'),
    path('metas/notificacion/<int:notificacion_id>/leida/', marcar_notificacion_leida, name='marcar_notificacion_leida'),
    
    # URLs de actividad y auditoría
    path('actividad/', actividad_reciente, name='actividad_reciente'),
    path('actividad/asignar-usuarios/', asignar_usuarios_auditoria, name='asignar_usuarios_auditoria'),
]

urlpatterns += [
    path('inventario/', inventario, name='inventario'),
    path('inventario/descargar-plantilla/', descargar_plantilla_inventario, name='descargar_plantilla_inventario'),
    path('inventario/subir-excel/', subir_inventario_excel, name='subir_inventario_excel'),
]

urlpatterns += [
    path('saldos-iniciales/', saldos_iniciales, name='saldos_iniciales'),
    path('inventario-detallado-inicial/', inventario_detallado_inicial, name='inventario_detallado_inicial'),
    
    # URLs de prueba para filtros
    path('test/filtros/', test_filtros_fecha, name='test_filtros_fecha'),
    path('test/verificar-fecha/', verificar_datos_fecha, name='verificar_datos_fecha'),
    
    # URLs para API de códigos de barras
    path('api/buscar-codigo-barras/', buscar_por_codigo_barras, name='buscar_codigo_barras'),
    path('api/validar-codigo-barras/', validar_codigo_barras, name='validar_codigo_barras'),
    
    # APIs de Comercio
    path('api/categorias/', categorias_api, name='categorias_api'),
    path('api/categorias/<int:categoria_id>/', categoria_delete_api, name='categoria_delete_api'),
    path('api/clientes/', clientes_api, name='clientes_api'),
    path('api/proveedores/', proveedores_api, name='proveedores_api'),
    path('api/cuentas-cobrar/', cuentas_cobrar_api, name='cuentas_cobrar_api'),
    path('api/cuentas-pagar/', cuentas_pagar_api, name='cuentas_pagar_api'),
    
    # URLs de gestión de deudas
    path('gestion-deudas/', gestion_deudas, name='gestion_deudas'),
    path('registrar-pago-cobrar/', registrar_pago_cobrar, name='registrar_pago_cobrar'),
    path('registrar-pago-pagar/', registrar_pago_pagar, name='registrar_pago_pagar'),
    
    # API para materias primas
    path('api/materias-primas/', materias_primas_api, name='materias_primas_api'),
    
    # URLs de manufactura
    path('manufactura/', dashboard_manufactura, name='dashboard_manufactura'),
    path('manufactura/materias-primas/', listar_materias_primas, name='listar_materias_primas'),
    path('manufactura/materias-primas/crear/', crear_materia_prima, name='crear_materia_prima'),
    path('manufactura/materias-primas/<int:materia_id>/editar/', editar_materia_prima, name='editar_materia_prima'),
    path('manufactura/proveedores/', listar_proveedores_simple, name='listar_proveedores'),
    path('manufactura/proveedores/crear-ajax/', crear_proveedor_ajax, name='crear_proveedor_ajax'),
    path('manufactura/productos/', listar_productos_manufacturados, name='listar_productos_manufacturados'),
    path('manufactura/productos/crear/', crear_producto_manufacturado, name='crear_producto_manufacturado'),
    path('manufactura/productos/<int:producto_id>/editar/', editar_producto_manufacturado, name='editar_producto_manufacturado'),
    path('manufactura/ordenes/', listar_ordenes_produccion, name='listar_ordenes_produccion'),
    path('manufactura/ordenes/crear/', crear_orden_produccion, name='crear_orden_produccion'),
    path('manufactura/ordenes/<int:orden_id>/', detalle_orden_produccion, name='detalle_orden_produccion'),
    path('manufactura/ordenes/<int:orden_id>/iniciar/', iniciar_produccion, name='iniciar_produccion'),
    path('manufactura/ordenes/<int:orden_id>/completar/', completar_produccion, name='completar_produccion'),
    path('manufactura/productos/<int:producto_id>/cambiar-estado/', cambiar_estado_producto, name='cambiar_estado_producto'),
    
    # URLs de ventas para manufactura
    path('manufactura/ventas/', listar_ventas_manufactura, name='listar_ventas_manufactura'),
    path('manufactura/ventas/crear/', crear_venta_manufactura, name='crear_venta_manufactura'),
    
    # URLs de servicios
    path('servicios/', listar_tipos_servicios, name='listar_tipos_servicios'),
    path('servicios/crear/', crear_tipo_servicio, name='crear_tipo_servicio'),
    path('servicios/<int:servicio_id>/editar/', editar_tipo_servicio, name='editar_tipo_servicio'),
    path('servicios/<int:servicio_id>/eliminar/', eliminar_tipo_servicio, name='eliminar_tipo_servicio'),
    
    # URLs del asistente de ayuda global
    path('asistente/', asistente_ayuda, name='asistente_ayuda'),
    path('asistente/historial/', historial_solicitudes, name='historial_solicitudes'),
    
    # URLs de páginas de exportaciones
    path('exportaciones/comercio/', exportaciones_comercio, name='exportaciones_comercio'),
    path('exportaciones/manufactura/', exportaciones_manufactura, name='exportaciones_manufactura'),
    
    # URLs de exportaciones para manufactura
    path('manufactura/exportar/excel/materias-primas/', exportar_excel_materias_primas, name='exportar_excel_materias_primas'),
    path('manufactura/exportar/excel/productos/', exportar_excel_productos_manufacturados, name='exportar_excel_productos_manufacturados'),
    path('manufactura/exportar/excel/ordenes/', exportar_excel_ordenes_produccion, name='exportar_excel_ordenes_produccion'),
    path('manufactura/exportar/excel/ventas/', exportar_excel_ventas_manufactura, name='exportar_excel_ventas_manufactura'),
    path('manufactura/exportar/pdf/bancario/', exportar_pdf_manufactura_bancario, name='exportar_pdf_manufactura_bancario'),
    path('manufactura/exportar/pdf/interno/', exportar_pdf_manufactura_interno, name='exportar_pdf_manufactura_interno'),
    
    # URLs de exportaciones para comercio
    path('comercio/exportar/pdf/bancario/', exportar_pdf_comercio_bancario, name='exportar_pdf_comercio_bancario'),
    path('comercio/exportar/pdf/interno/', exportar_pdf_comercio_interno, name='exportar_pdf_comercio_interno'),
    
    # URL de valuación de empresa
    path('valuacion/', lambda request: __import__('empresa.views.valuacion', fromlist=['valuacion_empresa']).valuacion_empresa(request), name='valuacion_empresa'),
    
    # URL para responder solicitudes desde web
    path('responder/<int:solicitud_id>/', lambda request, solicitud_id: __import__('empresa.views.responder_solicitud', fromlist=['responder_solicitud_web']).responder_solicitud_web(request, solicitud_id), name='responder_solicitud_web'),
    
    # URLs del Agente de IA
    path('agente-ia/', agente_ia, name='agente_ia'),
    path('chat-ia/', chat_ia, name='chat_ia'),
    path('generar-reporte-ia/', generar_reporte_ia, name='generar_reporte_ia'),
    path('actualizar-analisis/', actualizar_analisis, name='actualizar_analisis'),
    
    # URLs del Sistema de Aprendizaje
    path('aprendizaje/', dashboard_aprendizaje, name='aprendizaje_dashboard'),
    path('aprendizaje/modulo/<int:modulo_id>/', modulo_detalle, name='aprendizaje_modulo'),
    path('aprendizaje/leccion/<int:leccion_id>/', leccion_detalle, name='aprendizaje_leccion'),
    path('aprendizaje/perfil/', perfil_usuario, name='aprendizaje_perfil'),
    path('aprendizaje/paso-completado/', paso_completado, name='aprendizaje_paso_completado'),
    
    # URLs Sociales (Fase 5)
    path('aprendizaje/social/', social.dashboard_social, name='social_dashboard'),
    path('aprendizaje/social/crear-reto/', social.crear_reto, name='crear_reto'),
    path('aprendizaje/social/compartir-logro/', social.compartir_logro, name='compartir_logro'),
    path('aprendizaje/social/toggle-like/', social.toggle_like_logro, name='toggle_like_logro'),
    path('aprendizaje/social/clasificacion/', social.clasificacion_completa, name='clasificacion_completa'),
    path('aprendizaje/social/mis-retos/', social.mis_retos, name='mis_retos'),
    path('aprendizaje/social/feed/', social.feed_social, name='feed_social'),
    # APIs de Simulaciones
    path('api/simulacion/tipos/', simulacion_tipos_api, name='simulacion_tipos_api'),
    path('api/simulacion/escenarios/', simulacion_escenarios_api, name='simulacion_escenarios_api'),
    path('api/simulacion/start/', simulacion_start_api, name='simulacion_start_api'),
    path('api/simulacion/<int:simulacion_id>/step/', simulacion_step_api, name='simulacion_step_api'),
    path('api/simulacion/<int:simulacion_id>/result/', simulacion_result_api, name='simulacion_result_api'),
    
    # APIs de Recomendaciones
    path('api/recomendaciones/', obtener_recomendaciones_api, name='recomendaciones_api'),
    path('api/recomendaciones/interaccion/', registrar_interaccion_api, name='registrar_interaccion_api'),
    path('api/recomendaciones/siguiente/', obtener_siguiente_leccion_api, name='siguiente_leccion_api'),
    
    # APIs de Ranking y Ligas
    path('api/ranking/semanal/', ranking_semanal_api, name='ranking_semanal_api'),
    path('api/ligas/activas/', ligas_activas_api, name='ligas_activas_api'),
    path('api/ligas/<int:liga_id>/inscribir/', inscribir_liga_api, name='inscribir_liga_api'),
    path('api/retos/activos/', retos_activos_api, name='retos_activos_api'),
    
    # Vista de Ranking
    path('aprendizaje/ranking/', ranking_view, name='aprendizaje_ranking'),
    
    # URLs de Simulaciones
    path('aprendizaje/simulacion/venta/', simulacion_venta, name='simulacion_venta'),
    path('aprendizaje/simulacion/venta/<int:leccion_id>/', simulacion_venta, name='simulacion_venta_leccion'),
    path('aprendizaje/simulacion/receta/', simulacion_receta, name='simulacion_receta'),
    path('aprendizaje/simulacion/receta/<int:leccion_id>/', simulacion_receta, name='simulacion_receta_leccion'),
    path('aprendizaje/simulacion/servicio/', simulacion_servicio, name='simulacion_servicio'),
    path('aprendizaje/simulacion/servicio/<int:leccion_id>/', simulacion_servicio, name='simulacion_servicio_leccion'),
    
    # URLs de Reportes IA
    path('reporte-ia/', lambda request: __import__('empresa.views.ai_reports', fromlist=['vista_reporte_ia']).vista_reporte_ia(request), name='vista_reporte_ia'),
    path('reporte-ia/pdf/', lambda request: __import__('empresa.views.ai_reports', fromlist=['generar_reporte_ia_pdf']).generar_reporte_ia_pdf(request), name='generar_reporte_ia_pdf'),
    
    # URLs de Comandos IA
    path('ai-comandos/', lambda request: __import__('django.shortcuts', fromlist=['render']).render(request, 'empresa/ai_comandos.html'), name='ai_comandos_page'),
    path('api/ai-comandos/', lambda request: __import__('empresa.views.ai_comandos', fromlist=['AIComandosView']).AIComandosView.as_view()(request), name='ai_comandos'),
    path('api/comando-rapido/', lambda request: __import__('empresa.views.ai_comandos', fromlist=['procesar_comando_rapido']).procesar_comando_rapido(request), name='comando_rapido'),
    path('api/ayuda-comandos/', lambda request: __import__('empresa.views.ai_comandos', fromlist=['ayuda_comandos']).ayuda_comandos(request), name='ayuda_comandos'),
    path('api/ejemplos-comandos/', lambda request: __import__('empresa.views.ai_comandos', fromlist=['ejemplos_comandos']).ejemplos_comandos(request), name='ejemplos_comandos'),
    
    # URLs de nuevas funcionalidades IA
    path('api/comando-voz/', procesar_comando_voz, name='comando_voz'),
    path('api/chat-movil/', chat_movil, name='chat_movil'),
    path('api/dashboard-movil/', dashboard_movil, name='dashboard_movil'),
    path('api/comando-rapido-movil/', comando_rapido_movil, name='comando_rapido_movil'),
    
    # URLs del Admin Simple
    path('admin-simple/', admin_dashboard, name='admin_simple'),
    path('admin-simple/crear-codigo/', crear_codigo_invitacion, name='crear_codigo_invitacion'),
    
    # URLs de mensajería (deshabilitadas hasta migrar DB)
    # path('bandeja/', lambda request: __import__('empresa.views.mensajeria', fromlist=['bandeja_entrada']).bandeja_entrada(request), name='bandeja_entrada'),
    # path('conversacion/<int:conversacion_id>/', lambda request, conversacion_id: __import__('empresa.views.mensajeria', fromlist=['ver_conversacion']).ver_conversacion(request, conversacion_id), name='ver_conversacion'),
    # path('admin/conversacion/<int:conversacion_id>/', lambda request, conversacion_id: __import__('empresa.views.mensajeria', fromlist=['responder_conversacion']).responder_conversacion(request, conversacion_id), name='responder_conversacion'),
]
