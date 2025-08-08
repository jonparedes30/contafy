# empresa/utils/normalizador.py

def normalizar_provincia(provincia):
    """Normaliza nombres de provincia para benchmarking"""
    mapeo_provincias = {
        'pichincha': ['pichincha', 'quito'],
        'guayas': ['guayas', 'guayaquil'],
        'azuay': ['azuay', 'cuenca'],
        'manabi': ['manabí', 'manabi', 'manta', 'portoviejo'],
        'tungurahua': ['tungurahua', 'ambato'],
        'el_oro': ['el oro', 'machala'],
        'imbabura': ['imbabura', 'ibarra'],
        'loja': ['loja'],
        'chimborazo': ['chimborazo', 'riobamba'],
        'cotopaxi': ['cotopaxi', 'latacunga'],
        'otros': []
    }
    
    if not provincia:
        return 'otros'
    
    provincia_lower = provincia.lower().strip()
    
    for provincia_norm, variantes in mapeo_provincias.items():
        if provincia_norm == 'otros':
            continue
        if provincia_lower in variantes or provincia_lower == provincia_norm:
            return provincia_norm
    
    return 'otros'


def normalizar_tipo_negocio(tipo_negocio, categoria):
    """
    Normaliza el tipo de negocio para benchmarking
    Agrupa tipos similares bajo categorías estándar
    """
    if not tipo_negocio:
        return 'otros'
    
    tipo_lower = tipo_negocio.lower().strip()
    
    # Mapeo de normalización por categoría
    mapeo_comercial = {
        'licoreria': ['licorería', 'licoreria', 'venta de licores', 'bebidas alcohólicas'],
        'farmacia': ['farmacia', 'botica', 'droguería', 'medicamentos'],
        'minimarket': ['minimarket', 'mini market', 'tienda', 'abarrotes', 'viveres'],
        'ferreteria': ['ferretería', 'ferreteria', 'materiales construcción', 'herramientas'],
        'ropa': ['ropa', 'vestimenta', 'confección', 'textiles', 'moda'],
        'electrodomesticos': ['electrodomésticos', 'electrónicos', 'tecnología'],
        'otros': []
    }
    
    mapeo_manufactura = {
        'panaderia': ['panadería', 'panaderia', 'pan', 'repostería', 'pastelería'],
        'carpinteria': ['carpintería', 'carpinteria', 'muebles', 'madera'],
        'herreria': ['herrería', 'herreria', 'metal', 'soldadura'],
        'alimentos': ['alimentos', 'comida', 'procesadora', 'bebidas', 'dulces'],
        'textil': ['textil', 'confección', 'ropa', 'costura'],
        'artesanias': ['artesanías', 'artesanias', 'manualidades', 'cerámica'],
        'otros': []
    }
    
    mapeo_servicios = {
        'salud': ['médico', 'dental', 'consultorio', 'clínica', 'veterinaria'],
        'belleza': ['peluquería', 'belleza', 'estética', 'spa'],
        'mecanico': ['mecánico', 'automotriz', 'taller mecánico'],
        'restauracion': ['restaurante', 'cafetería', 'comida', 'bar'],
        'limpieza': ['limpieza', 'lavandería', 'mantenimiento'],
        'educacion': ['academia', 'educación', 'enseñanza', 'guardería'],
        'consultoria': ['consultoría', 'contable', 'asesoría', 'legal'],
        'otros': []
    }
    
    # Seleccionar mapeo según categoría
    if categoria == 'comercial':
        mapeo = mapeo_comercial
    elif categoria == 'manufactura':
        mapeo = mapeo_manufactura
    elif categoria == 'servicios':
        mapeo = mapeo_servicios
    else:
        return 'otros'
    
    # Buscar coincidencia
    for categoria_normalizada, palabras_clave in mapeo.items():
        if categoria_normalizada == 'otros':
            continue
        for palabra in palabras_clave:
            if palabra in tipo_lower:
                return categoria_normalizada
    
    return 'otros'


def obtener_categoria_benchmarking(empresa):
    """
    Obtiene la categoría normalizada para benchmarking
    """
    return normalizar_tipo_negocio(empresa.tipo_negocio, empresa.categoria)


def obtener_ubicacion_benchmarking(empresa):
    """
    Obtiene la ubicación normalizada para benchmarking
    """
    return {
        'provincia': normalizar_provincia(empresa.provincia),
        'ciudad': empresa.ciudad.lower().strip() if empresa.ciudad else 'otros',
        'latitud': float(empresa.latitud) if empresa.latitud else None,
        'longitud': float(empresa.longitud) if empresa.longitud else None
    }


def calcular_distancia_km(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia entre dos puntos GPS en kilómetros
    Usa la fórmula de Haversine
    """
    import math
    
    if not all([lat1, lon1, lat2, lon2]):
        return None
    
    # Radio de la Tierra en km
    R = 6371.0
    
    # Convertir grados a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferencias
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula de Haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def obtener_empresas_cercanas(empresa, radio_km=10):
    """
    Obtiene empresas cercanas dentro del radio especificado
    """
    if not (empresa.latitud and empresa.longitud):
        return []
    
    from empresa.models import Empresa
    
    empresas_cercanas = []
    empresas_con_gps = Empresa.objects.filter(
        latitud__isnull=False, 
        longitud__isnull=False
    ).exclude(id=empresa.id)
    
    for otra_empresa in empresas_con_gps:
        distancia = calcular_distancia_km(
            float(empresa.latitud), float(empresa.longitud),
            float(otra_empresa.latitud), float(otra_empresa.longitud)
        )
        
        if distancia and distancia <= radio_km:
            empresas_cercanas.append({
                'empresa': otra_empresa,
                'distancia_km': round(distancia, 2)
            })
    
    # Ordenar por distancia
    return sorted(empresas_cercanas, key=lambda x: x['distancia_km'])