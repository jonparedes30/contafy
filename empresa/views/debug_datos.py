from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from empresa.models import Capital, CuentaContable, MovimientoContable

@login_required
def debug_datos(request):
    """Vista para verificar qué datos hay en la base de datos"""
    
    empresa = request.user.empresa
    
    # Verificar capital
    capital_records = Capital.objects.filter(empresa=empresa)
    
    # Verificar cuentas contables
    cuentas = CuentaContable.objects.filter(empresa=empresa)
    
    # Verificar movimientos contables
    movimientos = MovimientoContable.objects.filter(empresa=empresa)
    
    html = f"""
    <h1>DEBUG - Datos de {empresa.nombre}</h1>
    
    <h2>Capital ({capital_records.count()} registros)</h2>
    <ul>
    """
    
    for capital in capital_records:
        html += f"<li>${capital.monto} ({capital.tipo}) - {capital.fecha}</li>"
    
    html += f"""
    </ul>
    
    <h2>Cuentas Contables ({cuentas.count()} registros)</h2>
    <ul>
    """
    
    for cuenta in cuentas:
        html += f"<li>{cuenta.nombre} ({cuenta.tipo})</li>"
    
    html += f"""
    </ul>
    
    <h2>Movimientos Contables ({movimientos.count()} registros)</h2>
    <ul>
    """
    
    for mov in movimientos:
        html += f"<li>{mov.cuenta_text} - {mov.tipo} ${mov.monto} - {mov.descripcion}</li>"
    
    html += """
    </ul>
    
    <p><a href="/app-beta-2024/capital/registrar/">Registrar Capital</a></p>
    <p><a href="/app-beta-2024/balance-general/">Ver Balance</a></p>
    <p><a href="/app-beta-2024/cuentas/listar/">Ver Cuentas</a></p>
    """
    
    return HttpResponse(html)