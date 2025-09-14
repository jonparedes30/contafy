from django import forms
from .models import CuentaContable, Capital, Empresa, Usuario
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