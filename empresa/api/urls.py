from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Contenido
    path('modulos/', views.modulos_list, name='modulos-list'),
    path('lecciones/', views.lecciones_list, name='lecciones-list'),
    path('lecciones/<int:leccion_id>/', views.leccion_detail, name='leccion-detail'),
    path('escenarios/', views.escenarios_list, name='escenarios-list'),
    
    # Simulaciones
    path('simulacion/start/', views.simulacion_start, name='simulacion-start'),
    path('simulacion/<int:simulacion_id>/', views.simulacion_detail, name='simulacion-detail'),
    path('simulacion/<int:simulacion_id>/guardar/', views.simulacion_guardar, name='simulacion-guardar'),
    path('simulacion/<int:simulacion_id>/finalizar/', views.simulacion_finalizar, name='simulacion-finalizar'),
    
    # Progreso y recomendaciones
    path('progreso/', views.progreso_usuario, name='progreso-usuario'),
    path('recomendaciones/', views.recomendaciones, name='recomendaciones'),
]