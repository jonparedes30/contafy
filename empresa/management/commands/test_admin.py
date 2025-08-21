from django.core.management.base import BaseCommand
from django.contrib import admin
from django.apps import apps

class Command(BaseCommand):
    help = 'Prueba la configuración del admin'

    def handle(self, *args, **options):
        self.stdout.write("=== PRUEBA DE CONFIGURACIÓN ADMIN ===")
        
        try:
            # 1. Verificar modelos registrados
            self.stdout.write("\n1. MODELOS REGISTRADOS:")
            registered_models = admin.site._registry
            self.stdout.write(f"Total modelos registrados: {len(registered_models)}")
            
            for model, admin_class in registered_models.items():
                self.stdout.write(f"✅ {model.__name__} -> {admin_class.__class__.__name__}")
            
            # 2. Verificar errores específicos
            self.stdout.write("\n2. VERIFICANDO ERRORES ESPECÍFICOS:")
            
            # Verificar ModuloAprendizaje
            try:
                from empresa.models_aprendizaje import ModuloAprendizaje
                fields = [f.name for f in ModuloAprendizaje._meta.fields]
                self.stdout.write(f"ModuloAprendizaje campos: {fields}")
                
                if 'nombre' in fields:
                    self.stdout.write("✅ Campo 'nombre' existe")
                else:
                    self.stdout.write("❌ Campo 'nombre' NO existe")
                    
            except Exception as e:
                self.stdout.write(f"❌ Error con ModuloAprendizaje: {e}")
            
            # Verificar PasoCompletado
            try:
                from empresa.models_aprendizaje import PasoCompletado
                fields = [f.name for f in PasoCompletado._meta.fields]
                self.stdout.write(f"PasoCompletado campos: {fields}")
                
                if 'creado_en' in fields:
                    self.stdout.write("✅ Campo 'creado_en' existe")
                else:
                    self.stdout.write("❌ Campo 'creado_en' NO existe")
                    
            except Exception as e:
                self.stdout.write(f"❌ Error con PasoCompletado: {e}")
            
            # 3. Verificar imports problemáticos
            self.stdout.write("\n3. VERIFICANDO IMPORTS:")
            
            try:
                from empresa.models_aprendizaje import (
                    ModuloAprendizaje, Leccion, ProgresoUsuario, 
                    PerfilAprendizaje, PasoCompletado
                )
                self.stdout.write("✅ Imports de aprendizaje OK")
            except Exception as e:
                self.stdout.write(f"❌ Error imports aprendizaje: {e}")
            
            # 4. Verificar admin específicos
            self.stdout.write("\n4. VERIFICANDO ADMIN CLASSES:")
            
            try:
                from empresa.admin import ModuloAprendizajeAdmin
                self.stdout.write("✅ ModuloAprendizajeAdmin importado")
            except Exception as e:
                self.stdout.write(f"❌ Error ModuloAprendizajeAdmin: {e}")
                
            try:
                from empresa.admin import PasoCompletadoAdmin
                self.stdout.write("✅ PasoCompletadoAdmin importado")
            except Exception as e:
                self.stdout.write(f"❌ Error PasoCompletadoAdmin: {e}")
            
        except Exception as e:
            self.stdout.write(f"❌ Error general: {e}")
            import traceback
            traceback.print_exc()
        
        self.stdout.write("\n=== RECOMENDACIÓN ===")
        self.stdout.write("Si hay errores, usar admin simple en lugar de Django admin")
        self.stdout.write("URL: /app-beta-2024/admin-simple/")