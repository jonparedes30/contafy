import os
import django
from django.core.mail import send_mail
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def test_email():
    try:
        print("Enviando email de prueba...")
        
        resultado = send_mail(
            subject='[CONTAFY] Prueba de Email',
            message='''
¡Hola Jonathan!

Esta es una prueba del sistema de notificaciones de CONTAFY.

Si recibes este email, significa que el sistema está funcionando correctamente.

Saludos,
Sistema CONTAFY
            '''.strip(),
            from_email='jonathanparedes738@gmail.com',
            recipient_list=['jonathanparedes738@gmail.com'],
            fail_silently=False,
        )
        
        if resultado:
            print("Email enviado correctamente!")
            print("Revisa tu bandeja de entrada: jonathanparedes738@gmail.com")
        else:
            print("Error: No se pudo enviar el email")
            
    except Exception as e:
        print(f"Error enviando email: {e}")
        print("\nVerifica:")
        print("1. Contraseña de aplicación correcta en .env")
        print("2. Verificación en 2 pasos activada en Gmail")
        print("3. Conexión a internet")

if __name__ == "__main__":
    test_email()