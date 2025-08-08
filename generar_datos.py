#!/usr/bin/env python
"""Script para generar datos de prueba para el sistema contable"""
import os
import django
from decimal import Decimal
from datetime import date, timedelta
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.models import (
    Empresa, Usuario, Cliente, Proveedor, CategoriaProducto, 
    Producto, Venta, Compra, Gasto, CuentaPorCobrar, CuentaPorPagar
)

def generar_datos():
    print("Generando datos para sistema contable...")
    
    # 1. Crear empresa principal
    empresa, created = Empresa.objects.get_or_create(
        ruc="1792146739001",
        defaults={
            'nombre': "Comercial San Martin",
            'direccion': "Av. Amazonas 123, Quito"
        }
    )
    print(f"Empresa creada: {empresa.nombre}")
    
    # 2. Crear usuario principal
    usuario = Usuario.objects.create_user(
        username="jona30",
        email="jona@comercial.com",
        password="password123",
        first_name="Jonathan",
        last_name="Paredes",
        empresa=empresa
    )
    print(f"Usuario creado: {usuario.username}")
    
    # 3. Crear categorías de productos
    categorias = [
        ("Electrónicos", "Productos electrónicos y tecnología"),
        ("Hogar", "Artículos para el hogar"),
        ("Oficina", "Suministros de oficina"),
        ("Alimentación", "Productos alimenticios"),
        ("Limpieza", "Productos de limpieza")
    ]
    
    cats_creadas = []
    for nombre, desc in categorias:
        cat = CategoriaProducto.objects.create(
            empresa=empresa,
            nombre=nombre,
            descripcion=desc
        )
        cats_creadas.append(cat)
    print(f"{len(cats_creadas)} categorias creadas")
    
    # 4. Crear clientes
    clientes_data = [
        ("María González", "1712345678", "0987654321", 1000),
        ("Carlos Pérez", "1798765432", "0912345678", 1500),
        ("Ana Rodríguez", "1723456789", "0923456789", 800),
        ("Luis Morales", "1734567890", "0934567890", 2000),
        ("Sofia Herrera", "1745678901", "0945678901", 1200)
    ]
    
    clientes = []
    for nombre, doc, tel, credito in clientes_data:
        cliente = Cliente.objects.create(
            empresa=empresa,
            nombre=nombre,
            numero_documento=doc,
            telefono=tel,
            limite_credito=credito
        )
        clientes.append(cliente)
    print(f"{len(clientes)} clientes creados")
    
    # 5. Crear proveedores
    proveedores_data = [
        ("Distribuidora Tech", "1792123456001", "0987123456", 30),
        ("Suministros Hogar", "1793234567001", "0987234567", 15),
        ("Papelería Central", "1794345678001", "0987345678", 45),
        ("Alimentos Frescos", "1795456789001", "0987456789", 7),
        ("Limpieza Total", "1796567890001", "0987567890", 30)
    ]
    
    proveedores = []
    for nombre, ruc, tel, dias in proveedores_data:
        proveedor = Proveedor.objects.create(
            empresa=empresa,
            nombre=nombre,
            ruc=ruc,
            telefono=tel,
            dias_credito=dias
        )
        proveedores.append(proveedor)
    print(f"{len(proveedores)} proveedores creados")
    
    # 6. Crear productos
    productos_data = [
        ("Laptop HP", "TECH001", cats_creadas[0], 800, 1200, 5, 50),
        ("Mouse Inalámbrico", "TECH002", cats_creadas[0], 15, 25, 20, 100),
        ("Silla Oficina", "HOG001", cats_creadas[1], 120, 180, 3, 20),
        ("Mesa Escritorio", "HOG002", cats_creadas[1], 200, 300, 2, 15),
        ("Papel A4", "OF001", cats_creadas[2], 3, 5, 50, 200),
        ("Bolígrafos", "OF002", cats_creadas[2], 0.5, 1, 100, 500),
        ("Café Premium", "ALI001", cats_creadas[3], 8, 12, 25, 100),
        ("Detergente", "LIM001", cats_creadas[4], 4, 6, 30, 150)
    ]
    
    productos = []
    for nombre, codigo, cat, costo, pvp, stock_min, stock in productos_data:
        producto = Producto.objects.create(
            empresa=empresa,
            nombre=nombre,
            codigo=codigo,
            categoria=cat,
            precio_unitario=costo,
            pvp=pvp,
            stock=stock,
            stock_minimo=stock_min,
            stock_maximo=stock * 2
        )
        productos.append(producto)
    print(f"{len(productos)} productos creados")
    
    # 7. Crear ventas del último mes
    print("Generando ventas...")
    for i in range(30):
        fecha = date.today() - timedelta(days=i)
        # 2-5 ventas por día
        num_ventas = random.randint(2, 5)
        
        for _ in range(num_ventas):
            cliente = random.choice(clientes) if random.random() > 0.3 else None
            producto = random.choice(productos)
            cantidad = random.randint(1, 5)
            precio = producto.pvp
            
            total = cantidad * precio
            venta = Venta.objects.create(
                empresa=empresa,
                cliente_fk=cliente,
                cliente_nombre=cliente.nombre if cliente else f"Cliente {random.randint(1000, 9999)}",
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio,
                monto=total,
                tipo_pago=random.choice(['contado', 'credito']),
                fecha=fecha
            )
            
            # Crear cuenta por cobrar si es a crédito
            if venta.tipo_pago == 'credito' and cliente:
                CuentaPorCobrar.objects.create(
                    empresa=empresa,
                    cliente=cliente,
                    venta=venta,
                    monto_original=venta.monto,
                    monto_pendiente=venta.monto * random.uniform(0.3, 1.0),
                    fecha_vencimiento=fecha + timedelta(days=30),
                    estado='pendiente'
                )
    
    print("Ventas generadas para los ultimos 30 dias")
    
    # 8. Crear compras
    print("Generando compras...")
    for i in range(20):
        fecha = date.today() - timedelta(days=i*2)
        proveedor = random.choice(proveedores)
        producto = random.choice(productos)
        cantidad = random.randint(10, 50)
        total = cantidad * producto.precio_unitario
        
        compra = Compra.objects.create(
            empresa=empresa,
            proveedor_fk=proveedor,
            proveedor_nombre=proveedor.nombre,
            producto=producto,
            cantidad=cantidad,
            monto=total,
            tipo_pago=random.choice(['contado', 'credito']),
            fecha=fecha
        )
        
        # Crear cuenta por pagar si es a crédito
        if compra.tipo_pago == 'credito':
            CuentaPorPagar.objects.create(
                empresa=empresa,
                proveedor=proveedor,
                compra=compra,
                monto_original=total,
                monto_pendiente=total * random.uniform(0.5, 1.0),
                fecha_vencimiento=fecha + timedelta(days=proveedor.dias_credito),
                estado='pendiente'
            )
    
    print("Compras generadas")
    
    # 9. Crear gastos
    gastos_data = [
        ("Alquiler local", 800),
        ("Servicios básicos", 150),
        ("Internet", 45),
        ("Combustible", 120),
        ("Publicidad", 200),
        ("Mantenimiento", 80),
        ("Seguros", 100)
    ]
    
    for i in range(15):
        fecha = date.today() - timedelta(days=i*2)
        desc, monto_base = random.choice(gastos_data)
        monto = monto_base * random.uniform(0.8, 1.2)
        
        Gasto.objects.create(
            empresa=empresa,
            descripcion=f"{desc} - {fecha.strftime('%B')}",
            monto=round(monto, 2),
            fecha=fecha
        )
    
    print("Gastos generados")
    
    print("\nDatos generados exitosamente!")
    print("Usuario: jona30 / password123")
    print(f"Empresa: {empresa.nombre}")
    print("Datos listos para usar")

if __name__ == "__main__":
    generar_datos()