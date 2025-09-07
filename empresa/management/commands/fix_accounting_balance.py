from django.core.management.base import BaseCommand
from django.db import transaction
from empresa.models import MovimientoContable, CuentaContable
from collections import defaultdict
from decimal import Decimal

class Command(BaseCommand):
    help = 'Corrige asientos contables desbalanceados creando contrapartidas faltantes'
    
    def handle(self, *args, **options):
        empresas_procesadas = set()
        
        # Agrupar movimientos por empresa y descripción
        movimientos = MovimientoContable.objects.all().order_by('empresa', 'descripcion')
        
        for movimiento in movimientos:
            if movimiento.empresa.id in empresas_procesadas:
                continue
                
            self.stdout.write(f"\n=== Procesando empresa: {movimiento.empresa.nombre} ===")
            self.fix_empresa_balance(movimiento.empresa)
            empresas_procesadas.add(movimiento.empresa.id)
    
    def fix_empresa_balance(self, empresa):
        movimientos = MovimientoContable.objects.filter(empresa=empresa)
        
        # Agrupar por descripción
        trans = defaultdict(lambda: {'debitos': Decimal('0.00'), 'creditos': Decimal('0.00'), 'movs': []})
        
        for m in movimientos:
            key = (m.descripcion or '').strip()
            trans[key]['movs'].append(m)
            if m.tipo == 'debito':
                trans[key]['debitos'] += Decimal(m.monto)
            else:
                trans[key]['creditos'] += Decimal(m.monto)
        
        correcciones = 0
        
        for desc, vals in trans.items():
            diferencia = vals['debitos'] - vals['creditos']
            
            if abs(diferencia) > Decimal('0.01'):
                self.stdout.write(f"  Corrigiendo: {desc[:50]}... (Dif: {diferencia})")
                
                with transaction.atomic():
                    if diferencia > 0:
                        # Faltan créditos
                        self.crear_contrapartida(empresa, desc, diferencia, 'credito')
                    else:
                        # Faltan débitos
                        self.crear_contrapartida(empresa, desc, abs(diferencia), 'debito')
                
                correcciones += 1
        
        if correcciones == 0:
            self.stdout.write("  ✓ Empresa ya balanceada")
        else:
            self.stdout.write(f"  ✓ {correcciones} transacciones corregidas")
    
    def crear_contrapartida(self, empresa, descripcion, monto, tipo):
        # Obtener o crear cuenta de ajustes
        cuenta_ajuste, created = CuentaContable.objects.get_or_create(
            empresa=empresa,
            nombre='Ajustes Contables',
            defaults={'tipo': 'capital'}
        )
        
        # Crear movimiento de ajuste
        MovimientoContable.objects.create(
            empresa=empresa,
            cuenta_fk=cuenta_ajuste,
            tipo=tipo,
            monto=monto,
            descripcion=f"{descripcion} - AJUSTE AUTOMÁTICO"
        )