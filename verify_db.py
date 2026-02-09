#!/usr/bin/env python
"""
Script de verificación de conexión a la base de datos
Útil para diagnosticar problemas de deploy en Render
"""
import os
import sys
import time
from urllib.parse import urlparse

def verificar_database_url():
    """Verifica que DATABASE_URL esté configurada correctamente"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL no está configurada")
        return False
    
    print("✅ DATABASE_URL está configurada")
    
    # Parsear la URL
    try:
        parsed = urlparse(database_url)
        print(f"📊 Detalles de conexión:")
        print(f"   - Esquema: {parsed.scheme}")
        print(f"   - Hostname: {parsed.hostname}")
        print(f"   - Puerto: {parsed.port or 5432}")
        print(f"   - Base de datos: {parsed.path.lstrip('/')}")
        print(f"   - Usuario: {parsed.username}")
        return True
    except Exception as e:
        print(f"❌ ERROR al parsear DATABASE_URL: {e}")
        return False

def verificar_dns():
    """Verifica que el hostname se pueda resolver"""
    import socket
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        return False
    
    try:
        parsed = urlparse(database_url)
        hostname = parsed.hostname
        
        print(f"\n🔍 Verificando resolución DNS para: {hostname}")
        ip = socket.gethostbyname(hostname)
        print(f"✅ Hostname resuelto a: {ip}")
        return True
    except socket.gaierror as e:
        print(f"❌ ERROR: No se pudo resolver el hostname: {e}")
        print("   Posibles causas:")
        print("   1. La base de datos aún no está completamente aprovisionada")
        print("   2. Problema temporal de red/DNS")
        print("   3. Hostname interno incorrecto")
        return False
    except Exception as e:
        print(f"❌ ERROR inesperado: {e}")
        return False

def verificar_conexion_postgres():
    """Intenta conectarse a PostgreSQL"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return False
        
        print("\n🔌 Intentando conectar a PostgreSQL...")
        
        # Intentar conexión con timeout
        conn = psycopg2.connect(database_url, connect_timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Conexión exitosa!")
        print(f"   PostgreSQL version: {version}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ ERROR de conexión: {e}")
        return False
    except ImportError:
        print("⚠️ psycopg2 no está instalado, saltando prueba de conexión")
        return None
    except Exception as e:
        print(f"❌ ERROR inesperado: {e}")
        return False

def main():
    print("=" * 60)
    print("🔧 VERIFICACIÓN DE CONEXIÓN A BASE DE DATOS")
    print("=" * 60)
    
    # Paso 1: Verificar DATABASE_URL
    if not verificar_database_url():
        sys.exit(1)
    
    # Paso 2: Verificar DNS
    time.sleep(1)
    if not verificar_dns():
        print("\n💡 SOLUCIONES SUGERIDAS:")
        print("   1. Espera 5-10 minutos para que la base de datos termine de aprovisionarse")
        print("   2. Verifica en Render Dashboard que la base de datos esté 'Available'")
        print("   3. Usa la External Connection String en lugar de la Internal")
        print("   4. Contacta a Render Support si el problema persiste")
        sys.exit(1)
    
    # Paso 3: Verificar conexión
    time.sleep(1)
    result = verificar_conexion_postgres()
    
    if result is False:
        print("\n💡 La resolución DNS funciona pero la conexión falla.")
        print("   Verifica las credenciales y que la base de datos acepte conexiones.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ TODAS LAS VERIFICACIONES PASARON")
    print("=" * 60)
    sys.exit(0)

if __name__ == "__main__":
    main()
