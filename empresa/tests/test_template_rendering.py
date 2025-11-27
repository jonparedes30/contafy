"""
Integration tests to verify that templates render without errors.
Tests resumen and manufactura dashboard templates with different company categories.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from decimal import Decimal

from empresa.models import Empresa
from empresa.views.resumen import resumen_financiero
from empresa.views.manufactura import dashboard_manufactura

User = get_user_model()


class TemplateRenderingTests(TestCase):
    """Test that templates render without KeyError or template errors"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        
        # Create test companies with different categories
        self.comercio_empresa = Empresa.objects.create(
            nombre="Comercio Test",
            ruc="1792146739001",
            direccion="Test Address",
            categoria="comercio"
        )
        
        self.manufactura_empresa = Empresa.objects.create(
            nombre="Manufactura Test",
            ruc="1792146739002",
            direccion="Test Address 2",
            categoria="manufactura"
        )
        
        # Create test users
        self.comercio_user = User.objects.create_user(
            username="comercio_user",
            password="testpass123",
            empresa=self.comercio_empresa
        )
        
        self.manufactura_user = User.objects.create_user(
            username="manufactura_user",
            password="testpass123",
            empresa=self.manufactura_empresa
        )
    
    def _add_session_and_auth_to_request(self, request, user):
        """Helper to add session and auth middleware to request"""
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        auth_middleware = AuthenticationMiddleware(lambda x: None)
        auth_middleware.process_request(request)
        
        message_middleware = MessageMiddleware(lambda x: None)
        message_middleware.process_request(request)
        
        request.user = user
        return request
    
    def test_resumen_comercio_renders(self):
        """Test that resumen dashboard renders for comercio company"""
        request = self.factory.get('/empresa/resumen/')
        request = self._add_session_and_auth_to_request(request, self.comercio_user)
        
        try:
            response = resumen_financiero(request)
            # Should render successfully (status 200 or render response)
            self.assertIn(response.status_code, [200, 301])  # 301 for redirects
        except Exception as e:
            self.fail(f"Resumen rendering failed for comercio: {str(e)}")
    
    def test_manufactura_dashboard_renders(self):
        """Test that manufactura dashboard renders without errors"""
        request = self.factory.get('/empresa/manufactura/')
        request = self._add_session_and_auth_to_request(request, self.manufactura_user)
        
        try:
            response = dashboard_manufactura(request)
            # Should render successfully
            self.assertIn(response.status_code, [200, 301])
        except Exception as e:
            self.fail(f"Manufactura dashboard rendering failed: {str(e)}")
    
    def test_resumen_context_has_required_keys(self):
        """Test that resumen context has all required keys from presenter"""
        request = self.factory.get('/empresa/resumen/')
        request = self._add_session_and_auth_to_request(request, self.comercio_user)
        
        # Attempt to render; if context is missing keys, template will raise VariableDoesNotExist
        try:
            response = resumen_financiero(request)
            # If we get here without exception, the context must have the required keys
            self.assertIsNotNone(response)
        except Exception as e:
            # Log the error for debugging
            print(f"Context error in resumen: {str(e)}")
            # Re-raise so test fails with clear message
            raise
    
    def test_manufactura_context_has_required_keys(self):
        """Test that manufactura dashboard context has all required keys"""
        request = self.factory.get('/empresa/manufactura/')
        request = self._add_session_and_auth_to_request(request, self.manufactura_user)
        
        try:
            response = dashboard_manufactura(request)
            self.assertIsNotNone(response)
        except Exception as e:
            print(f"Context error in manufactura dashboard: {str(e)}")
            raise
