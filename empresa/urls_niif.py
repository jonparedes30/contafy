from django.urls import path
from empresa.views import niif_compliance

urlpatterns = [
    path('dashboard/', niif_compliance.dashboard_niif, name='niif_dashboard'),
    path('actualizar-deterioro/', niif_compliance.actualizar_deterioro_ajax, name='niif_actualizar_deterioro'),
    path('reporte-cumplimiento/', niif_compliance.reporte_cumplimiento_niif, name='niif_reporte_cumplimiento'),
    path('ejecutar-cierre/', niif_compliance.ejecutar_cierre_niif, name='niif_ejecutar_cierre'),
    path('contratos-niif15/', niif_compliance.gestionar_contratos_niif15, name='niif_contratos_niif15'),
    path('estado-situacion-financiera/', niif_compliance.estado_situacion_financiera_niif, name='niif_estado_situacion_financiera'),
    path('estado-resultados-niif/', niif_compliance.estado_resultados_niif, name='niif_estado_resultados_niif'),
    path('notas-explicativas/', niif_compliance.notas_explicativas_niif, name='niif_notas_explicativas'),
    path('reporte-completo/', niif_compliance.reporte_cumplimiento_completo, name='niif_reporte_completo'),
]