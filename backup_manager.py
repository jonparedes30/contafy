#!/usr/bin/env python
"""
Script de respaldo automático para CONTAFY
Ejecutar: python backup_manager.py
"""
import os
import subprocess
import datetime
from pathlib import Path
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def backup_database():
    """Crear respaldo de la base de datos"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    
    if 'postgres' in settings.DATABASES['default']['ENGINE']:
        # PostgreSQL backup
        db_config = settings.DATABASES['default']
        backup_file = backup_dir / f'contafy_backup_{timestamp}.sql'
        
        cmd = [
            'pg_dump',
            f"--host={db_config.get('HOST', 'localhost')}",
            f"--port={db_config.get('PORT', '5432')}",
            f"--username={db_config['USER']}",
            f"--dbname={db_config['NAME']}",
            f"--file={backup_file}"
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['PASSWORD']
        
        subprocess.run(cmd, env=env, check=True)
        print(f"✅ Backup PostgreSQL creado: {backup_file}")
        
    else:
        # SQLite backup
        db_path = settings.DATABASES['default']['NAME']
        backup_file = backup_dir / f'contafy_backup_{timestamp}.db'
        
        import shutil
        shutil.copy2(db_path, backup_file)
        print(f"✅ Backup SQLite creado: {backup_file}")
    
    return backup_file

def cleanup_old_backups(days=7):
    """Eliminar backups antiguos"""
    backup_dir = Path('backups')
    if not backup_dir.exists():
        return
    
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    
    for backup_file in backup_dir.glob('contafy_backup_*'):
        if backup_file.stat().st_mtime < cutoff.timestamp():
            backup_file.unlink()
            print(f"🗑️ Backup eliminado: {backup_file}")

if __name__ == '__main__':
    try:
        backup_file = backup_database()
        cleanup_old_backups()
        print(f"✅ Proceso de backup completado exitosamente")
    except Exception as e:
        print(f"❌ Error en backup: {e}")