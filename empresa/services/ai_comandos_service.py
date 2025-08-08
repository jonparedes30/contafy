import re
from decimal import Decimal
from datetime import datetime, date, timedelta
from django.db.models import Sum, F
from django.db import models
from empresa.models import (
    Empresa, Producto, CategoriaProducto, Cliente, Proveedor, 
    Venta, Compra, Gasto, MetaFinanciera, CuentaContable,
    MovimientoContable, MateriaPrima, ProductoManufacturado
)

class AIComandosService:
    """Servicio de IA para procesar comandos de texto natural"""
    
    def __init__(self, empresa, usuario):
        self.empresa = empresa
        self.usuario = usuario
    
    def procesar_comando(self, texto):
        """Procesa comando de texto natural y ejecuta acción"""
        texto_original = texto
        texto = texto.lower().strip()
        
        # Detectar si es confirmación
        if any(word in texto for word in ['si', 'sí', 'confirmar', 'ejecutar', 'ok', 'adelante']):
            return {"confirmacion_recibida": True, "mensaje": "Confirmación recibida. Ejecutando acción..."}
        
        if any(word in texto for word in ['no', 'cancelar', 'detener']):
            return {"cancelado": True, "mensaje": "Acción cancelada por el usuario."}
        
        # CREAR PRODUCTOS - mejorado
        if (any(word in texto for word in ['crear', 'añadir', 'agregar', 'generar', 'generame']) and 'producto' in texto) or \
           ('nuevo producto' in texto) or \
           (any(word in texto for word in ['costo', 'pvp']) and any(word in texto for word in ['producto', 'llamar'])):
            return self.crear_producto_desde_texto(texto_original)
        
        # CREAR CATEGORÍAS
        elif any(word in texto for word in ['crear', 'añadir']) and 'categoria' in texto:
            return self.crear_categoria_desde_texto(texto_original)
        
        # CREAR CLIENTES
        elif any(word in texto for word in ['crear', 'añadir']) and 'cliente' in texto:
            return self.crear_cliente_desde_texto(texto_original)
        
        # REGISTRAR VENTAS
        elif 'vender' in texto or 'venta' in texto:
            return self.registrar_venta_desde_texto(texto_original)
        
        # REGISTRAR GASTOS
        elif 'gasto' in texto or 'pagar' in texto:
            return self.registrar_gasto_desde_texto(texto_original)
        
        # GENERAR REPORTES
        elif 'reporte' in texto or 'informe' in texto:
            return self.generar_reporte_desde_texto(texto_original)
        
        # CREAR METAS
        elif 'meta' in texto or 'objetivo' in texto:
            return self.crear_meta_desde_texto(texto_original)
        
        # CONSULTAS
        elif any(word in texto for word in ['cuanto', 'como', 'mostrar', 'ver', 'vendi']):
            return self.consultar_desde_texto(texto_original)
        
        # PROCESOS AUTOMÁTICOS
        elif 'automatizar' in texto or 'proceso' in texto:
            return self.crear_proceso_automatico(texto_original)
        
        else:
            return {"error": "No entendí el comando. Intenta: 'crear producto', 'registrar venta', 'generar reporte', etc."}
    
    def crear_producto_desde_texto(self, texto):
        """Extrae datos y crea producto desde texto natural"""
        try:
            # Extraer datos del producto - mejorado
            nombre_match = re.search(r'(?:producto|llamar[aá]?)\s+["\']?([^"\'\d]+)["\']?', texto)
            if not nombre_match:
                nombre_match = re.search(r'se\s+llamar[aá]?\s+([^\d\$]+)', texto)
            if not nombre_match:
                nombre_match = re.search(r'["\']([^"\']+)["\']', texto)
            
            if nombre_match:
                nombre = nombre_match.group(1).strip()
                # Limpiar palabras innecesarias
                nombre = re.sub(r'\b(que|se|llamara|llamará|costo|pvp|precio|de|con)\b', '', nombre, flags=re.IGNORECASE).strip()
            else:
                nombre = "Producto Nuevo"
            
            # Extraer precio (PVP tiene prioridad)
            pvp_match = re.search(r'pvp\s*[de\s]*[\$]?(\d+(?:\.\d{2})?)', texto)
            precio_match = re.search(r'precio\s*[\$]?(\d+(?:\.\d{2})?)', texto)
            
            if pvp_match:
                precio = Decimal(pvp_match.group(1))
            elif precio_match:
                precio = Decimal(precio_match.group(1))
            else:
                precio = Decimal('15.00')
            
            # Extraer costo si está especificado
            costo_match = re.search(r'costo\s*[de\s]*[\$]?(\d+(?:\.\d{2})?)', texto)
            costo_especificado = Decimal(costo_match.group(1)) if costo_match else None
            
            stock_match = re.search(r'stock\s*(\d+)', texto)
            stock = int(stock_match.group(1)) if stock_match else 50
            
            codigo_match = re.search(r'codigo\s*["\']?([A-Z0-9]+)["\']?', texto)
            if codigo_match:
                codigo = codigo_match.group(1)
            else:
                # Generar código único
                import time
                timestamp = str(int(time.time()))[-4:]  # Últimos 4 dígitos del timestamp
                codigo = f"PROD{timestamp}"
            
            categoria_match = re.search(r'categoria\s*["\']?([^"\']+)["\']?', texto)
            categoria_nombre = categoria_match.group(1).strip() if categoria_match else "General"
            
            # DETECCIÓN DEL TIPO DE EMPRESA PARA CONFIRMACIÓN
            if self.empresa.categoria == 'comercial':
                tipo_mensaje = f"producto comercial '{nombre}' (para reventa) con precio ${precio}, stock {stock} unidades"
            elif self.empresa.categoria == 'manufactura':
                tipo_mensaje = f"producto manufacturado '{nombre}' (requiere receta) con precio ${precio}, stock {stock} unidades"
            else:
                tipo_mensaje = f"servicio '{nombre}' con precio ${precio} (stock ilimitado)"
            
            # CONFIRMACIÓN PREVIA
            return {
                "requiere_confirmacion": True,
                "accion_propuesta": "CREAR_PRODUCTO",
                "mensaje": f"¿Confirmas crear el {tipo_mensaje}, código {codigo} en categoría '{categoria_nombre}' para tu empresa de {self.empresa.categoria}?",
                "datos_pendientes": {
                    "nombre": nombre,
                    "precio": float(precio),
                    "stock": stock,
                    "codigo": codigo,
                    "categoria_nombre": categoria_nombre
                },
                "instruccion": "Responde 'sí' para confirmar o 'no' para cancelar"
            }
            
        except Exception as e:
            return {"error": f"Error procesando datos del producto: {str(e)}"}
    
    def crear_categoria_desde_texto(self, texto):
        """Crea categoría desde texto"""
        try:
            nombre_match = re.search(r'categoria\s*["\']?([^"\']+)["\']?', texto)
            nombre = nombre_match.group(1).strip() if nombre_match else "Nueva Categoría"
            
            categoria, created = CategoriaProducto.objects.get_or_create(
                empresa=self.empresa,
                nombre=nombre,
                defaults={'descripcion': f'Categoría {nombre} creada por IA'}
            )
            
            if created:
                return {
                    "success": True,
                    "mensaje": f"[OK] Categoria creada: {categoria.nombre}"
                }
            else:
                return {
                    "success": False,
                    "mensaje": f"[INFO] La categoria '{nombre}' ya existe"
                }
                
        except Exception as e:
            return {"error": f"Error creando categoría: {str(e)}"}
    
    def crear_cliente_desde_texto(self, texto):
        """Crea cliente desde texto"""
        try:
            # Extraer nombre
            nombre_match = re.search(r'cliente\s*["\']?([^"\']+)["\']?', texto)
            nombre = nombre_match.group(1).strip() if nombre_match else "Cliente Nuevo"
            
            # Extraer documento
            doc_match = re.search(r'(?:cedula|ruc|documento)\s*(\d+)', texto)
            documento = doc_match.group(1) if doc_match else f"999{Cliente.objects.filter(empresa=self.empresa).count() + 1:07d}"
            
            # Extraer teléfono
            tel_match = re.search(r'telefono\s*(\d+)', texto)
            telefono = tel_match.group(1) if tel_match else ""
            
            cliente = Cliente.objects.create(
                empresa=self.empresa,
                nombre=nombre,
                numero_documento=documento,
                telefono=telefono,
                tipo_documento='cedula' if len(documento) == 10 else 'ruc',
                limite_credito=1000
            )
            
            return {
                "success": True,
                "mensaje": f"[OK] Cliente creado: {cliente.nombre}",
                "datos": {
                    "nombre": cliente.nombre,
                    "documento": cliente.numero_documento,
                    "telefono": cliente.telefono
                }
            }
            
        except Exception as e:
            return {"error": f"Error creando cliente: {str(e)}"}
    
    def registrar_venta_desde_texto(self, texto):
        """Registra venta desde texto"""
        try:
            # Extraer producto - mejorado
            producto_match = re.search(r'vender\s+([^\s]+)', texto)
            if not producto_match:
                producto_match = re.search(r'(?:vender|producto)\s*["\']?([^"\']+)["\']?', texto)
            
            if not producto_match:
                return {"error": "No se especificó el producto a vender"}
            
            producto_nombre = producto_match.group(1).strip()
            
            # Buscar producto existente
            producto = Producto.objects.filter(
                empresa=self.empresa,
                nombre__icontains=producto_nombre
            ).first()
            
            # Si no existe, crear automáticamente con stock suficiente
            if not producto:
                precio_default = 15.0  # Precio por defecto más realista
                precio_match = re.search(r'precio\s*[\$]?(\d+(?:\.\d{2})?)', texto)
                if precio_match:
                    precio_default = float(precio_match.group(1))
                
                # Extraer cantidad para asegurar stock suficiente
                cantidad_temp = 1
                cantidad_match = re.search(r'cantidad\s*(\d+)', texto)
                if cantidad_match:
                    cantidad_temp = int(cantidad_match.group(1))
                else:
                    numero_match = re.search(r'\b(\d+)\b', texto)
                    if numero_match:
                        cantidad_temp = int(numero_match.group(1))
                
                stock_inicial = max(100, cantidad_temp * 2)  # Stock suficiente
                
                producto = Producto.objects.create(
                    empresa=self.empresa,
                    nombre=producto_nombre,
                    codigo=f"AUTO{Producto.objects.filter(empresa=self.empresa).count() + 1:03d}",
                    precio_unitario=precio_default * 0.7,
                    pvp=precio_default,
                    stock=stock_inicial,
                    stock_minimo=10
                )
            
            # Extraer cantidad - mejorado
            cantidad_match = re.search(r'cantidad\s*(\d+)', texto)
            if not cantidad_match:
                # Buscar números sueltos que puedan ser cantidad
                numero_match = re.search(r'\b(\d+)\b', texto)
                cantidad = int(numero_match.group(1)) if numero_match else 1
            else:
                cantidad = int(cantidad_match.group(1))
            
            # Extraer cliente
            cliente = None
            cliente_match = re.search(r'cliente\s*["\']?([^"\']+)["\']?', texto)
            if cliente_match:
                cliente_nombre = cliente_match.group(1).strip()
                cliente = Cliente.objects.filter(
                    empresa=self.empresa,
                    nombre__icontains=cliente_nombre
                ).first()
            
            # Verificar stock disponible
            if producto.stock < cantidad:
                return {
                    "error": f"Stock insuficiente. Disponible: {producto.stock}, Solicitado: {cantidad}"
                }
            
            # Crear venta
            venta = Venta.objects.create(
                empresa=self.empresa,
                cliente_fk=cliente,
                cliente_nombre=cliente.nombre if cliente else "Cliente General",
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.pvp,
                monto=producto.pvp * cantidad,
                tipo_pago='contado'
            )
            
            # ACTUALIZAR STOCK AUTOMÁTICAMENTE
            producto.stock -= cantidad
            producto.save()
            
            # GESTIÓN AUTÓNOMA: Si stock queda bajo, generar compra automática
            acciones_autonomas = []
            if producto.stock <= producto.stock_minimo:
                cantidad_compra = producto.stock_minimo * 3  # Comprar para 3 meses
                costo_compra = float(producto.precio_unitario) * cantidad_compra
                
                # Crear compra automática
                compra_auto = Compra.objects.create(
                    empresa=self.empresa,
                    producto=producto,
                    cantidad=cantidad_compra,
                    monto=costo_compra,
                    proveedor_nombre="Proveedor Automático",
                    tipo_pago='credito'
                )
                
                # Actualizar stock con la compra
                producto.stock += cantidad_compra
                producto.save()
                
                acciones_autonomas.append({
                    "accion": "COMPRA_AUTOMATICA",
                    "razon": f"Stock bajo ({producto.stock - cantidad_compra} <= {producto.stock_minimo})",
                    "compra_id": compra_auto.id,
                    "cantidad_comprada": cantidad_compra,
                    "costo": costo_compra,
                    "stock_final": producto.stock
                })
            
            # Verificar que se creó
            venta_verificacion = Venta.objects.filter(id=venta.id).first()
            
            return {
                "success": True,
                "mensaje": f"[CONFIRMADO] Venta registrada: {cantidad}x {producto.nombre} = ${venta.monto} | Stock actualizado: {producto.stock + cantidad} -> {producto.stock}",
                "accion_ejecutada": "VENTA_CREADA_CON_STOCK_ACTUALIZADO",
                "confirmacion": f"Venta ID #{venta.id} creada y stock descontado automáticamente" + (f" | Compra automática generada (ID #{acciones_autonomas[0]['compra_id']})" if acciones_autonomas else ""),
                "datos": {
                    "venta_id": venta.id,
                    "producto": producto.nombre,
                    "codigo_producto": producto.codigo,
                    "cantidad": cantidad,
                    "precio_unitario": float(producto.pvp),
                    "total": float(venta.monto),
                    "cliente": venta.cliente_nombre,
                    "fecha": venta.fecha.strftime('%Y-%m-%d %H:%M'),
                    "stock_antes_venta": (producto.stock + cantidad) if not acciones_autonomas else (producto.stock - acciones_autonomas[0]['cantidad_comprada'] + cantidad),
                    "stock_despues_venta": producto.stock,
                    "stock_descontado": cantidad,
                    "gestion_stock_automatica": True,
                    "acciones_autonomas": acciones_autonomas,
                    "verificado": venta_verificacion is not None
                }
            }
            
        except Exception as e:
            return {"error": f"Error registrando venta: {str(e)}"}
    
    def registrar_gasto_desde_texto(self, texto):
        """Registra gasto desde texto"""
        try:
            # Extraer descripción mejorado
            desc_match = re.search(r'gasto\s*["\']?([^"\'\$\d]+)["\']?', texto)
            if not desc_match:
                desc_match = re.search(r'(?:de|por)\s+([^\$\d]+)', texto)
            
            descripcion = desc_match.group(1).strip() if desc_match else "Gasto registrado por IA"
            descripcion = descripcion.replace('por', '').replace('de', '').strip()
            
            # Extraer monto
            monto_match = re.search(r'[\$]?(\d+(?:\.\d{2})?)', texto)
            if not monto_match:
                return {"error": "No se especificó el monto del gasto"}
            
            monto = Decimal(monto_match.group(1))
            
            # Determinar categoría automáticamente
            categoria = 'Variable'
            if any(word in texto.lower() for word in ['alquiler', 'renta', 'sueldo', 'salario', 'seguro', 'fijo', 'mensual']):
                categoria = 'Fijo'
            
            # CONFIRMACIÓN PREVIA
            return {
                "requiere_confirmacion": True,
                "accion_propuesta": "REGISTRAR_GASTO",
                "mensaje": f"¿Confirmas registrar el gasto '{descripcion}' por ${monto} como gasto {categoria}?",
                "datos_pendientes": {
                    "descripcion": descripcion,
                    "monto": float(monto),
                    "categoria": categoria
                },
                "instruccion": "Responde 'sí' para confirmar o 'no' para cancelar"
            }
            
        except Exception as e:
            return {"error": f"Error procesando gasto: {str(e)}"}
    
    def generar_reporte_desde_texto(self, texto):
        """Genera reportes desde texto"""
        try:
            hoy = date.today()
            mes_actual = hoy.month
            anio_actual = hoy.year
            
            if 'ventas' in texto:
                ventas = Venta.objects.filter(
                    empresa=self.empresa,
                    fecha__month=mes_actual,
                    fecha__year=anio_actual
                )
                total_ventas = ventas.aggregate(total=Sum('monto'))['total'] or 0
                
                return {
                    "success": True,
                    "tipo": "reporte_ventas",
                    "datos": {
                        "total_ventas": float(total_ventas),
                        "cantidad_ventas": ventas.count(),
                        "periodo": f"{mes_actual}/{anio_actual}"
                    }
                }
            
            elif 'gastos' in texto:
                gastos = Gasto.objects.filter(
                    empresa=self.empresa,
                    fecha__month=mes_actual,
                    fecha__year=anio_actual
                )
                total_gastos = gastos.aggregate(total=Sum('monto'))['total'] or 0
                
                return {
                    "success": True,
                    "tipo": "reporte_gastos",
                    "datos": {
                        "total_gastos": float(total_gastos),
                        "cantidad_gastos": gastos.count(),
                        "periodo": f"{mes_actual}/{anio_actual}"
                    }
                }
            
            elif 'balance' in texto or 'resumen' in texto:
                ventas_total = Venta.objects.filter(
                    empresa=self.empresa,
                    fecha__month=mes_actual,
                    fecha__year=anio_actual
                ).aggregate(total=Sum('monto'))['total'] or 0
                
                gastos_total = Gasto.objects.filter(
                    empresa=self.empresa,
                    fecha__month=mes_actual,
                    fecha__year=anio_actual
                ).aggregate(total=Sum('monto'))['total'] or 0
                
                utilidad = ventas_total - gastos_total
                
                return {
                    "success": True,
                    "tipo": "balance_general",
                    "datos": {
                        "ventas": float(ventas_total),
                        "gastos": float(gastos_total),
                        "utilidad": float(utilidad),
                        "periodo": f"{mes_actual}/{anio_actual}"
                    }
                }
            
            else:
                return {"error": "Especifica el tipo de reporte: ventas, gastos o balance"}
                
        except Exception as e:
            return {"error": f"Error generando reporte: {str(e)}"}
    
    def crear_meta_desde_texto(self, texto):
        """Crea meta financiera desde texto"""
        try:
            # Extraer tipo de meta
            tipo = 'ventas'  # default
            if 'gasto' in texto:
                tipo = 'gastos'
            elif 'utilidad' in texto:
                tipo = 'utilidad'
            elif 'cliente' in texto:
                tipo = 'clientes'
            
            # Extraer objetivo
            objetivo_match = re.search(r'[\$]?(\d+(?:\.\d{2})?)', texto)
            if not objetivo_match:
                return {"error": "No se especificó el objetivo de la meta"}
            
            objetivo = Decimal(objetivo_match.group(1))
            
            # Extraer mes (default: actual)
            mes = date.today().month
            anio = date.today().year
            
            meta, created = MetaFinanciera.objects.get_or_create(
                empresa=self.empresa,
                tipo=tipo,
                mes=mes,
                anio=anio,
                defaults={
                    'objetivo_mensual': objetivo,
                    'es_dinamica': True,
                    'alertas_activas': True
                }
            )
            
            if created:
                return {
                    "success": True,
                    "mensaje": f"[OK] Meta creada: {tipo} ${objetivo} para {mes}/{anio}"
                }
            else:
                meta.objetivo_mensual = objetivo
                meta.save()
                return {
                    "success": True,
                    "mensaje": f"[OK] Meta actualizada: {tipo} ${objetivo} para {mes}/{anio}"
                }
                
        except Exception as e:
            return {"error": f"Error creando meta: {str(e)}"}
    
    def consultar_desde_texto(self, texto):
        """Responde consultas desde texto"""
        try:
            if 'stock' in texto:
                productos_bajo_stock = Producto.objects.filter(
                    empresa=self.empresa,
                    stock__lte=models.F('stock_minimo')
                )
                
                if productos_bajo_stock.exists():
                    productos_lista = [f"{p.nombre}: {p.stock} unidades" for p in productos_bajo_stock[:5]]
                    return {
                        "success": True,
                        "mensaje": f"[ALERTA] Productos con stock bajo:\n" + "\n".join(productos_lista)
                    }
                else:
                    return {
                        "success": True,
                        "mensaje": "[OK] Todos los productos tienen stock suficiente"
                    }
            
            elif ('venta' in texto or 'vendi' in texto) and ('hoy' in texto or 'dia' in texto):
                ventas_hoy = Venta.objects.filter(
                    empresa=self.empresa,
                    fecha__date=date.today()
                )
                total = ventas_hoy.aggregate(total=Sum('monto'))['total'] or 0
                
                return {
                    "success": True,
                    "mensaje": f"[VENTAS] Ventas de hoy: ${total} ({ventas_hoy.count()} transacciones)"
                }
            
            elif 'cliente' in texto:
                clientes_count = Cliente.objects.filter(empresa=self.empresa).count()
                return {
                    "success": True,
                    "mensaje": f"[CLIENTES] Tienes {clientes_count} clientes registrados"
                }
            
            else:
                return {"error": "No entendí la consulta. Intenta: 'cuánto stock', 'ventas de hoy', 'cuántos clientes'"}
                
        except Exception as e:
            return {"error": f"Error en consulta: {str(e)}"}
    
    def crear_proceso_automatico(self, texto):
        """Crea procesos automáticos"""
        try:
            if 'stock' in texto and 'bajo' in texto:
                # Simular activación de alertas de stock
                return {
                    "success": True,
                    "mensaje": "[IA] Proceso activado: Alertas automaticas de stock bajo",
                    "proceso": "alertas_stock_bajo"
                }
            
            elif 'recordatorio' in texto and 'cobro' in texto:
                return {
                    "success": True,
                    "mensaje": "[IA] Proceso activado: Recordatorios automaticos de cobros",
                    "proceso": "recordatorios_cobros"
                }
            
            elif 'reporte' in texto and 'mensual' in texto:
                return {
                    "success": True,
                    "mensaje": "[IA] Proceso activado: Reportes mensuales automaticos",
                    "proceso": "reportes_mensuales"
                }
            
            else:
                return {"error": "Procesos disponibles: 'stock bajo', 'recordatorios cobros', 'reportes mensuales'"}
                
        except Exception as e:
            return {"error": f"Error creando proceso: {str(e)}"}

    def ejecutar_accion_confirmada(self, accion_propuesta, datos_pendientes):
        """Ejecuta la acción después de confirmación"""
        try:
            if accion_propuesta == "CREAR_PRODUCTO":
                return self._ejecutar_crear_producto(datos_pendientes)
            elif accion_propuesta == "REGISTRAR_GASTO":
                return self._ejecutar_registrar_gasto(datos_pendientes)
            elif accion_propuesta == "REGISTRAR_VENTA":
                return self._ejecutar_registrar_venta(datos_pendientes)
            else:
                return {"error": f"Acción '{accion_propuesta}' no reconocida"}
        except Exception as e:
            return {"error": f"Error ejecutando acción: {str(e)}"}
    
    def _ejecutar_crear_producto(self, datos):
        """Ejecuta creación de producto confirmada según tipo de empresa"""
        # Crear categoría si no existe
        categoria = None
        if datos['categoria_nombre']:
            categoria, _ = CategoriaProducto.objects.get_or_create(
                empresa=self.empresa,
                nombre=datos['categoria_nombre'],
                defaults={'descripcion': f'Categoría {datos["categoria_nombre"]}'}
            )
        
        # Asegurar código único
        codigo_base = datos['codigo']
        codigo_final = codigo_base
        contador = 1
        
        while Producto.objects.filter(empresa=self.empresa, codigo=codigo_final).exists():
            codigo_final = f"{codigo_base}_{contador}"
            contador += 1
        
        # DETECCIÓN AUTOMÁTICA DEL TIPO DE EMPRESA
        if self.empresa.categoria == 'comercial':
            # EMPRESA DE COMERCIO: Producto simple para reventa
            producto = Producto.objects.create(
                empresa=self.empresa,
                nombre=datos['nombre'],
                codigo=datos['codigo'],
                precio_unitario=Decimal(str(datos['precio'])) * Decimal('0.6'),  # Costo de compra estimado
                pvp=Decimal(str(datos['precio'])),
                stock=datos['stock'],
                categoria=categoria,
                stock_minimo=max(5, datos['stock'] // 5)
            )
            
            tipo_producto = "PRODUCTO_COMERCIO"
            detalles_extra = {
                "tipo_empresa": "Comercio",
                "costo_compra": float(producto.precio_unitario),
                "margen_ganancia": f"{((producto.pvp - producto.precio_unitario) / producto.pvp * 100):.1f}%",
                "listo_para_venta": True
            }
            
        elif self.empresa.categoria == 'manufactura':
            # EMPRESA DE MANUFACTURA: Crear ProductoManufacturado
            from empresa.models import ProductoManufacturado
            
            producto = ProductoManufacturado.objects.create(
                empresa=self.empresa,
                nombre=datos['nombre'],
                codigo=datos['codigo'],
                precio_venta=Decimal(str(datos['precio'])),
                precio_costo=0,  # Se calculará con la receta
                stock_actual=datos['stock'],
                stock_minimo=max(5, datos['stock'] // 5),
                categoria=categoria,
                tiempo_produccion=60  # 1 hora por defecto
            )
            
            tipo_producto = "PRODUCTO_MANUFACTURA"
            detalles_extra = {
                "tipo_empresa": "Manufactura",
                "requiere_receta": True,
                "tiempo_produccion": "60 minutos",
                "costo_pendiente": "Definir receta con materias primas"
            }
            
        else:
            # EMPRESA DE SERVICIOS: Producto como servicio
            producto = Producto.objects.create(
                empresa=self.empresa,
                nombre=datos['nombre'],
                codigo=datos['codigo'],
                precio_unitario=Decimal('0'),  # Servicios no tienen costo de compra
                pvp=Decimal(str(datos['precio'])),
                stock=999,  # Servicios tienen stock "ilimitado"
                categoria=categoria,
                stock_minimo=1
            )
            
            tipo_producto = "SERVICIO"
            detalles_extra = {
                "tipo_empresa": "Servicios",
                "es_servicio": True,
                "stock_ilimitado": True,
                "sin_costo_material": True
            }
        
        # Verificar creación
        if self.empresa.categoria == 'manufactura':
            producto_verificacion = ProductoManufacturado.objects.filter(id=producto.id).first()
        else:
            producto_verificacion = Producto.objects.filter(id=producto.id).first()
        
        return {
            "success": True,
            "mensaje": f"[CONFIRMADO] {tipo_producto.replace('_', ' ').title()} '{producto.nombre}' creado exitosamente para empresa de {self.empresa.categoria}",
            "accion_ejecutada": tipo_producto,
            "confirmacion": f"{tipo_producto.replace('_', ' ').title()} ID #{producto.id} registrado en la base de datos",
            "datos": {
                "producto_id": producto.id,
                "nombre": producto.nombre,
                "codigo": producto.codigo,
                "precio": float(producto.precio_venta if hasattr(producto, 'precio_venta') else producto.pvp),
                "stock": producto.stock_actual if hasattr(producto, 'stock_actual') else producto.stock,
                "categoria": categoria.nombre if categoria else "Sin categoría",
                "verificado": producto_verificacion is not None,
                **detalles_extra
            }
        }
    
    def _ejecutar_registrar_gasto(self, datos):
        """Ejecuta registro de gasto confirmado"""
        gasto = Gasto.objects.create(
            empresa=self.empresa,
            descripcion=datos['descripcion'],
            monto=Decimal(str(datos['monto'])),
            categoria=datos['categoria']
        )
        
        # Verificar creación
        gasto_verificacion = Gasto.objects.filter(id=gasto.id).first()
        
        # GESTIÓN AUTÓNOMA: Verificar si gastos superan umbral
        acciones_autonomas = []
        gastos_mes = Gasto.objects.filter(
            empresa=self.empresa,
            fecha__month=date.today().month
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        if gastos_mes > 5000:  # Umbral de alerta
            acciones_autonomas.append({
                "accion": "ALERTA_GASTOS_ALTOS",
                "razon": f"Gastos mensuales superan ${gastos_mes}",
                "recomendacion": "Revisar gastos no esenciales"
            })
        
        return {
            "success": True,
            "mensaje": f"[CONFIRMADO] Gasto '{datos['descripcion']}' registrado por ${datos['monto']}",
            "accion_ejecutada": "GASTO_REGISTRADO",
            "confirmacion": f"Gasto ID #{gasto.id} registrado en la base de datos",
            "datos": {
                "gasto_id": gasto.id,
                "descripcion": datos['descripcion'],
                "monto": float(datos['monto']),
                "categoria": datos['categoria'],
                "fecha": gasto.fecha.strftime('%Y-%m-%d %H:%M'),
                "gastos_mes_total": float(gastos_mes),
                "acciones_autonomas": acciones_autonomas,
                "verificado": gasto_verificacion is not None
            }
        }

# Variables globales para mantener estado de confirmación
_acciones_pendientes = {}

# Función helper para usar en views
def procesar_comando_ia(empresa, usuario, comando):
    """Función helper para procesar comandos de IA"""
    global _acciones_pendientes
    
    ai_service = AIComandosService(empresa, usuario)
    resultado = ai_service.procesar_comando(comando)
    
    # Si requiere confirmación, guardar en estado
    if resultado.get('requiere_confirmacion'):
        key = f"{empresa.id}_{usuario.id}"
        _acciones_pendientes[key] = {
            'accion_propuesta': resultado['accion_propuesta'],
            'datos_pendientes': resultado['datos_pendientes']
        }
        return resultado
    
    # Si es confirmación, ejecutar acción pendiente
    elif resultado.get('confirmacion_recibida'):
        key = f"{empresa.id}_{usuario.id}"
        if key in _acciones_pendientes:
            accion_data = _acciones_pendientes[key]
            del _acciones_pendientes[key]  # Limpiar estado
            return ai_service.ejecutar_accion_confirmada(
                accion_data['accion_propuesta'],
                accion_data['datos_pendientes']
            )
        else:
            return {"error": "No hay acciones pendientes de confirmación"}
    
    # Si es cancelación
    elif resultado.get('cancelado'):
        key = f"{empresa.id}_{usuario.id}"
        if key in _acciones_pendientes:
            del _acciones_pendientes[key]
        return resultado
    
    return resultado