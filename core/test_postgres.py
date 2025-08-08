import psycopg2

try:
    conn = psycopg2.connect(
        dbname='contafy_db',
        user='django_user',
        password='Django123!',
        host='localhost',
        port='5432'
    )
    print("✅ Conexión exitosa a PostgreSQL")
    conn.close()
except Exception as e:
    print("❌ Error de conexión:")
    print(e)

