from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import (
    Empresa,
    Gasto,
    Venta,
    Producto,
    Compra,
    CuentaContable,
    MovimientoContable,
    Usuario,
    MateriaPrima,
    ProductoManufacturado,
    RecetaProduccion,
    OrdenProduccion,
    CategoriaProducto,
    Capital,
    Proveedor,
)
from .validators import validar_ruc_ecuador, validar_codigo_producto, validar_monto_positivo, validar_codigo_barras


# === FORMULARIO EMPRESA ===
class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'ruc', 'direccion']

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre or nombre.strip() == '':
            raise forms.ValidationError("El nombre no puede estar vacío.")
        return nombre

    def clean_ruc(self):
        ruc = self.cleaned_data.get('ruc')
        if len(ruc) == 13:
            try:
                validar_ruc_ecuador(ruc)
            except ValidationError as e:
                raise forms.ValidationError(str(e))
        elif len(ruc) == 10:
            # Validación básica de cédula (solo dígitos)
            if not ruc.isdigit():
                raise forms.ValidationError("La cédula debe contener solo números.")
        else:
            raise forms.ValidationError("Debe tener 10 dígitos (cédula) o 13 dígitos (RUC).")
        return ruc


# === FORMULARIO EDITAR EMPRESA ===
class EditarEmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'ruc', 'direccion', 'provincia', 'ciudad', 'telefono_whatsapp', 'tipo_negocio']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'provincia': forms.Select(attrs={'class': 'form-select'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_whatsapp': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_negocio': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['provincia'].choices = [
            ('azuay', 'Azuay'), ('bolivar', 'Bolívar'), ('canar', 'Cañar'),
            ('carchi', 'Carchi'), ('chimborazo', 'Chimborazo'), ('cotopaxi', 'Cotopaxi'),
            ('el_oro', 'El Oro'), ('esmeraldas', 'Esmeraldas'), ('galapagos', 'Galápagos'),
            ('guayas', 'Guayas'), ('imbabura', 'Imbabura'), ('loja', 'Loja'),
            ('los_rios', 'Los Ríos'), ('manabi', 'Manabí'), ('morona_santiago', 'Morona Santiago'),
            ('napo', 'Napo'), ('orellana', 'Orellana'), ('pastaza', 'Pastaza'),
            ('pichincha', 'Pichincha'), ('santa_elena', 'Santa Elena'), ('santo_domingo', 'Santo Domingo'),
            ('sucumbios', 'Sucumbíos'), ('tungurahua', 'Tungurahua'), ('zamora_chinchipe', 'Zamora Chinchipe')
        ]


# === FORMULARIO GASTO ===
class GastoForm(forms.ModelForm):
    def __init__(self, *args, empresa=None, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)
        self.fields['tipo_pago'].widget.attrs.update({'class': 'form-select'})
    
    class Meta:
        model = Gasto
        exclude = ['empresa', 'creado_por', 'modificado_por']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo_pago': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        try:
            validar_monto_positivo(monto)
        except ValidationError as e:
            raise forms.ValidationError(str(e))
        return monto


# === FORMULARIO VENTA ===
class VentaForm(forms.ModelForm):
    def __init__(self, *args, empresa=None, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)
        if empresa:
            from .models import Cliente
            self.fields['cliente_fk'].queryset = Cliente.objects.filter(empresa=empresa, activo=True)
            self.fields['producto'].queryset = Producto.objects.filter(empresa=empresa)
        
        self.fields['cliente_fk'].widget.attrs.update({'class': 'form-select'})
        self.fields['cliente_nombre'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nombre del cliente (si no está registrado)'
        })
        self.fields['producto'].widget.attrs.update({'class': 'form-select'})
        self.fields['cantidad'].widget.attrs.update({'id': 'id_cantidad', 'class': 'form-control'})
        self.fields['precio_unitario'].widget.attrs.update({
            'id': 'id_precio_unitario', 
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Editable para descuentos'
        })
        self.fields['tipo_pago'].widget.attrs.update({'class': 'form-select'})
        self.fields['monto_neto'].widget.attrs.update({
            'id': 'id_monto_neto',
            'class': 'form-control',
            'step': '0.01'
        })
        self.fields['iva'].widget.attrs.update({
            'id': 'id_iva',
            'class': 'form-control',
            'readonly': 'readonly',
            'step': '0.01'
        })
        self.fields['monto'].widget.attrs.update({
            'id': 'id_monto_total',
            'class': 'form-control',
            'readonly': 'readonly',
            'step': '0.01'
        })
        self.fields['tasa_iva'].widget.attrs.update({
            'id': 'id_tasa_iva',
            'class': 'form-control',
            'step': '0.01'
        })

    class Meta:
        model = Venta
        fields = ['cliente_fk', 'cliente_nombre', 'producto', 'cantidad', 'precio_unitario', 'monto_neto', 'iva', 'monto', 'tasa_iva', 'tipo_pago']

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto is None or monto <= 0:
            raise forms.ValidationError("El monto total debe ser mayor a cero.")
        return monto
    
    def clean(self):
        cleaned_data = super().clean()
        # Cliente es opcional - no validar
        return cleaned_data

    def save(self, commit=True):
        instancia = super().save(commit=False)
        if self.empresa:
            instancia.empresa = self.empresa
        # Calcular el monto automáticamente
        instancia.monto = instancia.cantidad * instancia.precio_unitario
        if commit:
            instancia.save()
        return instancia


# === FORMULARIO PRODUCTO ===
class ProductoForm(forms.ModelForm):
    def __init__(self, *args, empresa=None, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)
        if empresa:
            from .models import CategoriaProducto
            # Crear categoría por defecto si no existe ninguna
            if not CategoriaProducto.objects.filter(empresa=empresa).exists():
                CategoriaProducto.objects.create(
                    empresa=empresa,
                    nombre='General',
                    descripcion='Categoría general para productos'
                )
            # Configurar queryset y hacer el campo opcional
            self.fields['categoria'].queryset = CategoriaProducto.objects.filter(
                empresa=empresa, activa=True
            )
            self.fields['categoria'].required = False
            self.fields['categoria'].empty_label = "Seleccionar categoría..."
    
    class Meta:
        model = Producto
        exclude = ['empresa', 'creado_por', 'modificado_por', 'creado_en', 'modificado_en']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: PROD001'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del producto (opcional)'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'codigo_barras': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: 1234567890123 (opcional)'
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'lote': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: L001 (opcional)'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0'
            }),
            'stock_maximo': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0'
            }),
            'pvp': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Precio de venta (opcional)'
            }),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre or nombre.strip() == '':
            raise forms.ValidationError("El nombre no puede estar vacío.")
        return nombre

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if not codigo or codigo.strip() == '':
            raise forms.ValidationError("El código no puede estar vacío.")
        try:
            validar_codigo_producto(codigo.upper())
        except ValidationError as e:
            raise forms.ValidationError(str(e))
        return codigo.upper()
    
    def clean_codigo_barras(self):
        codigo_barras = self.cleaned_data.get('codigo_barras')
        if codigo_barras:
            try:
                validar_codigo_barras(codigo_barras)
            except ValidationError as e:
                raise forms.ValidationError(str(e))
        return codigo_barras
    
    def clean(self):
        cleaned_data = super().clean()
        stock_minimo = cleaned_data.get('stock_minimo')
        stock_maximo = cleaned_data.get('stock_maximo')
        
        if stock_minimo and stock_maximo and stock_minimo > stock_maximo:
            raise forms.ValidationError(
                'El stock mínimo no puede ser mayor al stock máximo'
            )
        
        return cleaned_data

    def clean_precio_unitario(self):
        precio = self.cleaned_data.get('precio_unitario')
        if precio is None or precio <= 0:
            raise forms.ValidationError("El precio unitario debe ser mayor a cero.")
        return precio

    def save(self, commit=True):
        instancia = super().save(commit=False)
        if self.empresa:
            instancia.empresa = self.empresa
        # Si no se seleccionó categoría, asignar la categoría "General"
        if not instancia.categoria:
            from .models import CategoriaProducto
            categoria_general, created = CategoriaProducto.objects.get_or_create(
                empresa=self.empresa,
                nombre='General',
                defaults={'descripcion': 'Categoría general para productos'}
            )
            instancia.categoria = categoria_general
        if commit:
            instancia.save()
        return instancia


# === FORMULARIO COMPRA ===
class CompraForm(forms.ModelForm):
    precio_unitario = forms.DecimalField(
        label="Precio Unitario",
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'id': 'precio_unitario'
        })
    )
    
    def __init__(self, *args, empresa=None, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)
        if empresa:
            from .models import Proveedor
            self.fields['proveedor_fk'].queryset = Proveedor.objects.filter(empresa=empresa, activo=True)
            self.fields['producto'].queryset = Producto.objects.filter(empresa=empresa)
        
        # Asignar clases y readonly
        self.fields['proveedor_fk'].widget.attrs.update({'class': 'form-select'})
        self.fields['proveedor_nombre'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nombre del proveedor (si no está registrado)'
        })
        self.fields['producto'].widget.attrs.update({'class': 'form-select'})
        self.fields['cantidad'].widget.attrs.update({'class': 'form-control'})
        self.fields['tipo_pago'].widget.attrs.update({'class': 'form-select'})
        self.fields['monto_neto'].widget.attrs.update({
            'id': 'id_monto_neto_compra',
            'class': 'form-control',
            'step': '0.01'
        })
        self.fields['iva'].widget.attrs.update({
            'id': 'id_iva_compra',
            'class': 'form-control',
            'readonly': 'readonly',
            'step': '0.01'
        })
        self.fields['monto'].widget.attrs.update({
            'id': 'id_monto_total_compra',
            'class': 'form-control',
            'readonly': 'readonly',
            'step': '0.01'
        })
        self.fields['tasa_iva'].widget.attrs.update({
            'id': 'id_tasa_iva_compra',
            'class': 'form-control',
            'step': '0.01'
        })

    class Meta:
        model = Compra
        fields = ['proveedor_fk', 'proveedor_nombre', 'producto', 'cantidad', 'monto_neto', 'iva', 'monto', 'tasa_iva', 'tipo_pago']

    def clean(self):
        cleaned_data = super().clean()
        cantidad = cleaned_data.get('cantidad')
        monto = cleaned_data.get('monto')
        
        if cantidad and cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor a cero.")
        if monto and monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor a cero.")
        
        return cleaned_data

    def save(self, commit=True):
        instancia = super().save(commit=False)
        if self.empresa:
            instancia.empresa = self.empresa
        if commit:
            instancia.save()
        return instancia


# === FORMULARIO CUENTA CONTABLE ===
class CuentaContableForm(forms.ModelForm):
    class Meta:
        model = CuentaContable
        fields = ['nombre', 'tipo', 'monto_inicial']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'monto_inicial': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
        }
        labels = {
            'monto_inicial': '💰 Monto inicial (opcional)',
        }
        help_texts = {
            'monto_inicial': 'Para préstamos, activos o deudas con valor inicial',
        }

    def __init__(self, *args, empresa=None, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instancia = super().save(commit=False)
        if self.empresa:
            instancia.empresa = self.empresa
        if commit:
            instancia.save()
        return instancia


# === FORMULARIO CAPITAL ===
class CapitalForm(forms.ModelForm):
    class Meta:
        model = Capital
        exclude = ['empresa', 'creado_por', 'modificado_por']
        widgets = {
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, empresa=None, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instancia = super().save(commit=False)
        if self.empresa:
            instancia.empresa = self.empresa
        if commit:
            instancia.save()
        return instancia


# === FORMULARIO REGISTRO ===
class RegistroForm(UserCreationForm):
    email = forms.EmailField(label="Email")
    first_name = forms.CharField(label="Nombre (usuario)")
    last_name = forms.CharField(label="Apellidos")
    
    # Sobreescribir campos de contraseña con help_text personalizado
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Tu contraseña debe tener al menos 8 caracteres y contener: mayúsculas, minúsculas, números y símbolos (ej: MiPass123!)"
    )
    password2 = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Confirma tu contraseña"
    )
    # Campos de empresa:
    nombre_empresa = forms.CharField(max_length=100, label="🏢 Nombre de la empresa")
    ruc = forms.CharField(
        max_length=13, 
        label="📇 RUC o Cédula",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'RUC: 1234567890001 o Cédula: 1234567890'
        }),
        help_text="RUC de 13 dígitos para empresas o Cédula de 10 dígitos para personas naturales"
    )
    direccion = forms.CharField(max_length=200, label="📍 Dirección de la empresa")
    
    # Ubicación geográfica
    provincia = forms.ChoiceField(
        choices=[
            ('azuay', 'Azuay'), ('bolivar', 'Bolívar'), ('canar', 'Cañar'),
            ('carchi', 'Carchi'), ('chimborazo', 'Chimborazo'), ('cotopaxi', 'Cotopaxi'),
            ('el_oro', 'El Oro'), ('esmeraldas', 'Esmeraldas'), ('galapagos', 'Galápagos'),
            ('guayas', 'Guayas'), ('imbabura', 'Imbabura'), ('loja', 'Loja'),
            ('los_rios', 'Los Ríos'), ('manabi', 'Manabí'), ('morona_santiago', 'Morona Santiago'),
            ('napo', 'Napo'), ('orellana', 'Orellana'), ('pastaza', 'Pastaza'),
            ('pichincha', 'Pichincha'), ('santa_elena', 'Santa Elena'), ('santo_domingo', 'Santo Domingo'),
            ('sucumbios', 'Sucumbíos'), ('tungurahua', 'Tungurahua'), ('zamora_chinchipe', 'Zamora Chinchipe')
        ],
        label="🗺️ Provincia",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    ciudad = forms.CharField(
        max_length=50, 
        label="🏢 Ciudad",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Quito, Guayaquil, Cuenca...'})
    )
    
    # WhatsApp
    telefono_whatsapp = forms.CharField(
        max_length=15,
        required=False,
        label="📱 WhatsApp (opcional)",
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '+593987654321',
            'pattern': r'\+?593[0-9]{9}'
        }),
        help_text="Para recibir notificaciones importantes"
    )
    
    # Ubicación GPS
    latitud = forms.DecimalField(
        max_digits=10,
        decimal_places=7,
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_latitud'})
    )
    longitud = forms.DecimalField(
        max_digits=10,
        decimal_places=7,
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_longitud'})
    )
    
    # Nuevos campos para categorización
    categoria = forms.ChoiceField(
        choices=[
            ('comercial', 'Comercial - Compra y venta de productos'),
            ('manufactura', 'Manufactura - Producción y fabricación'),
            ('servicios', 'Servicios - Prestación de servicios'),
        ],
        label="🏭 Categoría de tu negocio",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_categoria'})
    )
    
    tipo_negocio = forms.CharField(
        max_length=50,
        label="🏪 Tipo específico de negocio",
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'id': 'id_tipo_negocio',
            'placeholder': 'Ej: Panadería, Carpintería, Consultorio...',
            'list': 'sugerencias_negocio'
        }),
        help_text="Describe tu tipo de negocio específico"
    )
    
    # CÓDIGO DE INVITACIÓN - OBLIGATORIO
    codigo_invitacion = forms.CharField(
        max_length=50,
        label="🔑 Código de Invitación",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu código de invitación',
            'required': True
        }),
        help_text="Código necesario para registrarse en la plataforma"
    )

    class Meta:
        model = Usuario
        fields = [
            'username', 'email',
            'first_name', 'last_name',
            'password1', 'password2',
            'nombre_empresa', 'ruc', 'direccion',
            'provincia', 'ciudad', 'telefono_whatsapp',
            'latitud', 'longitud',
            'categoria', 'tipo_negocio',
            'codigo_invitacion',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if field.widget.__class__.__name__ != 'Select':
                field.widget.attrs.update({'class': 'form-control'})
        

        
        # Opciones de tipos de negocio por categoría
        self.tipos_negocio = {
            'comercial': [
                ('licoreria', 'Licorería'),
                ('farmacia', 'Farmacia'),
                ('minimarket', 'Minimarket'),
                ('ferreteria', 'Ferretería'),
                ('papeleria', 'Papelería'),
                ('tienda_ropa', 'Tienda de Ropa'),
                ('otro_comercial', 'Otro Comercial'),
            ],
            'manufactura': [
                ('panaderia', 'Panadería'),
                ('carpinteria', 'Carpintería'),
                ('herreria', 'Herrería'),
                ('confeccion', 'Confección de Ropa'),
                ('procesadora_alimentos', 'Procesadora de Alimentos'),
                ('artesanias', 'Artesanías'),
                ('otro_manufactura', 'Otro Manufactura'),
            ],
            'servicios': [
                ('consultorio', 'Consultorio Médico'),
                ('peluqueria', 'Peluquería'),
                ('taller_mecanico', 'Taller Mecánico'),
                ('restaurante', 'Restaurante'),
                ('cafeteria', 'Cafetería'),
                ('limpieza', 'Servicios de Limpieza'),
                ('otro_servicios', 'Otro Servicios'),
            ],
        }
        
        # No necesitamos establecer choices para campo de texto
        pass

    def clean_ruc(self):
        ruc = self.cleaned_data.get('ruc')
        if not ruc:
            raise forms.ValidationError("Este campo es obligatorio.")
        
        # Validar longitud
        if len(ruc) not in [10, 13]:
            raise forms.ValidationError("Debe tener 10 dígitos (cédula) o 13 dígitos (RUC).")
        
        # Verificar duplicados
        if Empresa.objects.filter(ruc=ruc).exists():
            raise forms.ValidationError("Ya existe una empresa registrada con este RUC/Cédula.")
        
        return ruc
    
    def clean_codigo_invitacion(self):
        """Validar que el código de invitación existe y está disponible"""
        from .models import CodigoInvitacion
        
        codigo = self.cleaned_data.get('codigo_invitacion')
        if not codigo:
            raise forms.ValidationError("El código de invitación es obligatorio.")
        
        try:
            codigo_obj = CodigoInvitacion.objects.get(codigo=codigo)
            if codigo_obj.usado:
                raise forms.ValidationError("Este código de invitación ya ha sido utilizado.")
        except CodigoInvitacion.DoesNotExist:
            raise forms.ValidationError("Código de invitación inválido.")
        
        return codigo

    def save(self, commit=True):
        from .models import CodigoInvitacion
        
        # Crear empresa primero
        empresa = Empresa(
            nombre=self.cleaned_data['nombre_empresa'],
            ruc=self.cleaned_data['ruc'],
            direccion=self.cleaned_data['direccion'],
            provincia=self.cleaned_data['provincia'],
            ciudad=self.cleaned_data['ciudad'],
            telefono_whatsapp=self.cleaned_data.get('telefono_whatsapp', ''),
            latitud=self.cleaned_data.get('latitud'),
            longitud=self.cleaned_data.get('longitud'),
            categoria=self.cleaned_data['categoria'],
            tipo_negocio=self.cleaned_data['tipo_negocio']
        )
        empresa.save()

        # Crear usuario normalmente
        usuario = super().save(commit=False)
        usuario.empresa_id = empresa.id  # Usar ID en lugar del objeto
        
        if commit:
            usuario.save()
            
            # Marcar código como usado
            codigo_invitacion = CodigoInvitacion.objects.get(
                codigo=self.cleaned_data['codigo_invitacion']
            )
            codigo_invitacion.usado = True
            codigo_invitacion.usado_por = usuario
            codigo_invitacion.save()
            
        return usuario


class SaldosInicialesForm(forms.Form):
    # === OPCIÓN 1: INVENTARIO GLOBAL ===
    inventario_global = forms.DecimalField(
        label="📦 Inventario Inicial Global", 
        min_value=0, 
        decimal_places=2, 
        required=False, 
        initial=0,
        help_text="Monto total del inventario inicial (se creará un producto 'Inventario Inicial')"
    )
    
    # === OPCIÓN 2: INVENTARIO POR PRODUCTO ===
    usar_inventario_detallado = forms.BooleanField(
        label="📋 Usar inventario detallado por producto",
        required=False,
        help_text="Marcar si quieres registrar el inventario inicial por cada producto individual"
    )
    
    # === CAMPOS BÁSICOS ===
    caja_banco = forms.DecimalField(
        label="💰 Saldo inicial de Caja/Banco", 
        min_value=0, 
        decimal_places=2, 
        required=False, 
        initial=0
    )
    
    # El capital social se calculará como contrapartida
    
    def __init__(self, *args, empresa=None, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)
        
        # Agregar clases CSS
        for field_name, field in self.fields.items():
            if isinstance(field, forms.DecimalField):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field, forms.BooleanField):
                field.widget.attrs.update({'class': 'form-check-input'})
    
    def clean(self):
        cleaned_data = super().clean()
        inventario_global = cleaned_data.get('inventario_global', 0) or 0
        usar_inventario_detallado = cleaned_data.get('usar_inventario_detallado', False)
        
        # Validar que al menos una opción de inventario esté seleccionada
        if inventario_global == 0 and not usar_inventario_detallado:
            raise forms.ValidationError(
                "Debes seleccionar al menos una opción de inventario: "
                "inventario global o inventario detallado por producto."
            )
        
        return cleaned_data


class InventarioDetalladoForm(forms.Form):
    """Formulario para registrar inventario inicial por producto individual"""
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.none(),
        label="Producto",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cantidad_inicial = forms.IntegerField(
        label="Cantidad inicial",
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    precio_unitario_inicial = forms.DecimalField(
        label="Precio unitario inicial",
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields['producto'].queryset = Producto.objects.filter(empresa=empresa)


class EmpleadoEmpresaForm(UserCreationForm):
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label="Nombre (usuario)", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Apellidos", widget=forms.TextInput(attrs={'class': 'form-control'}))
    # Poderes iniciales
    puede_ver_reportes = forms.BooleanField(label="Ver reportes", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    puede_registrar_ventas = forms.BooleanField(label="Registrar ventas", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    puede_editar_productos = forms.BooleanField(label="Editar productos", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    puede_gestionar_cuentas = forms.BooleanField(label="Gestionar cuentas", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    puede_registrar_gastos = forms.BooleanField(label="Registrar gastos", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    puede_gestionar_inventario = forms.BooleanField(label="Gestionar inventario", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    puede_gestionar_metas = forms.BooleanField(label="Gestionar metas", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = Usuario
        fields = [
            'username', 'email',
            'first_name', 'last_name',
            'password1', 'password2',
            'puede_ver_reportes', 'puede_registrar_ventas', 'puede_editar_productos',
            'puede_gestionar_cuentas', 'puede_registrar_gastos', 'puede_gestionar_inventario', 'puede_gestionar_metas',
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if self.empresa:
            # Verificar que el username sea único para esta empresa específica
            if Usuario.objects.filter(username=username, empresa=self.empresa).exists():
                raise forms.ValidationError("Ya existe un empleado con este nombre de usuario en tu empresa.")
        return username

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if self.empresa:
            usuario.empresa = self.empresa
        if commit:
            usuario.save()
            # Crear poderes iniciales
            from empresa.models import PoderEmpleado
            PoderEmpleado.objects.create(
                empleado=usuario,
                empresa=self.empresa,
                puede_ver_reportes=self.cleaned_data.get('puede_ver_reportes', False),
                puede_registrar_ventas=self.cleaned_data.get('puede_registrar_ventas', False),
                puede_editar_productos=self.cleaned_data.get('puede_editar_productos', False),
                puede_gestionar_cuentas=self.cleaned_data.get('puede_gestionar_cuentas', False),
                puede_registrar_gastos=self.cleaned_data.get('puede_registrar_gastos', False),
                puede_gestionar_inventario=self.cleaned_data.get('puede_gestionar_inventario', False),
                puede_gestionar_metas=self.cleaned_data.get('puede_gestionar_metas', False),
            )
        return usuario


# === FORMULARIO PROVEEDOR ===
class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        exclude = ['empresa', 'activo', 'creado_en']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'dias_credito': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, empresa=None, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instancia = super().save(commit=False)
        if self.empresa:
            instancia.empresa = self.empresa
        if commit:
            instancia.save()
        return instancia


# === FORMULARIOS PARA MANUFACTURA ===

class MateriaPrimaForm(forms.ModelForm):
    class Meta:
        model = MateriaPrima
        exclude = ['empresa']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'unidad_medida': forms.Select(attrs={'class': 'form-select'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'proveedor_principal': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, empresa=None, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)
        if empresa:
            from .models import Proveedor
            self.fields['proveedor_principal'].queryset = Proveedor.objects.filter(
                empresa=empresa, activo=True
            )
    
    def save(self, commit=True):
        instancia = super().save(commit=False)
        if self.empresa:
            instancia.empresa = self.empresa
        if commit:
            instancia.save()
        return instancia


class ProductoManufacturadoForm(forms.ModelForm):
    class Meta:
        model = ProductoManufacturado
        exclude = ['empresa', 'precio_costo', 'stock_actual', 'stock_minimo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tiempo_produccion': forms.NumberInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, empresa=None, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields['categoria'].queryset = CategoriaProducto.objects.filter(
                empresa=empresa, activa=True
            )
        # Hacer que el producto esté activo por defecto
        self.fields['activo'].initial = True
    
    def save(self, commit=True):
        instancia = super().save(commit=False)
        if hasattr(self, 'empresa'):
            instancia.empresa = self.empresa
        if commit:
            instancia.save()
        return instancia


class RecetaProduccionForm(forms.ModelForm):
    class Meta:
        model = RecetaProduccion
        fields = ['materia_prima', 'cantidad_necesaria']
        widgets = {
            'materia_prima': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_necesaria': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields['materia_prima'].queryset = MateriaPrima.objects.filter(empresa=empresa)


class OrdenProduccionForm(forms.ModelForm):
    class Meta:
        model = OrdenProduccion
        exclude = ['empresa', 'numero_orden', 'cantidad_producida']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_solicitada': forms.NumberInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'fecha_inicio': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'fecha_fin': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, empresa=None, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields['producto'].queryset = ProductoManufacturado.objects.filter(
                empresa=empresa, activo=True
            )
    
    def save(self, commit=True):
        instancia = super().save(commit=False)
        if self.empresa:
            instancia.empresa = self.empresa
            # Generar número de orden automáticamente
            if not instancia.numero_orden:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                instancia.numero_orden = f"OP-{timestamp}"
        if commit:
            instancia.save()
        return instancia
