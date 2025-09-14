from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Sum, Q
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from datetime import date, timedelta
from empresa.models import CuentaPorCobrar, CuentaPorPagar, PagoCuentaPorCobrar, PagoCuentaPorPagar
import logging

logger = logging.getLogger(__name__)

@login_required
def gestion_deudas(request):
    """Vista principal para gestión de deudas (cuentas por cobrar y pagar)"""
    try:
        empresa = request.user.empresa
        
        # Cuentas por cobrar
        cuentas_cobrar = CuentaPorCobrar.objects.filter(
            empresa=empresa,
            estado__in=['pendiente', 'vencida'],
            monto_pendiente__gt=0
        ).select_related('cliente', 'venta').order_by('fecha_vencimiento')
        
        # Cuentas por pagar
        cuentas_pagar = CuentaPorPagar.objects.filter(
            empresa=empresa,
            estado__in=['pendiente', 'vencida'],
            monto_pendiente__gt=0
        ).select_related('proveedor', 'compra').order_by('fecha_vencimiento')
        
        # Totales
        total_por_cobrar = cuentas_cobrar.aggregate(total=Sum('monto_pendiente'))['total'] or 0
        total_por_pagar = cuentas_pagar.aggregate(total=Sum('monto_pendiente'))['total'] or 0
        
        # Vencidas
        hoy = date.today()
        cobrar_vencidas = cuentas_cobrar.filter(fecha_vencimiento__lt=hoy).count()
        pagar_vencidas = cuentas_pagar.filter(fecha_vencimiento__lt=hoy).count()
        
        context = {
            'cuentas_cobrar': cuentas_cobrar,
            'cuentas_pagar': cuentas_pagar,
            'total_por_cobrar': total_por_cobrar,
            'total_por_pagar': total_por_pagar,
            'cobrar_vencidas': cobrar_vencidas,
            'pagar_vencidas': pagar_vencidas,
            'balance_neto': total_por_cobrar - total_por_pagar,
            'today': hoy,
        }
        
        return render(request, 'empresa/gestion_deudas.html', context)
    
    except Exception as exc:
        logger.exception("Error en gestion_deudas: %s", exc)
        return render(request, 'empresa/error_resumen.html', {
            "mensaje": "Error al cargar la gestión de deudas. El equipo técnico ha sido notificado."
        }, status=500)

@login_required
@csrf_exempt
def registrar_pago_cobrar(request):
    """Registrar pago recibido de cuenta por cobrar"""
    if request.method == 'POST':
        try:
            cuenta_id = request.POST.get('cuenta_id')
            monto_pagado = Decimal(request.POST.get('monto_pagado'))
            metodo_pago = request.POST.get('metodo_pago', 'efectivo')
            
            cuenta = get_object_or_404(CuentaPorCobrar, 
                id=cuenta_id, 
                empresa=request.user.empresa
            )
            
            if monto_pagado > cuenta.monto_pendiente:
                return JsonResponse({
                    'success': False, 
                    'error': 'El monto no puede ser mayor al pendiente'
                })
            
            with transaction.atomic():
                # Crear registro de pago (el modelo se encarga de actualizar la cuenta)
                pago = PagoCuentaPorCobrar.objects.create(
                    empresa=request.user.empresa,
                    cuenta_por_cobrar=cuenta,
                    monto_pagado=monto_pagado,
                    metodo_pago=metodo_pago
                )
                # La cuenta se actualiza automáticamente en el método save() del modelo PagoCuentaPorCobrar
            
            return JsonResponse({
                'success': True,
                'mensaje': f'Pago de ${monto_pagado} registrado correctamente'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
@csrf_exempt
def registrar_pago_pagar(request):
    """Registrar pago realizado de cuenta por pagar"""
    if request.method == 'POST':
        try:
            cuenta_id = request.POST.get('cuenta_id')
            monto_pagado = Decimal(request.POST.get('monto_pagado'))
            metodo_pago = request.POST.get('metodo_pago', 'efectivo')
            
            cuenta = get_object_or_404(CuentaPorPagar, 
                id=cuenta_id, 
                empresa=request.user.empresa
            )
            
            if monto_pagado > cuenta.monto_pendiente:
                return JsonResponse({
                    'success': False, 
                    'error': 'El monto no puede ser mayor al pendiente'
                })
            
            with transaction.atomic():
                # Crear registro de pago (el modelo se encarga de actualizar la cuenta)
                pago = PagoCuentaPorPagar.objects.create(
                    empresa=request.user.empresa,
                    cuenta_por_pagar=cuenta,
                    monto_pagado=monto_pagado,
                    metodo_pago=metodo_pago
                )
                # La cuenta se actualiza automáticamente en el método save() del modelo PagoCuentaPorPagar
            
            return JsonResponse({
                'success': True,
                'mensaje': f'Pago de ${monto_pagado} registrado correctamente'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def api_cuentas_cobrar(request):
    """API para obtener cuentas por cobrar"""
    empresa = request.user.empresa
    cuentas = CuentaPorCobrar.objects.filter(
        empresa=empresa,
        estado__in=['pendiente', 'vencida'],
        monto_pendiente__gt=0
    ).select_related('cliente', 'venta')
    
    data = []
    hoy = date.today()
    
    for cuenta in cuentas:
        dias_vencido = (hoy - cuenta.fecha_vencimiento).days if hoy > cuenta.fecha_vencimiento else 0
        data.append({
            'id': cuenta.id,
            'cliente_nombre': cuenta.cliente.nombre if cuenta.cliente else 'Cliente no registrado',
            'monto_original': float(cuenta.monto_original),
            'monto_pendiente': float(cuenta.monto_pendiente),
            'fecha_vencimiento': cuenta.fecha_vencimiento.strftime('%d/%m/%Y'),
            'dias_vencido': dias_vencido,
            'estado': cuenta.estado,
            'venta_id': cuenta.venta.id if cuenta.venta else None
        })
    
    return JsonResponse(data, safe=False)

@login_required
def api_cuentas_pagar(request):
    """API para obtener cuentas por pagar"""
    empresa = request.user.empresa
    cuentas = CuentaPorPagar.objects.filter(
        empresa=empresa,
        estado__in=['pendiente', 'vencida'],
        monto_pendiente__gt=0
    ).select_related('proveedor', 'compra')
    
    data = []
    hoy = date.today()
    
    for cuenta in cuentas:
        dias_vencido = (hoy - cuenta.fecha_vencimiento).days if hoy > cuenta.fecha_vencimiento else 0
        data.append({
            'id': cuenta.id,
            'proveedor_nombre': cuenta.proveedor.nombre if cuenta.proveedor else 'Proveedor no registrado',
            'monto_original': float(cuenta.monto_original),
            'monto_pendiente': float(cuenta.monto_pendiente),
            'fecha_vencimiento': cuenta.fecha_vencimiento.strftime('%d/%m/%Y'),
            'dias_vencido': dias_vencido,
            'estado': cuenta.estado,
            'compra_id': cuenta.compra.id if cuenta.compra else None
        })
    
    return JsonResponse(data, safe=False)