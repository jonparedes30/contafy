#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'heroku_settings')
django.setup()

from empresa.models import Usuario, Empresa

print("=== PRUEBA DE CREACIÓN DE USUARIO ===")

# Verificar si podemos crear un usuario de prueba
try:
    # Crear empresa de prueba si no existe
    empresa_test, created = Empresa.objects.get_or_create(
        nombre="Empresa Test Admin",
        defaults={'categoria': 'comercial'}
    )
    
    if created:
        print(f"✅ Empresa creada: {empresa_test.nombre}")
    else:
        print(f"✅ Empresa existente: {empresa_test.nombre}")
    
    # Crear usuario de prueba
    usuario_test = Usuario.objects.create_user(
        username='test_admin_user',
        email='test@admin.com',
        password='test123',
        empresa=empresa_test
    )
    
    print(f"✅ Usuario creado exitosamente:")
    print(f"   - Username: {usuario_test.username}")
    print(f"   - Email: {usuario_test.email}")
    print(f"   - Empresa: {usuario_test.empresa.nombre}")
    print(f"   - ID: {usuario_test.id}")
    
    # Verificar que el usuario se puede autenticar
    from django.contrib.auth import authenticate
    auth_user = authenticate(username='test_admin_user', password='test123')
    
    if auth_user:
        print("✅ Usuario puede autenticarse correctamente")
    else:
        print("❌ Error en autenticación")
    
    print("\n=== USUARIOS ACTUALES ===")
    for u in Usuario.objects.all():
        print(f"- {u.username} ({u.email}) - Empresa: {u.empresa.nombre if u.empresa else 'Sin empresa'}")
        
except Exception as e:
    print(f"❌ Error al crear usuario: {e}")
    import traceback
    traceback.print_exc()