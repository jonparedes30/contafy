from django.core.management.base import BaseCommand
from django.db import transaction
from empresa.models import (
    Empresa, Usuario, Producto, Venta, Compra, Gasto, Cliente, Proveedor,
    CategoriaProducto, CuentaContable, MovimientoContable, Capital
)
from datetime import date, timedelta
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Crea 3 cuentas demo con datos reales: Comercio, Manufactura y Servicios'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Creando cuentas demo...'))
        
        with transaction.atomic():
            # Limpiar demos anteriores
            Usuario.objects.filter(username__in=['demo_comercio', 'demo_manufactura', 'demo_servicios']).delete()
            Empresa.objects.filter(ruc__in=['1234567890001', '0987654321001', '1122334455001']).delete()
            
            # 1. DEMO COMERCIO - Minimarket
            self.crear_demo_comercio()
            
            # 2. DEMO MANUFACTURA - Panadería
            self.crear_demo_manufactura()
            
            # 3. DEMO SERVICIOS - Peluquería
            self.crear_demo_servicios()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Cuentas demo creadas exitosamente!\n'))
        self.mostrar_credenciales()

    def crear_demo_comercio(self):
        """Demo de Minimarket (Comercio)"""
        self.stdout.write('📦 Creando demo de COMERCIO (Minimarket)...')
        
        # Crear empresa
        empresa = Empresa.objects.create(
            nombre='Minimarket Don Pepe',
            ruc='1234567890001',
            direccion='Av. Principal 123, Quito',
            categoria='comercial',
            tipo_negocio='Minimarket',
            provincia='Pichincha',
            ciudad='Quito',
            telefono_whatsapp='+593987654321',
            latitud=-0.1807,
            longitud=-78.4678
        )
        
        # Crear usuario
        usuario = Usuario.objects.create_user(
            username='demo_comercio',
            password='demo123',
            email='comercio@contafy.com',
            empresa=empresa,
            first_name='Pedro',
            last_name='Comerciante'
        )
        
        # Capital inicial
        Capital.objects.create(
            empresa=empresa,
            monto=5000,
            descripcion='Capital inicial Minimarket',
            fecha=date.today() - timedelta(days=90)
        )
        
        # Categorías
        cat_bebidas = CategoriaProducto.objects.create(empresa=empresa, nombre='Bebidas')
        cat_snacks = CategoriaProducto.objects.create(empresa=empresa, nombre='Snacks')
        cat_lacteos = CategoriaProducto.objects.create(empresa=empresa, nombre='Lácteos')
        
        # Proveedores
        prov1 = Proveedor.objects.create(
            empresa=empresa,
            nombre='Distribuidora La Favorita',
            ruc='1790000000001',
            telefono='022345678',
            dias_credito=15
        )
        
        prov2 = Proveedor.objects.create(
            empresa=empresa,
            nombre='Coca Cola Ecuador',
            ruc='1790111111001',
            telefono='022456789',
            dias_credito=30
        )
        
        # Clientes
        clientes = [
            Cliente.objects.create(empresa=empresa, nombre='María González', numero_documento='1712345678', tipo_documento='cedula'),
            Cliente.objects.create(empresa=empresa, nombre='Juan Pérez', numero_documento='1723456789', tipo_documento='cedula'),
            Cliente.objects.create(empresa=empresa, nombre='Ana Torres', numero_documento='1734567890', tipo_documento='cedula'),
        ]
        
        # Productos
        productos = [
            Producto.objects.create(empresa=empresa, codigo='BEB001', nombre='Coca Cola 2L', descripcion='Gaseosa Coca Cola 2 litros', 
                                   precio_unitario=Decimal('1.20'), pvp=Decimal('1.80'), stock=500, categoria=cat_bebidas, stock_minimo=10),
            Producto.objects.create(empresa=empresa, codigo='BEB002', nombre='Agua Dasani 600ml', descripcion='Agua purificada 600ml', 
                                   precio_unitario=Decimal('0.30'), pvp=Decimal('0.50'), stock=1000, categoria=cat_bebidas, stock_minimo=20),
            Producto.objects.create(empresa=empresa, codigo='SNK001', nombre='Doritos Nacho', descripcion='Papas fritas sabor nacho 150g', 
                                   precio_unitario=Decimal('1.00'), pvp=Decimal('1.50'), stock=400, categoria=cat_snacks, stock_minimo=10),
            Producto.objects.create(empresa=empresa, codigo='SNK002', nombre='Chochos Salados', descripcion='Chochos listos para comer 200g', 
                                   precio_unitario=Decimal('0.80'), pvp=Decimal('1.20'), stock=300, categoria=cat_snacks, stock_minimo=10),
            Producto.objects.create(empresa=empresa, codigo='LAC001', nombre='Leche Vita 1L', descripcion='Leche entera pasteurizada 1 litro', 
                                   precio_unitario=Decimal('0.90'), pvp=Decimal('1.30'), stock=600, categoria=cat_lacteos, stock_minimo=15),
            Producto.objects.create(empresa=empresa, codigo='LAC002', nombre='Yogurt Toni 1L', descripcion='Yogurt natural 1 litro', 
                                   precio_unitario=Decimal('1.50'), pvp=Decimal('2.20'), stock=350, categoria=cat_lacteos, stock_minimo=10),
        ]
        
        # Compras (últimos 90 días) - REDUCIDAS para coherencia
        for i in range(8):
            producto = random.choice(productos)
            proveedor = random.choice([prov1, prov2])
            cantidad = random.randint(15, 30)  # REDUCIDO de 20-50
            fecha_compra = date.today() - timedelta(days=random.randint(1, 90))
            
            compra = Compra.objects.create(
                empresa=empresa,
                producto=producto,
                proveedor_nombre=proveedor.nombre,
                cantidad=cantidad,
                monto_neto=cantidad * producto.precio_unitario,
                iva=(cantidad * producto.precio_unitario) * Decimal('0.15'),
                monto=(cantidad * producto.precio_unitario) * Decimal('1.15'),
                tasa_iva=15,
                tipo_pago=random.choice(['contado', 'credito']),
            )
            # auto_now_add ignora fecha en create, forzar con update
            Compra.objects.filter(pk=compra.pk).update(fecha=fecha_compra)
        
        # Ventas (últimos 30 días - DISTRIBUIDAS EN FEBRERO) - AUMENTADAS
        for i in range(250):
            producto = random.choice(productos)
            cliente = random.choice(clientes) if random.random() > 0.3 else None
            cantidad = random.randint(2, 8)
            fecha_venta = date.today() - timedelta(days=random.randint(0, 30))
            
            if producto.stock >= cantidad:
                venta = Venta.objects.create(
                    empresa=empresa,
                    producto=producto,
                    cliente_fk=cliente,
                    cliente_nombre=cliente.nombre if cliente else 'Cliente General',
                    cantidad=cantidad,
                    precio_unitario=producto.pvp,
                    monto_neto=cantidad * producto.pvp,
                    iva=(cantidad * producto.pvp) * Decimal('0.15'),
                    monto=(cantidad * producto.pvp) * Decimal('1.15'),
                    tasa_iva=15,
                    tipo_pago=random.choice(['contado', 'contado', 'contado', 'credito']),
                )
                # auto_now_add ignora fecha en create, forzar con update
                Venta.objects.filter(pk=venta.pk).update(fecha=fecha_venta)
                producto.stock -= cantidad
                producto.save()
        
        # Gastos (distribuidos en 1 mes - datos recientes) - REDUCIDOS para demostracion
        gastos_data = [
            ('Arriendo local', 150, 'Arriendo mensual del local comercial'),
            ('Luz', 40, 'Consumo eléctrico mensual'),
            ('Agua', 15, 'Consumo de agua mensual'),
            ('Internet', 20, 'Servicio de internet'),
            ('Sueldos', 300, 'Pago de sueldos empleados'),
        ]
        
        # Crear gastos solo para 1 mes (datos recientes)
        for nombre, monto_val, desc in gastos_data:
            fecha_gasto = date.today() - timedelta(days=5)
            gasto = Gasto.objects.create(
                empresa=empresa,
                descripcion=f'{nombre} - {desc}',
                monto=monto_val,
                categoria='Fijo' if nombre in ('Arriendo local', 'Internet', 'Sueldos') else 'Variable',
            )
            Gasto.objects.filter(pk=gasto.pk).update(fecha=fecha_gasto)
        
        self.stdout.write(self.style.SUCCESS('  ✓ Minimarket creado con 6 productos, 120 ventas, 8 compras'))

    def crear_demo_manufactura(self):
        """Demo de Panadería (Manufactura)"""
        self.stdout.write('🍞 Creando demo de MANUFACTURA (Panadería)...')
        
        # Crear empresa
        empresa = Empresa.objects.create(
            nombre='Panadería El Buen Pan',
            ruc='0987654321001',
            direccion='Calle García Moreno 456, Cuenca',
            categoria='manufactura',
            tipo_negocio='Panadería',
            provincia='Azuay',
            ciudad='Cuenca',
            telefono_whatsapp='+593998765432',
            latitud=-2.9001,
            longitud=-79.0059
        )
        
        # Crear usuario
        usuario = Usuario.objects.create_user(
            username='demo_manufactura',
            password='demo123',
            email='manufactura@contafy.com',
            empresa=empresa,
            first_name='Carlos',
            last_name='Panadero'
        )
        
        # Capital inicial
        Capital.objects.create(
            empresa=empresa,
            monto=8000,
            descripcion='Capital inicial Panadería',
            fecha=date.today() - timedelta(days=90)
        )
        
        # Categorías
        cat_pan = CategoriaProducto.objects.create(empresa=empresa, nombre='Panes')
        cat_pasteles = CategoriaProducto.objects.create(empresa=empresa, nombre='Pasteles')
        cat_galletas = CategoriaProducto.objects.create(empresa=empresa, nombre='Galletas')
        
        # Proveedores de materias primas
        prov1 = Proveedor.objects.create(
            empresa=empresa,
            nombre='Molinos Champion',
            ruc='1790222222001',
            telefono='072345678',
            dias_credito=15
        )
        
        prov2 = Proveedor.objects.create(
            empresa=empresa,
            nombre='Distribuidora Azúcar Valdez',
            ruc='1790333333001',
            telefono='072456789',
            dias_credito=20
        )
        
        # Clientes
        clientes = [
            Cliente.objects.create(empresa=empresa, nombre='Restaurant El Fogón', numero_documento='0190123456001', tipo_documento='ruc'),
            Cliente.objects.create(empresa=empresa, nombre='Cafetería Central', numero_documento='0190234567001', tipo_documento='ruc'),
            Cliente.objects.create(empresa=empresa, nombre='Rosa Martínez', numero_documento='0112345678', tipo_documento='cedula'),
        ]
        
        # Productos manufacturados
        productos = [
            Producto.objects.create(empresa=empresa, codigo='PAN001', nombre='Pan Integral', descripcion='Pan integral de 500g', 
                                   precio_unitario=Decimal('0.80'), pvp=Decimal('1.50'), stock=400, categoria=cat_pan, stock_minimo=20),
            Producto.objects.create(empresa=empresa, codigo='PAN002', nombre='Pan Blanco', descripcion='Pan blanco tradicional 400g', 
                                   precio_unitario=Decimal('0.60'), pvp=Decimal('1.00'), stock=500, categoria=cat_pan, stock_minimo=30),
            Producto.objects.create(empresa=empresa, codigo='PAS001', nombre='Torta Chocolate', descripcion='Torta de chocolate 1kg', 
                                   precio_unitario=Decimal('5.00'), pvp=Decimal('12.00'), stock=150, categoria=cat_pasteles, stock_minimo=5),
            Producto.objects.create(empresa=empresa, codigo='PAS002', nombre='Pastel de Tres Leches', descripcion='Pastel tres leches 1kg', 
                                   precio_unitario=Decimal('6.00'), pvp=Decimal('15.00'), stock=100, categoria=cat_pasteles, stock_minimo=3),
            Producto.objects.create(empresa=empresa, codigo='GAL001', nombre='Galletas de Avena', descripcion='Galletas de avena 250g', 
                                   precio_unitario=Decimal('1.20'), pvp=Decimal('2.50'), stock=300, categoria=cat_galletas, stock_minimo=15),
            Producto.objects.create(empresa=empresa, codigo='GAL002', nombre='Galletas de Chocolate', descripcion='Galletas con chips de chocolate 250g', 
                                   precio_unitario=Decimal('1.50'), pvp=Decimal('3.00'), stock=250, categoria=cat_galletas, stock_minimo=10),
        ]
        
        # Compras de materias primas (últimos 90 días) - REDUCIDAS
        materias_primas = [
            ('Harina de trigo', Decimal('25.00'), 'Saco de 50kg'),
            ('Azúcar', Decimal('20.00'), 'Saco de 50kg'),
            ('Mantequilla', Decimal('15.00'), 'Caja de 5kg'),
            ('Huevos', Decimal('8.00'), 'Cubeta de 30 unidades'),
            ('Levadura', Decimal('5.00'), 'Paquete de 1kg'),
        ]
        
        for nombre, precio, desc in materias_primas:
            for i in range(2):  # REDUCIDO de 3 a 2
                fecha_compra = date.today() - timedelta(days=random.randint(1, 90))
                cantidad = random.randint(3, 8)  # REDUCIDO de 5-15 a 3-8
                
                # Crear producto temporal para materia prima
                mp = Producto.objects.create(
                    empresa=empresa,
                    codigo=f'MP{random.randint(100,999)}',
                    nombre=nombre,
                    descripcion=desc,
                    precio_unitario=precio,
                    pvp=precio,
                    stock=cantidad
                )
                
                compra = Compra.objects.create(
                    empresa=empresa,
                    producto=mp,
                    proveedor_nombre=random.choice([prov1, prov2]).nombre,
                    cantidad=cantidad,
                    monto_neto=cantidad * precio,
                    iva=(cantidad * precio) * Decimal('0.15'),
                    monto=(cantidad * precio) * Decimal('1.15'),
                    tasa_iva=15,
                    tipo_pago=random.choice(['contado', 'credito']),
                )
                Compra.objects.filter(pk=compra.pk).update(fecha=fecha_compra)
        
        # Ventas (últimos 30 días) - AUMENTADAS para rentabilidad
        for i in range(200):
            producto = random.choice(productos)
            cliente = random.choice(clientes) if random.random() > 0.4 else None
            cantidad = random.randint(2, 8)
            fecha_venta = date.today() - timedelta(days=random.randint(0, 30))
            
            if producto.stock >= cantidad:
                venta = Venta.objects.create(
                    empresa=empresa,
                    producto=producto,
                    cliente_fk=cliente,
                    cliente_nombre=cliente.nombre if cliente else 'Cliente General',
                    cantidad=cantidad,
                    precio_unitario=producto.pvp,
                    monto_neto=cantidad * producto.pvp,
                    iva=(cantidad * producto.pvp) * Decimal('0.15'),
                    monto=(cantidad * producto.pvp) * Decimal('1.15'),
                    tasa_iva=15,
                    tipo_pago=random.choice(['contado', 'contado', 'credito']),
                )
                Venta.objects.filter(pk=venta.pk).update(fecha=fecha_venta)
                producto.stock -= cantidad
                producto.save()
        
        # Gastos (distribuidos en 1 mes - datos recientes) - REDUCIDOS para demostracion
        gastos_data = [
            ('Arriendo local', 200, 'Arriendo mensual panadería'),
            ('Luz', 80, 'Consumo eléctrico hornos'),
            ('Agua', 30, 'Consumo de agua'),
            ('Gas', 40, 'Gas para hornos'),
            ('Sueldos', 600, 'Pago de sueldos panaderos'),
            ('Mantenimiento', 50, 'Mantenimiento de equipos'),
        ]
        
        for mes_offset in range(1):  # REDUCIDO a 1 mes solamente
            for nombre, monto_val, desc in gastos_data:
                fecha_gasto = date.today() - timedelta(days=5)
                gasto = Gasto.objects.create(
                    empresa=empresa,
                    descripcion=f'{nombre} - {desc}',
                    monto=monto_val,
                    categoria='Fijo' if nombre in ('Arriendo local', 'Sueldos') else 'Variable',
                )
                Gasto.objects.filter(pk=gasto.pk).update(fecha=fecha_gasto)
        
        self.stdout.write(self.style.SUCCESS('  ✓ Panadería creada con 6 productos, 150 ventas, materias primas'))

    def crear_demo_servicios(self):
        """Demo de Peluquería (Servicios)"""
        self.stdout.write('💇 Creando demo de SERVICIOS (Peluquería)...')
        
        # Crear empresa
        empresa = Empresa.objects.create(
            nombre='Peluquería Estilo & Belleza',
            ruc='1122334455001',
            direccion='Av. 9 de Octubre 789, Guayaquil',
            categoria='servicios',
            tipo_negocio='Peluquería',
            provincia='Guayas',
            ciudad='Guayaquil',
            telefono_whatsapp='+593991234567',
            latitud=-2.1894,
            longitud=-79.8890
        )
        
        # Crear usuario
        usuario = Usuario.objects.create_user(
            username='demo_servicios',
            password='demo123',
            email='servicios@contafy.com',
            empresa=empresa,
            first_name='Laura',
            last_name='Estilista'
        )
        
        # Capital inicial
        Capital.objects.create(
            empresa=empresa,
            monto=3000,
            descripcion='Capital inicial Peluquería',
            fecha=date.today() - timedelta(days=90)
        )
        
        # Categorías
        cat_cortes = CategoriaProducto.objects.create(empresa=empresa, nombre='Cortes')
        cat_tratamientos = CategoriaProducto.objects.create(empresa=empresa, nombre='Tratamientos')
        cat_productos = CategoriaProducto.objects.create(empresa=empresa, nombre='Productos')
        
        # Proveedores
        prov1 = Proveedor.objects.create(
            empresa=empresa,
            nombre='Distribuidora Belleza Total',
            ruc='0990444444001',
            telefono='042345678',
            dias_credito=30
        )
        
        # Clientes frecuentes
        clientes = [
            Cliente.objects.create(empresa=empresa, nombre='Patricia Gómez', numero_documento='0912345678', tipo_documento='cedula'),
            Cliente.objects.create(empresa=empresa, nombre='Andrea Silva', numero_documento='0923456789', tipo_documento='cedula'),
            Cliente.objects.create(empresa=empresa, nombre='Roberto Mendoza', numero_documento='0934567890', tipo_documento='cedula'),
            Cliente.objects.create(empresa=empresa, nombre='Sofía Ramírez', numero_documento='0945678901', tipo_documento='cedula'),
            Cliente.objects.create(empresa=empresa, nombre='Diego Castro', numero_documento='0956789012', tipo_documento='cedula'),
        ]
        
        # Servicios como productos
        servicios = [
            Producto.objects.create(empresa=empresa, codigo='SRV001', nombre='Corte Dama', descripcion='Corte de cabello para dama', 
                                   precio_unitario=Decimal('3.00'), pvp=Decimal('12.00'), stock=999, categoria=cat_cortes),
            Producto.objects.create(empresa=empresa, codigo='SRV002', nombre='Corte Caballero', descripcion='Corte de cabello para caballero', 
                                   precio_unitario=Decimal('2.00'), pvp=Decimal('8.00'), stock=999, categoria=cat_cortes),
            Producto.objects.create(empresa=empresa, codigo='SRV003', nombre='Tinte Completo', descripcion='Tinte de cabello completo', 
                                   precio_unitario=Decimal('8.00'), pvp=Decimal('35.00'), stock=999, categoria=cat_tratamientos),
            Producto.objects.create(empresa=empresa, codigo='SRV004', nombre='Mechas', descripcion='Aplicación de mechas', 
                                   precio_unitario=Decimal('10.00'), pvp=Decimal('45.00'), stock=999, categoria=cat_tratamientos),
            Producto.objects.create(empresa=empresa, codigo='SRV005', nombre='Keratina', descripcion='Tratamiento de keratina', 
                                   precio_unitario=Decimal('15.00'), pvp=Decimal('80.00'), stock=999, categoria=cat_tratamientos),
            Producto.objects.create(empresa=empresa, codigo='SRV006', nombre='Manicure', descripcion='Manicure completo', 
                                   precio_unitario=Decimal('2.50'), pvp=Decimal('10.00'), stock=999, categoria=cat_tratamientos),
            Producto.objects.create(empresa=empresa, codigo='SRV007', nombre='Pedicure', descripcion='Pedicure completo', 
                                   precio_unitario=Decimal('3.00'), pvp=Decimal('12.00'), stock=999, categoria=cat_tratamientos),
        ]
        
        # Productos de venta
        productos_venta = [
            Producto.objects.create(empresa=empresa, codigo='PRD001', nombre='Shampoo Profesional', descripcion='Shampoo profesional 500ml', 
                                   precio_unitario=Decimal('5.00'), pvp=Decimal('12.00'), stock=20, categoria=cat_productos, stock_minimo=5),
            Producto.objects.create(empresa=empresa, codigo='PRD002', nombre='Acondicionador', descripcion='Acondicionador 500ml', 
                                   precio_unitario=Decimal('5.50'), pvp=Decimal('13.00'), stock=15, categoria=cat_productos, stock_minimo=5),
            Producto.objects.create(empresa=empresa, codigo='PRD003', nombre='Gel Fijador', descripcion='Gel fijador extra fuerte 250ml', 
                                   precio_unitario=Decimal('3.00'), pvp=Decimal('8.00'), stock=25, categoria=cat_productos, stock_minimo=8),
        ]
        
        # Compras de insumos (últimos 90 días)
        insumos = [
            ('Tinte Negro', Decimal('8.00')),
            ('Tinte Castaño', Decimal('8.00')),
            ('Tinte Rubio', Decimal('9.00')),
            ('Keratina Brasileña', Decimal('25.00')),
            ('Shampoo Profesional', Decimal('5.00')),
            ('Acondicionador', Decimal('5.50')),
        ]
        
        for nombre, precio in insumos:
            for i in range(2):
                fecha_compra = date.today() - timedelta(days=random.randint(1, 90))
                cantidad = random.randint(3, 10)
                
                prod = Producto.objects.create(
                    empresa=empresa,
                    codigo=f'INS{random.randint(100,999)}',
                    nombre=nombre,
                    descripcion=f'Insumo profesional {nombre}',
                    precio_unitario=precio,
                    pvp=precio,
                    stock=cantidad
                )
                
                compra = Compra.objects.create(
                    empresa=empresa,
                    producto=prod,
                    proveedor_nombre=prov1.nombre,
                    cantidad=cantidad,
                    monto_neto=cantidad * precio,
                    iva=(cantidad * precio) * Decimal('0.15'),
                    monto=(cantidad * precio) * Decimal('1.15'),
                    tasa_iva=15,
                    tipo_pago=random.choice(['contado', 'credito']),
                )
                Compra.objects.filter(pk=compra.pk).update(fecha=fecha_compra)
        
        # Ventas de servicios (últimos 30 días) - AUMENTADAS
        for i in range(250):
            servicio = random.choice(servicios)
            cliente = random.choice(clientes)
            fecha_venta = date.today() - timedelta(days=random.randint(0, 30))
            
            venta = Venta.objects.create(
                empresa=empresa,
                producto=servicio,
                cliente_fk=cliente,
                cliente_nombre=cliente.nombre,
                cantidad=1,
                precio_unitario=servicio.pvp,
                monto_neto=servicio.pvp,
                iva=servicio.pvp * Decimal('0.15'),
                monto=servicio.pvp * Decimal('1.15'),
                tasa_iva=15,
                tipo_pago=random.choice(['contado', 'contado', 'contado', 'tarjeta']),
            )
            Venta.objects.filter(pk=venta.pk).update(fecha=fecha_venta)
        
        # Ventas de productos
        for i in range(20):
            producto = random.choice(productos_venta)
            cliente = random.choice(clientes) if random.random() > 0.5 else None
            fecha_venta = date.today() - timedelta(days=random.randint(0, 90))
            
            if producto.stock > 0:
                venta = Venta.objects.create(
                    empresa=empresa,
                    producto=producto,
                    cliente_fk=cliente,
                    cliente_nombre=cliente.nombre if cliente else 'Cliente General',
                    cantidad=1,
                    precio_unitario=producto.pvp,
                    monto_neto=producto.pvp,
                    iva=producto.pvp * Decimal('0.15'),
                    monto=producto.pvp * Decimal('1.15'),
                    tasa_iva=15,
                    tipo_pago='contado',
                )
                Venta.objects.filter(pk=venta.pk).update(fecha=fecha_venta)
                producto.stock -= 1
                producto.save()
        
        # Gastos (distribuidos en 1 mes - datos recientes) - REDUCIDOS para demostracion
        gastos_data = [
            ('Arriendo local', 300, 'Arriendo mensual peluquería'),
            ('Luz', 60, 'Consumo eléctrico'),
            ('Agua', 30, 'Consumo de agua'),
            ('Internet', 25, 'Servicio de internet'),
            ('Sueldos', 700, 'Pago de sueldos estilistas'),
            ('Publicidad', 80, 'Publicidad en redes sociales'),
        ]
        
        for mes_offset in range(1):  # REDUCIDO a 1 mes
            for nombre, monto_val, desc in gastos_data:
                fecha_gasto = date.today() - timedelta(days=5)
                gasto = Gasto.objects.create(
                    empresa=empresa,
                    descripcion=f'{nombre} - {desc}',
                    monto=monto_val,
                    categoria='Fijo' if nombre in ('Arriendo local', 'Internet', 'Sueldos') else 'Variable',
                )
                Gasto.objects.filter(pk=gasto.pk).update(fecha=fecha_gasto)
        
        self.stdout.write(self.style.SUCCESS('  ✓ Peluquería creada con 7 servicios, 100 ventas, productos'))

    def mostrar_credenciales(self):
        """Muestra las credenciales de acceso"""
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('CREDENCIALES DE ACCESO A LAS DEMOS'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        demos = [
            ('COMERCIO - Minimarket Don Pepe', 'demo_comercio', 'demo123', 'Quito, Pichincha'),
            ('MANUFACTURA - Panadería El Buen Pan', 'demo_manufactura', 'demo123', 'Cuenca, Azuay'),
            ('SERVICIOS - Peluquería Estilo & Belleza', 'demo_servicios', 'demo123', 'Guayaquil, Guayas'),
        ]
        
        for nombre, usuario, password, ubicacion in demos:
            self.stdout.write(f'\n📍 {nombre}')
            self.stdout.write(f'   Ubicación: {ubicacion}')
            self.stdout.write(f'   Usuario: {usuario}')
            self.stdout.write(f'   Contraseña: {password}')
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.WARNING('\n⚠️  Estas cuentas son PÚBLICAS para demostración'))
        self.stdout.write(self.style.WARNING('   Los datos pueden ser modificados por cualquier usuario\n'))
