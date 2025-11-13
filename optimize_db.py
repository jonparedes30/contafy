"""
Script para optimizar la base de datos SQLite
Ejecutar con: python optimize_db.py
"""
import sqlite3
import os

DB_PATH = 'contafy_sistema.db'

if not os.path.exists(DB_PATH):
    print(f"Base de datos no encontrada: {DB_PATH}")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("Optimizando base de datos...")

# Analizar y optimizar
cursor.execute("ANALYZE")
cursor.execute("VACUUM")

# Configurar pragmas para mejor rendimiento
cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
cursor.execute("PRAGMA synchronous=NORMAL")  # Balance entre velocidad y seguridad
cursor.execute("PRAGMA cache_size=-64000")  # 64MB de caché
cursor.execute("PRAGMA temp_store=MEMORY")  # Usar memoria para temporales

conn.commit()
conn.close()

print("✓ Base de datos optimizada")
print("✓ Modo WAL activado para mejor concurrencia")
print("✓ Caché aumentado a 64MB")
