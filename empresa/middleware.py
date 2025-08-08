import threading
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)
_user = threading.local()

def get_current_user():
    """Obtiene el usuario actual desde el thread local"""
    return getattr(_user, 'value', None)

class CurrentUserMiddleware(MiddlewareMixin):
    """Middleware para capturar el usuario actual en cada request"""
    
    def process_request(self, request):
        try:
            _user.value = request.user if request.user.is_authenticated else None
            if request.user.is_authenticated:
                logger.info(f"Usuario {request.user.username} accedió a {request.path}")
        except Exception as e:
            logger.error(f"Error en CurrentUserMiddleware: {str(e)}")
            _user.value = None
    
    def process_exception(self, request, exception):
        """Log de excepciones"""
        if isinstance(exception, PermissionDenied):
            logger.warning(f"Acceso denegado para {request.user}: {request.path}")
        else:
            logger.error(f"Excepción en {request.path}: {str(exception)}")
        return None

class SecurityMiddleware(MiddlewareMixin):
    """Middleware de seguridad adicional"""
    
    def process_request(self, request):
        # Rate limiting básico por IP
        ip = self.get_client_ip(request)
        
        # Log de intentos sospechosos
        if self.is_suspicious_request(request):
            logger.warning(f"Solicitud sospechosa desde {ip}: {request.path}")
        
        return None
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_suspicious_request(self, request):
        """Detecta patrones sospechosos"""
        suspicious_patterns = [
            'admin', 'wp-admin', 'phpmyadmin', '.env', 'config'
        ]
        return any(pattern in request.path.lower() for pattern in suspicious_patterns) 