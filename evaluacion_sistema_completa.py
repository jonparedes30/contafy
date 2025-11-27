"""
Script de Evaluación Completa del Sistema CONTAFY
Verifica la integridad de datos en todas las fases críticas del sistema
"""

import os
import django
import sys
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db.models import Sum, Count, Q
from empresa.models import (
    Empresa, Usuario, Producto, Venta, Compra, Gasto, Capital,
    CuentaContable, MovimientoContable, Cliente, Proveedor,
    CuentaPorCobrar, CuentaPorPagar, MateriaPrima, ProductoManufacturado,
    RecetaProduccion, TipoServicio, MaterialServicio
)
from empresa.services.contabilidad_service import ContabilidadService


class EvaluadorSistema:
    """Evaluador completo del sistema CONTAFY"""
    
    def __init__(self):
        self.errores = []
        self.advertencias = []
        self.exitos = []
    
    def log_error(self, mensaje):
        """Registra un error"""
        self.errores.append(f"[ERROR] {mensaje}")
        print(f"[ERROR] {mensaje}")
    
    def log_advertencia(self, mensaje):
        """Registra una advertencia"""
        self.advertencias.append(f"[ADVERTENCIA] {mensaje}")
        print(f"[ADVERTENCIA] {mensaje}")
    
    def log_exito(self, mensaje):
        """Registra un éxito"""
        self.exitos.append(f"[OK] {mensaje}")
        print(f"[OK] {mensaje}")
    
    def evaluar_empresas(self):
        """Evalúa la creación y configuración de empresas"""
        print("\n" + "="*80)
        print("EVALUANDO EMPRESAS")
        print("="*80)
        
        empresas = Empresa.objects.all()
        
        if not empresas.exists():
            self.log_advertencia("No hay empresas registradas en el sistema")
            return
        
        self.log_exito(f"Se encontraron {empresas.count()} empresas registradas")
        
        for empresa in empresas:
            # Verificar campos obligatorios
            if not empresa.nombre:
                self.log_error(f"Empresa ID {empresa.id} sin nombre")
            
            if not empresa.ruc:
                self.log_error(f"Empresa {empresa.nombre} sin RUC")
            
            if not empresa.categoria:
                self.log_error(f"Empresa {empresa.nombre} sin categoría")
            
            # Verificar propietario
            if not empresa.propietario:
                self.log_advertencia(f"Empresa {empresa.nombre} sin propietario asignado")
            
            # Verificar usuarios asociados
            usuarios_count = empresa.usuarios.count()
            if usuarios_count == 0:
                self.log_advertencia(f"Empresa {empresa.nombre} sin usuarios asociados")
            else:
                self.log_exito(f"Empresa {empresa.nombre}: {usuarios_count} usuarios")
    
    def evaluar_productos(self):
        """Evalúa la creación y gestión de productos"""
        print("\n" + "="*80)
        print("EVALUANDO PRODUCTOS")
        print("="*80)
        
        productos = Producto.objects.all()
        
        if not productos.exists():
            self.log_advertencia("No hay productos registrados")
            return
        
        self.log_exito(f"Se encontraron {productos.count()} productos")
        
        for producto in productos:
            # Verificar campos obligatorios
            if not producto.codigo:
                self.log_error(f"Producto {producto.nombre} sin código")
            
            if producto.precio_unitario <= 0:
                self.log_error(f"Producto {producto.nombre} con precio inválido: {producto.precio_unitario}")
            
            # Verificar stock
            if producto.stock < 0:
                self.log_error(f"Producto {producto.nombre} con stock negativo: {producto.stock}")
            
            if producto.necesita_restock:
                self.log_advertencia(f"Producto {producto.nombre} necesita restock (stock: {producto.stock})")
            
            # Verificar productos vencidos
            if producto.esta_vencido:
                self.log_advertencia(f"Producto {producto.nombre} está vencido")
    
    def evaluar_ventas(self):
        """Evalúa las ventas y sus asientos contables"""
        print("\n" + "="*80)
        print("EVALUANDO VENTAS")
        print("="*80)
        
        ventas = Venta.objects.all()
        
        if not ventas.exists():
            self.log_advertencia("No hay ventas registradas")
            return
        
        self.log_exito(f"Se encontraron {ventas.count()} ventas")
        
        for venta in ventas:
            # Verificar cálculo de IVA
            iva_calculado = venta.monto_neto * (venta.tasa_iva / 100)
            diferencia_iva = abs(venta.iva - iva_calculado)
            
            if diferencia_iva > Decimal('0.02'):
                self.log_error(
                    f"Venta ID {venta.id}: IVA mal calculado. "
                    f"Esperado: {iva_calculado}, Actual: {venta.iva}"
                )
            
            # Verificar monto total
            total_calculado = venta.monto_neto + venta.iva
            diferencia_total = abs(venta.monto - total_calculado)
            
            if diferencia_total > Decimal('0.02'):
                self.log_error(
                    f"Venta ID {venta.id}: Total mal calculado. "
                    f"Esperado: {total_calculado}, Actual: {venta.monto}"
                )
            
            # Verificar asientos contables
            movimientos = MovimientoContable.objects.filter(
                empresa=venta.empresa,
                descripcion__icontains=f'Venta'
            ).filter(
                Q(descripcion__icontains=venta.producto.nombre) |
                Q(descripcion__icontains=f'#{venta.id}')
            )
            
            if not movimientos.exists():
                self.log_error(f"Venta ID {venta.id} sin asientos contables")
            
            # Verificar cuentas por cobrar si es a crédito
            if venta.tipo_pago == 'credito':
                cxc = CuentaPorCobrar.objects.filter(venta=venta).first()
                if not cxc:
                    self.log_error(f"Venta a crédito ID {venta.id} sin cuenta por cobrar")
    
    def evaluar_compras(self):
        """Evalúa las compras y sus asientos contables"""
        print("\n" + "="*80)
        print("EVALUANDO COMPRAS")
        print("="*80)
        
        compras = Compra.objects.all()
        
        if not compras.exists():
            self.log_advertencia("No hay compras registradas")
            return
        
        self.log_exito(f"Se encontraron {compras.count()} compras")
        
        for compra in compras:
            # Verificar cálculo de IVA
            iva_calculado = compra.monto_neto * (compra.tasa_iva / 100)
            diferencia_iva = abs(compra.iva - iva_calculado)
            
            if diferencia_iva > Decimal('0.02'):
                self.log_error(
                    f"Compra ID {compra.id}: IVA mal calculado. "
                    f"Esperado: {iva_calculado}, Actual: {compra.iva}"
                )
            
            # Verificar monto total
            total_calculado = compra.monto_neto + compra.iva
            diferencia_total = abs(compra.monto - total_calculado)
            
            if diferencia_total > Decimal('0.02'):
                self.log_error(
                    f"Compra ID {compra.id}: Total mal calculado. "
                    f"Esperado: {total_calculado}, Actual: {compra.monto}"
                )
            
            # Verificar cuentas por pagar si es a crédito
            if compra.tipo_pago == 'credito':
                cxp = CuentaPorPagar.objects.filter(compra=compra).first()
                if not cxp:
                    self.log_error(f"Compra a crédito ID {compra.id} sin cuenta por pagar")
    
    def evaluar_gastos(self):
        """Evalúa los gastos y sus asientos contables"""
        print("\n" + "="*80)
        print("EVALUANDO GASTOS")
        print("="*80)
        
        gastos = Gasto.objects.all()
        
        if not gastos.exists():
            self.log_advertencia("No hay gastos registrados")
            return
        
        self.log_exito(f"Se encontraron {gastos.count()} gastos")
        
        for gasto in gastos:
            # Verificar monto positivo
            if gasto.monto <= 0:
                self.log_error(f"Gasto ID {gasto.id} con monto inválido: {gasto.monto}")
            
            # Verificar descripción
            if not gasto.descripcion:
                self.log_advertencia(f"Gasto ID {gasto.id} sin descripción")
    
    def evaluar_clientes(self):
        """Evalúa los clientes registrados"""
        print("\n" + "="*80)
        print("EVALUANDO CLIENTES")
        print("="*80)
        
        clientes = Cliente.objects.all()
        
        if not clientes.exists():
            self.log_advertencia("No hay clientes registrados")
            return
        
        self.log_exito(f"Se encontraron {clientes.count()} clientes")
        
        for cliente in clientes:
            # Verificar documento
            if not cliente.numero_documento:
                self.log_error(f"Cliente {cliente.nombre} sin número de documento")
            
            # Verificar límite de crédito
            if cliente.limite_credito < 0:
                self.log_error(f"Cliente {cliente.nombre} con límite de crédito negativo")
    
    def evaluar_proveedores(self):
        """Evalúa los proveedores registrados"""
        print("\n" + "="*80)
        print("EVALUANDO PROVEEDORES")
        print("="*80)
        
        proveedores = Proveedor.objects.all()
        
        if not proveedores.exists():
            self.log_advertencia("No hay proveedores registrados")
            return
        
        self.log_exito(f"Se encontraron {proveedores.count()} proveedores")
        
        for proveedor in proveedores:
            # Verificar RUC
            if not proveedor.ruc:
                self.log_error(f"Proveedor {proveedor.nombre} sin RUC")
    
    def evaluar_cuentas_contables(self):
        """Evalúa las cuentas contables"""
        print("\n" + "="*80)
        print("EVALUANDO CUENTAS CONTABLES")
        print("="*80)
        
        cuentas = CuentaContable.objects.all()
        
        if not cuentas.exists():
            self.log_advertencia("No hay cuentas contables registradas")
            return
        
        self.log_exito(f"Se encontraron {cuentas.count()} cuentas contables")
        
        # Verificar cuentas básicas por empresa
        empresas = Empresa.objects.all()
        for empresa in empresas:
            cuentas_empresa = CuentaContable.objects.filter(empresa=empresa)
            
            cuentas_basicas = ['Caja', 'Ventas', 'Inventario', 'Capital']
            for cuenta_nombre in cuentas_basicas:
                if not cuentas_empresa.filter(nombre=cuenta_nombre).exists():
                    self.log_advertencia(
                        f"Empresa {empresa.nombre} sin cuenta básica: {cuenta_nombre}"
                    )
    
    def evaluar_movimientos_contables(self):
        """Evalúa los movimientos contables y su balance"""
        print("\n" + "="*80)
        print("EVALUANDO MOVIMIENTOS CONTABLES")
        print("="*80)
        
        movimientos = MovimientoContable.objects.all()
        
        if not movimientos.exists():
            self.log_advertencia("No hay movimientos contables registrados")
            return
        
        self.log_exito(f"Se encontraron {movimientos.count()} movimientos contables")
        
        # Verificar integridad por empresa
        empresas = Empresa.objects.all()
        for empresa in empresas:
            reporte = ContabilidadService.verificar_integridad_empresa(empresa)
            
            if reporte['integridad_ok']:
                self.log_exito(
                    f"Empresa {empresa.nombre}: Integridad contable OK "
                    f"({reporte['total_transacciones']} transacciones)"
                )
            else:
                self.log_error(
                    f"Empresa {empresa.nombre}: {len(reporte['desbalances'])} "
                    f"transacciones desbalanceadas"
                )
                for desbalance in reporte['desbalances'][:5]:  # Mostrar primeros 5
                    self.log_error(
                        f"  Transacción {desbalance['transaccion_id']}: "
                        f"Débitos={desbalance['debitos']}, "
                        f"Créditos={desbalance['creditos']}, "
                        f"Diferencia={desbalance['diferencia']}"
                    )
    
    def evaluar_cuentas_por_cobrar(self):
        """Evalúa las cuentas por cobrar"""
        print("\n" + "="*80)
        print("EVALUANDO CUENTAS POR COBRAR")
        print("="*80)
        
        cuentas = CuentaPorCobrar.objects.all()
        
        if not cuentas.exists():
            self.log_advertencia("No hay cuentas por cobrar registradas")
            return
        
        self.log_exito(f"Se encontraron {cuentas.count()} cuentas por cobrar")
        
        # Verificar cuentas vencidas
        vencidas = cuentas.filter(estado='vencida').count()
        if vencidas > 0:
            self.log_advertencia(f"{vencidas} cuentas por cobrar vencidas")
        
        # Verificar montos pendientes
        for cuenta in cuentas:
            if cuenta.monto_pendiente < 0:
                self.log_error(
                    f"Cuenta por cobrar ID {cuenta.id} con monto pendiente negativo: "
                    f"{cuenta.monto_pendiente}"
                )
            
            if cuenta.monto_pendiente > cuenta.monto_original:
                self.log_error(
                    f"Cuenta por cobrar ID {cuenta.id}: monto pendiente mayor al original"
                )
    
    def evaluar_cuentas_por_pagar(self):
        """Evalúa las cuentas por pagar"""
        print("\n" + "="*80)
        print("EVALUANDO CUENTAS POR PAGAR")
        print("="*80)
        
        cuentas = CuentaPorPagar.objects.all()
        
        if not cuentas.exists():
            self.log_advertencia("No hay cuentas por pagar registradas")
            return
        
        self.log_exito(f"Se encontraron {cuentas.count()} cuentas por pagar")
        
        # Verificar cuentas vencidas
        vencidas = cuentas.filter(estado='vencida').count()
        if vencidas > 0:
            self.log_advertencia(f"{vencidas} cuentas por pagar vencidas")
    
    def evaluar_manufactura(self):
        """Evalúa el módulo de manufactura"""
        print("\n" + "="*80)
        print("EVALUANDO MANUFACTURA")
        print("="*80)
        
        materias_primas = MateriaPrima.objects.all()
        productos_manuf = ProductoManufacturado.objects.all()
        recetas = RecetaProduccion.objects.all()
        
        if not materias_primas.exists():
            self.log_advertencia("No hay materias primas registradas")
        else:
            self.log_exito(f"Se encontraron {materias_primas.count()} materias primas")
        
        if not productos_manuf.exists():
            self.log_advertencia("No hay productos manufacturados registrados")
        else:
            self.log_exito(f"Se encontraron {productos_manuf.count()} productos manufacturados")
        
        if not recetas.exists():
            self.log_advertencia("No hay recetas de producción registradas")
        else:
            self.log_exito(f"Se encontraron {recetas.count()} recetas de producción")
        
        # Verificar costos de productos manufacturados
        for producto in productos_manuf:
            costo_calculado = producto.costo_produccion
            if abs(producto.precio_costo - costo_calculado) > Decimal('0.01'):
                self.log_advertencia(
                    f"Producto {producto.nombre}: costo desactualizado. "
                    f"Guardado: {producto.precio_costo}, Calculado: {costo_calculado}"
                )
    
    def evaluar_servicios(self):
        """Evalúa el módulo de servicios"""
        print("\n" + "="*80)
        print("EVALUANDO SERVICIOS")
        print("="*80)
        
        tipos_servicio = TipoServicio.objects.all()
        materiales = MaterialServicio.objects.all()
        
        if not tipos_servicio.exists():
            self.log_advertencia("No hay tipos de servicio registrados")
        else:
            self.log_exito(f"Se encontraron {tipos_servicio.count()} tipos de servicio")
        
        if not materiales.exists():
            self.log_advertencia("No hay materiales de servicio registrados")
        else:
            self.log_exito(f"Se encontraron {materiales.count()} materiales de servicio")
    
    def generar_reporte_final(self):
        """Genera el reporte final de la evaluación"""
        print("\n" + "="*80)
        print("REPORTE FINAL DE EVALUACIÓN")
        print("="*80)
        
        print(f"\n[OK] EXITOS: {len(self.exitos)}")
        print(f"[ADVERTENCIA] ADVERTENCIAS: {len(self.advertencias)}")
        print(f"[ERROR] ERRORES: {len(self.errores)}")
        
        if self.errores:
            print("\n" + "="*80)
            print("ERRORES CRÍTICOS ENCONTRADOS:")
            print("="*80)
            for error in self.errores:
                print(error)
        
        if self.advertencias:
            print("\n" + "="*80)
            print("ADVERTENCIAS:")
            print("="*80)
            for advertencia in self.advertencias[:10]:  # Mostrar primeras 10
                print(advertencia)
            if len(self.advertencias) > 10:
                print(f"... y {len(self.advertencias) - 10} advertencias más")
        
        # Calcular puntuación
        total_checks = len(self.exitos) + len(self.advertencias) + len(self.errores)
        if total_checks > 0:
            puntuacion = (len(self.exitos) / total_checks) * 100
            print(f"\n[PUNTUACION] INTEGRIDAD: {puntuacion:.1f}%")
            
            if puntuacion >= 90:
                print("[EXCELENTE] El sistema esta en muy buen estado")
            elif puntuacion >= 70:
                print("[BUENO] El sistema funciona correctamente con algunas mejoras menores")
            elif puntuacion >= 50:
                print("[REGULAR] Se requieren correcciones")
            else:
                print("[CRITICO] Se requiere atencion inmediata")
    
    def ejecutar_evaluacion_completa(self):
        """Ejecuta la evaluación completa del sistema"""
        print("\n" + "="*80)
        print("INICIANDO EVALUACIÓN COMPLETA DEL SISTEMA CONTAFY")
        print("="*80)
        
        self.evaluar_empresas()
        self.evaluar_productos()
        self.evaluar_clientes()
        self.evaluar_proveedores()
        self.evaluar_ventas()
        self.evaluar_compras()
        self.evaluar_gastos()
        self.evaluar_cuentas_contables()
        self.evaluar_movimientos_contables()
        self.evaluar_cuentas_por_cobrar()
        self.evaluar_cuentas_por_pagar()
        self.evaluar_manufactura()
        self.evaluar_servicios()
        
        self.generar_reporte_final()


if __name__ == '__main__':
    evaluador = EvaluadorSistema()
    evaluador.ejecutar_evaluacion_completa()
