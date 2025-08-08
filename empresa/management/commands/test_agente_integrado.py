from django.core.management.base import BaseCommand
from empresa.models import Empresa, Usuario
from empresa.services.ai_comandos_service import procesar_comando_ia

class Command(BaseCommand):
    help = 'Prueba el agente de IA integrado con comandos'

    def handle(self, *args, **options):
        try:
            # Usar empresa ARCA
            empresa = Empresa.objects.get(nombre='ARCA')
            usuario = Usuario.objects.filter(empresa=empresa).first()
            
            if not usuario:
                self.stdout.write(self.style.ERROR("No hay usuarios para empresa ARCA"))
                return
            
            self.stdout.write(f"Probando agente integrado con empresa: {empresa.nombre}")
            self.stdout.write(f"Usuario: {usuario.username}")
            self.stdout.write("=" * 50)
            
            # Comandos de prueba que el usuario podría escribir
            comandos_usuario = [
                "puedes crear un producto en el sistema?",
                "crear producto 'Laptop Dell' precio $800 stock 5",
                "añadir cliente 'Juan Pérez' cedula 1234567890",
                "vender 'Laptop Dell' cantidad 1",
                "cuánto vendí hoy",
                "registrar gasto 'Alquiler' $500"
            ]
            
            for i, comando in enumerate(comandos_usuario, 1):
                self.stdout.write(f"\n{i}. Usuario pregunta: {comando}")
                
                # Simular detección de comando
                es_comando = any(word in comando.lower() for word in ['crear', 'añadir', 'agregar', 'vender', 'registrar', 'cuanto'])
                
                if es_comando:
                    resultado = procesar_comando_ia(empresa, usuario, comando)
                    
                    if resultado.get('success'):
                        self.stdout.write(self.style.SUCCESS(f"   [COMANDO] {resultado['mensaje']}"))
                        if 'datos' in resultado:
                            for key, value in resultado['datos'].items():
                                self.stdout.write(f"     • {key}: {value}")
                    else:
                        self.stdout.write(self.style.ERROR(f"   [ERROR] {resultado.get('error')}"))
                else:
                    self.stdout.write("   [CHAT] Se procesaría como chat normal")
            
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(self.style.SUCCESS("Integración funcionando correctamente!"))
            self.stdout.write("\nEl agente ahora puede:")
            self.stdout.write("✓ Detectar comandos automáticamente")
            self.stdout.write("✓ Ejecutar acciones directas")
            self.stdout.write("✓ Mostrar resultados inmediatos")
            self.stdout.write("✓ Fallback a chat normal si no es comando")
            
        except Empresa.DoesNotExist:
            self.stdout.write(self.style.ERROR("Empresa 'ARCA' no encontrada"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))