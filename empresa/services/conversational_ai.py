"""
Servicio de IA Conversacional Avanzada para CONTAFY
"""
import json
import re
from datetime import datetime, date, timedelta
from django.core.cache import cache
from empresa.models import Venta, Gasto, Producto, Cliente, MetaFinanciera
from empresa.services.ml_service import MLService
from empresa.services.predicciones_service import PrediccionesAvanzadas
from empresa.services.automation_service import AutomatizacionCompleta

class ConversationalAI:
    """IA Conversacional con contexto y memoria de conversaciones"""
    
    def __init__(self, empresa, usuario):
        self.empresa = empresa
        self.usuario = usuario
        self.contexto_key = f"contexto_conversacion_{empresa.id}_{usuario.id}"
        self.contexto = self._cargar_contexto()
        
    def procesar_consulta_compleja(self, pregunta):
        """Procesa consultas complejas multi-paso"""
        try:
            # Actualizar contexto con nueva pregunta
            self._actualizar_contexto(pregunta)
            
            # Detectar tipo de consulta
            tipo_consulta = self._detectar_tipo_consulta(pregunta)
            
            # Procesar según tipo
            if tipo_consulta == 'analisis_multifactor':
                return self._procesar_analisis_multifactor(pregunta)
            elif tipo_consulta == 'planificacion_estrategica':
                return self._procesar_planificacion_estrategica(pregunta)
            elif tipo_consulta == 'comparacion_temporal':
                return self._procesar_comparacion_temporal(pregunta)
            elif tipo_consulta == 'optimizacion_operacional':
                return self._procesar_optimizacion_operacional(pregunta)
            elif tipo_consulta == 'seguimiento_conversacion':
                return self._procesar_seguimiento_conversacion(pregunta)
            else:
                return self._procesar_consulta_general(pregunta)
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error procesando consulta compleja: {str(e)}'
            }
    
    def mantener_contexto_conversacion(self):
        """Mantiene contexto de conversación entre interacciones"""
        return {
            'conversaciones_anteriores': self.contexto.get('historial', [])[-5:],  # Últimas 5
            'temas_activos': self.contexto.get('temas_activos', []),
            'datos_referenciados': self.contexto.get('datos_referenciados', {}),
            'objetivos_usuario': self.contexto.get('objetivos_usuario', [])
        }
    
    def _detectar_tipo_consulta(self, pregunta):
        """Detecta el tipo de consulta compleja"""
        pregunta_lower = pregunta.lower()
        
        # Patrones para análisis multifactor
        if any(word in pregunta_lower for word in ['porque', 'por que', 'razones', 'factores', 'causas']):
            if any(word in pregunta_lower for word in ['ventas', 'gastos', 'utilidad', 'perdida']):
                return 'analisis_multifactor'
        
        # Patrones para planificación estratégica
        if any(phrase in pregunta_lower for phrase in ['como puedo', 'que debo hacer', 'estrategia', 'plan']):
            if any(word in pregunta_lower for word in ['mejorar', 'aumentar', 'reducir', 'optimizar']):
                return 'planificacion_estrategica'
        
        # Patrones para comparación temporal
        if any(phrase in pregunta_lower for phrase in ['comparado con', 'vs', 'diferencia', 'cambio']):
            if any(word in pregunta_lower for word in ['mes', 'año', 'anterior', 'pasado']):
                return 'comparacion_temporal'
        
        # Patrones para optimización operacional
        if any(word in pregunta_lower for word in ['optimizar', 'eficiencia', 'productividad', 'automatizar']):
            return 'optimizacion_operacional'
        
        # Patrones para seguimiento de conversación
        if any(phrase in pregunta_lower for phrase in ['y que mas', 'ademas', 'tambien', 'siguiendo']):
            return 'seguimiento_conversacion'
        
        return 'consulta_general'
    
    def _procesar_analisis_multifactor(self, pregunta):
        """Procesa análisis multifactor (¿Por qué mis ventas bajaron?)"""
        try:
            # Identificar qué se está analizando
            if 'venta' in pregunta.lower():
                return self._analizar_factores_ventas()
            elif 'gasto' in pregunta.lower():
                return self._analizar_factores_gastos()
            elif 'utilidad' in pregunta.lower() or 'ganancia' in pregunta.lower():
                return self._analizar_factores_utilidad()
            else:
                return self._analizar_factores_generales()
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _procesar_planificacion_estrategica(self, pregunta):
        """Procesa consultas de planificación estratégica"""
        try:
            # Obtener datos actuales
            datos_actuales = self._obtener_datos_empresa_completos()
            
            # Usar ML para predicciones
            ml_service = MLService(self.empresa)
            predicciones_ml = ml_service.predecir_ventas_mes_siguiente()
            
            # Usar predicciones avanzadas
            predicciones_service = PrediccionesAvanzadas(self.empresa)
            flujo_caja = predicciones_service.predecir_flujo_caja(3)
            
            # Generar plan estratégico
            if 'aumentar ventas' in pregunta.lower() or 'mejorar ventas' in pregunta.lower():
                plan = self._generar_plan_aumento_ventas(datos_actuales, predicciones_ml)
            elif 'reducir gastos' in pregunta.lower():
                plan = self._generar_plan_reduccion_gastos(datos_actuales)
            elif 'mejorar utilidad' in pregunta.lower():
                plan = self._generar_plan_mejora_utilidad(datos_actuales)
            else:
                plan = self._generar_plan_general(datos_actuales)
            
            # Actualizar contexto con el plan
            self._actualizar_contexto_plan(plan)
            
            return {
                'success': True,
                'tipo': 'plan_estrategico',
                'plan': plan,
                'datos_base': datos_actuales,
                'predicciones': predicciones_ml,
                'flujo_caja_proyectado': flujo_caja.get('predicciones', [])[:3],
                'seguimiento': 'Pregúntame sobre cualquier paso específico del plan'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _procesar_comparacion_temporal(self, pregunta):
        """Procesa comparaciones temporales"""
        try:
            # Detectar períodos a comparar
            if 'mes anterior' in pregunta.lower() or 'mes pasado' in pregunta.lower():
                periodo_comparacion = 'mes_anterior'
            elif 'año anterior' in pregunta.lower() or 'año pasado' in pregunta.lower():
                periodo_comparacion = 'año_anterior'
            else:
                periodo_comparacion = 'trimestre_anterior'
            
            # Obtener datos de comparación
            datos_actuales = self._obtener_datos_periodo_actual()
            datos_comparacion = self._obtener_datos_periodo_comparacion(periodo_comparacion)
            
            # Calcular diferencias y tendencias
            analisis_comparativo = self._generar_analisis_comparativo(datos_actuales, datos_comparacion)
            
            return {
                'success': True,
                'tipo': 'comparacion_temporal',
                'periodo_actual': datos_actuales,
                'periodo_comparacion': datos_comparacion,
                'analisis': analisis_comparativo,
                'tendencias': self._identificar_tendencias(datos_actuales, datos_comparacion),
                'recomendaciones': self._generar_recomendaciones_comparativas(analisis_comparativo)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _procesar_optimizacion_operacional(self, pregunta):
        """Procesa consultas de optimización operacional"""
        try:
            # Usar servicio de automatización
            automation = AutomatizacionCompleta(self.empresa)
            
            # Identificar área de optimización
            if 'inventario' in pregunta.lower():
                resultado = automation.proceso_gestion_inventario_automatica()
                tipo_optimizacion = 'inventario'
            elif 'cobranza' in pregunta.lower():
                resultado = automation.proceso_cobranza_automatica()
                tipo_optimizacion = 'cobranzas'
            else:
                resultado = automation.proceso_analisis_financiero_automatico()
                tipo_optimizacion = 'general'
            
            # Generar recomendaciones de optimización
            recomendaciones_optimizacion = self._generar_recomendaciones_optimizacion(tipo_optimizacion, resultado)
            
            return {
                'success': True,
                'tipo': 'optimizacion_operacional',
                'area_optimizacion': tipo_optimizacion,
                'analisis_actual': resultado,
                'recomendaciones': recomendaciones_optimizacion,
                'impacto_estimado': self._calcular_impacto_optimizacion(recomendaciones_optimizacion),
                'pasos_implementacion': self._generar_pasos_implementacion(recomendaciones_optimizacion)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _procesar_seguimiento_conversacion(self, pregunta):
        """Procesa seguimiento de conversaciones anteriores"""
        try:
            # Obtener último tema de conversación
            ultimo_tema = self.contexto.get('ultimo_tema', 'general')
            datos_anteriores = self.contexto.get('datos_referenciados', {})
            
            # Continuar conversación basada en contexto
            if ultimo_tema == 'plan_estrategico':
                return self._continuar_plan_estrategico(pregunta, datos_anteriores)
            elif ultimo_tema == 'analisis_multifactor':
                return self._profundizar_analisis(pregunta, datos_anteriores)
            elif ultimo_tema == 'comparacion_temporal':
                return self._extender_comparacion(pregunta, datos_anteriores)
            else:
                return self._seguimiento_general(pregunta)
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _analizar_factores_ventas(self):
        """Analiza factores que afectan las ventas"""
        try:
            # Obtener datos de ventas
            hoy = date.today()
            mes_actual = hoy.month
            mes_anterior = mes_actual - 1 if mes_actual > 1 else 12
            año_anterior = hoy.year if mes_actual > 1 else hoy.year - 1
            
            ventas_actual = Venta.objects.filter(
                empresa=self.empresa,
                fecha__month=mes_actual,
                fecha__year=hoy.year
            ).aggregate(total=sum('monto'))['total'] or 0
            
            ventas_anterior = Venta.objects.filter(
                empresa=self.empresa,
                fecha__month=mes_anterior,
                fecha__year=año_anterior
            ).aggregate(total=sum('monto'))['total'] or 0
            
            # Análisis de factores
            factores = []
            
            # Factor 1: Cambio en cantidad de productos vendidos
            productos_actual = Venta.objects.filter(
                empresa=self.empresa,
                fecha__month=mes_actual
            ).count()
            
            productos_anterior = Venta.objects.filter(
                empresa=self.empresa,
                fecha__month=mes_anterior
            ).count()
            
            if productos_actual < productos_anterior:
                factores.append({
                    'factor': 'Reducción en cantidad de transacciones',
                    'impacto': 'Alto',
                    'descripcion': f'Pasaste de {productos_anterior} a {productos_actual} transacciones',
                    'recomendacion': 'Implementar estrategias de marketing para atraer más clientes'
                })
            
            # Factor 2: Cambio en precios promedio
            precio_promedio_actual = ventas_actual / productos_actual if productos_actual > 0 else 0
            precio_promedio_anterior = ventas_anterior / productos_anterior if productos_anterior > 0 else 0
            
            if precio_promedio_actual < precio_promedio_anterior * 0.9:
                factores.append({
                    'factor': 'Reducción en precio promedio de venta',
                    'impacto': 'Medio',
                    'descripcion': f'Precio promedio bajó de ${precio_promedio_anterior:.2f} a ${precio_promedio_actual:.2f}',
                    'recomendacion': 'Revisar estrategia de precios y valor agregado'
                })
            
            # Factor 3: Estacionalidad
            if mes_actual in [1, 2, 7, 8]:  # Meses típicamente bajos
                factores.append({
                    'factor': 'Estacionalidad del negocio',
                    'impacto': 'Medio',
                    'descripcion': f'El mes {mes_actual} suele tener menores ventas',
                    'recomendacion': 'Planificar promociones especiales para meses de baja temporada'
                })
            
            return {
                'success': True,
                'tipo': 'analisis_factores_ventas',
                'ventas_actual': float(ventas_actual),
                'ventas_anterior': float(ventas_anterior),
                'cambio_porcentual': ((ventas_actual - ventas_anterior) / ventas_anterior * 100) if ventas_anterior > 0 else 0,
                'factores_identificados': factores,
                'recomendacion_principal': self._generar_recomendacion_principal_ventas(factores)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generar_plan_aumento_ventas(self, datos_actuales, predicciones_ml):
        """Genera plan específico para aumentar ventas"""
        plan = {
            'objetivo': f"Aumentar ventas de ${datos_actuales['ventas_mes']:.2f} a ${datos_actuales['ventas_mes'] * 1.3:.2f} (30% más)",
            'plazo': '3 meses',
            'estrategias': []
        }
        
        # Estrategia 1: Optimización de productos
        productos_top = self._obtener_productos_top()
        if productos_top:
            plan['estrategias'].append({
                'estrategia': 'Promocionar productos estrella',
                'descripcion': f'Enfocar marketing en {productos_top[0]["nombre"]} que genera ${productos_top[0]["ventas"]:.2f}/mes',
                'acciones': [
                    'Crear promociones especiales',
                    'Aumentar stock del producto',
                    'Capacitar equipo en beneficios del producto'
                ],
                'impacto_estimado': '15-20% aumento en ventas',
                'tiempo_implementacion': '2 semanas'
            })
        
        # Estrategia 2: Captación de clientes
        plan['estrategias'].append({
            'estrategia': 'Programa de referidos',
            'descripcion': 'Implementar sistema de recompensas por referir nuevos clientes',
            'acciones': [
                'Ofrecer descuento 10% por cada cliente referido',
                'Crear tarjetas de referidos',
                'Seguimiento mensual de referidos'
            ],
            'impacto_estimado': '10-15% aumento en clientes nuevos',
            'tiempo_implementacion': '1 semana'
        })
        
        # Estrategia 3: Precios dinámicos
        if datos_actuales['margen_promedio'] > 30:
            plan['estrategias'].append({
                'estrategia': 'Optimización de precios',
                'descripcion': 'Ajustar precios basado en demanda y competencia',
                'acciones': [
                    'Analizar precios de competencia',
                    'Implementar precios premium en productos únicos',
                    'Crear paquetes de productos'
                ],
                'impacto_estimado': '5-10% aumento en ingresos',
                'tiempo_implementacion': '3 semanas'
            })
        
        return plan
    
    def _obtener_datos_empresa_completos(self):
        """Obtiene datos completos de la empresa para análisis"""
        hoy = date.today()
        inicio_mes = hoy.replace(day=1)
        
        # Ventas del mes
        ventas_mes = Venta.objects.filter(
            empresa=self.empresa,
            fecha__gte=inicio_mes
        ).aggregate(total=sum('monto'))['total'] or 0
        
        # Gastos del mes
        gastos_mes = Gasto.objects.filter(
            empresa=self.empresa,
            fecha__gte=inicio_mes
        ).aggregate(total=sum('monto'))['total'] or 0
        
        # Productos activos
        productos_activos = Producto.objects.filter(empresa=self.empresa).count()
        
        # Clientes activos
        clientes_activos = Cliente.objects.filter(empresa=self.empresa).count()
        
        return {
            'ventas_mes': float(ventas_mes),
            'gastos_mes': float(gastos_mes),
            'utilidad_mes': float(ventas_mes - gastos_mes),
            'margen_promedio': (ventas_mes - gastos_mes) / ventas_mes * 100 if ventas_mes > 0 else 0,
            'productos_activos': productos_activos,
            'clientes_activos': clientes_activos,
            'fecha_analisis': hoy.isoformat()
        }
    
    def _obtener_productos_top(self):
        """Obtiene productos con mejores ventas"""
        from django.db.models import Sum
        
        productos_top = Venta.objects.filter(
            empresa=self.empresa,
            fecha__gte=date.today() - timedelta(days=30)
        ).values('producto__nombre').annotate(
            ventas=Sum('monto'),
            cantidad=Sum('cantidad')
        ).order_by('-ventas')[:3]
        
        return list(productos_top)
    
    def _cargar_contexto(self):
        """Carga contexto de conversación desde cache"""
        contexto = cache.get(self.contexto_key, {})
        if not contexto:
            contexto = {
                'historial': [],
                'temas_activos': [],
                'datos_referenciados': {},
                'objetivos_usuario': [],
                'ultimo_tema': 'general'
            }
        return contexto
    
    def _actualizar_contexto(self, pregunta):
        """Actualiza contexto con nueva pregunta"""
        self.contexto['historial'].append({
            'pregunta': pregunta,
            'timestamp': datetime.now().isoformat(),
            'tipo': self._detectar_tipo_consulta(pregunta)
        })
        
        # Mantener solo últimas 10 conversaciones
        if len(self.contexto['historial']) > 10:
            self.contexto['historial'] = self.contexto['historial'][-10:]
        
        # Guardar en cache por 1 hora
        cache.set(self.contexto_key, self.contexto, 3600)
    
    def _actualizar_contexto_plan(self, plan):
        """Actualiza contexto con plan generado"""
        self.contexto['ultimo_tema'] = 'plan_estrategico'
        self.contexto['datos_referenciados']['ultimo_plan'] = plan
        cache.set(self.contexto_key, self.contexto, 3600)
    
    def _procesar_consulta_general(self, pregunta):
        """Procesa consultas generales con contexto"""
        return {
            'success': True,
            'tipo': 'consulta_general',
            'respuesta': f'Entiendo tu consulta sobre: {pregunta}. ¿Podrías ser más específico sobre qué aspecto te interesa analizar?',
            'sugerencias': [
                'Analizar factores que afectan mis ventas',
                'Crear plan para mejorar utilidad',
                'Comparar rendimiento con meses anteriores',
                'Optimizar procesos operacionales'
            ]
        }

# Función helper para usar en views
def procesar_consulta_conversacional(empresa, usuario, pregunta):
    """Procesa consulta usando IA conversacional avanzada"""
    ai_conversacional = ConversationalAI(empresa, usuario)
    return ai_conversacional.procesar_consulta_compleja(pregunta)