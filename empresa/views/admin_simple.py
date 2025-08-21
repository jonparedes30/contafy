from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model
from empresa.models import Empresa, CodigoInvitacion
from django.http import JsonResponse

User = get_user_model()

def is_superuser(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_superuser)
def admin_dashboard(request):
    """Dashboard administrativo simple"""
    
    # Estadísticas básicas
    total_usuarios = User.objects.count()
    total_empresas = Empresa.objects.count()
    total_codigos = CodigoInvitacion.objects.count()
    codigos_disponibles = CodigoInvitacion.objects.filter(usado=False).count()
    
    # Usuarios recientes
    usuarios_recientes = User.objects.all().order_by('-date_joined')[:10]
    
    # Códigos de invitación
    codigos = CodigoInvitacion.objects.all().order_by('-fecha_creacion')[:20]
    
    context = {
        'total_usuarios': total_usuarios,
        'total_empresas': total_empresas,
        'total_codigos': total_codigos,
        'codigos_disponibles': codigos_disponibles,
        'usuarios_recientes': usuarios_recientes,
        'codigos': codigos,
    }
    
    return render(request, 'empresa/admin_simple.html', context)

@user_passes_test(is_superuser)
def crear_codigo_invitacion(request):
    """Crear nuevo código de invitación"""
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        if codigo:
            obj, created = CodigoInvitacion.objects.get_or_create(
                codigo=codigo,
                defaults={'usado': False}
            )
            if created:
                return JsonResponse({'success': True, 'message': f'Código {codigo} creado'})
            else:
                return JsonResponse({'success': False, 'message': 'El código ya existe'})
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})