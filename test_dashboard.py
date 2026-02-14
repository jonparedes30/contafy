import os, django, sys
from pathlib import Path

env_path = Path(r'c:\Proyectos\contafy\.env')
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.models import Venta, Gasto, Empresa, CuentaContable
from django.db.models import Sum, F
from empresa.services.filtros_service import FiltrosFechaService
from datetime import datetime, timedelta
from django.utils import timezone
import calendar

with open(r'c:\Proyectos\contafy\dashboard_test.txt', 'w', encoding='utf-8') as f:
    for empresa in Empresa.objects.all():
        f.write(f"\n{'='*60}\n")
        f.write(f"EMPRESA: {empresa.nombre} ({empresa.categoria})\n")
        f.write(f"{'='*60}\n")
        
        # Simular el rango de fechas por defecto (3 meses)
        hoy = timezone.now().date()
        fecha_inicio = (hoy.replace(day=1) - timedelta(days=60)).replace(day=1)
        fecha_fin = hoy
        f.write(f"Rango: {fecha_inicio} a {fecha_fin}\n")
        
        # Generar meses
        meses = []
        labels_meses = []
        ventas_mensuales = []
        gastos_mensuales = []
        
        fecha_iter = fecha_inicio.replace(day=1)
        while fecha_iter <= fecha_fin:
            meses.append((fecha_iter.year, fecha_iter.month))
            labels_meses.append(f"{fecha_iter.strftime('%b')} {fecha_iter.year}")
            if fecha_iter.month == 12:
                fecha_iter = fecha_iter.replace(year=fecha_iter.year+1, month=1)
            else:
                fecha_iter = fecha_iter.replace(month=fecha_iter.month+1)
        
        for anio, mes in meses:
            fecha_mes_inicio = timezone.datetime(anio, mes, 1).date()
            if mes == 12:
                fecha_mes_fin = timezone.datetime(anio+1, 1, 1).date() - timezone.timedelta(days=1)
            else:
                fecha_mes_fin = timezone.datetime(anio, mes+1, 1).date() - timezone.timedelta(days=1)
            
            ventas_mes = Venta.objects.filter(
                empresa=empresa,
                fecha__date__gte=fecha_mes_inicio,
                fecha__date__lte=fecha_mes_fin
            ).aggregate(total=Sum('monto_neto'))['total'] or 0
            
            gastos_mes = Gasto.objects.filter(
                empresa=empresa,
                fecha__date__gte=fecha_mes_inicio,
                fecha__date__lte=fecha_mes_fin
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            ventas_mensuales.append(round(float(ventas_mes), 2))
            gastos_mensuales.append(round(float(gastos_mes), 2))
        
        f.write(f"\nLabels: {labels_meses}\n")
        f.write(f"Ventas mensuales: {ventas_mensuales}\n")
        f.write(f"Gastos mensuales: {gastos_mensuales}\n")
        f.write(f"Total ventas: ${sum(ventas_mensuales):.2f}\n")
        f.write(f"Total gastos: ${sum(gastos_mensuales):.2f}\n")

print("Resultado escrito en dashboard_test.txt")
