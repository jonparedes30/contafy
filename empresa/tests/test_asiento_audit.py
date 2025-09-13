from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from empresa.models import Empresa
from empresa.models_simulaciones import TipoSimulacion, SimulacionUsuario
from empresa.models_audit import AsientoAudit

User = get_user_model()

class AsientoAuditTests(TestCase):
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
        self.simulacion = SimulacionUsuario.objects.create(
            usuario=self.user,
            tipo_simulacion=self.tipo_simulacion,
            es_sandbox=True
        )
    
    def test_crear_asientos_audit(self):
        """Test creación de asientos audit"""
        asientos = [
            {
                'cuenta': 'Caja',
                'tipo_cuenta': 'activo',
                'tipo_movimiento': 'debito',
                'monto': Decimal('100.00'),
                'descripcion': 'Test debito'
            },
            {
                'cuenta': 'Ventas',
                'tipo_cuenta': 'ingreso',
                'tipo_movimiento': 'credito',
                'monto': Decimal('100.00'),
                'descripcion': 'Test credito'
            }
        ]
        
        AsientoAudit.crear_desde_asientos(
            self.simulacion,
            asientos,
            'test_transaction'
        )
        
        # Verificar que se crearon los asientos
        audit_records = AsientoAudit.objects.filter(simulacion=self.simulacion)
        self.assertEqual(audit_records.count(), 2)
        
        # Verificar datos
        debito = audit_records.filter(tipo_movimiento='debito').first()
        self.assertEqual(debito.cuenta, 'Caja')
        self.assertEqual(debito.monto, Decimal('100.00'))
        
        credito = audit_records.filter(tipo_movimiento='credito').first()
        self.assertEqual(credito.cuenta, 'Ventas')
        self.assertEqual(credito.monto, Decimal('100.00'))
    
    def test_validar_balance_correcto(self):
        """Test validación de balance correcto"""
        AsientoAudit.objects.create(
            simulacion=self.simulacion,
            cuenta='Caja',
            tipo_cuenta='activo',
            tipo_movimiento='debito',
            monto=Decimal('100.00'),
            descripcion='Test',
            transaccion_id='test'
        )
        AsientoAudit.objects.create(
            simulacion=self.simulacion,
            cuenta='Ventas',
            tipo_cuenta='ingreso',
            tipo_movimiento='credito',
            monto=Decimal('100.00'),
            descripcion='Test',
            transaccion_id='test'
        )
        
        balance = AsientoAudit.validar_balance(self.simulacion)
        self.assertTrue(balance['balanceado'])
        self.assertEqual(balance['debitos'], Decimal('100.00'))
        self.assertEqual(balance['creditos'], Decimal('100.00'))
        self.assertEqual(balance['diferencia'], Decimal('0.00'))
    
    def test_validar_balance_desbalanceado(self):
        """Test validación de balance desbalanceado"""
        AsientoAudit.objects.create(
            simulacion=self.simulacion,
            cuenta='Caja',
            tipo_cuenta='activo',
            tipo_movimiento='debito',
            monto=Decimal('100.00'),
            descripcion='Test',
            transaccion_id='test'
        )
        AsientoAudit.objects.create(
            simulacion=self.simulacion,
            cuenta='Ventas',
            tipo_cuenta='ingreso',
            tipo_movimiento='credito',
            monto=Decimal('90.00'),
            descripcion='Test',
            transaccion_id='test'
        )
        
        balance = AsientoAudit.validar_balance(self.simulacion)
        self.assertFalse(balance['balanceado'])
        self.assertEqual(balance['diferencia'], Decimal('10.00'))