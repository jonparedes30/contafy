from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import (
    CuentaContable, Capital, Empresa, Usuario, Producto, Venta, Gasto, Compra,
    MateriaPrima, ProductoManufacturado, RecetaProduccion, OrdenProduccion, Proveedor
)
from .services.accounting_setup import DEFAULT_CONTRAPARTIDAS, ensure_contrapartidas_for_account

class CuentaContableForm(forms.ModelForm):
    class Meta:
        model = CuentaContable
        fields = ['nombre', 'tipo', 'monto_inicial']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'monto_inicial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)

class CapitalForm(forms.ModelForm):
    class Meta:
        model = Capital
        fields = ['monto', 'tipo', 'descripcion']
        widgets = {
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'ruc', 'direccion', 'categoria']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
        }

class EmpleadoEmpresaForm(forms.ModelForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
        label='Contraseña',
        help_text='Contraseña temporal para el empleado'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar contraseña'}),
        label='Confirmar Contraseña',
    )
    
    # Campos de permisos (PoderEmpleado)
    puede_ver_reportes = forms.BooleanField(required=False, label='Ver reportes',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    puede_registrar_ventas = forms.BooleanField(required=False, label='Registrar ventas',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    puede_editar_productos = forms.BooleanField(required=False, label='Editar productos',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    puede_gestionar_cuentas = forms.BooleanField(required=False, label='Gestionar cuentas',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    puede_registrar_gastos = forms.BooleanField(required=False, label='Registrar gastos',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    puede_gestionar_inventario = forms.BooleanField(required=False, label='Gestionar inventario',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    puede_gestionar_metas = forms.BooleanField(required=False, label='Gestionar metas',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned_data
    
    def save(self, commit=True):
        empleado = super().save(commit=False)
        if self.empresa:
            empleado.empresa = self.empresa
        if commit:
            empleado.set_password(self.cleaned_data['password1'])
            empleado.save()
            # Crear poderes del empleado
            from empresa.models import PoderEmpleado
            PoderEmpleado.objects.create(
                empleado=empleado,
                empresa=self.empresa,
                puede_ver_reportes=self.cleaned_data.get('puede_ver_reportes', False),
                puede_registrar_ventas=self.cleaned_data.get('puede_registrar_ventas', False),
                puede_editar_productos=self.cleaned_data.get('puede_editar_productos', False),
                puede_gestionar_cuentas=self.cleaned_data.get('puede_gestionar_cuentas', False),
                puede_registrar_gastos=self.cleaned_data.get('puede_registrar_gastos', False),
                puede_gestionar_inventario=self.cleaned_data.get('puede_gestionar_inventario', False),
                puede_gestionar_metas=self.cleaned_data.get('puede_gestionar_metas', False),
            )
        return empleado

class EditarEmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'direccion', 'categoria', 'tipo_negocio']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'tipo_negocio': forms.TextInput(attrs={'class': 'form-control'}),
        }

class RegistroForm(UserCreationForm):
    # Datos personales
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        label='Nombres',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan Carlos'}),
        error_messages={
            'required': 'El nombre es obligatorio.',
            'max_length': 'El nombre no puede exceder 30 caracteres.'
        }
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        label='Apellidos',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pérez García'}),
        error_messages={
            'required': 'Los apellidos son obligatorios.',
            'max_length': 'Los apellidos no pueden exceder 30 caracteres.'
        }
    )
    email = forms.EmailField(
        required=True,
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu@email.com'}),
        error_messages={
            'required': 'El correo electrónico es obligatorio.',
            'invalid': 'Ingrese un correo electrónico válido.'
        }
    )
    
    # Datos de la empresa
    nombre_empresa = forms.CharField(
        max_length=200, 
        required=True,
        label='Nombre de la Empresa',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Mi Negocio S.A.'}),
        error_messages={
            'required': 'El nombre de la empresa es obligatorio.',
            'max_length': 'El nombre no puede exceder 200 caracteres.'
        }
    )
    ruc = forms.CharField(
        max_length=13, 
        required=True,
        label='RUC o Cédula',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1234567890001'}),
        help_text='RUC de la empresa (13 dígitos) o cédula del propietario (10 dígitos)',
        error_messages={
            'required': 'El RUC o cédula es obligatorio.',
            'max_length': 'El RUC no puede exceder 13 dígitos.'
        }
    )
    direccion = forms.CharField(
        max_length=300, 
        required=True,
        label='Dirección de la Empresa',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Av. Principal 123 y Secundaria'}),
        error_messages={
            'required': 'La dirección es obligatoria.',
            'max_length': 'La dirección no puede exceder 300 caracteres.'
        }
    )
    
    # Categoría y tipo de negocio
    CATEGORIA_CHOICES = [
        ('comercial', 'Comercial - Compra y venta'),
        ('manufactura', 'Manufactura - Producción'),
        ('servicios', 'Servicios - Prestación de servicios')
    ]
    categoria = forms.ChoiceField(
        choices=CATEGORIA_CHOICES,
        required=True,
        label='Categoría del Negocio',
        widget=forms.Select(attrs={'class': 'form-select'}),
        error_messages={
            'required': 'Debe seleccionar una categoría de negocio.'
        }
    )
    tipo_negocio = forms.CharField(
        max_length=50,
        required=True,
        label='Tipo Específico de Negocio',
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Ej: Minimarket, Panadería, Consultorio',
            'list': 'sugerencias_negocio',
            'maxlength': '50'
        }),
        help_text='Describe específicamente tu tipo de negocio (máx. 50 caracteres)',
        error_messages={
            'required': 'El tipo de negocio es obligatorio.',
            'max_length': 'El tipo de negocio no puede exceder 50 caracteres.'
        }
    )
    
    # Ubicación
    PROVINCIAS_ECUADOR = [
        ('azuay', 'Azuay'), ('bolivar', 'Bolívar'), ('canar', 'Cañar'),
        ('carchi', 'Carchi'), ('chimborazo', 'Chimborazo'), ('cotopaxi', 'Cotopaxi'),
        ('el_oro', 'El Oro'), ('esmeraldas', 'Esmeraldas'), ('galapagos', 'Galápagos'),
        ('guayas', 'Guayas'), ('imbabura', 'Imbabura'), ('loja', 'Loja'),
        ('los_rios', 'Los Ríos'), ('manabi', 'Manabí'), ('morona_santiago', 'Morona Santiago'),
        ('napo', 'Napo'), ('orellana', 'Orellana'), ('pastaza', 'Pastaza'),
        ('pichincha', 'Pichincha'), ('santa_elena', 'Santa Elena'), ('santo_domingo', 'Santo Domingo'),
        ('sucumbios', 'Sucumbíos'), ('tungurahua', 'Tungurahua'), ('zamora_chinchipe', 'Zamora Chinchipe')
    ]
    provincia = forms.ChoiceField(
        choices=PROVINCIAS_ECUADOR,
        required=True,
        label='Provincia',
        widget=forms.Select(attrs={'class': 'form-select'}),
        error_messages={
            'required': 'Debe seleccionar una provincia.'
        }
    )
    ciudad = forms.CharField(
        max_length=50,
        required=True,
        label='Ciudad',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Quito, Guayaquil, Cuenca', 'maxlength': '50'}),
        error_messages={
            'required': 'La ciudad es obligatoria.',
            'max_length': 'El nombre de la ciudad no puede exceder 50 caracteres.'
        }
    )
    
    # Contacto opcional
    telefono_whatsapp = forms.CharField(
        max_length=15,
        required=False,
        label='Número de WhatsApp (Opcional)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: +593987654321'}),
        help_text='Formato: +593987654321 (opcional para notificaciones)',
        error_messages={
            'max_length': 'El número no puede exceder 15 caracteres.'
        }
    )
    
    # GPS (opcional)
    latitud = forms.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        required=False,
        widget=forms.HiddenInput()
    )
    longitud = forms.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        required=False,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: juanperez'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'Nombre de Usuario',
            'password1': 'Contraseña',
            'password2': 'Confirmar Contraseña',
        }
        error_messages = {
            'username': {
                'required': 'El nombre de usuario es obligatorio.',
                'unique': 'Este nombre de usuario ya está en uso.',
            }
        }
    
    def clean_ruc(self):
        ruc = self.cleaned_data.get('ruc')
        if ruc:
            # Limpiar espacios y caracteres especiales
            ruc = ruc.replace(' ', '').replace('-', '')
            
            # Validación básica de RUC ecuatoriano
            if not ruc.isdigit():
                raise forms.ValidationError('El RUC/Cédula debe contener solo números.')
            
            if len(ruc) not in [10, 13]:
                raise forms.ValidationError('El RUC debe tener 13 dígitos o la cédula 10 dígitos.')
            
            # Verificar que no exista otra empresa con el mismo RUC
            from empresa.models import Empresa
            if Empresa.objects.filter(ruc=ruc).exists():
                raise forms.ValidationError('Ya existe una empresa registrada con este RUC/Cédula.')
                
        return ruc
    
    def clean_telefono_whatsapp(self):
        telefono = self.cleaned_data.get('telefono_whatsapp')
        if telefono:
            # Limpiar formato
            telefono = telefono.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            
            # Validar que contenga solo números y el signo +
            if not all(c.isdigit() or c == '+' for c in telefono):
                raise forms.ValidationError('El número de WhatsApp debe contener solo números.')
            
            # Formatear número ecuatoriano
            if not telefono.startswith('+593'):
                if telefono.startswith('0'):
                    telefono = '+593' + telefono[1:]
                elif telefono.startswith('593'):
                    telefono = '+' + telefono
                else:
                    telefono = '+593' + telefono
            
            # Validar longitud final
            if len(telefono) != 13:  # +593 + 9 dígitos
                raise forms.ValidationError('El número de WhatsApp debe tener 9 dígitos después del código de país.')
                
        return telefono
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            from empresa.models import Usuario
            if Usuario.objects.filter(email=email).exists():
                raise forms.ValidationError('Ya existe un usuario registrado con este correo electrónico.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            from empresa.models import Usuario
            if Usuario.objects.filter(username=username).exists():
                raise forms.ValidationError('Este nombre de usuario ya está en uso. Elija otro.')
            
            # Validar formato del username
            if len(username) < 3:
                raise forms.ValidationError('El nombre de usuario debe tener al menos 3 caracteres.')
                
            if not username.replace('_', '').replace('.', '').isalnum():
                raise forms.ValidationError('El nombre de usuario solo puede contener letras, números, puntos y guiones bajos.')
                
        return username
    
    def save(self, commit=True):
        from empresa.models import Empresa
        from django.db import transaction
        import logging
        
        logger = logging.getLogger(__name__)
        
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            try:
                with transaction.atomic():
                    user.save()
                    logger.info(f'Usuario creado: {user.username}')
                    
                    # Crear empresa
                    empresa = Empresa.objects.create(
                        nombre=self.cleaned_data['nombre_empresa'],
                        ruc=self.cleaned_data['ruc'],
                        direccion=self.cleaned_data['direccion'],
                        categoria=self.cleaned_data['categoria'],
                        tipo_negocio=self.cleaned_data['tipo_negocio'],
                        provincia=self.cleaned_data['provincia'],
                        ciudad=self.cleaned_data['ciudad'],
                        telefono_whatsapp=self.cleaned_data.get('telefono_whatsapp', ''),
                        latitud=self.cleaned_data.get('latitud'),
                        longitud=self.cleaned_data.get('longitud'),
                        propietario=user
                    )
                    logger.info(f'Empresa creada: {empresa.nombre}')
                    
                    # Asignar empresa al usuario
                    user.empresa = empresa
                    user.save()
                    logger.info(f'Usuario {user.username} asociado a empresa {empresa.nombre}')
                    
            except Exception as e:
                logger.error(f'Error en save del formulario: {str(e)}')
                raise forms.ValidationError(f'Error al crear la cuenta: {str(e)}')
                
        return user

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo', 'codigo_barras', 'nombre', 'descripcion', 'precio_unitario', 'pvp', 'stock', 'categoria', 'fecha_vencimiento', 'lote', 'stock_minimo', 'stock_maximo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pvp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lote': forms.TextInput(attrs={'class': 'form-control'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_maximo': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        producto = super().save(commit=False)
        if self.empresa:
            producto.empresa = self.empresa
        if commit:
            producto.save()
        return producto

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['producto', 'cantidad', 'precio_unitario', 'tipo_pago']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo_pago': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        if self.empresa:
            self.fields['producto'].queryset = Producto.objects.filter(empresa=self.empresa)

class GastoForm(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = ['descripcion', 'monto', 'categoria', 'tipo_pago']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'tipo_pago': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)

class CompraForm(forms.ModelForm):
    precio_unitario = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'precio_unitario'}),
        label='Precio Unitario (sin IVA)'
    )
    monto_neto = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_monto_neto_compra', 'readonly': 'readonly'}),
        label='Monto Neto'
    )
    tasa_iva = forms.DecimalField(
        required=False,
        initial=15,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_tasa_iva_compra'}),
        label='Tasa IVA (%)'
    )
    iva = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_iva_compra', 'readonly': 'readonly'}),
        label='IVA'
    )
    monto = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Total'
    )
    
    class Meta:
        model = Compra
        fields = ['proveedor_fk', 'producto', 'cantidad', 'tipo_pago', 'monto']
        widgets = {
            'proveedor_fk': forms.Select(attrs={'class': 'form-select'}),
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'tipo_pago': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'proveedor_fk': 'Proveedor',
        }
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        if self.empresa:
            self.fields['producto'].queryset = Producto.objects.filter(empresa=self.empresa)
            from empresa.models import Proveedor
            self.fields['proveedor_fk'].queryset = Proveedor.objects.filter(empresa=self.empresa, activo=True)
        self.fields['proveedor_fk'].required = False

class SaldosInicialesForm(forms.Form):
    producto = forms.ModelChoiceField(queryset=None, widget=forms.Select(attrs={'class': 'form-select'}))
    cantidad = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    costo_unitario = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    
    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields['producto'].queryset = Producto.objects.filter(empresa=empresa)

class MateriaPrimaForm(forms.ModelForm):
    class Meta:
        model = MateriaPrima
        fields = ['codigo', 'nombre', 'descripcion', 'unidad_medida', 'precio_unitario', 'stock_actual', 'stock_minimo', 'proveedor_principal']
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
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        if self.empresa:
            self.fields['proveedor_principal'].queryset = Proveedor.objects.filter(empresa=self.empresa, activo=True)
        self.fields['proveedor_principal'].required = False

class ProductoManufacturadoForm(forms.ModelForm):
    class Meta:
        model = ProductoManufacturado
        fields = ['codigo', 'nombre', 'descripcion', 'categoria', 'precio_venta', 'tiempo_produccion', 'stock_actual', 'stock_minimo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tiempo_produccion': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        if self.empresa:
            from empresa.models import CategoriaProducto
            self.fields['categoria'].queryset = CategoriaProducto.objects.filter(empresa=self.empresa)
        self.fields['categoria'].required = False

class RecetaProduccionForm(forms.ModelForm):
    class Meta:
        model = RecetaProduccion
        fields = ['materia_prima', 'cantidad_necesaria']
        widgets = {
            'materia_prima': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_necesaria': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class OrdenProduccionForm(forms.ModelForm):
    class Meta:
        model = OrdenProduccion
        fields = ['producto', 'cantidad_solicitada']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_solicitada': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        if self.empresa:
            self.fields['producto'].queryset = ProductoManufacturado.objects.filter(empresa=self.empresa, activo=True)

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'ruc', 'telefono', 'email', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        proveedor = super().save(commit=False)
        if self.empresa:
            proveedor.empresa = self.empresa
        if commit:
            proveedor.save()
        return proveedor

class ClienteForm(forms.ModelForm):
    class Meta:
        from .models import Cliente
        model = Cliente
        fields = ['nombre', 'tipo_documento', 'numero_documento', 'telefono', 'email', 'direccion', 'limite_credito']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo del cliente'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula o RUC'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0987654321'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'cliente@email.com'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Dirección del cliente'}),
            'limite_credito': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '0'}),
        }
        labels = {
            'nombre': 'Nombre Completo',
            'tipo_documento': 'Tipo de Documento',
            'numero_documento': 'Número de Documento',
            'telefono': 'Teléfono',
            'email': 'Correo Electrónico',
            'direccion': 'Dirección',
            'limite_credito': 'Límite de Crédito',
        }
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
        self.fields['telefono'].required = False
        self.fields['direccion'].required = False
    
    def save(self, commit=True):
        cliente = super().save(commit=False)
        if self.empresa:
            cliente.empresa = self.empresa
        if commit:
            cliente.save()
        return cliente

class CategoriaProductoForm(forms.ModelForm):
    class Meta:
        from .models import CategoriaProducto
        model = CategoriaProducto
        fields = ['nombre', 'descripcion', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Electrónicos, Alimentos, etc.'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descripción de la categoría (opcional)'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nombre': 'Nombre de la Categoría',
            'descripcion': 'Descripción',
            'activa': 'Categoría Activa',
        }
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        self.fields['descripcion'].required = False
    
    def save(self, commit=True):
        categoria = super().save(commit=False)
        if self.empresa:
            categoria.empresa = self.empresa
        if commit:
            categoria.save()
        return categoria