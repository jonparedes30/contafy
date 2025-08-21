from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from empresa.models import Empresa, CodigoInvitacion
from django.db import connection
import traceback

User = get_user_model()

class Command(BaseCommand):
    help = 'Diagnóstico completo del sistema'

    def handle(self, *args, **options):
        self.stdout.write("=== DIAGNÓSTICO COMPLETO DEL SISTEMA ===")
        
        # 1. Verificar base de datos
        self.stdout.write("\n1. ESTADO DE LA BASE DE DATOS:")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                tables = cursor.fetchall()
                self.stdout.write(f"Tablas en DB: {len(tables)}")
                
                # Verificar tablas críticas
                critical_tables = [
                    'empresa_usuario', 'empresa_empresa', 'empresa_codigoinvitacion',
                    'empresa_moduloaprendizaje', 'empresa_leccion', 'empresa_progresousuario'
                ]
                
                existing_tables = [t[0] for t in tables]
                for table in critical_tables:
                    if table in existing_tables:
                        self.stdout.write(f"✅ {table}")
                    else:
                        self.stdout.write(f"❌ {table} - FALTA")
        except Exception as e:
            self.stdout.write(f"❌ Error DB: {e}")
        
        # 2. Verificar modelos
        self.stdout.write("\n2. ESTADO DE LOS MODELOS:")
        try:
            users_count = User.objects.count()
            empresas_count = Empresa.objects.count()
            codigos_count = CodigoInvitacion.objects.count()
            
            self.stdout.write(f"✅ Usuarios: {users_count}")
            self.stdout.write(f"✅ Empresas: {empresas_count}")
            self.stdout.write(f"✅ Códigos: {codigos_count}")
            
        except Exception as e:
            self.stdout.write(f"❌ Error modelos: {e}")
            traceback.print_exc()
        
        # 3. Verificar migraciones
        self.stdout.write("\n3. ESTADO DE MIGRACIONES:")
        try:
            from django.db.migrations.executor import MigrationExecutor
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            
            if plan:
                self.stdout.write(f"❌ Migraciones pendientes: {len(plan)}")
                for migration, backwards in plan:
                    self.stdout.write(f"  - {migration}")
            else:
                self.stdout.write("✅ Todas las migraciones aplicadas")
                
        except Exception as e:
            self.stdout.write(f"❌ Error migraciones: {e}")
        
        # 4. Verificar configuración AUTH_USER_MODEL
        self.stdout.write("\n4. CONFIGURACIÓN DE USUARIO:")
        from django.conf import settings
        self.stdout.write(f"AUTH_USER_MODEL: {settings.AUTH_USER_MODEL}")
        
        # 5. Verificar superusuarios
        self.stdout.write("\n5. SUPERUSUARIOS:")
        try:
            superusers = User.objects.filter(is_superuser=True)
            for su in superusers:
                self.stdout.write(f"✅ {su.username} - {su.email} - Activo: {su.is_active}")
        except Exception as e:
            self.stdout.write(f"❌ Error superusuarios: {e}")
        
        # 6. Verificar admin
        self.stdout.write("\n6. CONFIGURACIÓN ADMIN:")
        try:
            from django.contrib import admin
            from django.apps import apps
            
            # Verificar si los modelos están registrados en admin
            registered_models = admin.site._registry.keys()
            self.stdout.write(f"Modelos en admin: {len(registered_models)}")
            
            # Verificar modelos específicos
            empresa_models = apps.get_app_config('empresa').get_models()
            for model in empresa_models:
                if model in registered_models:
                    self.stdout.write(f"✅ {model.__name__} registrado en admin")
                else:
                    self.stdout.write(f"❌ {model.__name__} NO registrado en admin")
                    
        except Exception as e:
            self.stdout.write(f"❌ Error admin: {e}")
        
        # 7. Verificar URLs
        self.stdout.write("\n7. URLS PROBLEMÁTICAS:")
        problematic_urls = [
            '/admin/', '/app-beta-2024/resumen/', '/app-beta-2024/admin-simple/'
        ]
        
        for url in problematic_urls:
            self.stdout.write(f"URL: {url}")
        
        # 8. Verificar archivos críticos
        self.stdout.write("\n8. ARCHIVOS CRÍTICOS:")
        import os
        critical_files = [
            'empresa/admin.py',
            'empresa/models.py', 
            'empresa/views/resumen.py',
            'empresa/views/admin_simple.py'
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                self.stdout.write(f"✅ {file_path}")
            else:
                self.stdout.write(f"❌ {file_path} - FALTA")
        
        self.stdout.write("\n=== RECOMENDACIONES ===")
        self.stdout.write("1. Verificar que todas las migraciones estén aplicadas")
        self.stdout.write("2. Verificar configuración de admin.py")
        self.stdout.write("3. Verificar imports en views problemáticas")
        self.stdout.write("4. Considerar usar admin simple en lugar de Django admin")