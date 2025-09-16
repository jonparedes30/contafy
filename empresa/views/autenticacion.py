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
        codigo_invitacion = request.POST.get('codigo_invitacion', '').strip()
        
        # Verificar código de invitación primero
        if not codigo_invitacion:
            messages.error(request, 'El código de invitación es obligatorio.')
            return render(request, 'empresa/registro.html', {'form': RegistroForm()})
        
        try:
            from empresa.models import CodigoInvitacion
            codigo = CodigoInvitacion.objects.get(codigo=codigo_invitacion, usado=False)
        except CodigoInvitacion.DoesNotExist:
            messages.error(request, 'Código de invitación inválido o ya utilizado. Verifique el código e intente nuevamente.')
            return render(request, 'empresa/registro.html', {'form': RegistroForm()})
        
        form = RegistroForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()  # El formulario ya maneja el orden correcto
                    logger.info(f"Usuario creado exitosamente: {user.username}, Empresa: {user.empresa.nombre}")
                    
                    # Marcar código como usado
                    codigo.usado = True
                    codigo.usado_por = user
                    codigo.save()
                    
                    messages.success(request, f'¡Registro exitoso! Bienvenido {user.first_name}. Tu cuenta y empresa "{user.empresa.nombre}" han sido creadas correctamente.')
                    return redirect('empresa:login')
            except Exception as e:
                logger.error(f"Error crítico al crear usuario: {str(e)}")
                messages.error(request, f'Error interno del sistema. Por favor contacte al soporte técnico. Detalle: {str(e)}')
        else:
            logger.error(f"Errores de validación en formulario: {form.errors}")
            
            # Mostrar errores específicos por campo
            error_count = 0
            for field_name, errors in form.errors.items():
                field_label = form.fields.get(field_name, {}).label or field_name.replace('_', ' ').title()
                for error in errors:
                    error_count += 1
                    if field_name == '__all__':
                        messages.error(request, f'Error general: {error}')
                    else:
                        messages.error(request, f'{field_label}: {error}')
            
            if error_count == 0:
                messages.error(request, 'Hay errores en el formulario. Por favor revise todos los campos.')
    else:
        form = RegistroForm()
    
    return render(request, 'empresa/registro.html', {
        'form': form,
    })
