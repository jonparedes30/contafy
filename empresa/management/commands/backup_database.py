from django.core.management.base import BaseCommand
from django.conf import settings
import os
import subprocess
import datetime
from pathlib import Path

class Command(BaseCommand):
    help = 'Crear respaldo de la base de datos'

    def handle(self, *args, **options):
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
            self.stdout.write(f"[OK] Backup PostgreSQL: {backup_file}")
            
        else:
            # SQLite backup
            db_path = settings.DATABASES['default']['NAME']
            backup_file = backup_dir / f'contafy_backup_{timestamp}.db'
            
            import shutil
            shutil.copy2(db_path, backup_file)
            self.stdout.write(f"[OK] Backup SQLite: {backup_file}")