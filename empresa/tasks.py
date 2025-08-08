"""
Tareas automáticas para notificaciones
"""
from django.core.management import call_command
from django.utils import timezone
from datetime import datetime, timedelta
from empresa.models import MetaFinanciera, Producto, NotificacionMeta
from empresa.services.notificaciones_service import NotificacionesService

def verificar_alertas_diarias():
    """Tarea que se ejecuta diariamente para verificar alertas"""
    call_command('verificar_alertas')

def notificar_vencimientos_productos():
    """Notifica productos próximos a vencer"""
    productos_por_vencer = Producto.objects.filter(
        fecha_vencimiento__lte=timezone.now().date() + timedelta(days=7),
        fecha_vencimiento__gt=timezone.now().date()
    )
    
    for producto in productos_por_vencer:
        mensaje = f"""
⏰ PRODUCTO POR VENCER

Producto: {producto.nombre}
Vence: {producto.fecha_vencimiento}
Días restantes: {producto.dias_para_vencer}
Stock: {producto.stock}

Revisa tu inventario en CONTAFY.
        """.strip()
        
        empresa = producto.empresa
        for usuario in empresa.usuarios.all():
            if usuario.email:
                NotificacionesService.enviar_email(
                    usuario.email,
                    f"Producto por vencer: {producto.nombre}",
                    mensaje,
                    empresa
                )
        
        if empresa.telefono_whatsapp:
            NotificacionesService.enviar_whatsapp(
                empresa.telefono_whatsapp,
                mensaje,
                empresa
            )

def recordatorio_metas_semanales():
    """Envía recordatorio semanal del progreso de metas"""
    hoy = datetime.now()
    metas_activas = MetaFinanciera.objects.filter(
        mes=hoy.month,
        anio=hoy.year,
        alertas_activas=True
    )
    
    for meta in metas_activas:
        if meta.estado in ['en_progreso', 'atrasada']:
            mensaje = f"""
📊 RECORDATORIO SEMANAL

Meta: {meta.get_tipo_display()}
Progreso: {meta.progreso_actual:.1f}%
Objetivo: ${meta.objetivo_mensual:,.2f}
Actual: ${meta.valor_actual:,.2f}
Días restantes: {meta.dias_restantes_mes()}

{meta.generar_recomendacion()}

Revisa tu progreso en CONTAFY.
            """.strip()
            
            empresa = meta.empresa
            for usuario in empresa.usuarios.all():
                if usuario.email:
                    NotificacionesService.enviar_email(
                        usuario.email,
                        f"Recordatorio: {meta.get_tipo_display()}",
                        mensaje,
                        empresa
                    )
            
            if empresa.telefono_whatsapp:
                NotificacionesService.enviar_whatsapp(
                    empresa.telefono_whatsapp,
                    mensaje,
                    empresa
                )