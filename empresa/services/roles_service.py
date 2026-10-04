"""
Servicio de Roles Predefinidos para empleados.

Define la matriz `ROLES_MATRIX` que mapea cada rol a su set de poderes.
Cuando el dueño asigna un rol a un empleado, automáticamente se configuran
los 19 booleanos de `PoderEmpleado` según este mapeo.

Si el dueño elige 'personalizado', los booleanos se respetan como están
(configuración manual fina).
"""

# Todos los poderes disponibles (orden coincide con campos de PoderEmpleado)
TODOS_LOS_PODERES = [
    # Originales
    'puede_ver_reportes',
    'puede_registrar_ventas',
    'puede_editar_productos',
    'puede_gestionar_cuentas',
    'puede_registrar_gastos',
    'puede_gestionar_inventario',
    'puede_gestionar_metas',
    # Granulares por operación
    'puede_editar_ventas',
    'puede_eliminar_ventas',
    'puede_registrar_compras',
    'puede_editar_compras',
    'puede_eliminar_compras',
    'puede_editar_gastos',
    'puede_eliminar_gastos',
    'puede_eliminar_productos',
    # Nuevos por funcionalidad
    'puede_ver_estados_financieros',
    'puede_gestionar_empleados',
    'puede_exportar_datos',
    'puede_gestionar_proveedores',
    'puede_gestionar_clientes',
]

# Matriz de roles: cada rol → lista de poderes que activa
ROLES_MATRIX = {
    'propietario': TODOS_LOS_PODERES,  # acceso total (en práctica no se usa porque
                                        # @require_owner detecta al dueño automáticamente)

    'gerente': [
        # Todo excepto eliminar empleados (eso solo el propietario)
        'puede_ver_reportes', 'puede_ver_estados_financieros',
        'puede_registrar_ventas', 'puede_editar_ventas', 'puede_eliminar_ventas',
        'puede_registrar_compras', 'puede_editar_compras', 'puede_eliminar_compras',
        'puede_registrar_gastos', 'puede_editar_gastos', 'puede_eliminar_gastos',
        'puede_editar_productos', 'puede_eliminar_productos',
        'puede_gestionar_inventario', 'puede_gestionar_cuentas',
        'puede_gestionar_metas', 'puede_gestionar_proveedores',
        'puede_gestionar_clientes', 'puede_exportar_datos',
        # NO incluye: puede_gestionar_empleados (solo dueño)
    ],

    'contador': [
        # CRUD de transacciones + estados financieros + reportes
        # No gestiona inventario ni productos
        'puede_ver_reportes', 'puede_ver_estados_financieros',
        'puede_registrar_ventas', 'puede_editar_ventas', 'puede_eliminar_ventas',
        'puede_registrar_compras', 'puede_editar_compras', 'puede_eliminar_compras',
        'puede_registrar_gastos', 'puede_editar_gastos', 'puede_eliminar_gastos',
        'puede_gestionar_cuentas', 'puede_exportar_datos',
        'puede_gestionar_proveedores', 'puede_gestionar_clientes',
    ],

    'vendedor': [
        # Crear ventas + ver inventario (sin editar/eliminar)
        'puede_registrar_ventas',
        # NO incluye: editar/eliminar ventas, productos, gastos, etc.
    ],

    'bodeguero': [
        # Gestión de inventario y productos
        'puede_gestionar_inventario',
        'puede_editar_productos',
        # NO incluye eliminar_productos (más restrictivo)
    ],

    'comprador': [
        # CRUD compras + gestión de proveedores
        'puede_registrar_compras', 'puede_editar_compras', 'puede_eliminar_compras',
        'puede_gestionar_proveedores',
    ],

    'auditor': [
        # Solo lectura: reportes + estados financieros + actividad
        # NO puede modificar nada
        'puede_ver_reportes', 'puede_ver_estados_financieros',
        'puede_exportar_datos',
    ],

    'personalizado': None,  # marcador especial: no tocar los booleanos individuales
}


def descripcion_rol(rol_clave: str) -> str:
    """Devuelve descripción amigable del rol."""
    descripciones = {
        'propietario':   'Acceso total al sistema. No requiere configuración de poderes.',
        'gerente':       'Puede hacer todo excepto gestionar empleados y eliminar la empresa.',
        'contador':      'Maneja ventas, compras, gastos, reportes y estados financieros. Sin acceso a productos/inventario.',
        'vendedor':      'Solo puede registrar ventas. Útil para cajeros — no puede editarlas ni eliminarlas.',
        'bodeguero':     'Gestiona inventario y productos. No tiene acceso a transacciones financieras.',
        'comprador':     'Maneja compras y proveedores. No tiene acceso a ventas ni gastos.',
        'auditor':       'Solo lectura: ve reportes, estados financieros y actividad. No puede modificar datos.',
        'personalizado': 'Configuración manual fina de cada poder individual.',
    }
    return descripciones.get(rol_clave, '')


def aplicar_rol(poder_empleado, rol_clave: str) -> 'PoderEmpleado':
    """
    Configura los 19 booleanos del PoderEmpleado según el rol elegido.

    Args:
        poder_empleado: instancia de PoderEmpleado (puede no estar guardada)
        rol_clave: uno de ROLES_MATRIX keys

    Returns:
        El mismo poder_empleado modificado (no se guarda automáticamente).

    Comportamiento:
        - Si rol == 'personalizado': no toca los booleanos (usa lo que ya están)
        - Si rol == 'propietario': activa TODO (acceso total)
        - Para los demás roles: activa solo los poderes listados, desactiva el resto
    """
    poder_empleado.rol = rol_clave

    poderes_activos = ROLES_MATRIX.get(rol_clave)

    # 'personalizado' → no tocar, respetar los booleanos manuales
    if poderes_activos is None:
        return poder_empleado

    # Aplicar matriz: activar lo que está en la lista, desactivar el resto
    for poder in TODOS_LOS_PODERES:
        setattr(poder_empleado, poder, poder in poderes_activos)

    return poder_empleado


def poderes_del_rol(rol_clave: str) -> list:
    """Devuelve la lista de poderes que activa un rol (útil para UI)."""
    return ROLES_MATRIX.get(rol_clave, []) or []
