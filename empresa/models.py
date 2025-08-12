from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from empresa.middleware import get_current_user
from django.core.validators import RegexValidator

# Importar modelos de aprendizaje para que Django los detecte en migraciones
try:
    from .models_aprendizaje import ModuloAprendizaje, Leccion, ProgresoUsuario, PerfilAprendizaje
except ImportError:
    pass

# Modelo Base para Auditoría
class AuditModel(models.Model):
    """Modelo base que agrega campos de auditoría automáticamente"""
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='%(class)s_creadas',
        on_delete=models.PROTECT,
        verbose_name='Creado por',
        null=True,
        blank=True
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='%(class)s_modificadas',
        null=True, 
        blank=True,
        on_delete=models.PROTECT,
        verbose_name='Modificado por'
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    modificado_en = models.DateTimeField(auto_now=True, verbose_name='Fecha de modificación')

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        user = get_current_user()
        if not self.pk and not self.creado_por:
            self.creado_por = user
        else:
            self.modificado_por = user
        super().save(*args, **kwargs)

# Modelo de Empresa
class CodigoInvitacion(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    usado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    
    def __str__(self):
        return f"Código: {self.codigo} - {'Usado' if self.usado else 'Disponible'}"


class Empresa(models.Model):
    CATEGORIA_CHOICES = [
        ('comercial', 'Comercial'),
        ('manufactura', 'Manufactura'),
        ('servicios', 'Servicios'),
    ]
    
    nombre = models.CharField(max_length=100, db_index=True)
    ruc = models.CharField(
        max_length=13, 
        unique=True, 
        db_index=True,
        help_text="RUC (13 dígitos) o Cédula (10 dígitos)"
    )
    direccion = models.CharField(max_length=200)
    categoria = models.CharField(
        max_length=20, 
        choices=CATEGORIA_CHOICES, 
        default='comercial',
        help_text="Categoría del negocio"
    )
    tipo_negocio = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Tipo específico de negocio (ej: panadería, carpintería, consultorio)"
    )
    provincia = models.CharField(
        max_length=50,
        blank=True,
        help_text="Provincia donde opera la empresa"
    )
    ciudad = models.CharField(
        max_length=50,
        blank=True,
        help_text="Ciudad donde opera la empresa"
    )
    telefono_whatsapp = models.CharField(
        max_length=15,
        blank=True,
        help_text="Número de WhatsApp para notificaciones (ej: +593987654321)"
    )
    latitud = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        help_text="Latitud GPS del negocio"
    )
    longitud = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        help_text="Longitud GPS del negocio"
    )

    class Meta:
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['ruc']),
            models.Index(fields=['categoria']),
            models.Index(fields=['provincia', 'ciudad']),
            models.Index(fields=['latitud', 'longitud']),
        ]

    def __str__(self):
        return self.nombre
    
    @property
    def tipo_negocio_normalizado(self):
        """Retorna el tipo de negocio normalizado para benchmarking"""
        from empresa.utils.normalizador import normalizar_tipo_negocio
        return normalizar_tipo_negocio(self.tipo_negocio, self.categoria)
    
    @property
    def ubicacion_completa(self):
        """Retorna la ubicación completa para benchmarking"""
        partes = [self.ciudad, self.provincia]
        return ", ".join([p for p in partes if p])
    
    @property
    def ubicacion_benchmarking(self):
        """Retorna ubicación normalizada para benchmarking"""
        from empresa.utils.normalizador import obtener_ubicacion_benchmarking
        return obtener_ubicacion_benchmarking(self)
    
    def empresas_cercanas(self, radio_km=10):
        """Obtiene empresas cercanas dentro del radio especificado"""
        from empresa.utils.normalizador import obtener_empresas_cercanas
        return obtener_empresas_cercanas(self, radio_km)
    
    @property
    def tiene_gps(self):
        """Verifica si la empresa tiene coordenadas GPS"""
        return bool(self.latitud and self.longitud)

# Usuario personalizado con empresa
class Usuario(AbstractUser):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True, related_name='usuarios')
    
    # Evitar conflictos con User por defecto
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='empresa_usuarios',
        related_query_name='empresa_usuario',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='empresa_usuarios',
        related_query_name='empresa_usuario',
    )

    class Meta:
        unique_together = ('username', 'empresa')
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.username} ({self.empresa})" if self.empresa else self.username

# Producto
class Producto(AuditModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=20, unique=True, help_text="Código interno del producto")
    codigo_barras = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        db_index=True,
        help_text="Código de barras para escáner (EAN-13, UPC-A, etc.)"
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    pvp = models.DecimalField('Precio de Venta al Público', max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.IntegerField(default=0)
    
    # Campos para COMERCIO
    categoria = models.ForeignKey(
        'empresa.CategoriaProducto', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Categoría del producto"
    )
    fecha_vencimiento = models.DateField(
        null=True, 
        blank=True,
        help_text="Fecha de vencimiento (opcional, para productos perecederos)"
    )
    lote = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Número de lote (opcional)"
    )
    stock_minimo = models.IntegerField(
        default=5,
        help_text="Stock mínimo para alertas"
    )
    stock_maximo = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Stock máximo recomendado (opcional)"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['empresa', 'codigo']),
            models.Index(fields=['empresa', 'codigo_barras']),
            models.Index(fields=['empresa', 'categoria']),
            models.Index(fields=['empresa', 'fecha_vencimiento']),
        ]
    
    @property
    def necesita_restock(self):
        """Verifica si el producto necesita restock"""
        return self.stock <= self.stock_minimo
    
    @property
    def dias_para_vencer(self):
        """Calcula días para vencimiento"""
        if not self.fecha_vencimiento:
            return None
        from datetime import date
        return (self.fecha_vencimiento - date.today()).days
    
    @property
    def esta_vencido(self):
        """Verifica si el producto está vencido"""
        dias = self.dias_para_vencer
        return dias is not None and dias < 0
    
    @property
    def proximo_a_vencer(self):
        """Verifica si está próximo a vencer (30 días)"""
        dias = self.dias_para_vencer
        return dias is not None and 0 <= dias <= 30

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

# Venta
class Venta(AuditModel):
    TIPO_PAGO_CHOICES = [
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    cliente_fk = models.ForeignKey(
        'empresa.Cliente', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='ventas',
        help_text="Cliente registrado (opcional)"
    )
    cliente_nombre = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Nombre del cliente (si no está registrado)"
    )
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_neto = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Monto sin IVA")
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="IVA calculado")
    monto = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monto total con IVA")
    tasa_iva = models.DecimalField(max_digits=5, decimal_places=2, default=12, help_text="Tasa de IVA (%)")
    tipo_pago = models.CharField(max_length=10, choices=TIPO_PAGO_CHOICES, default='contado')
    fecha = models.DateTimeField(auto_now_add=True)
    
    @property
    def cliente_display(self):
        """Retorna el nombre del cliente para mostrar"""
        if self.cliente_fk:
            return self.cliente_fk.nombre
        return self.cliente_nombre or 'Cliente General'

    def __str__(self):
        return f"Venta de {self.producto} - {self.monto}"
    
    def save(self, *args, **kwargs):
        """Calcular IVA y crear asientos contables automáticamente"""
        es_nuevo = not self.pk
        
        # Calcular IVA si no está establecido
        if self.monto_neto > 0 and self.iva == 0:
            self.iva = self.monto_neto * (self.tasa_iva / 100)
            self.monto = self.monto_neto + self.iva
        elif self.monto > 0 and self.monto_neto == 0:
            # Si solo se ingresó el monto total, calcular neto e IVA
            self.monto_neto = self.monto / (1 + self.tasa_iva / 100)
            self.iva = self.monto - self.monto_neto
        
        super().save(*args, **kwargs)
        
        if es_nuevo:
            self.crear_asientos_contables()
            self.crear_cuenta_por_cobrar_si_credito()
    
    def crear_asientos_contables(self):
        """Crear partida doble para la venta"""
        from empresa.models import CuentaContable, MovimientoContable
        
        try:
            # 1. Registrar la venta según tipo de pago
            if self.tipo_pago == 'contado':
                # Débito: Caja (Activo)
                cuenta_debito = CuentaContable.objects.get_or_create(
                    empresa=self.empresa,
                    nombre='Caja',
                    defaults={'tipo': 'activo'}
                )[0]
            else:  # crédito
                # Débito: Cuentas por Cobrar (Activo)
                cuenta_debito = CuentaContable.objects.get_or_create(
                    empresa=self.empresa,
                    nombre='Cuentas por Cobrar',
                    defaults={'tipo': 'activo'}
                )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_debito,
                tipo='debito',
                monto=self.monto,
                descripcion=f'Venta {self.tipo_pago} {self.producto.nombre} - {self.cantidad} unidades - {self.cliente_display}'
            )
            
            # 2. Registrar IVA por pagar si hay IVA
            if self.iva > 0:
                cuenta_iva_pagar = CuentaContable.objects.get_or_create(
                    empresa=self.empresa,
                    nombre='IVA por Pagar',
                    defaults={'tipo': 'pasivo'}
                )[0]
                
                MovimientoContable.objects.create(
                    empresa=self.empresa,
                    cuenta_fk=cuenta_iva_pagar,
                    tipo='credito',
                    monto=self.iva,
                    descripcion=f'IVA venta {self.producto.nombre} - {self.tasa_iva}%'
                )
            
            # 3. Crédito: Ventas (Ingreso) - solo el monto neto
            cuenta_ventas = CuentaContable.objects.get_or_create(
                empresa=self.empresa,
                nombre='Ventas',
                defaults={'tipo': 'ingreso'}
            )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_ventas,
                tipo='credito',
                monto=self.monto_neto,
                descripcion=f'Venta {self.producto.nombre} - {self.cantidad} unidades'
            )
            
            # 4. Calcular costo real del producto
            costo_unitario = self.obtener_costo_real()
            costo_total = self.cantidad * costo_unitario
            
            if costo_total > 0:
                # Débito: Costo de Ventas (Gasto)
                cuenta_costo = CuentaContable.objects.get_or_create(
                    empresa=self.empresa,
                    nombre='Costo de Ventas',
                    defaults={'tipo': 'gasto'}
                )[0]
                
                MovimientoContable.objects.create(
                    empresa=self.empresa,
                    cuenta_fk=cuenta_costo,
                    tipo='debito',
                    monto=costo_total,
                    descripcion=f'Costo venta {self.producto.nombre} - {self.cantidad} unidades'
                )
                
                # Crédito: Inventario (Activo)
                cuenta_inventario = CuentaContable.objects.get_or_create(
                    empresa=self.empresa,
                    nombre='Inventario',
                    defaults={'tipo': 'activo'}
                )[0]
                
                MovimientoContable.objects.create(
                    empresa=self.empresa,
                    cuenta_fk=cuenta_inventario,
                    tipo='credito',
                    monto=costo_total,
                    descripcion=f'Salida inventario {self.producto.nombre} - {self.cantidad} unidades'
                )
            
        except Exception as e:
            print(f'Error creando asientos contables para venta: {e}')
    
    def crear_cuenta_por_cobrar_si_credito(self):
        """Crear cuenta por cobrar si la venta es a crédito"""
        if self.tipo_pago == 'credito':
            try:
                from datetime import date, timedelta
                
                # Si no hay cliente registrado, crear uno genérico
                if not self.cliente_fk and self.cliente_nombre:
                    cliente, created = Cliente.objects.get_or_create(
                        empresa=self.empresa,
                        nombre=self.cliente_nombre,
                        defaults={
                            'numero_documento': '9999999999',
                            'limite_credito': 1000
                        }
                    )
                    # Actualizar sin triggear save() nuevamente
                    Venta.objects.filter(pk=self.pk).update(cliente_fk=cliente)
                    self.cliente_fk = cliente
                
                if self.cliente_fk:
                    CuentaPorCobrar.objects.create(
                        empresa=self.empresa,
                        cliente=self.cliente_fk,
                        venta=self,
                        monto_original=self.monto,
                        monto_pendiente=self.monto,
                        fecha_vencimiento=date.today() + timedelta(days=30),
                        estado='pendiente'
                    )
            except Exception as e:
                print(f'Error creando cuenta por cobrar: {e}')
    
    def obtener_costo_real(self):
        """Obtiene el costo real del producto según el tipo de empresa"""
        try:
            if self.empresa.categoria == 'manufactura':
                # Buscar si es producto manufacturado
                from empresa.models import ProductoManufacturado
                producto_manuf = ProductoManufacturado.objects.get(
                    empresa=self.empresa, codigo=self.producto.codigo
                )
                return producto_manuf.precio_costo or producto_manuf.costo_produccion
            else:
                # Para comercio/servicios, obtener el costo de la última compra
                from empresa.models import Compra
                ultima_compra = Compra.objects.filter(
                    empresa=self.empresa,
                    producto=self.producto
                ).order_by('-fecha').first()
                
                if ultima_compra:
                    return ultima_compra.monto_neto / ultima_compra.cantidad
                else:
                    # Fallback al precio_unitario del producto
                    return self.producto.precio_unitario
        except:
            # Fallback al precio_unitario del producto
            return self.producto.precio_unitario

# Compra
class Compra(AuditModel):
    TIPO_PAGO_CHOICES = [
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    proveedor_fk = models.ForeignKey(
        'empresa.Proveedor', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='compras',
        help_text="Proveedor registrado (opcional)"
    )
    proveedor_nombre = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Nombre del proveedor (si no está registrado)"
    )
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    monto_neto = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Monto sin IVA")
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="IVA pagado")
    monto = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monto total con IVA")
    tasa_iva = models.DecimalField(max_digits=5, decimal_places=2, default=12, help_text="Tasa de IVA (%)")
    tipo_pago = models.CharField(max_length=10, choices=TIPO_PAGO_CHOICES, default='contado')
    fecha = models.DateTimeField(auto_now_add=True)
    
    @property
    def proveedor_display(self):
        """Retorna el nombre del proveedor para mostrar"""
        if self.proveedor_fk:
            return self.proveedor_fk.nombre
        return self.proveedor_nombre or 'Proveedor General'

    def __str__(self):
        return f"Compra de {self.producto} - {self.monto}"
    
    def save(self, *args, **kwargs):
        """Calcular IVA y crear asientos contables automáticamente"""
        es_nuevo = not self.pk
        
        # Calcular IVA si no está establecido
        if self.monto_neto > 0 and self.iva == 0:
            self.iva = self.monto_neto * (self.tasa_iva / 100)
            self.monto = self.monto_neto + self.iva
        elif self.monto > 0 and self.monto_neto == 0:
            # Si solo se ingresó el monto total, calcular neto e IVA
            self.monto_neto = self.monto / (1 + self.tasa_iva / 100)
            self.iva = self.monto - self.monto_neto
        
        super().save(*args, **kwargs)
        
        if es_nuevo:
            self.crear_asientos_contables()
            self.crear_cuenta_por_pagar_si_credito()
    
    def crear_asientos_contables(self):
        """Crear partida doble para la compra"""
        from empresa.models import CuentaContable, MovimientoContable
        
        try:
            # 1. Débito: Inventario (Activo) - solo el monto neto
            cuenta_inventario = CuentaContable.objects.get_or_create(
                empresa=self.empresa,
                nombre='Inventario',
                defaults={'tipo': 'activo'}
            )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_inventario,
                tipo='debito',
                monto=self.monto_neto,
                descripcion=f'Compra {self.producto.nombre} - {self.cantidad} unidades'
            )
            
            # 2. Débito: IVA Crédito Fiscal (Activo) si hay IVA
            if self.iva > 0:
                cuenta_iva_credito = CuentaContable.objects.get_or_create(
                    empresa=self.empresa,
                    nombre='IVA Crédito Fiscal',
                    defaults={'tipo': 'activo'}
                )[0]
                
                MovimientoContable.objects.create(
                    empresa=self.empresa,
                    cuenta_fk=cuenta_iva_credito,
                    tipo='debito',
                    monto=self.iva,
                    descripcion=f'IVA compra {self.producto.nombre} - {self.tasa_iva}%'
                )
            
            # 3. Crédito: Caja o Cuentas por Pagar (monto total)
            if self.tipo_pago == 'contado':
                cuenta_pago = CuentaContable.objects.get_or_create(
                    empresa=self.empresa,
                    nombre='Caja',
                    defaults={'tipo': 'activo'}
                )[0]
            else:
                cuenta_pago = CuentaContable.objects.get_or_create(
                    empresa=self.empresa,
                    nombre='Cuentas por Pagar',
                    defaults={'tipo': 'pasivo'}
                )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_pago,
                tipo='credito',
                monto=self.monto,
                descripcion=f'Pago compra {self.producto.nombre} - {self.proveedor_display}'
            )
            
        except Exception as e:
            print(f'Error creando asientos contables para compra: {e}')
    
    def crear_cuenta_por_pagar_si_credito(self):
        """Crear cuenta por pagar si la compra es a crédito"""
        if self.tipo_pago == 'credito':
            try:
                from datetime import date, timedelta
                
                # Si no hay proveedor, usar el proveedor automático existente
                if not self.proveedor_fk:
                    proveedor = Proveedor.objects.filter(
                        empresa=self.empresa,
                        ruc='9999999999999'
                    ).first()
                    
                    if not proveedor:
                        # Crear proveedor automático si no existe
                        proveedor = Proveedor.objects.create(
                            empresa=self.empresa,
                            nombre='Proveedor Automático',
                            ruc='9999999999999',
                            dias_credito=30
                        )
                    
                    # Actualizar sin triggear save() nuevamente
                    Compra.objects.filter(pk=self.pk).update(proveedor_fk=proveedor)
                    self.proveedor_fk = proveedor
                
                # Crear cuenta por pagar
                CuentaPorPagar.objects.create(
                    empresa=self.empresa,
                    proveedor=self.proveedor_fk,
                    compra=self,
                    monto_original=self.monto,
                    monto_pendiente=self.monto,
                    fecha_vencimiento=date.today() + timedelta(days=self.proveedor_fk.dias_credito or 30),
                    estado='pendiente'
                )
                
            except Exception as e:
                print(f'Error creando cuenta por pagar: {e}')

# Gasto
class Gasto(AuditModel):
    TIPO_PAGO_CHOICES = [
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    tipo_pago = models.CharField(max_length=10, choices=TIPO_PAGO_CHOICES, default='contado')
    CATEGORIA_CHOICES = [
        ('Fijo', 'Fijo'),
        ('Variable', 'Variable'),
    ]
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='Fijo')

    def __str__(self):
        return f"{self.descripcion} - {self.monto}"
    
    def save(self, *args, **kwargs):
        """Crear asientos contables automáticamente"""
        super().save(*args, **kwargs)
        self.crear_asientos_contables()
    
    def crear_asientos_contables(self):
        """Crear partida doble para el gasto"""
        from empresa.models import CuentaContable, MovimientoContable
        
        try:
            # Débito: Gastos (Gasto)
            cuenta_gastos = CuentaContable.objects.get_or_create(
                empresa=self.empresa,
                nombre='Gastos',
                defaults={'tipo': 'gasto'}
            )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_gastos,
                tipo='debito',
                monto=self.monto,
                descripcion=self.descripcion
            )
            
            # Crédito: Caja o Cuentas por Pagar según tipo de pago
            if self.tipo_pago == 'contado':
                cuenta_credito = CuentaContable.objects.get_or_create(
                    empresa=self.empresa,
                    nombre='Caja/Banco',
                    defaults={'tipo': 'activo'}
                )[0]
            else:
                cuenta_credito = CuentaContable.objects.get_or_create(
                    empresa=self.empresa,
                    nombre='Cuentas por Pagar',
                    defaults={'tipo': 'pasivo'}
                )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_credito,
                tipo='credito',
                monto=self.monto,
                descripcion=f"{self.descripcion} - {self.get_tipo_pago_display()}"
            )
            
        except Exception as e:
            print(f'Error creando asientos contables para gasto: {e}')

# Movimiento Contable

class MovimientoContable(AuditModel):
    empresa     = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    cuenta_text = models.CharField(max_length=100)
    cuenta_fk   = models.ForeignKey(
        'CuentaContable',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='movimientos'
    )
    tipo        = models.CharField(
        max_length=10,
        choices=[('debito', 'Débito'), ('credito', 'Crédito')]
    )
    monto       = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.TextField()
    fecha       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cuenta_fk or self.cuenta_text} - {self.tipo} - {self.monto}"

# Cuenta Contable
class CuentaContable(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=[
        ('activo', 'Activo'),
        ('pasivo', 'Pasivo'),
        ('capital', 'Capital'),
        ('ingreso', 'Ingreso'),
        ('gasto', 'Gasto')
    ])
    monto_inicial = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Monto inicial para préstamos o deudas"
    )

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"
    
    def save(self, *args, **kwargs):
        es_nuevo = not self.pk
        super().save(*args, **kwargs)
        
        # Si es una cuenta nueva de pasivo con monto inicial, crear asientos y cuenta por pagar
        if es_nuevo and self.tipo == 'pasivo' and self.monto_inicial > 0:
            self.crear_asientos_iniciales()
            self.crear_cuenta_por_pagar_si_aplica()
    
    def crear_asientos_iniciales(self):
        """Crear asientos contables iniciales para la cuenta"""
        try:
            # Débito: Caja/Banco (recibimos el dinero)
            cuenta_caja = CuentaContable.objects.get_or_create(
                empresa=self.empresa,
                nombre='Caja/Banco',
                defaults={'tipo': 'activo'}
            )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_caja,
                tipo='debito',
                monto=self.monto_inicial,
                descripcion=f'Ingreso por {self.nombre}'
            )
            
            # Crédito: Esta cuenta (la deuda)
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=self,
                tipo='credito',
                monto=self.monto_inicial,
                descripcion=f'Registro de {self.nombre}'
            )
            
        except Exception as e:
            print(f'Error creando asientos iniciales para cuenta contable: {e}')
    
    def crear_cuenta_por_pagar_si_aplica(self):
        """Crear cuenta por pagar si es un préstamo o deuda"""
        # Verificar si es un préstamo bancario o deuda similar
        palabras_clave = ['prestamo', 'préstamo', 'credito', 'crédito', 'banco', 'financiera', 'deuda']
        es_prestamo = any(palabra in self.nombre.lower() for palabra in palabras_clave)
        
        if es_prestamo and self.monto_inicial > 0:
            try:
                # Crear o buscar proveedor "Entidad Financiera"
                proveedor, created = Proveedor.objects.get_or_create(
                    empresa=self.empresa,
                    nombre=f'Entidad Financiera - {self.nombre}',
                    defaults={
                        'ruc': '0000000000000',
                        'dias_credito': 30
                    }
                )
                
                # Crear cuenta por pagar
                from datetime import date, timedelta
                CuentaPorPagar.objects.create(
                    empresa=self.empresa,
                    proveedor=proveedor,
                    compra=None,  # No está asociada a una compra específica
                    monto_original=self.monto_inicial,
                    monto_pendiente=self.monto_inicial,
                    fecha_vencimiento=date.today() + timedelta(days=365),  # 1 año por defecto
                    estado='pendiente'
                )
                
            except Exception as e:
                print(f'Error creando cuenta por pagar para préstamo: {e}')

    @property
    def valor(self):
        """Calcula el saldo de la cuenta basado en los movimientos contables"""
        from django.db.models import Sum

        # Obtener todos los movimientos de esta cuenta
        movimientos = self.movimientos.all()

        if not movimientos.exists():
            return 0

        # Calcular saldo: débitos - créditos
        total_debitos = movimientos.filter(tipo='debito').aggregate(
            total=Sum('monto')
        )['total'] or 0

        total_creditos = movimientos.filter(tipo='credito').aggregate(
            total=Sum('monto')
        )['total'] or 0

        # Lógica contable correcta por tipo de cuenta:
        # - Activos: débitos - créditos (saldo deudor)
        # - Pasivos y Capital: créditos - débitos (saldo acreedor)
        # - Ingresos: créditos - débitos (saldo acreedor)
        # - Gastos: débitos - créditos (saldo deudor)
        if self.tipo == 'activo':
            return total_debitos - total_creditos
        elif self.tipo == 'gasto':
            return total_debitos - total_creditos
        else:  # pasivo, capital, ingreso
            return total_creditos - total_debitos

# Capital
class Capital(AuditModel):
    TIPO_CHOICES = [
        ('aporte', 'Aporte'),
        ('retiro', 'Retiro'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='aporte')
    descripcion = models.CharField(max_length=200, default='Aporte de capital')
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.monto} - {self.empresa}"
    
    def save(self, *args, **kwargs):
        """Crear asientos contables automáticamente"""
        super().save(*args, **kwargs)
        self.crear_asientos_contables()
    
    def crear_asientos_contables(self):
        """Crear partida doble para el capital"""
        from empresa.models import CuentaContable, MovimientoContable
        
        try:
            if self.tipo == 'aporte':
                # Débito: Caja/Banco (Activo)
                cuenta_caja = CuentaContable.objects.get_or_create(
                    empresa=self.empresa,
                    nombre='Caja/Banco',
                    defaults={'tipo': 'activo'}
                )[0]
                
                MovimientoContable.objects.create(
                    empresa=self.empresa,
                    cuenta_fk=cuenta_caja,
                    tipo='debito',
                    monto=self.monto,
                    descripcion=self.descripcion
                )
                
                # Crédito: Capital (Capital)
                cuenta_capital = CuentaContable.objects.get_or_create(
                    empresa=self.empresa,
                    nombre='Capital',
                    defaults={'tipo': 'capital'}
                )[0]
                
                MovimientoContable.objects.create(
                    empresa=self.empresa,
                    cuenta_fk=cuenta_capital,
                    tipo='credito',
                    monto=self.monto,
                    descripcion=self.descripcion
                )
            else:  # retiro
                # Débito: Capital (Capital)
                cuenta_capital = CuentaContable.objects.get_or_create(
                    empresa=self.empresa,
                    nombre='Capital',
                    defaults={'tipo': 'capital'}
                )[0]
                
                MovimientoContable.objects.create(
                    empresa=self.empresa,
                    cuenta_fk=cuenta_capital,
                    tipo='debito',
                    monto=self.monto,
                    descripcion=self.descripcion
                )
                
                # Crédito: Caja/Banco (Activo)
                cuenta_caja = CuentaContable.objects.get_or_create(
                    empresa=self.empresa,
                    nombre='Caja/Banco',
                    defaults={'tipo': 'activo'}
                )[0]
                
                MovimientoContable.objects.create(
                    empresa=self.empresa,
                    cuenta_fk=cuenta_caja,
                    tipo='credito',
                    monto=self.monto,
                    descripcion=self.descripcion
                )
                
        except Exception as e:
            print(f'Error creando asientos contables para capital: {e}')

# Meta Financiera
class MetaFinanciera(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=50, choices=[
        ('ventas', 'Ventas'),
        ('gastos', 'Gastos'),
        ('utilidad', 'Utilidad'),
        ('clientes', 'Clientes'),
        ('productos', 'Productos'),
    ])
    objetivo_mensual = models.DecimalField(max_digits=15, decimal_places=2)
    mes = models.IntegerField()
    anio = models.IntegerField()
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    # Nuevos campos para metas avanzadas
    es_dinamica = models.BooleanField(default=False, help_text="Meta que se ajusta automáticamente")
    factor_ajuste = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, 
                                      help_text="Factor de ajuste para metas dinámicas")
    recordatorio_dias = models.IntegerField(default=7, help_text="Días antes para recordatorio")
    alertas_activas = models.BooleanField(default=True, help_text="Activar alertas automáticas")
    
    class Meta:
        unique_together = ['empresa', 'tipo', 'mes', 'anio']
        ordering = ['-anio', '-mes']
    
    def __str__(self):
        return f"{self.empresa.nombre} - {self.get_tipo_display()} ({self.mes}/{self.anio})"
    
    @property
    def progreso_actual(self):
        """Calcula el progreso actual hacia la meta"""
        from django.db.models import Sum
        from datetime import datetime
        
        # Obtener el valor actual según el tipo de meta
        if self.tipo == 'ventas':
            valor_actual = Venta.objects.filter(
                empresa=self.empresa,
                fecha__month=self.mes,
                fecha__year=self.anio
            ).aggregate(total=Sum('monto'))['total'] or 0
        elif self.tipo == 'gastos':
            valor_actual = Gasto.objects.filter(
                empresa=self.empresa,
                fecha__month=self.mes,
                fecha__year=self.anio
            ).aggregate(total=Sum('monto'))['total'] or 0
        elif self.tipo == 'utilidad':
            ventas = Venta.objects.filter(
                empresa=self.empresa,
                fecha__month=self.mes,
                fecha__year=self.anio
            ).aggregate(total=Sum('monto'))['total'] or 0
            gastos = Gasto.objects.filter(
                empresa=self.empresa,
                fecha__month=self.mes,
                fecha__year=self.anio
            ).aggregate(total=Sum('monto'))['total'] or 0
            valor_actual = ventas - gastos
        else:
            valor_actual = 0
        
        if self.objetivo_mensual > 0:
            return min((valor_actual / self.objetivo_mensual) * 100, 100)
        return 0
    
    @property
    def estado(self):
        """Retorna el estado de la meta"""
        progreso = self.progreso_actual
        if progreso >= 100:
            return 'completada'
        elif progreso >= 75:
            return 'en_progreso'
        elif progreso >= 50:
            return 'atrasada'
        else:
            return 'crítica'
    
    @property
    def valor_actual(self):
        """Obtiene el valor actual de la meta"""
        from django.db.models import Sum
        
        if self.tipo == 'ventas':
            return Venta.objects.filter(
                empresa=self.empresa,
                fecha__month=self.mes,
                fecha__year=self.anio
            ).aggregate(total=Sum('monto'))['total'] or 0
        elif self.tipo == 'gastos':
            return Gasto.objects.filter(
                empresa=self.empresa,
                fecha__month=self.mes,
                fecha__year=self.anio
            ).aggregate(total=Sum('monto'))['total'] or 0
        elif self.tipo == 'utilidad':
            ventas = Venta.objects.filter(
                empresa=self.empresa,
                fecha__month=self.mes,
                fecha__year=self.anio
            ).aggregate(total=Sum('monto'))['total'] or 0
            gastos = Gasto.objects.filter(
                empresa=self.empresa,
                fecha__month=self.mes,
                fecha__year=self.anio
            ).aggregate(total=Sum('monto'))['total'] or 0
            return ventas - gastos
        else:
            return 0
    
    def actualizar_historial(self):
        """Actualiza el historial de la meta"""
        from .models import HistorialMeta
        
        HistorialMeta.objects.create(
            meta=self,
            valor_actual=self.valor_actual,
            progreso=self.progreso_actual,
            estado=self.estado
        )
    
    def generar_recomendacion(self):
        """Genera recomendaciones basadas en el progreso"""
        progreso = self.progreso_actual
        dias_restantes = self.dias_restantes_mes()
        
        if progreso >= 100:
            return "¡Excelente! Has superado tu meta. Considera establecer una meta más ambiciosa para el próximo mes."
        elif progreso >= 75:
            return f"Vas muy bien. Con {dias_restantes} días restantes, mantén el ritmo actual para alcanzar tu meta."
        elif progreso >= 50:
            return f"Estás a mitad de camino. Necesitas acelerar un {((100-progreso)/dias_restantes)*100:.1f}% diario para alcanzar tu meta."
        else:
            return f"Meta en riesgo. Necesitas un esfuerzo extraordinario de {((100-progreso)/dias_restantes)*100:.1f}% diario para alcanzar tu objetivo."
    
    def dias_restantes_mes(self):
        """Calcula los días restantes del mes"""
        from datetime import datetime
        from calendar import monthrange
        
        hoy = datetime.now()
        if hoy.month == self.mes and hoy.year == self.anio:
            _, ultimo_dia = monthrange(self.anio, self.mes)
            return ultimo_dia - hoy.day
        return 0

class CategoriaGastoKeyword(models.Model):
    CATEGORIA_CHOICES = [
        ('Fijo', 'Fijo'),
        ('Variable', 'Variable'),
    ]
    palabra = models.CharField(max_length=50, unique=True)
    categoria = models.CharField(max_length=10, choices=CATEGORIA_CHOICES)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.palabra} ({self.categoria})"

# Historial de Metas
class HistorialMeta(models.Model):
    meta = models.ForeignKey(MetaFinanciera, on_delete=models.CASCADE, related_name='historial')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    valor_actual = models.DecimalField(max_digits=15, decimal_places=2)
    progreso = models.DecimalField(max_digits=5, decimal_places=2)  # Porcentaje
    estado = models.CharField(max_length=20, choices=[
        ('completada', 'Completada'),
        ('en_progreso', 'En Progreso'),
        ('atrasada', 'Atrasada'),
        ('crítica', 'Crítica')
    ])
    
    class Meta:
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f"{self.meta} - {self.fecha_registro.strftime('%d/%m/%Y')}"

# Alertas de Metas
class AlertaMeta(models.Model):
    meta = models.ForeignKey(MetaFinanciera, on_delete=models.CASCADE, related_name='alertas')
    tipo = models.CharField(max_length=20, choices=[
        ('cumplimiento', 'Cumplimiento de Meta'),
        ('atraso', 'Meta Atrasada'),
        ('crítica', 'Meta Crítica'),
        ('recordatorio', 'Recordatorio'),
        ('felicitación', 'Felicitación')
    ])
    mensaje = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    enviada = models.BooleanField(default=False)
    leida = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.meta}"

# Benchmarking Sectorial
class BenchmarkingSectorial(models.Model):
    sector = models.CharField(max_length=50, choices=[
        ('comercio', 'Comercio'),
        ('servicios', 'Servicios'),
        ('manufactura', 'Manufactura'),
        ('tecnologia', 'Tecnología'),
        ('salud', 'Salud'),
        ('educacion', 'Educación'),
        ('restaurantes', 'Restaurantes'),
        ('construccion', 'Construcción'),
        ('otros', 'Otros')
    ])
    tamaño_empresa = models.CharField(max_length=20, choices=[
        ('micro', 'Micro (1-10 empleados)'),
        ('pequeña', 'Pequeña (11-50 empleados)'),
        ('mediana', 'Mediana (51-200 empleados)'),
        ('grande', 'Grande (200+ empleados)')
    ])
    indicador = models.CharField(max_length=30, choices=[
        ('ventas_mensuales', 'Ventas Mensuales'),
        ('gastos_mensuales', 'Gastos Mensuales'),
        ('rentabilidad', 'Rentabilidad'),
        ('roe', 'ROE'),
        ('liquidez', 'Liquidez'),
        ('rotacion_inventario', 'Rotación de Inventario')
    ])
    valor_promedio = models.DecimalField(max_digits=15, decimal_places=2)
    valor_mediano = models.DecimalField(max_digits=15, decimal_places=2)
    valor_minimo = models.DecimalField(max_digits=15, decimal_places=2)
    valor_maximo = models.DecimalField(max_digits=15, decimal_places=2)
    cantidad_empresas = models.IntegerField()
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['sector', 'tamaño_empresa', 'indicador']
        ordering = ['sector', 'tamaño_empresa', 'indicador']
    
    def __str__(self):
        return f"{self.get_sector_display()} - {self.get_tamaño_empresa_display()} - {self.get_indicador_display()}"

# Notificaciones de Metas
class NotificacionMeta(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, choices=[
        ('info', 'Información'),
        ('success', 'Éxito'),
        ('warning', 'Advertencia'),
        ('danger', 'Crítica')
    ])
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    accion_url = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.titulo} - {self.empresa.nombre}"
    
    def marcar_leida(self):
        from django.utils import timezone
        self.leida = True
        self.fecha_lectura = timezone.now()
        self.save()

class PoderEmpleado(models.Model):
    empleado = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='poderes')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='poderes_empleados')
    puede_ver_reportes = models.BooleanField(default=False)
    puede_registrar_ventas = models.BooleanField(default=False)
    puede_editar_productos = models.BooleanField(default=False)
    puede_gestionar_cuentas = models.BooleanField(default=False)
    puede_registrar_gastos = models.BooleanField(default=False)
    puede_gestionar_inventario = models.BooleanField(default=False)
    puede_gestionar_metas = models.BooleanField(default=False)

    class Meta:
        unique_together = ('empleado', 'empresa')
        verbose_name = 'Poder de Empleado'
        verbose_name_plural = 'Poderes de Empleados'

    def __str__(self):
        return f"Poderes de {self.empleado} en {self.empresa}"


# ======================
# MODELOS PARA COMERCIO
# ======================

class Proveedor(models.Model):
    """Proveedores para negocios de comercio"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='proveedores')
    nombre = models.CharField(max_length=100)
    ruc = models.CharField(max_length=13)
    telefono = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    dias_credito = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('empresa', 'ruc')
        indexes = [
            models.Index(fields=['empresa', 'nombre']),
            models.Index(fields=['empresa', 'activo']),
        ]
    
    def __str__(self):
        return f"{self.nombre} - {self.ruc}"


class Cliente(models.Model):
    """Clientes para negocios de comercio"""
    TIPO_DOCUMENTO_CHOICES = [
        ('cedula', 'Cédula'),
        ('ruc', 'RUC'),
        ('pasaporte', 'Pasaporte'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='clientes')
    nombre = models.CharField(max_length=100)
    tipo_documento = models.CharField(max_length=10, choices=TIPO_DOCUMENTO_CHOICES, default='cedula')
    numero_documento = models.CharField(max_length=13)
    telefono = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    limite_credito = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('empresa', 'numero_documento')
        indexes = [
            models.Index(fields=['empresa', 'nombre']),
            models.Index(fields=['empresa', 'activo']),
        ]
    
    def __str__(self):
        return f"{self.nombre} - {self.numero_documento}"


class CategoriaProducto(models.Model):
    """Categorías para organizar productos"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='categorias_productos')
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('empresa', 'nombre')
        verbose_name = 'Categoría de Producto'
        verbose_name_plural = 'Categorías de Productos'
    
    def __str__(self):
        return self.nombre


class CuentaPorCobrar(models.Model):
    """Cuentas por cobrar a clientes"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida'),
        ('cancelada', 'Cancelada'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='cuentas_por_cobrar')
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='cuentas_por_cobrar')
    monto_original = models.DecimalField(max_digits=10, decimal_places=2)
    monto_pendiente = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['cliente', 'fecha_vencimiento']),
        ]
    
    def __str__(self):
        return f"{self.cliente.nombre} - ${self.monto_pendiente}"


class CuentaPorPagar(models.Model):
    """Cuentas por pagar a proveedores"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida'),
        ('cancelada', 'Cancelada'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='cuentas_por_pagar')
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='cuentas_por_pagar', null=True, blank=True)
    monto_original = models.DecimalField(max_digits=10, decimal_places=2)
    monto_pendiente = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['proveedor', 'fecha_vencimiento']),
        ]
    
    def __str__(self):
        return f"{self.proveedor.nombre} - ${self.monto_pendiente}"


class PagoCuentaPorCobrar(AuditModel):
    """Registro de pagos de cuentas por cobrar"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    cuenta_por_cobrar = models.ForeignKey(CuentaPorCobrar, on_delete=models.CASCADE, related_name='pagos')
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(
        max_length=20,
        choices=[
            ('efectivo', 'Efectivo'),
            ('transferencia', 'Transferencia'),
            ('cheque', 'Cheque'),
            ('tarjeta', 'Tarjeta'),
        ],
        default='efectivo'
    )
    observaciones = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        es_nuevo = not self.pk
        super().save(*args, **kwargs)
        if es_nuevo:
            self.crear_asientos_contables()
            self.actualizar_cuenta_por_cobrar()
    
    def crear_asientos_contables(self):
        """Crear asientos contables para el pago recibido"""
        from empresa.models import CuentaContable, MovimientoContable
        
        try:
            # Débito: Caja (Activo)
            cuenta_caja = CuentaContable.objects.get_or_create(
                empresa=self.empresa,
                nombre='Caja',
                defaults={'tipo': 'activo'}
            )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_caja,
                tipo='debito',
                monto=self.monto_pagado,
                descripcion=f'Pago recibido de {self.cuenta_por_cobrar.cliente.nombre} - {self.get_metodo_pago_display()}'
            )
            
            # Crédito: Cuentas por Cobrar (Activo)
            cuenta_por_cobrar = CuentaContable.objects.get_or_create(
                empresa=self.empresa,
                nombre='Cuentas por Cobrar',
                defaults={'tipo': 'activo'}
            )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_por_cobrar,
                tipo='credito',
                monto=self.monto_pagado,
                descripcion=f'Pago recibido de {self.cuenta_por_cobrar.cliente.nombre} - {self.get_metodo_pago_display()}'
            )
            
        except Exception as e:
            print(f'Error creando asientos para pago de cuenta por cobrar: {e}')
    
    def actualizar_cuenta_por_cobrar(self):
        """Actualizar el saldo pendiente de la cuenta por cobrar"""
        cuenta = self.cuenta_por_cobrar
        cuenta.monto_pendiente -= self.monto_pagado
        
        if cuenta.monto_pendiente <= 0:
            cuenta.estado = 'pagada'
            cuenta.monto_pendiente = 0
        
        cuenta.save()
    
    def __str__(self):
        return f"Pago ${self.monto_pagado} - {self.cuenta_por_cobrar.cliente.nombre}"


class PagoCuentaPorPagar(AuditModel):
    """Registro de pagos de cuentas por pagar"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    cuenta_por_pagar = models.ForeignKey(CuentaPorPagar, on_delete=models.CASCADE, related_name='pagos')
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(
        max_length=20,
        choices=[
            ('efectivo', 'Efectivo'),
            ('transferencia', 'Transferencia'),
            ('cheque', 'Cheque'),
            ('tarjeta', 'Tarjeta'),
        ],
        default='efectivo'
    )
    observaciones = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        es_nuevo = not self.pk
        super().save(*args, **kwargs)
        if es_nuevo:
            self.crear_asientos_contables()
            self.actualizar_cuenta_por_pagar()
    
    def crear_asientos_contables(self):
        """Crear asientos contables para el pago realizado"""
        from empresa.models import CuentaContable, MovimientoContable
        
        try:
            # Débito: Cuentas por Pagar (Pasivo)
            cuenta_por_pagar = CuentaContable.objects.get_or_create(
                empresa=self.empresa,
                nombre='Cuentas por Pagar',
                defaults={'tipo': 'pasivo'}
            )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_por_pagar,
                tipo='debito',
                monto=self.monto_pagado,
                descripcion=f'Pago a {self.cuenta_por_pagar.proveedor.nombre} - {self.get_metodo_pago_display()}'
            )
            
            # Crédito: Caja (Activo)
            cuenta_caja = CuentaContable.objects.get_or_create(
                empresa=self.empresa,
                nombre='Caja',
                defaults={'tipo': 'activo'}
            )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_caja,
                tipo='credito',
                monto=self.monto_pagado,
                descripcion=f'Pago a {self.cuenta_por_pagar.proveedor.nombre} - {self.get_metodo_pago_display()}'
            )
            
        except Exception as e:
            print(f'Error creando asientos para pago de cuenta por pagar: {e}')
    
    def actualizar_cuenta_por_pagar(self):
        """Actualizar el saldo pendiente de la cuenta por pagar"""
        cuenta = self.cuenta_por_pagar
        cuenta.monto_pendiente -= self.monto_pagado
        
        if cuenta.monto_pendiente <= 0:
            cuenta.estado = 'pagada'
            cuenta.monto_pendiente = 0
        
        cuenta.save()
    
    def __str__(self):
        return f"Pago ${self.monto_pagado} - {self.cuenta_por_pagar.proveedor.nombre}"


# ======================
# MODELOS PARA MANUFACTURA
# ======================

class MateriaPrima(AuditModel):
    """Materias primas para negocios de manufactura"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='materias_primas')
    codigo = models.CharField(max_length=20, help_text="Código interno de la materia prima")
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    unidad_medida = models.CharField(
        max_length=20,
        choices=[
            ('kg', 'Kilogramos'),
            ('g', 'Gramos'),
            ('l', 'Litros'),
            ('ml', 'Mililitros'),
            ('m', 'Metros'),
            ('cm', 'Centímetros'),
            ('unidad', 'Unidades'),
            ('docena', 'Docenas'),
        ],
        default='unidad'
    )
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=5)
    proveedor_principal = models.ForeignKey(
        'Proveedor', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='materias_primas'
    )
    
    class Meta:
        unique_together = ('empresa', 'codigo')
        indexes = [
            models.Index(fields=['empresa', 'codigo']),
            models.Index(fields=['empresa', 'nombre']),
        ]
    
    @property
    def necesita_restock(self):
        return self.stock_actual <= self.stock_minimo
    
    def save(self, *args, **kwargs):
        """Override save para crear asientos contables y actualizar costos"""
        es_nuevo = not self.pk
        precio_cambio = False
        
        if self.pk:
            try:
                old_instance = MateriaPrima.objects.get(pk=self.pk)
                if old_instance.precio_unitario != self.precio_unitario:
                    precio_cambio = True
            except MateriaPrima.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Crear asientos contables para stock inicial
        if es_nuevo and self.stock_actual > 0:
            self.crear_asientos_stock_inicial()
        
        # Si cambió el precio, actualizar todos los productos que usen esta materia prima
        if precio_cambio:
            productos_afectados = ProductoManufacturado.objects.filter(
                receta__materia_prima=self
            ).distinct()
            for producto in productos_afectados:
                producto.actualizar_costo_automatico()
    
    def crear_asientos_stock_inicial(self):
        """Crear asientos contables para stock inicial de materia prima"""
        from empresa.models import CuentaContable, MovimientoContable
        
        try:
            valor_total = self.stock_actual * self.precio_unitario
            
            # Débito: Inventario - Materia Prima (Activo)
            cuenta_inventario = CuentaContable.objects.get_or_create(
                empresa=self.empresa,
                nombre='Inventario - Materia Prima',
                defaults={'tipo': 'activo'}
            )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_inventario,
                tipo='debito',
                monto=valor_total,
                descripcion=f'Stock inicial {self.nombre} - {self.stock_actual} {self.unidad_medida}'
            )
            
            # Crédito: Capital (Capital)
            cuenta_capital = CuentaContable.objects.get_or_create(
                empresa=self.empresa,
                nombre='Capital',
                defaults={'tipo': 'capital'}
            )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_capital,
                tipo='credito',
                monto=valor_total,
                descripcion=f'Stock inicial {self.nombre} - {self.stock_actual} {self.unidad_medida}'
            )
            
        except Exception as e:
            print(f'Error creando asientos para stock inicial de materia prima: {e}')
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class ProductoManufacturado(AuditModel):
    """Productos que se fabrican en el negocio"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='productos_manufacturados')
    codigo = models.CharField(max_length=20, help_text="Código interno del producto")
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    categoria = models.ForeignKey(
        'empresa.CategoriaProducto', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Categoría del producto manufacturado"
    )
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    precio_costo = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Costo calculado automáticamente basado en la receta"
    )
    tiempo_produccion = models.IntegerField(
        help_text="Tiempo de producción en minutos",
        default=60
    )
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5)
    activo = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('empresa', 'codigo')
        indexes = [
            models.Index(fields=['empresa', 'codigo']),
            models.Index(fields=['empresa', 'activo']),
        ]
    
    @property
    def costo_produccion(self):
        """Calcula el costo total de producción basado en la receta"""
        total = 0
        for ingrediente in self.receta.all():
            total += ingrediente.cantidad_necesaria * ingrediente.materia_prima.precio_unitario
        return total
    
    @property
    def margen_ganancia(self):
        """Calcula el margen de ganancia"""
        costo = self.costo_produccion
        if costo > 0:
            return ((self.precio_venta - costo) / self.precio_venta) * 100
        return 0
    
    def actualizar_costo_automatico(self):
        """Actualiza automáticamente el precio_costo basado en el costo de la receta"""
        self.precio_costo = self.costo_produccion
        self.save(update_fields=['precio_costo'])
        return self.precio_costo
    
    def recalcular_precios_por_cambio_materias(self):
        """Recalcula precios cuando cambian los precios de las materias primas"""
        self.actualizar_costo_automatico()
        return self.precio_costo
    
    def save(self, *args, **kwargs):
        """Override save para calcular costo automáticamente"""
        super().save(*args, **kwargs)
        # Calcular costo después de guardar (para que tenga ID)
        if self.pk and self.receta.exists():
            nuevo_costo = self.costo_produccion
            if self.precio_costo != nuevo_costo:
                self.precio_costo = nuevo_costo
                super().save(update_fields=['precio_costo'])
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class RecetaProduccion(models.Model):
    """Receta que define qué materias primas se necesitan para un producto"""
    producto = models.ForeignKey(
        ProductoManufacturado, 
        on_delete=models.CASCADE, 
        related_name='receta'
    )
    materia_prima = models.ForeignKey(MateriaPrima, on_delete=models.CASCADE)
    cantidad_necesaria = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Cantidad necesaria de esta materia prima"
    )
    
    class Meta:
        unique_together = ('producto', 'materia_prima')
    
    def save(self, *args, **kwargs):
        """Override save para actualizar costo del producto automáticamente"""
        super().save(*args, **kwargs)
        # Actualizar costo del producto después de modificar la receta
        self.producto.actualizar_costo_automatico()
    
    def delete(self, *args, **kwargs):
        """Override delete para actualizar costo del producto"""
        producto = self.producto
        super().delete(*args, **kwargs)
        # Actualizar costo del producto después de eliminar ingrediente
        producto.actualizar_costo_automatico()
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.materia_prima.nombre}: {self.cantidad_necesaria}"


class OrdenProduccion(AuditModel):
    """Orden de producción para fabricar productos"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    numero_orden = models.CharField(max_length=20, unique=True)
    producto = models.ForeignKey(ProductoManufacturado, on_delete=models.CASCADE)
    cantidad_solicitada = models.IntegerField()
    cantidad_producida = models.IntegerField(default=0)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    notas = models.TextField(blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['numero_orden']),
        ]
    
    @property
    def progreso_porcentaje(self):
        if self.cantidad_solicitada > 0:
            return (self.cantidad_producida / self.cantidad_solicitada) * 100
        return 0
    
    def completar_produccion(self):
        """Completar la orden de producción y generar asientos contables"""
        if self.estado != 'completada':
            self.estado = 'completada'
            self.cantidad_producida = self.cantidad_solicitada
            self.save()
            self.crear_asientos_produccion_terminada()
    
    def crear_asientos_produccion_terminada(self):
        """Crear asientos al terminar la producción"""
        from empresa.models import CuentaContable, MovimientoContable
        
        try:
            # Calcular costo total de producción
            costo_total_produccion = self.producto.costo_produccion * self.cantidad_producida
            
            # Débito: Inventario - Producto Terminado (Activo)
            cuenta_producto_terminado = CuentaContable.objects.get_or_create(
                empresa=self.empresa,
                nombre='Inventario - Producto Terminado',
                defaults={'tipo': 'activo'}
            )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_producto_terminado,
                tipo='debito',
                monto=costo_total_produccion,
                descripcion=f'Producción terminada {self.producto.nombre} - Orden {self.numero_orden} ({self.cantidad_producida} unidades)'
            )
            
            # Crédito: Producción en Proceso (Activo)
            cuenta_produccion_proceso = CuentaContable.objects.get_or_create(
                empresa=self.empresa,
                nombre='Producción en Proceso',
                defaults={'tipo': 'activo'}
            )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_produccion_proceso,
                tipo='credito',
                monto=costo_total_produccion,
                descripcion=f'Producción terminada {self.producto.nombre} - Orden {self.numero_orden} ({self.cantidad_producida} unidades)'
            )
            
            # Actualizar stock y precio_costo del producto
            self.producto.stock_actual += self.cantidad_producida
            self.producto.precio_costo = self.producto.costo_produccion
            self.producto.save()
            
        except Exception as e:
            print(f'Error creando asientos para producción terminada: {e}')
    
    def __str__(self):
        return f"Orden {self.numero_orden} - {self.producto.nombre}"


class ConsumoMateriaPrima(AuditModel):
    """Registro de consumo de materias primas en producción"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    orden_produccion = models.ForeignKey(
        OrdenProduccion, 
        on_delete=models.CASCADE, 
        related_name='consumos',
        null=True,
        blank=True
    )
    materia_prima = models.ForeignKey(MateriaPrima, on_delete=models.CASCADE)
    cantidad_consumida = models.DecimalField(max_digits=10, decimal_places=2)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    costo_total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_consumo = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        self.costo_total = self.cantidad_consumida * self.costo_unitario
        super().save(*args, **kwargs)
        self.crear_asientos_contables()
    
    def crear_asientos_contables(self):
        """Crear asientos contables para consumo de materia prima"""
        from empresa.models import CuentaContable, MovimientoContable
        
        try:
            # Débito: Producción en Proceso (Activo)
            cuenta_produccion = CuentaContable.objects.get_or_create(
                empresa=self.empresa,
                nombre='Producción en Proceso',
                defaults={'tipo': 'activo'}
            )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_produccion,
                tipo='debito',
                monto=self.costo_total,
                descripcion=f'Consumo {self.materia_prima.nombre} - Orden {self.orden_produccion.numero_orden if self.orden_produccion else "N/A"}'
            )
            
            # Crédito: Inventario - Materia Prima (Activo)
            cuenta_inventario = CuentaContable.objects.get_or_create(
                empresa=self.empresa,
                nombre='Inventario - Materia Prima',
                defaults={'tipo': 'activo'}
            )[0]
            
            MovimientoContable.objects.create(
                empresa=self.empresa,
                cuenta_fk=cuenta_inventario,
                tipo='credito',
                monto=self.costo_total,
                descripcion=f'Consumo {self.materia_prima.nombre} - Orden {self.orden_produccion.numero_orden if self.orden_produccion else "N/A"}'
            )
            
        except Exception as e:
            print(f'Error creando asientos para consumo de materia prima: {e}')
    
    def __str__(self):
        return f"{self.materia_prima.nombre} - {self.cantidad_consumida} - Orden {self.orden_produccion.numero_orden}"


# ======================
# MODELO PARA ASISTENTE DE AYUDA
# ======================

class SolicitudAyuda(models.Model):
    TIPO_CHOICES = [
        ('tecnico', 'Problema Técnico'),
        ('contable', 'Consulta Contable'),
        ('funcionalidad', 'Nueva Funcionalidad'),
        ('capacitacion', 'Capacitación'),
        ('otro', 'Otro'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('resuelto', 'Resuelto'),
        ('cerrado', 'Cerrado'),
    ]
    
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    asunto = models.CharField(max_length=200)
    mensaje = models.TextField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    respuesta = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Solicitud de Ayuda'
        verbose_name_plural = 'Solicitudes de Ayuda'
    
    def __str__(self):
        return f"{self.asunto} - {self.usuario.username}"

class ConversacionSoporte(models.Model):
    """Conversación de soporte entre usuario y administrador"""
    solicitud_ayuda = models.OneToOneField(
        SolicitudAyuda, 
        on_delete=models.CASCADE, 
        related_name='conversacion'
    )
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    cerrada = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_actualizacion']
    
    def __str__(self):
        return f"Conversación #{self.id} - {self.usuario.username}"

class MensajeSoporte(models.Model):
    """Mensajes dentro de una conversación de soporte"""
    TIPO_CHOICES = [
        ('usuario', 'Usuario'),
        ('soporte', 'Soporte'),
    ]
    
    conversacion = models.ForeignKey(
        ConversacionSoporte, 
        on_delete=models.CASCADE, 
        related_name='mensajes'
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['fecha_envio']
    
    def __str__(self):
        return f"{self.get_tipo_display()}: {self.mensaje[:50]}..."


# ======================
# MODELOS PARA SERVICIOS
# ======================

class TipoServicio(AuditModel):
    """Modelo para gestionar tipos de servicios que ofrece una empresa de servicios"""
    
    empresa = models.ForeignKey(
        Empresa, 
        on_delete=models.CASCADE, 
        related_name='tipos_servicios'
    )
    nombre = models.CharField(
        max_length=100,
        help_text="Nombre del tipo de servicio (ej: Consultoría, Mantenimiento, Diseño)"
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción detallada del servicio"
    )
    precio_base = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Precio base del servicio"
    )
    costo_directo = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        help_text="Costo directo asociado al servicio (materiales, subcontratación, etc.)"
    )
    tiempo_estimado = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Tiempo estimado en horas para completar el servicio"
    )
    unidad_medida = models.CharField(
        max_length=50,
        default='Servicio',
        help_text="Unidad de medida (ej: Hora, Proyecto, Consulta, etc.)"
    )
    activo = models.BooleanField(
        default=True,
        help_text="Si el servicio está activo y disponible"
    )
    
    class Meta:
        unique_together = ['empresa', 'nombre']
        ordering = ['nombre']
        verbose_name = 'Tipo de Servicio'
        verbose_name_plural = 'Tipos de Servicios'
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio_base}"
    
    @property
    def margen_ganancia(self):
        """Calcula el margen de ganancia del servicio"""
        if self.precio_base > 0:
            return ((self.precio_base - self.costo_directo) / self.precio_base) * 100
        return 0
    
    @property
    def utilidad_neta(self):
        """Calcula la utilidad neta del servicio"""
        return self.precio_base - self.costo_directo


class MaterialServicio(AuditModel):
    """Modelo para gestionar materiales asociados a un tipo de servicio"""
    
    tipo_servicio = models.ForeignKey(
        TipoServicio,
        on_delete=models.CASCADE,
        related_name='materiales'
    )
    nombre = models.CharField(
        max_length=100,
        help_text="Nombre del material o insumo"
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción del material"
    )
    costo_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Costo por unidad del material"
    )
    cantidad_necesaria = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        help_text="Cantidad necesaria del material por servicio"
    )
    unidad = models.CharField(
        max_length=20,
        default='Unidad',
        help_text="Unidad de medida (ej: Kg, Litros, Metros, etc.)"
    )
    
    class Meta:
        unique_together = ['tipo_servicio', 'nombre']
        ordering = ['nombre']
        verbose_name = 'Material de Servicio'
        verbose_name_plural = 'Materiales de Servicios'
    
    def __str__(self):
        return f"{self.nombre} ({self.tipo_servicio.nombre})"
    
    @property
    def costo_total(self):
        """Calcula el costo total del material para el servicio"""
        return self.costo_unitario * self.cantidad_necesaria
