#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.models import Empresa, CategoriaProducto, Producto

def verificar_categorias():
    print("=== VERIFICACION DE CATEGORIAS ===")
    
    for empresa in Empresa.objects.all():
        print(f"\n--- {empresa.nombre} ---")
        
        categorias = CategoriaProducto.objects.filter(empresa=empresa)
        productos_con_categoria = Producto.objects.filter(empresa=empresa, categoria__isnull=False)
        productos_sin_categoria = Producto.objects.filter(empresa=empresa, categoria__isnull=True)
        
        print(f"  Categorías: {categorias.count()}")
        print(f"  Productos con categoría: {productos_con_categoria.count()}")
        print(f"  Productos sin categoría: {productos_sin_categoria.count()}")
        
        if categorias.exists():
            print("  Categorías existentes:")
            for cat in categorias:
                productos_en_cat = Producto.objects.filter(empresa=empresa, categoria=cat).count()
                print(f"    - {cat.nombre}: {productos_en_cat} productos")
        else:
            print("  [PROBLEMA] No hay categorías creadas")
            
        if productos_sin_categoria.exists():
            print("  Productos sin categoría:")
            for prod in productos_sin_categoria[:3]:
                print(f"    - {prod.nombre}")

if __name__ == "__main__":
    verificar_categorias()