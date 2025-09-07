from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from empresa.models import *
from collections import defaultdict

class Command(BaseCommand):
    help = 'Limpia datos duplicados y consolida información'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra qué se eliminaría sin hacer cambios',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write("=== MODO DRY-RUN: Solo mostrando cambios ===\n")
        else:
            self.stdout.write("=== LIMPIANDO DUPLICADOS ===\n")
        
        # 1. Limpiar movimientos contables duplicados exactos
        self.limpiar_movimientos_duplicados(dry_run)
        
        # 2. Consolidar cuentas contables con nombres similares
        self.consolidar_cuentas_similares(dry_run)
        
        # 3. Limpiar productos duplicados
        self.limpiar_productos_duplicados(dry_run)
        
        # 4. Limpiar clientes duplicados
        self.limpiar_clientes_duplicados(dry_run)
        
        self.stdout.write("\n=== LIMPIEZA COMPLETADA ===")
    
    @transaction.atomic
    def limpiar_movimientos_duplicados(self, dry_run):
        self.stdout.write("1. LIMPIANDO MOVIMIENTOS CONTABLES DUPLICADOS:")
        
        # Buscar movimientos exactamente iguales (mismo monto, descripción, fecha, cuenta)
        duplicados = MovimientoContable.objects.values(
            'empresa', 'cuenta_fk', 'monto', 'descripcion', 'fecha__date', 'tipo'
        ).annotate(count=Count('id')).filter(count__gt=1)
        
        eliminados = 0
        for dup in duplicados:
            # Obtener todos los movimientos de este grupo
            movimientos = MovimientoContable.objects.filter(
                empresa_id=dup['empresa'],
                cuenta_fk_id=dup['cuenta_fk'],
                monto=dup['monto'],
                descripcion=dup['descripcion'],
                fecha__date=dup['fecha__date'],
                tipo=dup['tipo']
            ).order_by('id')
            
            if movimientos.count() > 1:
                # Mantener el primero, eliminar el resto
                mantener = movimientos.first()
                eliminar = movimientos.exclude(id=mantener.id)
                
                self.stdout.write(
                    f"  Grupo: {dup['descripcion'][:50]}... - "
                    f"Manteniendo 1, eliminando {eliminar.count()}"
                )
                
                if not dry_run:
                    eliminados += eliminar.count()
                    eliminar.delete()
        
        if not dry_run:
            self.stdout.write(f"  ✅ Eliminados {eliminados} movimientos duplicados")
        else:
            self.stdout.write(f"  📋 Se eliminarían {eliminados} movimientos duplicados")
    
    @transaction.atomic
    def consolidar_cuentas_similares(self, dry_run):
        self.stdout.write("\n2. CONSOLIDANDO CUENTAS CONTABLES SIMILARES:")
        
        empresas = Empresa.objects.all()
        consolidaciones = 0
        
        for empresa in empresas:
            cuentas = CuentaContable.objects.filter(empresa=empresa)
            
            # Buscar cuentas con nombres muy similares
            grupos_similares = defaultdict(list)
            
            for cuenta in cuentas:
                # Normalizar nombre para agrupación
                nombre_norm = cuenta.nombre.lower().strip()
                nombre_norm = nombre_norm.replace('/', '').replace('-', '').replace(' ', '')
                
                # Agrupar variaciones comunes
                if 'caja' in nombre_norm or 'banco' in nombre_norm:
                    grupos_similares['caja_banco'].append(cuenta)
                elif 'inventario' in nombre_norm:
                    grupos_similares['inventario'].append(cuenta)
                elif 'venta' in nombre_norm and 'costo' not in nombre_norm:
                    grupos_similares['ventas'].append(cuenta)
                elif 'gasto' in nombre_norm:
                    grupos_similares['gastos'].append(cuenta)
                elif 'capital' in nombre_norm:
                    grupos_similares['capital'].append(cuenta)
            
            # Consolidar grupos con más de una cuenta
            for grupo, cuentas_grupo in grupos_similares.items():
                if len(cuentas_grupo) > 1:
                    # Mantener la cuenta con más movimientos
                    cuenta_principal = max(
                        cuentas_grupo, 
                        key=lambda c: c.movimientos.count()
                    )
                    cuentas_secundarias = [c for c in cuentas_grupo if c != cuenta_principal]
                    
                    self.stdout.write(
                        f"  {empresa.nombre} - {grupo}: "
                        f"Consolidando {len(cuentas_secundarias)} cuentas en '{cuenta_principal.nombre}'"
                    )
                    
                    if not dry_run:
                        # Mover movimientos a la cuenta principal
                        for cuenta_sec in cuentas_secundarias:
                            MovimientoContable.objects.filter(
                                cuenta_fk=cuenta_sec
                            ).update(cuenta_fk=cuenta_principal)
                            cuenta_sec.delete()
                        
                        consolidaciones += len(cuentas_secundarias)
        
        if not dry_run:
            self.stdout.write(f"  ✅ Consolidadas {consolidaciones} cuentas")
        else:
            self.stdout.write(f"  📋 Se consolidarían {consolidaciones} cuentas")
    
    @transaction.atomic
    def limpiar_productos_duplicados(self, dry_run):
        self.stdout.write("\n3. LIMPIANDO PRODUCTOS DUPLICADOS:")
        
        # Buscar productos con mismo código en la misma empresa
        duplicados = Producto.objects.values('empresa', 'codigo').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        eliminados = 0
        for dup in duplicados:
            productos = Producto.objects.filter(
                empresa_id=dup['empresa'],
                codigo=dup['codigo']
            ).order_by('-id')  # Mantener el más reciente
            
            if productos.count() > 1:
                mantener = productos.first()
                eliminar = productos.exclude(id=mantener.id)
                
                # Verificar si tienen ventas/compras
                tiene_transacciones = any([
                    Venta.objects.filter(producto__in=eliminar).exists(),
                    Compra.objects.filter(producto__in=eliminar).exists()
                ])
                
                if tiene_transacciones:
                    self.stdout.write(
                        f"  ⚠️  Código {dup['codigo']}: Tiene transacciones, consolidando..."
                    )
                    
                    if not dry_run:
                        # Mover transacciones al producto principal
                        Venta.objects.filter(producto__in=eliminar).update(producto=mantener)
                        Compra.objects.filter(producto__in=eliminar).update(producto=mantener)
                        
                        # Sumar stocks
                        stock_total = sum(p.stock for p in eliminar) + mantener.stock
                        mantener.stock = stock_total
                        mantener.save()
                        
                        eliminar.delete()
                        eliminados += eliminar.count()
                else:
                    self.stdout.write(f"  Código {dup['codigo']}: Sin transacciones, eliminando duplicados")
                    if not dry_run:
                        eliminados += eliminar.count()
                        eliminar.delete()
        
        if not dry_run:
            self.stdout.write(f"  ✅ Procesados {eliminados} productos duplicados")
        else:
            self.stdout.write(f"  📋 Se procesarían {eliminados} productos duplicados")
    
    @transaction.atomic
    def limpiar_clientes_duplicados(self, dry_run):
        self.stdout.write("\n4. LIMPIANDO CLIENTES DUPLICADOS:")
        
        # Buscar clientes con mismo documento en la misma empresa
        duplicados = Cliente.objects.values('empresa', 'numero_documento').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        eliminados = 0
        for dup in duplicados:
            clientes = Cliente.objects.filter(
                empresa_id=dup['empresa'],
                numero_documento=dup['numero_documento']
            ).order_by('-id')  # Mantener el más reciente
            
            if clientes.count() > 1:
                mantener = clientes.first()
                eliminar = clientes.exclude(id=mantener.id)
                
                self.stdout.write(
                    f"  Documento {dup['numero_documento']}: "
                    f"Manteniendo 1, eliminando {eliminar.count()}"
                )
                
                if not dry_run:
                    # Mover ventas y cuentas por cobrar al cliente principal
                    Venta.objects.filter(cliente_fk__in=eliminar).update(cliente_fk=mantener)
                    CuentaPorCobrar.objects.filter(cliente__in=eliminar).update(cliente=mantener)
                    
                    eliminados += eliminar.count()
                    eliminar.delete()
        
        if not dry_run:
            self.stdout.write(f"  ✅ Procesados {eliminados} clientes duplicados")
        else:
            self.stdout.write(f"  📋 Se procesarían {eliminados} clientes duplicados")