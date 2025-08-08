from django.core.management.base import BaseCommand
from empresa.models import Empresa, Usuario
from empresa.services.ai_comandos_service import procesar_comando_ia

class Command(BaseCommand):
    help = 'Prueba el sistema de comandos de IA'

    def handle(self, *args, **options):
        try:
            # Usar la empresa de servicios que creamos
            empresa = Empresa.objects.get(nombre='Consultora Digital Quito')
            usuario = Usuario.objects.get(username='maria_consultora')
            
            self.stdout.write(f"Probando IA con empresa: {empresa.nombre}")
            self.stdout.write(f"Usuario: {usuario.username}")
            self.stdout.write("=" * 50)
            
            # Lista de comandos de prueba
            comandos_prueba = [
                "crear producto 'Laptop Gaming' precio $1200 stock 3 categoria 'Tecnología'",
                "añadir cliente 'Empresa XYZ' ruc 1791234567001 telefono 0987654321",
                "crear categoria 'Hardware'",
                "vender 'Consultoría Digital Básica' cantidad 1 cliente 'Restaurante El Fogón'",
                "registrar gasto 'Publicidad Facebook' $150",
                "generar reporte de ventas",
                "crear meta de ventas $10000",
                "cuánto vendí hoy",
                "cuánto stock tengo",
                "automatizar alertas de stock bajo"
            ]
            
            for i, comando in enumerate(comandos_prueba, 1):
                self.stdout.write(f"\n{i}. Comando: {comando}")
                resultado = procesar_comando_ia(empresa, usuario, comando)
                
                if resultado.get('success'):
                    self.stdout.write(self.style.SUCCESS(f"   [OK] {resultado['mensaje']}"))
                    if 'datos' in resultado:
                        for key, value in resultado['datos'].items():
                            self.stdout.write(f"     {key}: {value}")
                else:
                    self.stdout.write(self.style.ERROR(f"   [ERROR] {resultado.get('error', 'Error desconocido')}"))
            
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(self.style.SUCCESS("Pruebas de IA completadas!"))
            
        except Empresa.DoesNotExist:
            self.stdout.write(self.style.ERROR("Empresa 'Consultora Digital Quito' no encontrada"))
            self.stdout.write("Ejecuta: python manage.py crear_empresa_servicios")
        except Usuario.DoesNotExist:
            self.stdout.write(self.style.ERROR("Usuario 'maria_consultora' no encontrado"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))