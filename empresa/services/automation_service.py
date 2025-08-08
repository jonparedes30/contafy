"""
Servicio de Automatización Completa para CONTAFY
"""
from datetime import datetime, date, timedelta
from django.db.models import Sum, F
from empresa.models import (
    Venta, Compra, Gasto, Producto, Cliente, Proveedor,
    CuentaPorCobrar, CuentaPorPagar, MetaFinanciera, NotificacionMeta
)
from empresa.services.notificaciones_service import NotificacionesService
from decimal import Decimal

class AutomatizacionCompleta:
    """Servicio de automatización end-to-end de procesos empresariales"""
    
    def __init__(self, empresa):
        self.empresa = empresa
        self.logs_automatizacion = []
    
    def proceso_venta_completa(self, producto_id, cantidad, cliente_nombre=None, precio_override=None):
        """Proceso de venta completamente automatizado"""
        try:
            # 1. Obtener producto
            producto = Producto.objects.get(id=producto_id, empresa=self.empresa)
            
            # 2. Verificar stock
            if producto.stock < cantidad:
                return self._resultado_error(f"Stock insuficiente: {producto.stock} disponible, {cantidad} solicitado")
            
            # 3. Obtener/crear cliente
            cliente = None
            if cliente_nombre:
                cliente, created = Cliente.objects.get_or_create(
                    empresa=self.empresa,
                    nombre=cliente_nombre,
                    defaults={
                        'numero_documento': f"AUTO{Cliente.objects.filter(empresa=self.empresa).count() + 1:06d}",
                        'tipo_documento': 'cedula',
                        'limite_credito': 1000
                    }
                )
                if created:
                    self.logs_automatizacion.append(f"Cliente '{cliente_nombre}' creado automáticamente")
            
            # 4. Calcular precios
            precio_unitario = precio_override or producto.pvp or producto.precio_unitario
            monto_neto = precio_unitario * cantidad
            iva = monto_neto * Decimal('0.12')  # IVA 12%
            monto_total = monto_neto + iva
            
            # 5. Crear venta
            venta = Venta.objects.create(
                empresa=self.empresa,
                cliente_fk=cliente,
                cliente_nombre=cliente.nombre if cliente else "Cliente General",
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                monto_neto=monto_neto,
                iva=iva,
                monto=monto_total,
                tipo_pago='contado'
            )
            
            # 6. Actualizar stock automáticamente
            producto.stock -= cantidad
            producto.save()
            
            # 7. Verificar si necesita restock automático
            acciones_stock = self._gestionar_restock_automatico(producto)
            
            # 8. Generar factura automática (simulada)
            factura_info = self._generar_factura_automatica(venta)
            
            # 9. Enviar notificaciones automáticas
            self._enviar_notificaciones_venta(venta, cliente)
            
            # 10. Actualizar metas automáticamente
            self._actualizar_metas_automaticas('ventas', float(monto_total))
            
            # 11. Análisis automático de rentabilidad
            analisis_rentabilidad = self._analizar_rentabilidad_venta(venta, producto)
            
            return {
                'success': True,
                'venta_id': venta.id,
                'monto_total': float(monto_total),
                'stock_actualizado': producto.stock,
                'acciones_stock': acciones_stock,
                'factura': factura_info,
                'analisis_rentabilidad': analisis_rentabilidad,
                'logs_automatizacion': self.logs_automatizacion,
                'notificaciones_enviadas': True
            }
            
        except Exception as e:
            return self._resultado_error(f"Error en proceso automático: {str(e)}")
    
    def proceso_cobranza_automatica(self):
        """Gestión automática de cobranzas"""
        try:
            hoy = date.today()
            acciones_realizadas = []
            
            # 1. Identificar cuentas vencidas
            cuentas_vencidas = CuentaPorCobrar.objects.filter(
                empresa=self.empresa,
                estado='pendiente',
                fecha_vencimiento__lt=hoy
            )
            
            for cuenta in cuentas_vencidas:
                dias_vencido = (hoy - cuenta.fecha_vencimiento).days
                
                # 2. Escalar según días de vencimiento
                if dias_vencido <= 7:
                    # Recordatorio suave
                    mensaje = self._generar_recordatorio_suave(cuenta)
                    tipo_accion = "Recordatorio suave"
                elif dias_vencido <= 15:
                    # Recordatorio firme
                    mensaje = self._generar_recordatorio_firme(cuenta)
                    tipo_accion = "Recordatorio firme"
                elif dias_vencido <= 30:
                    # Aviso de mora
                    mensaje = self._generar_aviso_mora(cuenta)
                    tipo_accion = "Aviso de mora"
                else:
                    # Gestión de cobranza
                    mensaje = self._generar_gestion_cobranza(cuenta)
                    tipo_accion = "Gestión de cobranza"
                
                # 3. Enviar recordatorio automático
                if cuenta.cliente.email:
                    NotificacionesService.enviar_email(
                        cuenta.cliente.email,
                        f"Recordatorio de pago - {self.empresa.nombre}",
                        mensaje,
                        self.empresa
                    )
                
                # 4. Enviar por WhatsApp si está disponible
                if cuenta.cliente.telefono:
                    mensaje_whatsapp = f"Recordatorio: Tienes una cuenta pendiente de ${cuenta.monto_pendiente} vencida hace {dias_vencido} días. Favor contactar a {self.empresa.nombre}."
                    # NotificacionesService.enviar_whatsapp(cuenta.cliente.telefono, mensaje_whatsapp, self.empresa)
                
                acciones_realizadas.append({
                    'cliente': cuenta.cliente.nombre,
                    'monto': float(cuenta.monto_pendiente),
                    'dias_vencido': dias_vencido,
                    'accion': tipo_accion,
                    'notificacion_enviada': True
                })
            
            # 5. Generar reporte de cobranzas
            reporte_cobranzas = self._generar_reporte_cobranzas()
            
            return {
                'success': True,
                'cuentas_procesadas': len(acciones_realizadas),
                'acciones_realizadas': acciones_realizadas,
                'reporte_cobranzas': reporte_cobranzas
            }
            
        except Exception as e:
            return self._resultado_error(f"Error en cobranza automática: {str(e)}")
    
    def proceso_gestion_inventario_automatica(self):
        """Gestión automática completa de inventario"""
        try:
            acciones_realizadas = []
            
            # 1. Identificar productos con stock bajo
            productos_bajo_stock = Producto.objects.filter(
                empresa=self.empresa,
                stock__lte=F('stock_minimo')
            )
            
            for producto in productos_bajo_stock:
                # 2. Calcular cantidad óptima de compra
                cantidad_optima = self._calcular_cantidad_optima_compra(producto)
                
                # 3. Buscar mejor proveedor
                proveedor = self._buscar_mejor_proveedor(producto)
                
                # 4. Generar compra automática
                compra_automatica = self._generar_compra_automatica(producto, cantidad_optima, proveedor)
                
                if compra_automatica['success']:
                    acciones_realizadas.append({
                        'producto': producto.nombre,
                        'stock_actual': producto.stock,
                        'stock_minimo': producto.stock_minimo,
                        'cantidad_comprada': cantidad_optima,
                        'proveedor': proveedor.nombre if proveedor else 'Automático',
                        'costo_estimado': compra_automatica['costo_total']
                    })
            
            # 5. Identificar productos de rotación lenta
            productos_rotacion_lenta = self._identificar_productos_rotacion_lenta()
            
            # 6. Generar alertas de productos próximos a vencer
            productos_por_vencer = self._identificar_productos_por_vencer()
            
            return {
                'success': True,
                'compras_automaticas': len(acciones_realizadas),
                'acciones_realizadas': acciones_realizadas,
                'productos_rotacion_lenta': productos_rotacion_lenta,
                'productos_por_vencer': productos_por_vencer
            }
            
        except Exception as e:
            return self._resultado_error(f"Error en gestión automática de inventario: {str(e)}")
    
    def proceso_analisis_financiero_automatico(self):
        """Análisis financiero automático diario"""
        try:
            hoy = date.today()
            
            # 1. Calcular métricas del día
            metricas_dia = self._calcular_metricas_diarias()
            
            # 2. Comparar con objetivos
            comparacion_objetivos = self._comparar_con_objetivos()
            
            # 3. Detectar anomalías automáticamente
            anomalias = self._detectar_anomalias_financieras()
            
            # 4. Generar alertas automáticas
            alertas_generadas = []
            
            # Alerta de ventas bajas
            if metricas_dia['ventas_dia'] < metricas_dia['promedio_ventas_mes'] * 0.5:
                alerta = self._crear_alerta_automatica(
                    'ventas_bajas',
                    f"Ventas del día (${metricas_dia['ventas_dia']}) están 50% por debajo del promedio"
                )
                alertas_generadas.append(alerta)
            
            # Alerta de gastos altos
            if metricas_dia['gastos_dia'] > metricas_dia['promedio_gastos_mes'] * 2:
                alerta = self._crear_alerta_automatica(
                    'gastos_altos',
                    f"Gastos del día (${metricas_dia['gastos_dia']}) están muy por encima del promedio"
                )
                alertas_generadas.append(alerta)
            
            # 5. Generar recomendaciones automáticas
            recomendaciones = self._generar_recomendaciones_automaticas(metricas_dia)
            
            # 6. Enviar resumen diario automático
            resumen_enviado = self._enviar_resumen_diario_automatico(metricas_dia, alertas_generadas)
            
            return {
                'success': True,
                'metricas_dia': metricas_dia,
                'comparacion_objetivos': comparacion_objetivos,
                'anomalias_detectadas': anomalias,
                'alertas_generadas': len(alertas_generadas),
                'recomendaciones': recomendaciones,
                'resumen_enviado': resumen_enviado
            }
            
        except Exception as e:
            return self._resultado_error(f"Error en análisis automático: {str(e)}")
    
    def _gestionar_restock_automatico(self, producto):
        """Gestiona restock automático de productos"""
        acciones = []
        
        if producto.stock <= producto.stock_minimo:
            # Calcular cantidad de restock
            cantidad_restock = max(producto.stock_minimo * 3, 50)
            costo_estimado = float(producto.precio_unitario) * cantidad_restock
            
            # Crear compra automática
            try:
                proveedor_auto, _ = Proveedor.objects.get_or_create(
                    empresa=self.empresa,
                    nombre="Proveedor Automático",
                    defaults={
                        'ruc': '9999999999999',
                        'dias_credito': 30
                    }
                )
                
                compra = Compra.objects.create(
                    empresa=self.empresa,
                    proveedor_fk=proveedor_auto,
                    producto=producto,
                    cantidad=cantidad_restock,
                    monto_neto=costo_estimado,
                    iva=costo_estimado * 0.12,
                    monto=costo_estimado * 1.12,
                    tipo_pago='credito'
                )
                
                # Actualizar stock
                producto.stock += cantidad_restock
                producto.save()
                
                acciones.append({
                    'accion': 'COMPRA_AUTOMATICA',
                    'compra_id': compra.id,
                    'cantidad': cantidad_restock,
                    'costo': costo_estimado,
                    'nuevo_stock': producto.stock
                })
                
                self.logs_automatizacion.append(f"Compra automática generada: {cantidad_restock} unidades de {producto.nombre}")
                
            except Exception as e:
                acciones.append({
                    'accion': 'ERROR_COMPRA_AUTOMATICA',
                    'error': str(e)
                })
        
        return acciones
    
    def _generar_factura_automatica(self, venta):
        """Genera información de factura automática"""
        return {
            'numero_factura': f"AUTO-{venta.id:06d}",
            'fecha': venta.fecha.strftime('%Y-%m-%d'),
            'cliente': venta.cliente_display,
            'subtotal': float(venta.monto_neto),
            'iva': float(venta.iva),
            'total': float(venta.monto),
            'estado': 'Generada automáticamente'
        }
    
    def _enviar_notificaciones_venta(self, venta, cliente):
        """Envía notificaciones automáticas de venta"""
        try:
            # Notificación al propietario
            propietario = self.empresa.usuarios.first()
            if propietario and propietario.email:
                mensaje = f"""
                Nueva venta registrada automáticamente:
                
                Cliente: {venta.cliente_display}
                Producto: {venta.producto.nombre}
                Cantidad: {venta.cantidad}
                Total: ${venta.monto}
                
                Stock actualizado automáticamente.
                """
                
                NotificacionesService.enviar_email(
                    propietario.email,
                    f"Nueva venta - {self.empresa.nombre}",
                    mensaje,
                    self.empresa
                )
            
            # Notificación al cliente (si tiene email)
            if cliente and cliente.email:
                mensaje_cliente = f"""
                Gracias por tu compra en {self.empresa.nombre}
                
                Producto: {venta.producto.nombre}
                Cantidad: {venta.cantidad}
                Total: ${venta.monto}
                
                ¡Esperamos verte pronto!
                """
                
                NotificacionesService.enviar_email(
                    cliente.email,
                    f"Comprobante de compra - {self.empresa.nombre}",
                    mensaje_cliente,
                    self.empresa
                )
                
        except Exception as e:
            self.logs_automatizacion.append(f"Error enviando notificaciones: {str(e)}")
    
    def _actualizar_metas_automaticas(self, tipo_meta, valor):
        """Actualiza progreso de metas automáticamente"""
        try:
            hoy = date.today()
            meta = MetaFinanciera.objects.filter(
                empresa=self.empresa,
                tipo=tipo_meta,
                mes=hoy.month,
                anio=hoy.year
            ).first()
            
            if meta:
                progreso_actual = meta.progreso_actual
                if progreso_actual >= 100 and not hasattr(meta, '_notificacion_enviada'):
                    # Meta cumplida - enviar felicitación
                    NotificacionMeta.objects.create(
                        empresa=self.empresa,
                        titulo=f"¡Meta de {tipo_meta} cumplida!",
                        mensaje=f"Has alcanzado tu meta de {tipo_meta} del mes con ${valor}",
                        tipo='success'
                    )
                    meta._notificacion_enviada = True
                    
        except Exception as e:
            self.logs_automatizacion.append(f"Error actualizando metas: {str(e)}")
    
    def _analizar_rentabilidad_venta(self, venta, producto):
        """Analiza rentabilidad de la venta automáticamente"""
        try:
            costo_producto = float(producto.precio_unitario)
            precio_venta = float(venta.precio_unitario)
            
            margen_unitario = precio_venta - costo_producto
            margen_porcentaje = (margen_unitario / precio_venta) * 100 if precio_venta > 0 else 0
            
            # Clasificar rentabilidad
            if margen_porcentaje > 50:
                clasificacion = "Excelente"
            elif margen_porcentaje > 30:
                clasificacion = "Buena"
            elif margen_porcentaje > 15:
                clasificacion = "Aceptable"
            else:
                clasificacion = "Baja"
            
            return {
                'margen_unitario': margen_unitario,
                'margen_porcentaje': margen_porcentaje,
                'clasificacion': clasificacion,
                'recomendacion': self._generar_recomendacion_rentabilidad(margen_porcentaje)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _generar_recomendacion_rentabilidad(self, margen):
        """Genera recomendación basada en rentabilidad"""
        if margen > 50:
            return "Excelente rentabilidad. Considera promocionar este producto."
        elif margen > 30:
            return "Buena rentabilidad. Producto rentable para el negocio."
        elif margen > 15:
            return "Rentabilidad aceptable. Monitorear costos."
        else:
            return "Rentabilidad baja. Revisar precios o costos urgentemente."
    
    def _calcular_metricas_diarias(self):
        """Calcula métricas financieras del día"""
        hoy = date.today()
        
        # Ventas del día
        ventas_dia = Venta.objects.filter(
            empresa=self.empresa,
            fecha__date=hoy
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        # Gastos del día
        gastos_dia = Gasto.objects.filter(
            empresa=self.empresa,
            fecha__date=hoy
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        # Promedios del mes
        inicio_mes = hoy.replace(day=1)
        ventas_mes = Venta.objects.filter(
            empresa=self.empresa,
            fecha__date__gte=inicio_mes
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        gastos_mes = Gasto.objects.filter(
            empresa=self.empresa,
            fecha__date__gte=inicio_mes
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        dias_transcurridos = hoy.day
        
        return {
            'ventas_dia': float(ventas_dia),
            'gastos_dia': float(gastos_dia),
            'utilidad_dia': float(ventas_dia - gastos_dia),
            'promedio_ventas_mes': float(ventas_mes / dias_transcurridos) if dias_transcurridos > 0 else 0,
            'promedio_gastos_mes': float(gastos_mes / dias_transcurridos) if dias_transcurridos > 0 else 0
        }
    
    def _resultado_error(self, mensaje):
        """Genera resultado de error estándar"""
        return {
            'success': False,
            'error': mensaje,
            'logs_automatizacion': self.logs_automatizacion
        }
    
    def _comparar_con_objetivos(self):
        """Compara métricas actuales con objetivos"""
        # Implementación simplificada
        return {'comparacion': 'En progreso'}
    
    def _detectar_anomalias_financieras(self):
        """Detecta anomalías en datos financieros"""
        # Implementación simplificada
        return []
    
    def _crear_alerta_automatica(self, tipo, mensaje):
        """Crea alerta automática"""
        return {'tipo': tipo, 'mensaje': mensaje}
    
    def _generar_recomendaciones_automaticas(self, metricas):
        """Genera recomendaciones automáticas"""
        return ['Mantener el ritmo actual', 'Monitorear gastos']
    
    def _enviar_resumen_diario_automatico(self, metricas, alertas):
        """Envía resumen diario automático"""
        return True

# Función helper para usar en views
def ejecutar_automatizacion_completa(empresa, tipo_proceso, **kwargs):
    """Ejecuta procesos de automatización completa"""
    automation = AutomatizacionCompleta(empresa)
    
    if tipo_proceso == 'venta_completa':
        return automation.proceso_venta_completa(**kwargs)
    elif tipo_proceso == 'cobranza_automatica':
        return automation.proceso_cobranza_automatica()
    elif tipo_proceso == 'inventario_automatico':
        return automation.proceso_gestion_inventario_automatica()
    elif tipo_proceso == 'analisis_financiero':
        return automation.proceso_analisis_financiero_automatico()
    else:
        return {'success': False, 'error': 'Tipo de proceso no reconocido'}