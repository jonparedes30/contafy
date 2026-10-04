"""
Centro de Empresa — Vista unificada simplificada.

Estructura:
  - Header con tarjeta destacada de la empresa (datos visuales)
  - Tab "Equipo y Actividad" (default): empleados + sus actividades + timeline general
  - Tab "Configuración": editar empresa + log de cambios

Los KPIs financieros viven en `Resumen Financiero` (otra sección),
así que aquí NO se duplican.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from empresa.decorators import require_owner
from empresa.services.auditoria_service import AuditoriaService


TABS_VALIDOS = {'equipo', 'config'}


@login_required
@require_owner
def centro_empresa(request):
    """
    Vista única del Centro de Empresa.
    Tabs: equipo (default) y config.
    """
    empresa = request.user.empresa
    if not empresa:
        messages.warning(request, 'No tienes una empresa asociada.')
        return redirect('empresa:crear_empresa')

    tab = request.GET.get('tab', 'equipo')
    if tab not in TABS_VALIDOS:
        tab = 'equipo'

    context = {
        'empresa': empresa,
        'tab_activo': tab,
    }

    if tab == 'equipo':
        # Empleados con su última actividad + métricas del mes
        context['equipo'] = AuditoriaService.obtener_resumen_equipo(empresa)

        # Timeline general de actividades (paginado + filtrable)
        try:
            dias = int(request.GET.get('dias', 7))
        except (ValueError, TypeError):
            dias = 7
        try:
            page = int(request.GET.get('page', 1))
        except (ValueError, TypeError):
            page = 1
        context['historial'] = AuditoriaService.obtener_actividades(
            empresa,
            dias=dias,
            tipo=request.GET.get('tipo') or None,
            usuario_filtro=request.GET.get('usuario') or None,
            page=page,
            per_page=25,
        )

    elif tab == 'config':
        context['cambios_recientes'] = (
            empresa.auditoria
            .filter(modelo='Empresa')
            .order_by('-fecha')[:20]
        )

    return render(request, 'empresa/centro_empresa.html', context)


# ─── Redirects de URLs antiguas ───────────────────────────────────

@login_required
def redirect_a_resumen(request):
    """`/listar/` redirige al tab default del Centro de Empresa."""
    return redirect('/app-beta-2024/centro/')


@login_required
def redirect_a_historial(request):
    """`/actividad/` redirige al tab Equipo (que incluye el historial)."""
    qs = request.GET.urlencode()
    base = '/app-beta-2024/centro/?tab=equipo'
    if qs:
        base += '&' + qs
    return redirect(base)
