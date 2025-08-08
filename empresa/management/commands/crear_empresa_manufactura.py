from django.core.management.base import BaseCommand
from empresa.models import (
    Empresa, Usuario, Cliente, Proveedor, CategoriaProducto, 
    Producto, MateriaPrima, ProductoManufacturado, RecetaProduccion,
    Venta, Compra, Gasto, CuentaContable, MovimientoContable,
    MetaFinanciera
)
from decimal import Decimal
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Crea empresa de manufactura con datos demo ecuatorianos'

    def handle(self, *args, **options):
        # 1. Crear empresa de manufactura
        empresa, created = Empresa.objects.get_or_create(
            ruc="1793456789001",
            defaults={
                'nombre': "Panadería Artesanal Cuenca",
                'direccion': "Calle Larga 8-27, Centro Histórico, Cuenca",
                'categoria': 'manufactura',
                'tipo_negocio': 'panaderia',
                'provincia': 'Azuay',
                'ciudad': 'Cuenca',
                'telefono_whatsapp': '+593987123456',
                'latitud': Decimal('-2.9001'),
                'longitud': Decimal('-79.0059')
            }
        )
        
        if created:
            self.stdout.write(f"[OK] Empresa creada: {empresa.nombre}")
        else:
            self.stdout.write(f"[OK] Empresa ya existe: {empresa.nombre}")

        # 2. Crear usuario
        usuario, created = Usuario.objects.get_or_create(
            username="carlos_panadero",
            defaults={
                'email': "carlos@panaderiartesanal.com",
                'first_name': "Carlos",
                'last_name': "Morocho",
                'empresa': empresa
            }
        )
        
        if created:
            usuario.set_password("panadero123")
            usuario.save()
            self.stdout.write(f"[OK] Usuario creado: {usuario.username}")
        else:
            self.stdout.write(f"[OK] Usuario ya existe: {usuario.username}")

        # 3. Crear proveedores de materias primas
        proveedores_data = [
            ("Molinos del Ecuador", "1791111111001", "0987111111", 15),
            ("Distribuidora Lácteos", "1792222222001", "0987222222", 7),
            ("Azucarera San Carlos", "1793333333001", "0987333333", 30),
            ("Huevos Frescos del Campo", "1794444444001", "0987444444", 3),
            ("Levaduras Industriales", "1795555555001", "0987555555", 45)
        ]
        
        proveedores = []
        for nombre, ruc, tel, dias in proveedores_data:
            proveedor, created = Proveedor.objects.get_or_create(
                empresa=empresa,
                ruc=ruc,
                defaults={
                    'nombre': nombre,
                    'telefono': tel,
                    'dias_credito': dias
                }
            )
            proveedores.append(proveedor)
        
        self.stdout.write(f"[OK] {len(proveedores)} proveedores creados")

        # 4. Crear materias primas
        materias_primas_data = [
            ("Harina de Trigo", "HAR001", "kg", 1.20, 500, 50, proveedores[0]),
            ("Azúcar Blanca", "AZU001", "kg", 0.85, 200, 25, proveedores[2]),
            ("Leche Fresca", "LEC001", "l", 0.75, 100, 20, proveedores[1]),
            ("Huevos Frescos", "HUE001", "docena", 2.50, 50, 10, proveedores[3]),
            ("Levadura Seca", "LEV001", "kg", 8.50, 20, 5, proveedores[4]),
            ("Mantequilla", "MAN001", "kg", 4.20, 30, 5, proveedores[1]),
            ("Sal", "SAL001", "kg", 0.45, 25, 5, proveedores[0]),
            ("Vainilla", "VAN001", "ml", 0.15, 500, 50, proveedores[4])
        ]
        
        materias_primas = []
        for nombre, codigo, unidad, precio, stock, minimo, proveedor in materias_primas_data:
            materia, created = MateriaPrima.objects.get_or_create(
                empresa=empresa,
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'unidad_medida': unidad,
                    'precio_unitario': precio,
                    'stock_actual': stock,
                    'stock_minimo': minimo,
                    'proveedor_principal': proveedor
                }
            )
            materias_primas.append(materia)
        
        self.stdout.write(f"[OK] {len(materias_primas)} materias primas creadas")

        # 5. Crear categorías de productos
        categorias_productos = [
            ("Panes Dulces", "Panes y productos dulces"),
            ("Panes Salados", "Panes tradicionales y salados"),
            ("Pasteles", "Tortas y pasteles especiales"),
            ("Galletas", "Galletas artesanales"),
            ("Empanadas", "Empanadas y productos salados")
        ]
        
        categorias_creadas = []
        for nombre, desc in categorias_productos:
            cat, created = CategoriaProducto.objects.get_or_create(
                empresa=empresa,
                nombre=nombre,
                defaults={'descripcion': desc}
            )
            categorias_creadas.append(cat)
        
        self.stdout.write(f"[OK] {len(categorias_creadas)} categorias de productos creadas")

        # 6. Crear productos manufacturados
        productos_data = [
            ("Pan de Dulce", "PAN001", categorias_creadas[0], 2.50, 60, 20, 100),
            ("Pan Integral", "PAN002", categorias_creadas[1], 1.80, 45, 30, 150),
            ("Torta de Chocolate", "TOR001", categorias_creadas[2], 15.00, 120, 5, 20),
            ("Galletas de Avena", "GAL001", categorias_creadas[3], 3.50, 30, 25, 80),
            ("Empanadas de Pollo", "EMP001", categorias_creadas[4], 1.25, 25, 40, 120),
            ("Pan de Agua", "PAN003", categorias_creadas[1], 0.75, 15, 50, 200),
            ("Torta de Vainilla", "TOR002", categorias_creadas[2], 12.00, 90, 8, 25),
            ("Croissant", "CRO001", categorias_creadas[0], 2.00, 35, 20, 60)
        ]
        
        productos_manufacturados = []
        for nombre, codigo, cat, precio, tiempo, stock_min, stock in productos_data:
            producto, created = ProductoManufacturado.objects.get_or_create(
                empresa=empresa,
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'categoria': cat,
                    'precio_venta': precio,
                    'tiempo_produccion': tiempo,
                    'stock_actual': stock,
                    'stock_minimo': stock_min,
                    'activo': True
                }
            )
            productos_manufacturados.append(producto)
        
        self.stdout.write(f"[OK] {len(productos_manufacturados)} productos manufacturados creados")

        # 7. Crear recetas de producción (ejemplos básicos)
        recetas_data = [
            # Pan de Dulce
            (productos_manufacturados[0], [
                (materias_primas[0], 0.5),  # Harina 500g
                (materias_primas[1], 0.1),  # Azúcar 100g
                (materias_primas[2], 0.2),  # Leche 200ml
                (materias_primas[3], 0.1),  # Huevos (1.2 huevos)
                (materias_primas[4], 0.01), # Levadura 10g
                (materias_primas[5], 0.05)  # Mantequilla 50g
            ]),
            # Pan Integral
            (productos_manufacturados[1], [
                (materias_primas[0], 0.4),  # Harina 400g
                (materias_primas[6], 0.01), # Sal 10g
                (materias_primas[2], 0.15), # Leche 150ml
                (materias_primas[4], 0.008) # Levadura 8g
            ]),
            # Torta de Chocolate
            (productos_manufacturados[2], [
                (materias_primas[0], 0.3),  # Harina 300g
                (materias_primas[1], 0.2),  # Azúcar 200g
                (materias_primas[3], 0.25), # Huevos (3 huevos)
                (materias_primas[5], 0.15), # Mantequilla 150g
                (materias_primas[2], 0.1),  # Leche 100ml
                (materias_primas[7], 5)     # Vainilla 5ml
            ])
        ]
        
        for producto, ingredientes in recetas_data:
            for materia_prima, cantidad in ingredientes:
                RecetaProduccion.objects.get_or_create(
                    producto=producto,
                    materia_prima=materia_prima,
                    defaults={'cantidad_necesaria': cantidad}
                )
        
        self.stdout.write("[OK] Recetas de produccion creadas")

        # 8. Crear clientes
        clientes_data = [
            ("Supermercado La Esquina", "1791234567001", "0987654321", 2000),
            ("Cafetería Central", "1792345678001", "0987765432", 1500),
            ("Hotel Plaza", "1793456789001", "0987876543", 3000),
            ("Restaurante El Buen Sabor", "1794567890001", "0987987654", 2500),
            ("Tienda Doña María", "1795678901001", "0987098765", 1000),
            ("Colegio San José", "1796789012001", "0987109876", 4000)
        ]
        
        clientes = []
        for nombre, ruc, tel, credito in clientes_data:
            cliente, created = Cliente.objects.get_or_create(
                empresa=empresa,
                numero_documento=ruc,
                defaults={
                    'nombre': nombre,
                    'tipo_documento': 'ruc',
                    'telefono': tel,
                    'limite_credito': credito
                }
            )
            clientes.append(cliente)
        
        self.stdout.write(f"[OK] {len(clientes)} clientes creados")

        # 9. Crear cuentas contables para manufactura
        cuentas_manufactura = [
            ('Ventas de Productos', 'ingreso'),
            ('Caja', 'activo'),
            ('Banco del Austro', 'activo'),
            ('Inventario Materias Primas', 'activo'),
            ('Inventario Productos Terminados', 'activo'),
            ('Costo de Producción', 'gasto'),
            ('Gastos de Fabricación', 'gasto'),
            ('Maquinaria y Equipos', 'activo'),
            ('Capital Social', 'capital'),
            ('Cuentas por Pagar Proveedores', 'pasivo')
        ]
        
        for nombre, tipo in cuentas_manufactura:
            CuentaContable.objects.get_or_create(
                empresa=empresa,
                nombre=nombre,
                defaults={'tipo': tipo}
            )
        
        self.stdout.write("[OK] Cuentas contables para manufactura creadas")

        # 10. Generar ventas de productos manufacturados
        self.stdout.write("Generando ventas de productos manufacturados...")
        
        for i in range(30):  # 30 días de ventas
            fecha = date.today() - timedelta(days=i)
            # 3-8 ventas por día (panadería tiene mucho movimiento)
            num_ventas = random.randint(3, 8)
            
            for _ in range(num_ventas):
                cliente = random.choice(clientes) if random.random() > 0.4 else None
                # Crear producto regular para venta (no manufacturado para simplificar)
                productos_venta = []
                for prod_manuf in productos_manufacturados:
                    producto_venta, created = Producto.objects.get_or_create(
                        empresa=empresa,
                        codigo=prod_manuf.codigo,
                        defaults={
                            'nombre': prod_manuf.nombre,
                            'precio_unitario': prod_manuf.precio_venta * 0.6,  # Costo estimado
                            'pvp': prod_manuf.precio_venta,
                            'stock': prod_manuf.stock_actual,
                            'categoria': prod_manuf.categoria
                        }
                    )
                    productos_venta.append(producto_venta)
                
                producto = random.choice(productos_venta)
                cantidad = random.randint(1, 10)
                precio = producto.pvp
                
                venta = Venta.objects.create(
                    empresa=empresa,
                    cliente_fk=cliente,
                    cliente_nombre=cliente.nombre if cliente else f"Cliente {random.randint(1000, 9999)}",
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    monto=precio * cantidad,
                    tipo_pago=random.choice(['contado', 'credito']),
                    fecha=fecha
                )
        
        self.stdout.write("[OK] Ventas de productos manufacturados generadas")

        # 11. Crear gastos típicos de manufactura
        gastos_manufactura = [
            ("Alquiler local producción", 1200),
            ("Servicios básicos fábrica", 280),
            ("Gas industrial", 150),
            ("Mantenimiento hornos", 200),
            ("Sueldos operarios", 2400),
            ("Transporte distribución", 180),
            ("Empaques y etiquetas", 120),
            ("Limpieza y desinfección", 80),
            ("Seguros maquinaria", 150),
            ("Combustible vehículo", 200)
        ]
        
        for i in range(25):  # 25 gastos en el último mes
            fecha = date.today() - timedelta(days=i*1.2)
            desc, monto_base = random.choice(gastos_manufactura)
            monto = monto_base * random.uniform(0.8, 1.2)
            
            Gasto.objects.create(
                empresa=empresa,
                descripcion=f"{desc} - {fecha.strftime('%B %Y')}",
                monto=round(monto, 2),
                fecha=fecha,
                categoria=random.choice(['Fijo', 'Variable'])
            )
        
        self.stdout.write("[OK] Gastos de manufactura generados")

        # 12. Crear metas financieras para manufactura
        mes_actual = date.today().month
        anio_actual = date.today().year
        
        metas_manufactura = [
            ('ventas', 25000),
            ('gastos', 18000),
            ('utilidad', 7000),
            ('productos', 2000)
        ]
        
        for tipo, objetivo in metas_manufactura:
            MetaFinanciera.objects.get_or_create(
                empresa=empresa,
                tipo=tipo,
                mes=mes_actual,
                anio=anio_actual,
                defaults={
                    'objetivo_mensual': objetivo,
                    'es_dinamica': True,
                    'alertas_activas': True
                }
            )
        
        self.stdout.write("[OK] Metas financieras para manufactura creadas")

        # 13. Crear movimiento contable inicial (capital)
        cuenta_banco = CuentaContable.objects.get(empresa=empresa, nombre='Banco del Austro')
        cuenta_capital = CuentaContable.objects.get(empresa=empresa, nombre='Capital Social')
        
        MovimientoContable.objects.get_or_create(
            empresa=empresa,
            cuenta_fk=cuenta_banco,
            tipo='debito',
            monto=50000,
            descripcion='Capital inicial empresa manufacturera',
            defaults={'cuenta_text': 'Banco del Austro'}
        )
        
        MovimientoContable.objects.get_or_create(
            empresa=empresa,
            cuenta_fk=cuenta_capital,
            tipo='credito',
            monto=50000,
            descripcion='Capital inicial empresa manufacturera',
            defaults={'cuenta_text': 'Capital Social'}
        )
        
        self.stdout.write("[OK] Capital inicial registrado")

        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== EMPRESA DE MANUFACTURA CREADA EXITOSAMENTE! ===\n'
                f'Empresa: {empresa.nombre}\n'
                f'Usuario: {usuario.username} / panadero123\n'
                f'Tipo: {empresa.get_categoria_display()}\n'
                f'Ubicacion: {empresa.ciudad}, {empresa.provincia}\n'
                f'WhatsApp: {empresa.telefono_whatsapp}\n'
                f'Productos: {len(productos_manufacturados)} productos manufacturados\n'
                f'Materias Primas: {len(materias_primas)} materias primas\n'
                f'Proveedores: {len(proveedores)} proveedores\n'
                f'Clientes: {len(clientes)} clientes\n'
                f'Capital inicial: $50,000\n'
            )
        )