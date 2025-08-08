from django.core.management.base import BaseCommand
from empresa.models import CuentaContable, MovimientoContable, Empresa
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Verifica y corrige errores en la contabilidad'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa-id',
            type=int,
            help='ID de la empresa específica (opcional)',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Corregir errores encontrados',
        )

    def handle(self, *args, **options):
        empresa_id = options.get('empresa_id')
        fix = options.get('fix')
        
        if empresa_id:
            empresas = Empresa.objects.filter(id=empresa_id)
        else:
            empresas = Empresa.objects.all()
        
        if not empresas.exists():
            self.stdout.write(self.style.ERROR('No se encontraron empresas para procesar'))
            return
        
        for empresa in empresas:
            self.stdout.write(f'\nVerificando empresa: {empresa.nombre}')
            
            # Verificar cuentas con tipo 'patrimonio' (deberían ser 'capital')
            cuentas_patrimonio = CuentaContable.objects.filter(empresa=empresa, tipo='patrimonio')
            if cuentas_patrimonio.exists():
                self.stdout.write(f'  ⚠️  Encontradas {cuentas_patrimonio.count()} cuentas con tipo "patrimonio"')
                if fix:
                    cuentas_patrimonio.update(tipo='capital')
                    self.stdout.write(self.style.SUCCESS('    ✅ Corregidas a tipo "capital"'))
            
            # Verificar saldos de cuentas
            cuentas = CuentaContable.objects.filter(empresa=empresa)
            for cuenta in cuentas:
                # Calcular saldo manualmente para verificar
                debitos = MovimientoContable.objects.filter(
                    empresa=empresa,
                    cuenta_fk=cuenta,
                    tipo='debito'
                ).aggregate(total=Sum('monto'))['total'] or 0
                
                creditos = MovimientoContable.objects.filter(
                    empresa=empresa,
                    cuenta_fk=cuenta,
                    tipo='credito'
                ).aggregate(total=Sum('monto'))['total'] or 0
                
                # Calcular saldo correcto
                if cuenta.tipo == 'activo':
                    saldo_correcto = debitos - creditos
                elif cuenta.tipo == 'gasto':
                    saldo_correcto = debitos - creditos
                else:  # pasivo, capital, ingreso
                    saldo_correcto = creditos - debitos
                
                # Comparar con la propiedad valor
                saldo_propiedad = cuenta.valor
                
                if abs(saldo_correcto - saldo_propiedad) > 0.01:  # Tolerancia para decimales
                    self.stdout.write(f'  ⚠️  Cuenta "{cuenta.nombre}" ({cuenta.tipo}):')
                    self.stdout.write(f'      Saldo correcto: {saldo_correcto}')
                    self.stdout.write(f'      Saldo propiedad: {saldo_propiedad}')
            
            # Verificar que no haya movimientos sin cuenta_fk
            movimientos_sin_cuenta = MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk__isnull=True
            )
            if movimientos_sin_cuenta.exists():
                self.stdout.write(f'  ⚠️  Encontrados {movimientos_sin_cuenta.count()} movimientos sin cuenta_fk')
                if fix:
                    # Intentar asignar cuentas basándose en cuenta_text
                    for movimiento in movimientos_sin_cuenta:
                        cuenta, created = CuentaContable.objects.get_or_create(
                            empresa=empresa,
                            nombre=movimiento.cuenta_text,
                            defaults={'tipo': 'activo'}  # Por defecto
                        )
                        movimiento.cuenta_fk = cuenta
                        movimiento.save()
                    self.stdout.write(self.style.SUCCESS('    ✅ Asignadas cuentas a movimientos'))
            
            # Verificar balance (Activos = Pasivos + Capital)
            total_activos = sum(c.valor for c in CuentaContable.objects.filter(empresa=empresa, tipo='activo'))
            total_pasivos = sum(c.valor for c in CuentaContable.objects.filter(empresa=empresa, tipo='pasivo'))
            total_capital = sum(c.valor for c in CuentaContable.objects.filter(empresa=empresa, tipo='capital'))
            
            balance = total_activos - (total_pasivos + total_capital)
            
            if abs(balance) > 0.01:
                self.stdout.write(f'  ⚠️  Balance desequilibrado:')
                self.stdout.write(f'      Activos: {total_activos}')
                self.stdout.write(f'      Pasivos: {total_pasivos}')
                self.stdout.write(f'      Capital: {total_capital}')
                self.stdout.write(f'      Diferencia: {balance}')
            else:
                self.stdout.write(self.style.SUCCESS('  ✅ Balance equilibrado'))
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('Verificación completada') 