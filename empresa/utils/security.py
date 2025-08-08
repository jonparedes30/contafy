"""Utilidades de seguridad"""
import time
import hashlib
from django.core.cache import cache
from django.conf import settings


class RateLimiter:
    """Rate limiter simple usando cache"""
    
    @staticmethod
    def is_rate_limited(identifier, max_attempts=5, window=300):
        """
        Verifica si un identificador está limitado por rate limiting
        Args:
            identifier: IP, usuario, etc.
            max_attempts: máximo intentos permitidos
            window: ventana de tiempo en segundos
        """
        cache_key = f"rate_limit:{hashlib.md5(identifier.encode()).hexdigest()}"
        attempts = cache.get(cache_key, 0)
        
        if attempts >= max_attempts:
            return True
        
        cache.set(cache_key, attempts + 1, window)
        return False
    
    @staticmethod
    def reset_rate_limit(identifier):
        """Resetea el rate limit para un identificador"""
        cache_key = f"rate_limit:{hashlib.md5(identifier.encode()).hexdigest()}"
        cache.delete(cache_key)


def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_security_event(event_type, user, ip, details=""):
    """Log de eventos de seguridad"""
    import logging
    logger = logging.getLogger('empresa.security')
    
    logger.warning(f"SECURITY_EVENT: {event_type} | User: {user} | IP: {ip} | Details: {details}")


class LoginAttemptTracker:
    """Rastrea intentos de login fallidos"""
    
    @staticmethod
    def record_failed_attempt(username, ip):
        """Registra un intento fallido"""
        cache_key = f"failed_login:{username}:{ip}"
        attempts = cache.get(cache_key, 0) + 1
        cache.set(cache_key, attempts, 900)  # 15 minutos
        
        log_security_event("FAILED_LOGIN", username, ip, f"Attempt {attempts}")
        return attempts
    
    @staticmethod
    def is_locked_out(username, ip, max_attempts=5):
        """Verifica si está bloqueado"""
        cache_key = f"failed_login:{username}:{ip}"
        attempts = cache.get(cache_key, 0)
        return attempts >= max_attempts
    
    @staticmethod
    def reset_attempts(username, ip):
        """Resetea intentos después de login exitoso"""
        cache_key = f"failed_login:{username}:{ip}"
        cache.delete(cache_key)