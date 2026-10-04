"""
Validador de RUC y Cédula del Ecuador según algoritmos del SRI.

Acepta:
  - Cédula (10 dígitos) — para microempresarios sin RUC formal
  - RUC Persona Natural (13 dígitos, cédula + '001')
  - RUC Sociedad Privada (13 dígitos, 3er dígito = 9)
  - RUC Sociedad Pública (13 dígitos, 3er dígito = 6)

Uso:
    from empresa.utils.validador_ruc import validar_ruc_ecuador

    valido, error = validar_ruc_ecuador('1710034065')
    if not valido:
        raise ValidationError(error)

Política: NO restringe el uso del sistema a empresas formales con RUC.
Permite que microempresas con solo cédula también usen Contafy.
"""

# Provincias válidas en Ecuador: 01-24 + 30 (extranjeros)
PROVINCIAS_VALIDAS = set(range(1, 25)) | {30}


def _solo_digitos(s: str) -> bool:
    return bool(s) and s.isdigit()


def _validar_cedula(cedula: str) -> tuple[bool, str]:
    """
    Algoritmo módulo 10 del SRI para cédula ecuatoriana (10 dígitos).

    1. Provincia (2 primeros dígitos) válida
    2. Tercer dígito < 6 (personas naturales)
    3. Multiplicar dígitos 1,3,5,7,9 × 2 — si >9 restar 9
    4. Sumar todos los dígitos resultantes + dígitos 2,4,6,8
    5. Décimo dígito = (10 - (suma % 10)) % 10
    """
    if len(cedula) != 10 or not _solo_digitos(cedula):
        return False, "La cédula debe tener exactamente 10 dígitos."

    provincia = int(cedula[:2])
    if provincia not in PROVINCIAS_VALIDAS:
        return False, f"Provincia inválida ({provincia:02d}). Las provincias válidas son 01-24 y 30."

    tercer_digito = int(cedula[2])
    if tercer_digito >= 6:
        return False, "Tercer dígito inválido para cédula de persona natural (debe ser 0-5)."

    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    suma = 0
    for i, digito in enumerate(cedula[:9]):
        producto = int(digito) * coeficientes[i]
        if producto > 9:
            producto -= 9
        suma += producto

    digito_verificador = (10 - (suma % 10)) % 10
    if digito_verificador != int(cedula[9]):
        return False, "Dígito verificador inválido en la cédula."

    return True, ""


def _validar_ruc_persona_natural(ruc: str) -> tuple[bool, str]:
    """
    RUC Persona Natural (13 dígitos): cédula(10) + '001'.
    Reusa la validación de cédula.
    """
    if len(ruc) != 13 or not _solo_digitos(ruc):
        return False, "El RUC debe tener exactamente 13 dígitos."

    if ruc[10:] != "001":
        return False, "RUC de persona natural debe terminar en '001'."

    return _validar_cedula(ruc[:10])


def _validar_ruc_sociedad(ruc: str, publica: bool = False) -> tuple[bool, str]:
    """
    RUC Sociedad (13 dígitos):
    - Privada: 3er díg = 9, dígito verificador en posición 9, módulo 11
      Coeficientes: 4,3,2,7,6,5,4,3,2
    - Pública:  3er díg = 6, dígito verificador en posición 8, módulo 11
      Coeficientes: 3,2,7,6,5,4,3,2

    Privada: 3 últimos = '001'
    Pública: 4 últimos = '0001'
    """
    if len(ruc) != 13 or not _solo_digitos(ruc):
        return False, "El RUC debe tener exactamente 13 dígitos."

    provincia = int(ruc[:2])
    if provincia not in PROVINCIAS_VALIDAS:
        return False, f"Provincia inválida ({provincia:02d})."

    if publica:
        # Sociedad pública
        if ruc[-4:] != "0001":
            return False, "RUC de sociedad pública debe terminar en '0001'."
        coeficientes = [3, 2, 7, 6, 5, 4, 3, 2]
        cuerpo = ruc[:8]
        digito_verificador_pos = 8
    else:
        # Sociedad privada
        if ruc[-3:] != "001":
            return False, "RUC de sociedad privada debe terminar en '001'."
        coeficientes = [4, 3, 2, 7, 6, 5, 4, 3, 2]
        cuerpo = ruc[:9]
        digito_verificador_pos = 9

    suma = sum(int(d) * c for d, c in zip(cuerpo, coeficientes))
    residuo = suma % 11
    digito_verificador = 0 if residuo == 0 else 11 - residuo

    if digito_verificador != int(ruc[digito_verificador_pos]):
        tipo = "pública" if publica else "privada"
        return False, f"Dígito verificador inválido para RUC de sociedad {tipo}."

    return True, ""


def validar_ruc_ecuador(identificacion: str) -> tuple[bool, str]:
    """
    Punto de entrada principal. Acepta cédula (10 díg) o RUC (13 díg).

    Returns:
        (es_valido: bool, mensaje_error: str)

    Ejemplos:
        >>> validar_ruc_ecuador('1710034065')          # cédula válida
        (True, '')

        >>> validar_ruc_ecuador('1710034065001')       # RUC persona natural válido
        (True, '')

        >>> validar_ruc_ecuador('1790012345001')       # RUC sociedad privada
        (True/False según algoritmo, '')

        >>> validar_ruc_ecuador('1234567890')          # cédula falsa
        (False, 'Dígito verificador inválido en la cédula.')
    """
    if not identificacion:
        return False, "El RUC/Cédula es obligatorio."

    # Limpiar espacios y guiones por si el usuario los pone
    ident = "".join(c for c in str(identificacion) if c.isdigit())

    if not ident:
        return False, "El RUC/Cédula debe contener solo dígitos."

    if len(ident) == 10:
        # Cédula
        return _validar_cedula(ident)

    if len(ident) == 13:
        # RUC — determinar tipo por tercer dígito
        tercer_digito = int(ident[2])

        if tercer_digito < 6:
            # Persona natural (mismo algoritmo de cédula)
            return _validar_ruc_persona_natural(ident)

        if tercer_digito == 6:
            return _validar_ruc_sociedad(ident, publica=True)

        if tercer_digito == 9:
            return _validar_ruc_sociedad(ident, publica=False)

        return False, "Tercer dígito inválido (debe ser 0-5, 6 o 9 según el tipo)."

    return False, "Longitud inválida. Cédula = 10 dígitos, RUC = 13 dígitos."


def tipo_identificacion(identificacion: str) -> str:
    """
    Identifica el tipo de RUC/Cédula sin validar.

    Returns: 'cedula', 'ruc_persona_natural', 'ruc_sociedad_privada',
             'ruc_sociedad_publica', o 'desconocido'
    """
    ident = "".join(c for c in str(identificacion or "") if c.isdigit())

    if len(ident) == 10:
        return 'cedula'
    if len(ident) == 13:
        tercer = int(ident[2]) if ident[2].isdigit() else -1
        if 0 <= tercer < 6:
            return 'ruc_persona_natural'
        if tercer == 6:
            return 'ruc_sociedad_publica'
        if tercer == 9:
            return 'ruc_sociedad_privada'
    return 'desconocido'
