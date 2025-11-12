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
        except Exception as e:
            logger.error(f"Error en CurrentUserMiddleware: {str(e)}")
            _user.value = None
    
    def process_exception(self, request, exception):
        """Log de excepciones"""
        try:
            if isinstance(exception, PermissionDenied):
                logger.warning(f"Acceso denegado para {getattr(request, 'user', 'unknown')}: {request.path}")
            else:
                logger.error(f"Excepción en {request.path}: {str(exception)}")
        except Exception:
            pass
        return None

class SecurityMiddleware(MiddlewareMixin):
    """Middleware de seguridad adicional"""
    
    # Patrones sospechosos como atributo de clase (más eficiente)
    SUSPICIOUS_PATTERNS = frozenset(['wp-admin', 'phpmyadmin', '.env', 'config.php'])
    
    def process_request(self, request):
        # Solo verificar rutas sospechosas (más rápido)
        path_lower = request.path.lower()
        if any(pattern in path_lower for pattern in self.SUSPICIOUS_PATTERNS):
            logger.warning(f"Solicitud sospechosa: {request.path}")
        return None 