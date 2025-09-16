from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CuentaContable, Capital, Empresa, Usuario, Producto, Venta, Gasto, Compra
from .services.accounting_setup import DEFAULT_CONTRAPARTIDAS, ensure_contrapartidas_for_account

class CuentaContableForm(forms.ModelForm):
    contrapartidas_sugeridas = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Contrapartidas sugeridas"
    )
    
    class Meta:
        model = CuentaContable
        fields = ['nombre', 'tipo', 'monto_inicial']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generar opciones de contrapartidas
        choices = []
        for conf in DEFAULT_CONTRAPARTIDAS:
            nombre = conf["nombre_tpl"].format(base_nombre="[Nombre de cuenta]")
            choices.append((conf["codigo_suffix"], f"{nombre} ({conf['tipo']})"))
        self.fields['contrapartidas_sugeridas'].choices = choices

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
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

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
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pérez García'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu@email.com'})
    )
    
    # Datos de la empresa
    nombre_empresa = forms.CharField(
        max_length=200, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Mi Negocio S.A.'})
    )
    ruc = forms.CharField(
        max_length=13, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1234567890001'}),
        help_text='RUC de la empresa o cédula del propietario'
    )
    direccion = forms.CharField(
        max_length=300, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Av. Principal 123 y Secundaria'})
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
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tipo_negocio = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Ej: Minimarket, Panadería, Consultorio',
            'list': 'sugerencias_negocio'
        }),
        help_text='Describe específicamente tu tipo de negocio'
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
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    ciudad = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Quito, Guayaquil, Cuenca'})
    )
    
    # Contacto opcional
    telefono_whatsapp = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: +593987654321'}),
        help_text='Formato: +593987654321 (opcional)'
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
    
    def clean_ruc(self):
        ruc = self.cleaned_data.get('ruc')
        if ruc:
            # Validación básica de RUC ecuatoriano
            if not ruc.isdigit() or len(ruc) not in [10, 13]:
                raise forms.ValidationError('RUC debe tener 10 o 13 dígitos')
        return ruc
    
    def clean_telefono_whatsapp(self):
        telefono = self.cleaned_data.get('telefono_whatsapp')
        if telefono:
            # Limpiar formato
            telefono = telefono.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if not telefono.startswith('+593'):
                if telefono.startswith('0'):
                    telefono = '+593' + telefono[1:]
                elif telefono.startswith('593'):
                    telefono = '+' + telefono
                else:
                    telefono = '+593' + telefono
        return telefono
    
    def save(self, commit=True):
        from empresa.models import Empresa
        from django.db import transaction
        
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            with transaction.atomic():
                user.save()
                
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
                
                # Asignar empresa al usuario
                user.empresa = empresa
                user.save()
                
        return user

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'descripcion', 'precio_unitario', 'stock']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }

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

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['producto', 'cantidad', 'monto', 'tipo_pago']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo_pago': forms.Select(attrs={'class': 'form-select'}),
        }

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
        model = Producto  # Usando Producto como placeholder
        fields = ['nombre', 'descripcion', 'precio_unitario']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class ProductoManufacturadoForm(forms.ModelForm):
    class Meta:
        model = Producto  # Usando Producto como placeholder
        fields = ['nombre', 'descripcion', 'precio_unitario']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class OrdenProduccionForm(forms.ModelForm):
    class Meta:
        model = Producto  # Usando Producto como placeholder
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }