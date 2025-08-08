from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from empresa.models import CodigoInvitacion

def entrada_beta(request):
    """Vista de entrada para validar códigos de invitación"""
    if request.user.is_authenticated:
        return redirect('empresa:home')
    
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().upper()
        
        if not codigo:
            messages.error(request, 'Por favor ingresa un código de invitación')
            return render(request, 'empresa/entrada_beta.html')
        
        try:
            codigo_obj = CodigoInvitacion.objects.get(codigo=codigo, usado=False)
            # Código válido, redirigir al registro
            request.session['codigo_valido'] = codigo
            return redirect('empresa:registro')
        except CodigoInvitacion.DoesNotExist:
            messages.error(request, 'Código de invitación inválido o ya usado')
    
    return render(request, 'empresa/entrada_beta.html')