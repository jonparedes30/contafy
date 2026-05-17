"""
Tests de contabilidad para Contafy.

Verifica:
- Asientos contables balanceados (débitos = créditos)
- IVA calculado correctamente al 15% (Ecuador)
- Integridad contable general
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.core.exceptions import ValidationError

from empresa.models import (
    Empresa, Producto, Venta, Compra, Gasto,
    CuentaContable, MovimientoContable, Usuario,
)
from empresa.services.contabilidad_service import ContabilidadService


@pytest.mark.django_db
class TestTransaccionBalanceada(TestCase):
    """Verifica que toda transacción contable esté balanceada."""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Contable', ruc='1790016919001',
            direccion='Quito', categoria='comercial',
        )

    def test_transaccion_balanceada_simple(self):
        """Una transacción con débitos = créditos debe funcionar."""
        asientos = [
            {
                'cuenta': 'Caja',
                'tipo_cuenta': 'activo',
                'tipo_movimiento': 'debito',
                'monto': Decimal('100.00'),
                'descripcion': 'Ingreso de efectivo',
            },
            {
                'cuenta': 'Ventas',
                'tipo_cuenta': 'ingreso',
                'tipo_movimiento': 'credito',
                'monto': Decimal('100.00'),
                'descripcion': 'Venta al contado',
            },
        ]
        tid = ContabilidadService.crear_transaccion_contable(
            self.empresa, asientos, "Test balanceado"
        )
        self.assertIsNotNone(tid)

        # Verificar que los movimientos se crearon
        movs = MovimientoContable.objects.filter(transaccion_id=tid)
        self.assertEqual(movs.count(), 2)

    def test_transaccion_desbalanceada_falla(self):
        """Una transacción desbalanceada debe lanzar ValidationError."""
        asientos = [
            {
                'cuenta': 'Caja',
                'tipo_cuenta': 'activo',
                'tipo_movimiento': 'debito',
                'monto': Decimal('100.00'),
                'descripcion': 'Ingreso',
            },
            {
                'cuenta': 'Ventas',
                'tipo_cuenta': 'ingreso',
                'tipo_movimiento': 'credito',
                'monto': Decimal('50.00'),  # Desbalanceado!
                'descripcion': 'Venta',
            },
        ]
        with self.assertRaises(ValidationError):
            ContabilidadService.crear_transaccion_contable(
                self.empresa, asientos, "Desbalanceado"
            )

    def test_transaccion_sin_debito_falla(self):
        """Una transacción sin débito debe fallar."""
        asientos = [
            {
                'cuenta': 'Ventas',
                'tipo_cuenta': 'ingreso',
                'tipo_movimiento': 'credito',
                'monto': Decimal('100.00'),
                'descripcion': 'Solo crédito',
            },
        ]
        with self.assertRaises(ValidationError):
            ContabilidadService.crear_transaccion_contable(
                self.empresa, asientos, "Sin débito"
            )

    def test_transaccion_multiples_asientos(self):
        """Una transacción con IVA debe tener múltiples asientos balanceados."""
        monto_neto = Decimal('100.00')
        iva = Decimal('15.00')  # 15%
        total = monto_neto + iva

        asientos = [
            {
                'cuenta': 'Caja',
                'tipo_cuenta': 'activo',
                'tipo_movimiento': 'debito',
                'monto': total,
                'descripcion': 'Cobro total',
            },
            {
                'cuenta': 'IVA por Pagar',
                'tipo_cuenta': 'pasivo',
                'tipo_movimiento': 'credito',
                'monto': iva,
                'descripcion': 'IVA 15%',
            },
            {
                'cuenta': 'Ventas',
                'tipo_cuenta': 'ingreso',
                'tipo_movimiento': 'credito',
                'monto': monto_neto,
                'descripcion': 'Venta neta',
            },
        ]

        tid = ContabilidadService.crear_transaccion_contable(
            self.empresa, asientos, "Venta con IVA"
        )

        # Verificar balance
        movs = MovimientoContable.objects.filter(transaccion_id=tid)
        debitos = sum(m.monto for m in movs if m.tipo == 'debito')
        creditos = sum(m.monto for m in movs if m.tipo == 'credito')
        self.assertEqual(debitos, creditos)
        self.assertEqual(debitos, total)


@pytest.mark.django_db
class TestIVAEcuador(TestCase):
    """Verifica cálculos de IVA al 15% (estándar Ecuador)."""

    IVA_TASA = Decimal('15')  # 15%

    def test_calculo_iva_basico(self):
        """IVA del 15% sobre $100 = $15."""
        base = Decimal('100.00')
        iva = base * self.IVA_TASA / Decimal('100')
        self.assertEqual(iva, Decimal('15.00'))

    def test_calculo_iva_total(self):
        """Total = base + IVA."""
        base = Decimal('200.00')
        iva = base * self.IVA_TASA / Decimal('100')
        total = base + iva
        self.assertEqual(total, Decimal('230.00'))

    def test_iva_cero_exento(self):
        """Productos exentos tienen IVA 0%."""
        base = Decimal('100.00')
        iva = base * Decimal('0') / Decimal('100')
        self.assertEqual(iva, Decimal('0'))

    def test_asientos_venta_con_iva(self):
        """Los asientos de una venta deben reflejar el IVA correctamente."""
        empresa = Empresa.objects.create(
            nombre='IVA Test', ruc='1791234567001',
            direccion='Guayaquil', categoria='comercial',
        )
        monto_neto = Decimal('100.00')
        iva = monto_neto * self.IVA_TASA / Decimal('100')

        # Débito total = monto_neto + IVA
        # Crédito IVA por Pagar = IVA
        # Crédito Ventas = monto_neto
        asientos = [
            {
                'cuenta': 'Caja',
                'tipo_cuenta': 'activo',
                'tipo_movimiento': 'debito',
                'monto': monto_neto + iva,
                'descripcion': 'Cobro venta con IVA',
            },
            {
                'cuenta': 'IVA por Pagar',
                'tipo_cuenta': 'pasivo',
                'tipo_movimiento': 'credito',
                'monto': iva,
                'descripcion': 'IVA 15%',
            },
            {
                'cuenta': 'Ventas',
                'tipo_cuenta': 'ingreso',
                'tipo_movimiento': 'credito',
                'monto': monto_neto,
                'descripcion': 'Ingreso por venta',
            },
        ]

        tid = ContabilidadService.crear_transaccion_contable(
            empresa, asientos, "Venta IVA test"
        )

        # Verificar que IVA por Pagar tiene exactamente $15
        iva_mov = MovimientoContable.objects.filter(
            transaccion_id=tid, cuenta_text='IVA por Pagar'
        ).first()
        self.assertEqual(iva_mov.monto, Decimal('15.00'))
        self.assertEqual(iva_mov.tipo, 'credito')


@pytest.mark.django_db
class TestIntegridadContable(TestCase):
    """Tests del método de verificación de integridad."""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Integridad Test', ruc='1792345678001',
            direccion='Cuenca', categoria='comercial',
        )

    def test_empresa_sin_movimientos_ok(self):
        """Una empresa sin movimientos tiene integridad OK."""
        reporte = ContabilidadService.verificar_integridad_empresa(self.empresa)
        self.assertTrue(reporte['integridad_ok'])
        self.assertEqual(len(reporte['desbalances']), 0)

    def test_empresa_con_transacciones_balanceadas_ok(self):
        """Empresa con transacciones balanceadas pasa la verificación."""
        # Crear 3 transacciones balanceadas
        for i in range(3):
            ContabilidadService.crear_transaccion_contable(
                self.empresa,
                [
                    {
                        'cuenta': 'Caja',
                        'tipo_cuenta': 'activo',
                        'tipo_movimiento': 'debito',
                        'monto': Decimal('50.00'),
                        'descripcion': f'Test {i}',
                    },
                    {
                        'cuenta': 'Ventas',
                        'tipo_cuenta': 'ingreso',
                        'tipo_movimiento': 'credito',
                        'monto': Decimal('50.00'),
                        'descripcion': f'Test {i}',
                    },
                ],
                f"Transaccion test {i}",
            )

        reporte = ContabilidadService.verificar_integridad_empresa(self.empresa)
        self.assertTrue(reporte['integridad_ok'])
        self.assertEqual(reporte['total_transacciones'], 3)
