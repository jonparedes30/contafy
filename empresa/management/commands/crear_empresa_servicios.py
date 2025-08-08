from django.core.management.base import BaseCommand
from empresa.models import (
    Empresa, Usuario, Cliente, CategoriaProducto, 
    Producto, Venta, Gasto, CuentaContable, MovimientoContable,
    MetaFinanciera
)
from decimal import Decimal
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Crea empresa de servicios con datos demo ecuatorianos'

    def handle(self, *args, **options):
        # 1. Crear empresa de servicios
        empresa, created = Empresa.objects.get_or_create(
            ruc="1792345678001",
            defaults={
                'nombre': "Consultora Digital Quito",
                'direccion': "Av. 6 de Diciembre N24-253, Quito",
                'categoria': 'servicios',
                'tipo_negocio': 'consultoria',
                'provincia': 'Pichincha',
                'ciudad': 'Quito',
                'telefono_whatsapp': '+593987654321',
                'latitud': Decimal('-0.1807'),
                'longitud': Decimal('-78.4678')
            }
        )
        
        if created:
            self.stdout.write(f"[OK] Empresa creada: {empresa.nombre}")
        else:
            self.stdout.write(f"[OK] Empresa ya existe: {empresa.nombre}")

        # 2. Crear usuario
        usuario, created = Usuario.objects.get_or_create(
            username="maria_consultora",
            defaults={
                'email': "maria@consultoraquito.com",
                'first_name': "María",
                'last_name': "Vásquez",
                'empresa': empresa
            }
        )
        
        if created:
            usuario.set_password("consultora123")
            usuario.save()
            self.stdout.write(f"[OK] Usuario creado: {usuario.username}")
        else:
            self.stdout.write(f"[OK] Usuario ya existe: {usuario.username}")

        # 3. Crear categorías de servicios
        categorias_servicios = [
            ("Consultoría Digital", "Servicios de transformación digital"),
            ("Desarrollo Web", "Creación de sitios web y aplicaciones"),
            ("Marketing Digital", "Publicidad y marketing en línea"),
            ("Capacitación", "Cursos y talleres empresariales"),
            ("Soporte Técnico", "Mantenimiento y soporte IT")
        ]
        
        categorias_creadas = []
        for nombre, desc in categorias_servicios:
            cat, created = CategoriaProducto.objects.get_or_create(
                empresa=empresa,
                nombre=nombre,
                defaults={'descripcion': desc}
            )
            categorias_creadas.append(cat)
        
        self.stdout.write(f"[OK] {len(categorias_creadas)} categorias de servicios creadas")

        # 4. Crear clientes empresariales
        clientes_data = [
            ("Restaurante El Fogón", "1791234567001", "0987123456", 3000),
            ("Farmacia San José", "1792345678001", "0987234567", 2500),
            ("Taller Mecánico López", "1793456789001", "0987345678", 2000),
            ("Boutique Elegancia", "1794567890001", "0987456789", 1800),
            ("Panadería Doña Rosa", "1795678901001", "0987567890", 1500),
            ("Ferretería El Martillo", "1796789012001", "0987678901", 3500),
            ("Clínica Dental Sonrisa", "1797890123001", "0987789012", 4000)
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
        
        self.stdout.write(f"[OK] {len(clientes)} clientes empresariales creados")

        # 5. Crear servicios (productos)
        servicios_data = [
            ("Consultoría Digital Básica", "CONS001", categorias_creadas[0], 800, 1200, 1, 10),
            ("Auditoría de Procesos", "CONS002", categorias_creadas[0], 1200, 1800, 1, 5),
            ("Sitio Web Corporativo", "WEB001", categorias_creadas[1], 1500, 2500, 1, 8),
            ("Tienda Online", "WEB002", categorias_creadas[1], 2000, 3200, 1, 6),
            ("Campaña Facebook Ads", "MKT001", categorias_creadas[2], 300, 500, 1, 20),
            ("Gestión Redes Sociales", "MKT002", categorias_creadas[2], 400, 650, 1, 15),
            ("Curso Excel Empresarial", "CAP001", categorias_creadas[3], 150, 250, 1, 30),
            ("Taller Marketing Digital", "CAP002", categorias_creadas[3], 200, 350, 1, 25),
            ("Soporte Técnico Mensual", "SOP001", categorias_creadas[4], 100, 180, 1, 50),
            ("Instalación Software", "SOP002", categorias_creadas[4], 80, 150, 1, 40)
        ]
        
        servicios = []
        for nombre, codigo, cat, costo, precio, stock_min, stock in servicios_data:
            servicio, created = Producto.objects.get_or_create(
                empresa=empresa,
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'categoria': cat,
                    'precio_unitario': costo,
                    'pvp': precio,
                    'stock': stock,
                    'stock_minimo': stock_min,
                    'stock_maximo': stock * 2,
                    'descripcion': f"Servicio profesional de {nombre.lower()}"
                }
            )
            servicios.append(servicio)
        
        self.stdout.write(f"[OK] {len(servicios)} servicios creados")

        # 6. Crear cuentas contables específicas para servicios
        cuentas_servicios = [
            ('Ingresos por Servicios', 'ingreso'),
            ('Caja Chica', 'activo'),
            ('Banco Pichincha', 'activo'),
            ('Gastos Operativos', 'gasto'),
            ('Gastos de Marketing', 'gasto'),
            ('Equipos de Oficina', 'activo'),
            ('Cuentas por Cobrar Servicios', 'activo'),
            ('Capital Social', 'capital')
        ]
        
        for nombre, tipo in cuentas_servicios:
            CuentaContable.objects.get_or_create(
                empresa=empresa,
                nombre=nombre,
                defaults={'tipo': tipo}
            )
        
        self.stdout.write("[OK] Cuentas contables para servicios creadas")

        # 7. Generar ventas de servicios del último mes
        self.stdout.write("Generando ventas de servicios...")
        
        for i in range(25):  # 25 días de ventas
            fecha = date.today() - timedelta(days=i)
            # 1-3 servicios por día
            num_ventas = random.randint(1, 3)
            
            for _ in range(num_ventas):
                cliente = random.choice(clientes)
                servicio = random.choice(servicios)
                cantidad = 1  # Los servicios generalmente son unitarios
                precio = servicio.pvp
                
                venta = Venta.objects.create(
                    empresa=empresa,
                    cliente_fk=cliente,
                    cliente_nombre=cliente.nombre,
                    producto=servicio,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    monto=precio,
                    tipo_pago=random.choice(['contado', 'credito']),
                    fecha=fecha
                )
        
        self.stdout.write("[OK] Ventas de servicios generadas")

        # 8. Crear gastos típicos de empresa de servicios
        gastos_servicios = [
            ("Alquiler oficina", 650),
            ("Internet fibra óptica", 85),
            ("Servicios básicos", 120),
            ("Licencias software", 200),
            ("Publicidad Google Ads", 300),
            ("Combustible visitas clientes", 150),
            ("Telefonía móvil", 45),
            ("Material de oficina", 80),
            ("Capacitación equipo", 250),
            ("Hosting y dominios", 35)
        ]
        
        for i in range(20):  # 20 gastos en el último mes
            fecha = date.today() - timedelta(days=i*2)
            desc, monto_base = random.choice(gastos_servicios)
            monto = monto_base * random.uniform(0.8, 1.2)
            
            Gasto.objects.create(
                empresa=empresa,
                descripcion=f"{desc} - {fecha.strftime('%B %Y')}",
                monto=round(monto, 2),
                fecha=fecha,
                categoria=random.choice(['Fijo', 'Variable'])
            )
        
        self.stdout.write("[OK] Gastos de servicios generados")

        # 9. Crear metas financieras para servicios
        mes_actual = date.today().month
        anio_actual = date.today().year
        
        metas_servicios = [
            ('ventas', 8000),
            ('gastos', 3500),
            ('utilidad', 4500),
            ('clientes', 15)
        ]
        
        for tipo, objetivo in metas_servicios:
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
        
        self.stdout.write("[OK] Metas financieras para servicios creadas")

        # 10. Crear movimiento contable inicial (capital)
        cuenta_banco = CuentaContable.objects.get(empresa=empresa, nombre='Banco Pichincha')
        cuenta_capital = CuentaContable.objects.get(empresa=empresa, nombre='Capital Social')
        
        MovimientoContable.objects.get_or_create(
            empresa=empresa,
            cuenta_fk=cuenta_banco,
            tipo='debito',
            monto=15000,
            descripcion='Capital inicial empresa de servicios',
            defaults={'cuenta_text': 'Banco Pichincha'}
        )
        
        MovimientoContable.objects.get_or_create(
            empresa=empresa,
            cuenta_fk=cuenta_capital,
            tipo='credito',
            monto=15000,
            descripcion='Capital inicial empresa de servicios',
            defaults={'cuenta_text': 'Capital Social'}
        )
        
        self.stdout.write("[OK] Capital inicial registrado")

        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== EMPRESA DE SERVICIOS CREADA EXITOSAMENTE! ===\n'
                f'Empresa: {empresa.nombre}\n'
                f'Usuario: {usuario.username} / consultora123\n'
                f'Tipo: {empresa.get_categoria_display()}\n'
                f'Ubicacion: {empresa.ciudad}, {empresa.provincia}\n'
                f'WhatsApp: {empresa.telefono_whatsapp}\n'
                f'Servicios: {len(servicios)} servicios profesionales\n'
                f'Clientes: {len(clientes)} empresas\n'
                f'Capital inicial: $15,000\n'
            )
        )