from django.core.management.base import BaseCommand
from empresa.models import Usuario, Empresa

class Command(BaseCommand):
    help = 'Diagnostica problemas con usuarios y empresas'

    def handle(self, *args, **options):
        self.stdout.write("=== DIAGNÓSTICO DE USUARIOS ===")
        
        # 1. Usuarios sin empresa
        usuarios_sin_empresa = Usuario.objects.filter(empresa__isnull=True)
        self.stdout.write(f"Usuarios sin empresa: {usuarios_sin_empresa.count()}")
        for user in usuarios_sin_empresa:
            self.stdout.write(f"  - {user.username} (ID: {user.id})")
        
        # 2. Empresas sin usuarios
        empresas_sin_usuarios = Empresa.objects.filter(usuarios__isnull=True)
        self.stdout.write(f"Empresas sin usuarios: {empresas_sin_usuarios.count()}")
        for empresa in empresas_sin_usuarios:
            self.stdout.write(f"  - {empresa.nombre} (RUC: {empresa.ruc})")
        
        # 3. Usuarios duplicados por username
        from django.db.models import Count
        duplicados = Usuario.objects.values('username').annotate(
            count=Count('username')
        ).filter(count__gt=1)
        
        self.stdout.write(f"Usernames duplicados: {duplicados.count()}")
        for dup in duplicados:
            users = Usuario.objects.filter(username=dup['username'])
            self.stdout.write(f"  - {dup['username']} ({dup['count']} veces)")
            for user in users:
                empresa_info = f"Empresa: {user.empresa.nombre}" if user.empresa else "Sin empresa"
                self.stdout.write(f"    ID: {user.id}, {empresa_info}")
        
        # 4. Verificar usuarios activos
        usuarios_activos = Usuario.objects.filter(is_active=True)
        self.stdout.write(f"Usuarios activos: {usuarios_activos.count()}")
        
        # 5. Opción de limpieza
        if input("\n¿Quieres limpiar usuarios problemáticos? (s/n): ").lower() == 's':
            self.limpiar_usuarios()
    
    def limpiar_usuarios(self):
        self.stdout.write("=== LIMPIANDO USUARIOS ===")
        
        # Eliminar usuarios sin empresa
        usuarios_sin_empresa = Usuario.objects.filter(empresa__isnull=True)
        count = usuarios_sin_empresa.count()
        usuarios_sin_empresa.delete()
        self.stdout.write(f"Eliminados {count} usuarios sin empresa")
        
        # Eliminar empresas sin usuarios
        empresas_sin_usuarios = Empresa.objects.filter(usuarios__isnull=True)
        count = empresas_sin_usuarios.count()
        empresas_sin_usuarios.delete()
        self.stdout.write(f"Eliminadas {count} empresas sin usuarios")
        
        self.stdout.write("Limpieza completada")