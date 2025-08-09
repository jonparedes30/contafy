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
        
        # Debug: Buscar usuario específicamente
        try:
            from empresa.models import Usuario
            usuario_obj = Usuario.objects.get(username=username)
            logger.info(f"Usuario encontrado: {usuario_obj.username}, Empresa: {usuario_obj.empresa}, Activo: {usuario_obj.is_active}")
        except Usuario.DoesNotExist:
            logger.error(f"Usuario no encontrado: {username}")
        
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
                logger.info(f"Login exitoso para: {username}")
                
                if user.empresa:
                    return redirect('empresa:home')
                else:
                    messages.warning(request, 'Tu cuenta no tiene una empresa asociada. Contacta al administrador.')
                    return redirect('empresa:crear_empresa')
            else:
                messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador.')
                log_security_event("LOGIN_INACTIVE", username, ip)
                logger.error(f"Usuario inactivo: {username}")
        else:
            # Login fallido - registrar intento
            attempts = LoginAttemptTracker.record_failed_attempt(username, ip)
            remaining = 5 - attempts
            logger.error(f"Autenticación fallida para: {username}")
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

from django.db import transaction

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
            try:
                with transaction.atomic():
                    user = form.save()  # El formulario ya maneja el orden correcto
                    logger.info(f"Usuario creado: {user.username}, Empresa: {user.empresa}")
                    
                    # Marcar código como usado
                    codigo.usado = True
                    codigo.usado_por = user
                    codigo.save()
                    
                    messages.success(request, 'Cuenta y empresa creadas exitosamente.')
                    return redirect('empresa:login')
            except Exception as e:
                logger.error(f"Error al crear usuario: {str(e)}")
                messages.error(request, f'Error al crear la cuenta: {str(e)}')
        else:
            logger.error(f"Errores del formulario: {form.errors}")
            messages.error(request, 'Por favor corrige los siguientes errores:')
            for field, errors in form.errors.items():
                field_name = form.fields[field].label or field
                for error in errors:
                    messages.error(request, f'{field_name}: {error}')
    else:
        form = RegistroForm()
    return render(request, 'empresa/registro.html', {
        'form': form,
    })
