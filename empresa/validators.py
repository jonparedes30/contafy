"""Validadores personalizados para Contafy"""
import re
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def validar_ruc_ecuador(ruc):
    """Valida RUC ecuatoriano según algoritmo oficial"""
    if not ruc or len(ruc) != 13:
        raise ValidationError("El RUC debe tener 13 dígitos")
    
    if not ruc.isdigit():
        raise ValidationError("El RUC solo debe contener números")
    
    # Validar provincia (primeros 2 dígitos)
    provincia = int(ruc[:2])
    if provincia < 1 or provincia > 24:
        raise ValidationError("Código de provincia inválido")
    
    # Validar tercer dígito según tipo
    tercer_digito = int(ruc[2])
    if tercer_digito < 0 or tercer_digito > 9:
        raise ValidationError("RUC inválido")
    
    # Algoritmo de validación
    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    suma = 0
    
    for i in range(9):
        producto = int(ruc[i]) * coeficientes[i]
        if producto >= 10:
            producto = sum(int(d) for d in str(producto))
        suma += producto
    
    digito_verificador = (10 - (suma % 10)) % 10
    if digito_verificador != int(ruc[9]):
        raise ValidationError("RUC inválido - dígito verificador incorrecto")


def validar_codigo_producto(codigo):
    """Valida formato de código de producto"""
    if not re.match(r'^[A-Z0-9-_]{3,20}$', codigo):
        raise ValidationError(
            "Código debe tener 3-20 caracteres: letras mayúsculas, números, guiones"
        )


def validar_codigo_barras(codigo):
    """Valida formato de código de barras estándar"""
    if not codigo:
        return  # Campo opcional
    
    # Limpiar espacios
    codigo = codigo.strip()
    
    # Debe ser solo números
    if not codigo.isdigit():
        raise ValidationError("Código de barras debe contener solo números")
    
    # Validar longitudes estándar
    longitudes_validas = [8, 12, 13]  # EAN-8, UPC-A, EAN-13
    if len(codigo) not in longitudes_validas:
        raise ValidationError(
            f"Código de barras debe tener {', '.join(map(str, longitudes_validas))} dígitos"
        )
    
    # Validar dígito de control para EAN-13
    if len(codigo) == 13:
        if not _validar_digito_control_ean13(codigo):
            raise ValidationError("Código EAN-13 inválido - dígito de control incorrecto")


def _validar_digito_control_ean13(codigo):
    """Valida dígito de control EAN-13"""
    if len(codigo) != 13:
        return False
    
    # Algoritmo EAN-13
    suma = 0
    for i, digito in enumerate(codigo[:12]):
        peso = 1 if i % 2 == 0 else 3
        suma += int(digito) * peso
    
    digito_control = (10 - (suma % 10)) % 10
    return digito_control == int(codigo[12])


def validar_monto_positivo(monto):
    """Valida que el monto sea positivo"""
    if monto <= 0:
        raise ValidationError("El monto debe ser mayor a cero")


# Validadores regex
validador_nombre_empresa = RegexValidator(
    regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\.\-&]{2,100}$',
    message="Nombre debe tener 2-100 caracteres válidos"
)

validador_telefono = RegexValidator(
    regex=r'^\+?593?[0-9]{8,10}$',
    message="Formato: +593987654321 o 0987654321"
)

validador_codigo_barras = RegexValidator(
    regex=r'^[0-9]{8,13}$',
    message="Código de barras debe tener 8-13 dígitos numéricos"
)