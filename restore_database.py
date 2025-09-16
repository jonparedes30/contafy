#!/usr/bin/env python
"""
Script para restaurar respaldos de CONTAFY
Uso: python restore_database.py backup_file.sql
"""
import os
import sys
import subprocess
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings

def restore_database(backup_file):
    """Restaurar base de datos desde archivo de respaldo"""
    backup_path = Path(backup_file)
    
    if not backup_path.exists():
        print(f"❌ Archivo de respaldo no encontrado: {backup_file}")
        return False
    
    if 'postgres' in settings.DATABASES['default']['ENGINE']:
        # PostgreSQL restore
        db_config = settings.DATABASES['default']
        
        # Confirmar restauración
        response = input(f"⚠️ ¿Restaurar {backup_file}? Esto sobrescribirá la BD actual (s/N): ")
        if response.lower() != 's':
            print("Restauración cancelada")
            return False
        
        cmd = [
            'psql',
            f"--host={db_config.get('HOST', 'localhost')}",
            f"--port={db_config.get('PORT', '5432')}",
            f"--username={db_config['USER']}",
            f"--dbname={db_config['NAME']}",
            f"--file={backup_path}"
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['PASSWORD']
        
        subprocess.run(cmd, env=env, check=True)
        print(f"✅ Base de datos restaurada desde: {backup_file}")
        
    else:
        # SQLite restore
        db_path = settings.DATABASES['default']['NAME']
        
        response = input(f"⚠️ ¿Restaurar {backup_file}? Esto sobrescribirá la BD actual (s/N): ")
        if response.lower() != 's':
            print("Restauración cancelada")
            return False
        
        import shutil
        shutil.copy2(backup_path, db_path)
        print(f"✅ Base de datos SQLite restaurada desde: {backup_file}")
    
    return True

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Uso: python restore_database.py <archivo_respaldo>")
        print("Ejemplo: python restore_database.py backups/contafy_backup_20241201_140000.sql")
        sys.exit(1)
    
    backup_file = sys.argv[1]
    
    try:
        restore_database(backup_file)
    except Exception as e:
        print(f"❌ Error en restauración: {e}")