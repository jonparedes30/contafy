"""
Patches para bloquear side-effects externos durante simulaciones sandbox
"""
import logging
from unittest.mock import patch
from empresa.sandbox_mode import is_sandbox

logger = logging.getLogger(__name__)

# Mock functions que se ejecutan en lugar de las reales durante sandbox
def mock_send_mail(*args, **kwargs):
    if is_sandbox():
        logger.info("SANDBOX: Email bloqueado")
        return True
    # Si no es sandbox, importar y ejecutar la función real
    from django.core.mail import send_mail as real_send_mail
    return real_send_mail(*args, **kwargs)

def mock_requests_post(*args, **kwargs):
    if is_sandbox():
        logger.info("SANDBOX: HTTP POST bloqueado")
        return MockResponse(200, {"status": "sandbox_blocked"})
    # Si no es sandbox, importar y ejecutar la función real
    import requests
    return requests.post(*args, **kwargs)

def mock_celery_delay(self, *args, **kwargs):
    if is_sandbox():
        logger.info(f"SANDBOX: Celery task {self.name} bloqueado")
        return MockAsyncResult("sandbox_task_id")
    # Si no es sandbox, ejecutar la función real
    return self._original_delay(*args, **kwargs)

class MockResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data
    
    def json(self):
        return self._json_data

class MockAsyncResult:
    def __init__(self, task_id):
        self.id = task_id
        self.state = "SANDBOX"
    
    def get(self, timeout=None):
        return {"status": "sandbox_completed"}

def apply_sandbox_patches():
    """Aplica patches para bloquear side-effects en sandbox"""
    
    # Patch Django send_mail
    try:
        import django.core.mail
        django.core.mail.send_mail = mock_send_mail
    except ImportError:
        pass
    
    # Patch requests
    try:
        import requests
        requests.post = mock_requests_post
    except ImportError:
        pass
    
    # Patch Celery tasks
    try:
        from celery import Task
        if not hasattr(Task, '_original_delay'):
            Task._original_delay = Task.delay
            Task.delay = mock_celery_delay
    except ImportError:
        pass
    
    logger.info("Sandbox patches aplicados")

def remove_sandbox_patches():
    """Remueve patches y restaura funciones originales"""
    
    # Restaurar Celery
    try:
        from celery import Task
        if hasattr(Task, '_original_delay'):
            Task.delay = Task._original_delay
            delattr(Task, '_original_delay')
    except ImportError:
        pass
    
    logger.info("Sandbox patches removidos")

# Aplicar patches al importar el módulo
apply_sandbox_patches()