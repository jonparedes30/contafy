# empresa/views/autenticacion.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import logging

from empresa.forms import RegistroForm
from empresa.utils.errores import mensaje_error
from empresa.utils.security import LoginAttemptTracker, get_client_ip, log_security_event

logger = logging.getLogger(__name__)

def login_usuario(request):
    # Logging CSRF para diagnóstico
    if request.method == 'POST':
        logger.info(f"POST login - CSRF token en POST: {request.POST.get('csrfmiddlewaretoken', 'MISSING')[:20]}...")
        logger.info(f"POST login - CSRF cookie: {request.COOKIES.get('csrftoken', 'MISSING')[:20]}...")
        logger.info(f"POST login - Referer: {request.META.get('HTTP_REFERER', 'MISSING')}")
        logger.info(f"POST login - Origin: {request.META.get('HTTP_ORIGIN', 'MISSING')}")
    
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
from django.utils import timezone
from datetime import timedelta

def _error_codigo_invitacion(codigo):
    """Mensaje de error del código de invitación, o '' si es válido."""
    from empresa.models import CodigoInvitacion
    if not codigo:
        return 'Ingresa el código de invitación que recibiste.'
    if not CodigoInvitacion.objects.filter(codigo=codigo, usado=False).exists():
        return 'El código no es válido o ya fue utilizado.'
    return ''


@require_POST
def validar_registro_paso(request):
    """Valida solo los campos de una etapa del registro con las reglas reales del formulario.

    Devuelve {"ok": bool, "errores": {campo: mensaje}}. Así el asistente avisa
    en cada etapa (usuario ya tomado, RUC inválido, contraseña débil) y no al final.
    """
    campos = [c for c in request.POST.getlist('campos') if c in RegistroForm.base_fields or c == 'codigo_invitacion']
    form = RegistroForm(request.POST)
    form.is_valid()
    errores = {c: form.errors[c][0] for c in campos if c in form.errors}
    # Las contraseñas que no coinciden se reportan como error general del formulario.
    if 'password2' in campos and 'password2' not in errores:
        for e in form.non_field_errors():
            errores['password2'] = e
    if 'codigo_invitacion' in campos and request.POST.get('modo_demo') != '1':
        error = _error_codigo_invitacion(request.POST.get('codigo_invitacion', '').strip())
        if error:
            errores['codigo_invitacion'] = error
    return JsonResponse({'ok': not errores, 'errores': errores})


def registrar_usuario(request):
    modo_demo = request.GET.get('modo') == 'demo' or request.POST.get('modo_demo') == '1'

    if request.method == 'POST':
        codigo_invitacion = request.POST.get('codigo_invitacion', '').strip()
        modo_demo = request.POST.get('modo_demo') == '1'

        if not modo_demo:
            # Verificar código de invitación (flujo normal / beta)
            # Si el código falla se devuelve el formulario con lo que el usuario ya escribió.
            error_codigo = _error_codigo_invitacion(codigo_invitacion)
            if error_codigo:
                return render(request, 'empresa/registro.html', {
                    'form': RegistroForm(request.POST), 'modo_demo': False, 'error_codigo': error_codigo,
                })
            from empresa.models import CodigoInvitacion
            codigo = CodigoInvitacion.objects.get(codigo=codigo_invitacion, usado=False)

        form = RegistroForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()  # El formulario ya maneja el orden correcto
                    logger.info(f"Usuario creado exitosamente: {user.username}, Empresa: {user.empresa.nombre}")

                    if modo_demo:
                        # Marcar la empresa como demo y fijar expiración a 7 días
                        empresa = user.empresa
                        empresa.es_demo = True
                        empresa.demo_expira = timezone.now() + timedelta(days=7)
                        empresa.save(update_fields=['es_demo', 'demo_expira'])
                        logger.info(f"Cuenta demo creada para: {user.username}, expira: {empresa.demo_expira}")
                        messages.success(
                            request,
                            f'¡Bienvenido a tu demo, {user.first_name}! '
                            f'Tienes 7 días para explorar Contafy. '
                            f'Tu acceso expira el {empresa.demo_expira.strftime("%d/%m/%Y")}.'
                        )
                    else:
                        # Marcar código como usado (flujo beta)
                        codigo.usado = True
                        codigo.usado_por = user
                        codigo.save()
                        messages.success(
                            request,
                            f'¡Registro exitoso! Bienvenido {user.first_name}. '
                            f'Tu cuenta y empresa "{user.empresa.nombre}" han sido creadas correctamente.'
                        )
                    return redirect('empresa:login')
            except Exception as e:
                logger.error(f"Error crítico al crear usuario: {str(e)}")
                messages.error(request, mensaje_error(e, 'No se pudo crear la cuenta. Inténtalo de nuevo o contacta a soporte.'))
        else:
            logger.info("Registro con errores de validación: %s", list(form.errors))
            # Cada error se muestra junto a su campo; el asistente abre la etapa que lo contiene.
            messages.error(request, 'Revisa los campos marcados para completar el registro.')
    else:
        form = RegistroForm()

    return render(request, 'empresa/registro.html', {
        'form': form,
        'modo_demo': modo_demo,
    })
