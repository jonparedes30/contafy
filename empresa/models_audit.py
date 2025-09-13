from django.db import models
from django.conf import settings
from decimal import Decimal

class AsientoAudit(models.Model):
    """
    Modelo para auditar asientos contables creados en simulaciones sandbox.
    No afecta la contabilidad real, solo registra para análisis.
    """
    simulacion = models.ForeignKey(
        'empresa.SimulacionUsuario', 
        on_delete=models.CASCADE,
        related_name='asientos_audit'
    )
    cuenta = models.CharField(max_length=100)
    tipo_cuenta = models.CharField(max_length=20)  # activo, pasivo, capital, ingreso, gasto
    tipo_movimiento = models.CharField(max_length=10)  # debito, credito
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.TextField()
    transaccion_id = models.CharField(max_length=50)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Asiento Audit'
        verbose_name_plural = 'Asientos Audit'
        indexes = [
            models.Index(fields=['simulacion', 'transaccion_id']),
            models.Index(fields=['tipo_movimiento', 'creado_en']),
        ]
    
    def __str__(self):
        return f"{self.cuenta} - {self.tipo_movimiento} - ${self.monto}"
    
    @classmethod
    def crear_desde_asientos(cls, simulacion, asientos, transaccion_id):
        """Crea registros audit desde lista de asientos"""
        audit_records = []
        for asiento in asientos:
            audit_records.append(cls(
                simulacion=simulacion,
                cuenta=asiento['cuenta'],
                tipo_cuenta=asiento['tipo_cuenta'],
                tipo_movimiento=asiento['tipo_movimiento'],
                monto=asiento['monto'],
                descripcion=asiento['descripcion'],
                transaccion_id=transaccion_id
            ))
        return cls.objects.bulk_create(audit_records)
    
    @classmethod
    def validar_balance(cls, simulacion):
        """Valida que los asientos de una simulación estén balanceados"""
        asientos = cls.objects.filter(simulacion=simulacion)
        
        total_debitos = sum(
            a.monto for a in asientos if a.tipo_movimiento == 'debito'
        )
        total_creditos = sum(
            a.monto for a in asientos if a.tipo_movimiento == 'credito'
        )
        
        diferencia = abs(total_debitos - total_creditos)
        return {
            'balanceado': diferencia <= Decimal('0.01'),
            'debitos': total_debitos,
            'creditos': total_creditos,
            'diferencia': diferencia
        }