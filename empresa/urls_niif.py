from django.urls import path
from empresa.views import niif_compliance

app_name = 'niif'

urlpatterns = [
    path('dashboard/', niif_compliance.dashboard_niif, name='dashboard'),
    path('actualizar-deterioro/', niif_compliance.actualizar_deterioro_ajax, name='actualizar_deterioro_ajax'),
    path('reporte-cumplimiento/', niif_compliance.reporte_cumplimiento_niif, name='reporte_cumplimiento'),
    path('ejecutar-cierre/', niif_compliance.ejecutar_cierre_niif, name='ejecutar_cierre'),
    path('contratos-niif15/', niif_compliance.gestionar_contratos_niif15, name='contratos_niif15'),
    path('estado-situacion-financiera/', niif_compliance.estado_situacion_financiera_niif, name='estado_situacion_financiera'),
    path('estado-resultados-niif/', niif_compliance.estado_resultados_niif, name='estado_resultados_niif'),
    path('notas-explicativas/', niif_compliance.notas_explicativas_niif, name='notas_explicativas'),
    path('reporte-completo/', niif_compliance.reporte_cumplimiento_completo, name='reporte_completo'),
]