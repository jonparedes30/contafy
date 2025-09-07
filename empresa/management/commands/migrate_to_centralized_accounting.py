from django.core.management.base import BaseCommand
from django.db import transaction
from empresa.models import Empresa, MovimientoContable
from empresa.services.contabilidad_service import ContabilidadService
import uuid

class Command(BaseCommand):
    help = 'Migra datos contables existentes al nuevo sistema centralizado'
    
    def handle(self, *args, **options):
        empresas = Empresa.objects.all()
        
        for empresa in empresas:
            self.stdout.write(f"\n=== Migrando empresa: {empresa.nombre} ===")
            
            # Asignar transaccion_id a movimientos existentes que no lo tienen
            movimientos_sin_tid = MovimientoContable.objects.filter(
                empresa=empresa,
                transaccion_id__isnull=True
            )
            
            if movimientos_sin_tid.exists():
                self.stdout.write(f"Asignando transaccion_id a {movimientos_sin_tid.count()} movimientos...")
                
                # Agrupar por descripción para intentar reconstruir transacciones
                from collections import defaultdict
                grupos = defaultdict(list)
                
                for mov in movimientos_sin_tid:
                    # Usar descripción base (sin sufijos de ajuste)
                    desc_base = mov.descripcion.split(' - AJUSTE')[0]
                    grupos[desc_base].append(mov)
                
                for desc, movimientos in grupos.items():
                    tid = str(uuid.uuid4())[:12]
                    for mov in movimientos:
                        mov.transaccion_id = tid
                        mov.save(update_fields=['transaccion_id'])
                
                self.stdout.write(f"✓ Asignados {len(grupos)} grupos de transacciones")
            
            # Verificar integridad después de la migración
            reporte = ContabilidadService.verificar_integridad_empresa(empresa)
            
            if reporte['integridad_ok']:
                self.stdout.write(f"✅ {empresa.nombre}: Integridad contable OK")
            else:
                self.stdout.write(f"⚠️  {empresa.nombre}: {len(reporte['desbalances'])} desbalances encontrados")
                for desbalance in reporte['desbalances'][:5]:  # Mostrar solo los primeros 5
                    self.stdout.write(
                        f"   - {desbalance['transaccion_id'][:20]}...: "
                        f"D=${desbalance['debitos']} C=${desbalance['creditos']} "
                        f"Dif=${desbalance['diferencia']}"
                    )
        
        self.stdout.write("\n=== Migración completada ===")
        self.stdout.write("Recomendación: Ejecutar fix_accounting_balance para corregir desbalances restantes")