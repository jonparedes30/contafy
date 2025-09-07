from django.core.management.base import BaseCommand
from django.db.models import Sum
from decimal import Decimal
from empresa.models import Empresa, MovimientoContable, CuentaContable
from collections import defaultdict

class Command(BaseCommand):
    help = 'Verifica transacciones con debitos != creditos por descripcion y movimientos sin cuenta_fk'
    
    def handle(self, *args, **options):
        empresas = Empresa.objects.all()
        for emp in empresas:
            self.stdout.write(f"\n=== Empresa: {emp.nombre} ===")
            movimientos = MovimientoContable.objects.filter(empresa=emp)
            
            # movimientos sin cuenta_fk
            sin_cuenta = movimientos.filter(cuenta_fk__isnull=True)
            if sin_cuenta.exists():
                self.stdout.write(f"Movimientos sin cuenta_fk: {sin_cuenta.count()}")
                for m in sin_cuenta[:20]:
                    self.stdout.write(f"  id={m.id} tipo={m.tipo} monto={m.monto} desc={m.descripcion[:80]}")
            
            # agrupar por descripcion y comparar debitos vs creditos
            trans = defaultdict(lambda: {'debitos': Decimal('0.00'), 'creditos': Decimal('0.00'), 'count': 0})
            for m in movimientos:
                key = (m.descripcion or '').strip()
                trans[key]['count'] += 1
                if m.tipo == 'debito':
                    trans[key]['debitos'] += Decimal(m.monto)
                else:
                    trans[key]['creditos'] += Decimal(m.monto)
            
            problemas = 0
            for desc, vals in trans.items():
                if abs(vals['debitos'] - vals['creditos']) > Decimal('0.01'):
                    problemas += 1
                    self.stdout.write(f"DESBALANCE ({vals['count']}): D={vals['debitos']} C={vals['creditos']}  desc='{desc[:80]}'")
            
            if problemas == 0:
                self.stdout.write("OK: todas las transacciones agrupadas por descripcion estan balanceadas")