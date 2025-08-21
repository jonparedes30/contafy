from django.core.management.base import BaseCommand
from empresa.models import CodigoInvitacion

class Command(BaseCommand):
    help = 'Verifica códigos de invitación disponibles'

    def handle(self, *args, **options):
        self.stdout.write("=== CÓDIGOS DE INVITACIÓN ===")
        
        codigos = CodigoInvitacion.objects.all().order_by('-fecha_creacion')
        
        if not codigos.exists():
            self.stdout.write("No hay códigos de invitación creados")
            
            # Crear códigos de prueba
            codigos_prueba = ['BETA2024', 'PRUEBA123', 'DEMO2024', 'CONTAFY2024']
            for codigo in codigos_prueba:
                CodigoInvitacion.objects.create(codigo=codigo, usado=False)
                self.stdout.write(f"✓ Código creado: {codigo}")
            
            self.stdout.write("\n¡Códigos de prueba creados!")
            return
        
        for codigo in codigos:
            estado = "USADO" if codigo.usado else "DISPONIBLE"
            usado_por = f" por {codigo.usado_por.username}" if codigo.usado_por else ""
            
            self.stdout.write(f"Código: {codigo.codigo}")
            self.stdout.write(f"Estado: {estado}{usado_por}")
            self.stdout.write(f"Creado: {codigo.fecha_creacion}")
            self.stdout.write("---")
        
        disponibles = codigos.filter(usado=False).count()
        usados = codigos.filter(usado=True).count()
        
        self.stdout.write(f"\nResumen:")
        self.stdout.write(f"Total códigos: {codigos.count()}")
        self.stdout.write(f"Disponibles: {disponibles}")
        self.stdout.write(f"Usados: {usados}")
        
        if disponibles == 0:
            self.stdout.write("\n⚠️  NO HAY CÓDIGOS DISPONIBLES")
            self.stdout.write("Creando códigos adicionales...")
            
            nuevos_codigos = ['NUEVO2024', 'EXTRA123', 'ADICIONAL2024']
            for codigo in nuevos_codigos:
                obj, created = CodigoInvitacion.objects.get_or_create(
                    codigo=codigo,
                    defaults={'usado': False}
                )
                if created:
                    self.stdout.write(f"✓ Código adicional creado: {codigo}")
        else:
            self.stdout.write(f"\n✅ Hay {disponibles} códigos disponibles para registro")