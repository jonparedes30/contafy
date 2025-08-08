# En empresa/models.py - AGREGAR
class CodigoInvitacion(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    usado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usado_por = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    
    def __str__(self):
        return f"Código: {self.codigo} - {'Usado' if self.usado else 'Disponible'}"

# En empresa/views/autenticacion.py - MODIFICAR
from empresa.models import CodigoInvitacion
import secrets

def registrar_usuario(request):
    if request.method == 'POST':
        codigo_invitacion = request.POST.get('codigo_invitacion')
        
        # Verificar código de invitación
        try:
            codigo = CodigoInvitacion.objects.get(codigo=codigo_invitacion, usado=False)
        except CodigoInvitacion.DoesNotExist:
            messages.error(request, 'Código de invitación inválido o ya usado')
            return render(request, 'empresa/registro.html')
        
        # Resto del código de registro...
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Marcar código como usado
            codigo.usado = True
            codigo.usado_por = user
            codigo.save()
            
            messages.success(request, 'Usuario registrado exitosamente')
            return redirect('empresa:login')
    
    return render(request, 'empresa/registro.html')

# Comando para generar códigos - management/commands/generar_codigos.py
from django.core.management.base import BaseCommand
from empresa.models import CodigoInvitacion
import secrets

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('cantidad', type=int, help='Cantidad de códigos a generar')
    
    def handle(self, *args, **options):
        cantidad = options['cantidad']
        codigos_generados = []
        
        for i in range(cantidad):
            codigo = f"CONTAFY-{secrets.token_urlsafe(8).upper()}"
            CodigoInvitacion.objects.create(codigo=codigo)
            codigos_generados.append(codigo)
        
        self.stdout.write(f"Códigos generados:")
        for codigo in codigos_generados:
            self.stdout.write(f"- {codigo}")