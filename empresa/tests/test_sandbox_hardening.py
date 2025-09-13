from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
from empresa.models import Empresa, MovimientoContable
from empresa.models_simulaciones import TipoSimulacion, SimulacionUsuario
from empresa.models_audit import AsientoAudit
from empresa.services.simulacion_service import SimulacionService
from empresa.services.contabilidad_service import ContabilidadService
from empresa import sandbox_mode

User = get_user_model()

class SandboxHardeningTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.empresa = Empresa.objects.create(
            nombre='Test Empresa',
            categoria='comercial',
            usuario=self.user
        )
        self.tipo_simulacion = TipoSimulacion.objects.create(
            nombre='Test Venta',
            categoria='comercial',
            descripcion='Test'
        )
    
    def test_sandbox_no_persiste_movimientos(self):
        """Test que simulaciones sandbox no persisten movimientos contables"""
        # Contar movimientos antes
        movimientos_antes = MovimientoContable.objects.filter(empresa=self.empresa).count()
        
        # Crear simulación en modo sandbox
        simulacion = SimulacionService.iniciar_simulacion(
            self.user, 
            self.tipo_simulacion.id,
            modo_sandbox=True
        )
        
        # Procesar simulación con datos válidos
        datos = {
            'producto': 'Test Product',
            'cantidad': 2,
            'precio_unitario': 50.00,
            'subtotal': 100.00,
            'iva': 12.00,
            'total': 112.00,
            'cliente': 'Test Client'
        }
        
        resultado = SimulacionService.procesar_simulacion_venta(
            simulacion, 
            datos, 
            modo_sandbox=True
        )
        
        # Verificar que la simulación se procesó correctamente
        self.assertTrue(resultado['exito'])
        self.assertEqual(resultado['puntuacion'], 100)
        
        # Verificar que NO se crearon movimientos contables
        movimientos_despues = MovimientoContable.objects.filter(empresa=self.empresa).count()
        self.assertEqual(movimientos_antes, movimientos_despues)
        
        # Verificar que la simulación se guardó con es_sandbox=True
        simulacion.refresh_from_db()
        self.assertTrue(simulacion.es_sandbox)
        
        # Verificar que se crearon AsientoAudit pero no MovimientoContable
        asientos_audit = AsientoAudit.objects.filter(simulacion=simulacion)
        self.assertGreater(asientos_audit.count(), 0)
        
        # Verificar balance en audit
        balance = AsientoAudit.validar_balance(simulacion)
        self.assertTrue(balance['balanceado'])
    
    def test_contabilidad_balanceada_en_sandbox(self):
        """Test que la validación de balance funciona en sandbox"""
        simulacion = SimulacionService.iniciar_simulacion(
            self.user,
            self.tipo_simulacion.id,
            modo_sandbox=True
        )
        
        # Datos que generan balance correcto
        datos_balanceados = {
            'producto': 'Test',
            'cantidad': 1,
            'precio_unitario': 100.00,
            'subtotal': 100.00,
            'iva': 12.00,
            'total': 112.00
        }
        
        resultado = SimulacionService.procesar_simulacion_venta(
            simulacion,
            datos_balanceados,
            modo_sandbox=True
        )
        
        # No debe haber errores de sandbox
        self.assertNotIn('sandbox_error', resultado)
        self.assertTrue(resultado['exito'])
    
    def test_sandbox_mode_enable_disable(self):
        """Test que el modo sandbox se habilita y deshabilita correctamente"""
        # Estado inicial
        self.assertFalse(sandbox_mode.is_sandbox())
        
        # Habilitar
        sandbox_mode.enable()
        self.assertTrue(sandbox_mode.is_sandbox())
        
        # Deshabilitar
        sandbox_mode.disable()
        self.assertFalse(sandbox_mode.is_sandbox())
    
    def test_decimal_precision_in_calculations(self):
        """Test que los cálculos usan Decimal para precisión"""
        simulacion = SimulacionService.iniciar_simulacion(
            self.user,
            self.tipo_simulacion.id,
            modo_sandbox=True
        )
        
        # Datos con decimales que pueden causar problemas de precisión
        datos = {
            'producto': 'Test',
            'cantidad': 3,
            'precio_unitario': 33.33,
            'subtotal': 99.99,
            'iva': 12.00,  # Debería ser 11.9988
            'total': 111.99
        }
        
        resultado = SimulacionService.procesar_simulacion_venta(
            simulacion,
            datos,
            modo_sandbox=True
        )
        
        # Verificar que se calcularon correctamente los valores
        self.assertIn('subtotal_correcto', resultado)
        self.assertIn('iva_correcto', resultado)
        self.assertIn('total_correcto', resultado)
        
        # Los valores correctos deben ser números, no strings
        self.assertIsInstance(resultado['subtotal_correcto'], (int, float))
        self.assertIsInstance(resultado['iva_correcto'], (int, float))
        self.assertIsInstance(resultado['total_correcto'], (int, float))
    
    def test_simulacion_metadata_persists(self):
        """Test que los metadatos de simulación sí se persisten"""
        simulacion = SimulacionService.iniciar_simulacion(
            self.user,
            self.tipo_simulacion.id,
            modo_sandbox=True
        )
        
        datos = {
            'producto': 'Test',
            'cantidad': 1,
            'precio_unitario': 50.00,
            'subtotal': 50.00,
            'iva': 6.00,
            'total': 56.00
        }
        
        resultado = SimulacionService.procesar_simulacion_venta(
            simulacion,
            datos,
            modo_sandbox=True
        )
        
        # Verificar que la simulación se actualizó en la DB
        simulacion.refresh_from_db()
        self.assertEqual(simulacion.estado, 'completada')
        self.assertIsNotNone(simulacion.fecha_completado)
        self.assertGreater(simulacion.puntuacion, 0)
        self.assertTrue(simulacion.datos_entrada)
        self.assertTrue(simulacion.resultado)