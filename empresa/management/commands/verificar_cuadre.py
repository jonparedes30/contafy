"""
Comando: verificar_cuadre

Verifica que todas las transacciones contables (MovimientoContable) de una
empresa estén balanceadas según la regla de partida doble (Σ débitos = Σ créditos).

Identifica transacciones huérfanas (sin transaccion_id) o desbalanceadas,
y opcionalmente puede repararlas agrupándolas por descripción y fecha cercana.

Uso:
    python manage.py verificar_cuadre                 # Reporte de todas las empresas
    python manage.py verificar_cuadre --empresa 1     # Solo empresa con id 1
    python manage.py verificar_cuadre --reparar       # Aplica reparación automática (cuidado)
    python manage.py verificar_cuadre --detallado     # Muestra todos los movimientos por transacción
"""
from collections import defaultdict
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from empresa.models import Empresa, MovimientoContable
from empresa.services.contabilidad_service import ContabilidadService


class Command(BaseCommand):
    help = 'Verifica el cuadre de partida doble en MovimientoContable'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa', type=int, default=None,
            help='ID de empresa específica (omitir = todas)'
        )
        parser.add_argument(
            '--reparar', action='store_true',
            help='Intenta agrupar movimientos huérfanos por fecha cercana (USAR CON CUIDADO)'
        )
        parser.add_argument(
            '--detallado', action='store_true',
            help='Muestra detalle de cada transacción desbalanceada'
        )

    def handle(self, *args, **options):
        empresa_id = options['empresa']
        reparar = options['reparar']
        detallado = options['detallado']

        if empresa_id:
            empresas = Empresa.objects.filter(id=empresa_id)
            if not empresas.exists():
                self.stdout.write(self.style.ERROR(f'Empresa {empresa_id} no encontrada'))
                return
        else:
            empresas = Empresa.objects.all()

        self.stdout.write(self.style.NOTICE(
            f'=== VERIFICACIÓN DE CUADRE — {empresas.count()} empresa(s) ===\n'
        ))

        global_desbalanceados = 0
        global_reparados = 0

        for emp in empresas:
            self.stdout.write(self.style.MIGRATE_HEADING(f'\n> Empresa: {emp.nombre} (id={emp.id})'))

            reporte = ContabilidadService.verificar_integridad_empresa(emp)

            self.stdout.write(f'  Total transacciones agrupadas: {reporte["total_transacciones"]}')

            if reporte['integridad_ok']:
                self.stdout.write(self.style.SUCCESS('  [OK] Todo cuadra'))
                continue

            self.stdout.write(self.style.ERROR(
                f'  [X] Transacciones desbalanceadas: {len(reporte["desbalances"])}'
            ))
            global_desbalanceados += len(reporte['desbalances'])

            if detallado:
                for d in reporte['desbalances'][:20]:  # primeros 20 para no saturar
                    self.stdout.write(
                        f'    - TX {d["transaccion_id"][:30]}... '
                        f'D=${d["debitos"]:.2f} C=${d["creditos"]:.2f} '
                        f'diff=${d["diferencia"]:.2f}'
                    )
                if len(reporte['desbalances']) > 20:
                    self.stdout.write(self.style.WARNING(
                        f'    (... y {len(reporte["desbalances"])-20} más; usa --detallado en otra empresa)'
                    ))

            if reparar:
                reparados = self._reparar_huerfanos(emp)
                global_reparados += reparados
                self.stdout.write(self.style.SUCCESS(
                    f'  [OK] Movimientos agrupados/reparados: {reparados}'
                ))

        # Resumen final
        self.stdout.write(self.style.NOTICE('\n=== RESUMEN GLOBAL ==='))
        if global_desbalanceados == 0:
            self.stdout.write(self.style.SUCCESS('  [OK] Sistema 100% cuadrado'))
        else:
            self.stdout.write(self.style.ERROR(
                f'  [X] {global_desbalanceados} transacciones desbalanceadas'
            ))
            if reparar:
                self.stdout.write(self.style.SUCCESS(
                    f'  [OK] {global_reparados} movimientos reparados'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    '  Sugerencia: ejecuta con --reparar para intentar agrupar huérfanos'
                ))

    @transaction.atomic
    def _reparar_huerfanos(self, empresa):
        """
        Estrategia de reparación:
        Agrupa movimientos que parecen pertenecer a la misma transacción
        usando una ventana de tiempo (60s) + monto idéntico + cuentas
        complementarias (uno débito, uno crédito).

        Asigna a estos pares/grupos un mismo transaccion_id.
        """
        from datetime import timedelta

        # Movimientos sin transaccion_id (huérfanos) o con transaccion_id único
        # (auto-generado por save() pero no compartido)
        movs = MovimientoContable.objects.filter(empresa=empresa).order_by('fecha')
        agrupados = defaultdict(list)  # tid -> [movs]
        for m in movs:
            agrupados[m.transaccion_id or f'orphan-{m.id}'].append(m)

        reparados = 0
        for tid, lista in agrupados.items():
            if len(lista) == 1:  # solo un movimiento → es huérfano
                solo = lista[0]
                # Buscar pareja: monto igual, tipo opuesto, dentro de 60s
                opuesto = 'credito' if solo.tipo == 'debito' else 'debito'
                ventana_inicio = solo.fecha - timedelta(seconds=60)
                ventana_fin = solo.fecha + timedelta(seconds=60)

                candidatos = MovimientoContable.objects.filter(
                    empresa=empresa,
                    monto=solo.monto,
                    tipo=opuesto,
                    fecha__gte=ventana_inicio,
                    fecha__lte=ventana_fin,
                ).exclude(id=solo.id)

                # Filtrar candidatos que ya estén bien apareados
                for cand in candidatos:
                    cand_grupo = [m for m in agrupados.get(cand.transaccion_id, []) if m.id != cand.id]
                    if not cand_grupo:  # cand también está solo
                        # Agrupar: ambos comparten nuevo transaccion_id
                        import uuid
                        nuevo_tid = str(uuid.uuid4())[:12]
                        MovimientoContable.objects.filter(id__in=[solo.id, cand.id]).update(
                            transaccion_id=nuevo_tid
                        )
                        reparados += 2
                        break

        return reparados
