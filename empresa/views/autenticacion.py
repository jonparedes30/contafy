# empresa/views/autenticacion.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
import logging

from empresa.forms import RegistroForm
from empresa.utils.security import LoginAttemptTracker, get_client_ip, log_security_event

logger = logging.getLogger(__name__)

def login_usuario(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        ip = get_client_ip(request)
        
        # Verificar rate limiting
        if LoginAttemptTracker.is_locked_out(username, ip):
            log_security_event("LOGIN_BLOCKED", username, ip, "Too many failed attempts")
            messages.error(request, 'Demasiados intentos fallidos. Intenta en 15 minutos.')
            response = HttpResponse("Too many login attempts", status=429)
            return response
        
        if not username or not password:
            messages.error(request, 'Por favor ingresa usuario y contraseña')
            return render(request, 'empresa/login.html')
        
        user = authenticate(
            request,
            username=username,
            password=password
        )
        
        if user is not None:
            if user.is_active:
                # Login exitoso - resetear intentos
                LoginAttemptTracker.reset_attempts(username, ip)
                login(request, user)
                log_security_event("LOGIN_SUCCESS", username, ip)
                
                if user.empresa:
                    return redirect('empresa:home')
                else:
                    messages.warning(request, 'Tu cuenta no tiene una empresa asociada. Contacta al administrador.')
                    return redirect('empresa:crear_empresa')
            else:
                messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador.')
                log_security_event("LOGIN_INACTIVE", username, ip)
        else:
            # Login fallido - registrar intento
            attempts = LoginAttemptTracker.record_failed_attempt(username, ip)
            remaining = 5 - attempts
            if remaining > 0:
                messages.error(request, f'Usuario o contraseña incorrectos. {remaining} intentos restantes.')
            else:
                messages.error(request, 'Cuenta bloqueada por intentos fallidos.')
    
    return render(request, 'empresa/login.html')

def logout_usuario(request):
    # Limpiar todos los mensajes antes del logout
    storage = messages.get_messages(request)
    for message in storage:
        pass  # Consume todos los mensajes
    
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente')
    return redirect('empresa:login')

def registrar_usuario(request):
    if request.method == 'POST':
        codigo_invitacion = request.POST.get('codigo_invitacion')
        
        # Verificar código de invitación
        try:
            from empresa.models import CodigoInvitacion
            codigo = CodigoInvitacion.objects.get(codigo=codigo_invitacion, usado=False)
        except CodigoInvitacion.DoesNotExist:
            messages.error(request, 'Código de invitación inválido o ya usado')
            return render(request, 'empresa/registro.html', {'form': RegistroForm()})
        
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Marcar código como usado
            codigo.usado = True
            codigo.usado_por = user
            codigo.save()
            
            messages.success(request, 'Cuenta y empresa creadas exitosamente.')
            return redirect('empresa:login')
        messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = RegistroForm()
    return render(request, 'empresa/registro.html', {
        'form': form,
    })
