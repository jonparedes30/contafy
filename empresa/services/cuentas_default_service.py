"""
Servicio para gestionar cuentas contables por defecto según tipo de empresa
"""

class CuentasDefaultService:
    
    @staticmethod
    def obtener_cuentas_default(tipo_empresa):
        """Obtiene las cuentas contables por defecto según el tipo de empresa"""
        
        cuentas_base = [
            # ACTIVOS
            {'nombre': 'Caja', 'tipo': 'activo', 'categoria': 'corriente'},
            {'nombre': 'Bancos', 'tipo': 'activo', 'categoria': 'corriente'},
            {'nombre': 'Cuentas por Cobrar', 'tipo': 'activo', 'categoria': 'corriente'},
            
            # PASIVOS
            {'nombre': 'Cuentas por Pagar', 'tipo': 'pasivo', 'categoria': 'corriente'},
            {'nombre': 'IVA por Pagar', 'tipo': 'pasivo', 'categoria': 'corriente'},
            
            # PATRIMONIO
            {'nombre': 'Capital Social', 'tipo': 'capital', 'categoria': 'patrimonio'},
            {'nombre': 'Utilidades Retenidas', 'tipo': 'capital', 'categoria': 'patrimonio'},
            
            # INGRESOS
            {'nombre': 'Ventas', 'tipo': 'ingreso', 'categoria': 'operacional'},
            
            # GASTOS
            {'nombre': 'Gastos Administrativos', 'tipo': 'gasto', 'categoria': 'operacional'},
            {'nombre': 'Gastos de Ventas', 'tipo': 'gasto', 'categoria': 'operacional'},
        ]
        
        if tipo_empresa == 'comercial':
            cuentas_especificas = [
                {'nombre': 'Inventario', 'tipo': 'activo', 'categoria': 'corriente'},
                {'nombre': 'Costo de Ventas', 'tipo': 'gasto', 'categoria': 'operacional'},
                {'nombre': 'Descuentos en Ventas', 'tipo': 'gasto', 'categoria': 'operacional'},
            ]
        elif tipo_empresa == 'manufactura':
            cuentas_especificas = [
                {'nombre': 'Inventario Materias Primas', 'tipo': 'activo', 'categoria': 'corriente'},
                {'nombre': 'Inventario Productos en Proceso', 'tipo': 'activo', 'categoria': 'corriente'},
                {'nombre': 'Inventario Productos Terminados', 'tipo': 'activo', 'categoria': 'corriente'},
                {'nombre': 'Mano de Obra Directa', 'tipo': 'gasto', 'categoria': 'produccion'},
                {'nombre': 'Costos Indirectos de Fabricación', 'tipo': 'gasto', 'categoria': 'produccion'},
                {'nombre': 'Maquinaria y Equipo', 'tipo': 'activo', 'categoria': 'fijo'},
            ]
        elif tipo_empresa == 'servicios':
            cuentas_especificas = [
                {'nombre': 'Ingresos por Servicios', 'tipo': 'ingreso', 'categoria': 'operacional'},
                {'nombre': 'Gastos de Personal', 'tipo': 'gasto', 'categoria': 'operacional'},
                {'nombre': 'Equipos de Oficina', 'tipo': 'activo', 'categoria': 'fijo'},
                {'nombre': 'Gastos de Capacitación', 'tipo': 'gasto', 'categoria': 'operacional'},
            ]
        else:
            cuentas_especificas = []
        
        return cuentas_base + cuentas_especificas
    
    @staticmethod
    def crear_cuentas_default(empresa):
        """Crea las cuentas por defecto para una empresa nueva"""
        from empresa.models import CuentaContable
        
        cuentas_default = CuentasDefaultService.obtener_cuentas_default(empresa.categoria)
        cuentas_creadas = []
        
        for cuenta_data in cuentas_default:
            cuenta, created = CuentaContable.objects.get_or_create(
                empresa=empresa,
                nombre=cuenta_data['nombre'],
                defaults={
                    'tipo': cuenta_data['tipo']
                }
            )
            if created:
                cuentas_creadas.append(cuenta)
        
        return cuentas_creadas
    
    @staticmethod
    def obtener_contrapartidas_sugeridas(tipo_cuenta, tipo_empresa):
        """Obtiene contrapartidas sugeridas según el tipo de cuenta que se está creando"""
        
        sugerencias = {
            'activo': [
                'Capital Social',
                'Bancos', 
                'Cuentas por Pagar',
                'Utilidades Retenidas'
            ],
            'pasivo': [
                'Caja',
                'Bancos',
                'Capital Social'
            ],
            'capital': [
                'Caja',
                'Bancos',
                'Inventario' if tipo_empresa == 'comercial' else 'Equipos de Oficina'
            ],
            'ingreso': [
                'Caja',
                'Bancos',
                'Cuentas por Cobrar'
            ],
            'gasto': [
                'Caja',
                'Bancos',
                'Cuentas por Pagar'
            ]
        }
        
        return sugerencias.get(tipo_cuenta, ['Caja', 'Bancos', 'Capital Social'])