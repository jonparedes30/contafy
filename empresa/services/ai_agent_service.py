"""
Servicio del Agente de IA CONTAFY
"""
from django.conf import settings
from django.db.models import Sum, Avg
from empresa.models import Venta, Gasto, Compra, Empresa
from datetime import datetime, timedelta
import json
import re

# Usar la capa de abstracción de proveedores de IA
from empresa.services.ai_provider import get_ai_provider

class ContafyAIAgent:
    
    def __init__(self):
        # Usar la capa de abstracción de IA (soporta OpenAI, Gemini, Mock)
        self._ai_provider = get_ai_provider()
        if self._ai_provider.is_available():
            provider_name = type(self._ai_provider).__name__
            self.provider = getattr(settings, 'AI_PROVIDER', 'gemini').lower()
            print(f"DEBUG: Usando {provider_name}")
        else:
            self.provider = 'local'
            print("DEBUG: Usando análisis local (proveedor IA no disponible)")
    
    def obtener_datos_empresa(self, empresa):
        """Obtiene datos financieros de la empresa - CORREGIDO para coincidir con reportes"""
        from empresa.models import CuentaContable, MovimientoContable
        
        hoy = datetime.now().date()
        hace_30_dias = hoy - timedelta(days=30)
        hace_90_dias = hoy - timedelta(days=90)
        
        # USAR MODELOS DIRECTOS PARA COINCIDIR CON REPORTES
        ventas_mes = Venta.objects.filter(
            empresa=empresa,
            fecha__date__gte=hace_30_dias
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        gastos_mes = Gasto.objects.filter(
            empresa=empresa,
            fecha__date__gte=hace_30_dias
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        # Costo de ventas (solo para análisis detallado, no para utilidad principal)
        
        # COSTO DE VENTAS - ADAPTADO POR TIPO DE EMPRESA
        if empresa.categoria == 'servicios':
            # SERVICIOS: Costo desde precio_unitario del producto (puede ser 0)
            costo_ventas_mes = 0
            ventas_detalle = Venta.objects.filter(
                empresa=empresa,
                fecha__date__gte=hace_30_dias
            ).select_related('producto')
            
            for venta in ventas_detalle:
                if venta.producto and venta.producto.precio_unitario:
                    # precio_unitario = costo del servicio (ej: materiales, subcontratación)
                    costo_ventas_mes += float(venta.producto.precio_unitario) * float(venta.cantidad)
        else:
            # COMERCIO/MANUFACTURA: Usar cuenta contable "Costo de Ventas"
            try:
                cuenta_costo = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Costo de Ventas')
                costo_ventas_mes = MovimientoContable.objects.filter(
                    empresa=empresa,
                    cuenta_fk=cuenta_costo,
                    tipo='debito',
                    fecha__date__gte=hace_30_dias
                ).aggregate(total=Sum('monto'))['total'] or 0
            except CuentaContable.DoesNotExist:
                costo_ventas_mes = 0
        
        # DATOS DE LOS ÚLTIMOS 3 MESES
        
        # Ventas 3 meses
        try:
            ventas_3m = MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk=cuenta_ventas,
                tipo='credito',
                fecha__date__gte=hace_90_dias
            ).aggregate(total=Sum('monto'))['total'] or 0
        except:
            ventas_3m = 0
        
        # Gastos 3 meses
        try:
            gastos_3m = MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk=cuenta_gastos,
                tipo='debito',
                fecha__date__gte=hace_90_dias
            ).aggregate(total=Sum('monto'))['total'] or 0
        except:
            gastos_3m = 0
        
        # Costo de ventas 3 meses
        if empresa.categoria == 'manufactura':
            try:
                costo_ventas_3m = MovimientoContable.objects.filter(
                    empresa=empresa,
                    cuenta_fk=cuenta_costo,
                    tipo='debito',
                    fecha__date__gte=hace_90_dias
                ).aggregate(total=Sum('monto'))['total'] or 0
            except:
                costo_ventas_3m = 0
        else:
            try:
                cuenta_costo = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Costo de Ventas')
                costo_ventas_3m = MovimientoContable.objects.filter(
                    empresa=empresa,
                    cuenta_fk=cuenta_costo,
                    tipo='debito',
                    fecha__date__gte=hace_90_dias
                ).aggregate(total=Sum('monto'))['total'] or 0
            except:
                costo_ventas_3m = float(ventas_3m) * 0.6
        
        # Top gastos (desde MovimientoContable para mayor precisión)
        try:
            top_gastos = list(MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk=cuenta_gastos,
                tipo='debito',
                fecha__date__gte=hace_30_dias
            ).values('descripcion').annotate(
                total=Sum('monto')
            ).order_by('-total')[:5])
        except:
            top_gastos = []
        
        # Top productos vendidos (mantener desde Venta para detalle)
        from empresa.models import Producto
        top_productos = list(Venta.objects.filter(
            empresa=empresa,
            fecha__date__gte=hace_30_dias
        ).values('producto__nombre').annotate(
            total_vendido=Sum('monto'),
            cantidad_vendida=Sum('cantidad')
        ).order_by('-total_vendido')[:5])
        
        # BALANCE GENERAL COMPLETO SEGUN NIIF
        try:
            # ACTIVOS
            activos_corrientes = sum(c.valor for c in CuentaContable.objects.filter(empresa=empresa, tipo='activo', nombre__in=['Caja', 'Bancos', 'Cuentas por Cobrar', 'Inventario']))
            activos_no_corrientes = sum(c.valor for c in CuentaContable.objects.filter(empresa=empresa, tipo='activo').exclude(nombre__in=['Caja', 'Bancos', 'Cuentas por Cobrar', 'Inventario']))
            total_activos = activos_corrientes + activos_no_corrientes
            
            # PASIVOS
            pasivos_corrientes = sum(c.valor for c in CuentaContable.objects.filter(empresa=empresa, tipo='pasivo', nombre__icontains='corto'))
            pasivos_no_corrientes = sum(c.valor for c in CuentaContable.objects.filter(empresa=empresa, tipo='pasivo').exclude(nombre__icontains='corto'))
            total_pasivos = pasivos_corrientes + pasivos_no_corrientes
            
            # PATRIMONIO
            total_capital = sum(c.valor for c in CuentaContable.objects.filter(empresa=empresa, tipo='capital'))
            
            # Si no hay datos, usar aproximaciones
            if total_activos == 0:
                # Aproximar activos basado en ventas (regla general: activos = 0.8 * ventas anuales)
                total_activos = float(ventas_mes) * 12 * 0.8
                activos_corrientes = total_activos * 0.6
                activos_no_corrientes = total_activos * 0.4
            
            if total_pasivos == 0:
                # Aproximar pasivos (regla general: 40% de activos)
                total_pasivos = total_activos * 0.4
                pasivos_corrientes = total_pasivos * 0.7
                pasivos_no_corrientes = total_pasivos * 0.3
                
            if total_capital == 0:
                total_capital = total_activos - total_pasivos
                
        except:
            # Valores por defecto basados en ventas
            total_activos = float(ventas_mes) * 12 * 0.8
            activos_corrientes = total_activos * 0.6
            activos_no_corrientes = total_activos * 0.4
            total_pasivos = total_activos * 0.4
            pasivos_corrientes = total_pasivos * 0.7
            pasivos_no_corrientes = total_pasivos * 0.3
            total_capital = total_activos - total_pasivos
        
        # CALCULO SEGUN NIIF (Normas Internacionales)
        # ESTRUCTURA NIIF:
        # Ventas - Costo de Ventas = Utilidad Bruta
        # Utilidad Bruta - Gastos Operacionales = Utilidad Operacional
        
        ventas_float = float(ventas_mes)
        costo_ventas_float = float(costo_ventas_mes)
        gastos_operacionales = float(gastos_mes)  # Gastos administrativos y de ventas
        
        # CALCULO NIIF CORRECTO:
        utilidad_bruta = ventas_float - costo_ventas_float
        utilidad_operacional = utilidad_bruta - gastos_operacionales  # NIIF: Bruta - Gastos Op.
        
        # MARGENES SEGUN NIIF:
        margen_bruto_niif = (utilidad_bruta / ventas_float * 100) if ventas_float > 0 else 0
        margen_operacional_niif = (utilidad_operacional / ventas_float * 100) if ventas_float > 0 else 0
        
        return {
            'ventas_mes': float(ventas_mes),
            'gastos_mes': float(gastos_mes),
            'ventas_3m': float(ventas_3m),
            'gastos_3m': float(gastos_3m),
            'costo_ventas_mes': float(costo_ventas_mes),
            'costo_ventas_3m': float(costo_ventas_3m),
            'utilidad_bruta_mes': utilidad_bruta,  # NIIF: Ventas - Costo Ventas
            'utilidad_mes': utilidad_operacional,  # NIIF: Utilidad Operacional
            'margen_bruto': margen_bruto_niif,  # NIIF: Margen Bruto
            'margen_mes': margen_operacional_niif,  # NIIF: Margen Operacional
            'top_gastos': top_gastos,
            'top_productos': top_productos,
            # BALANCE GENERAL
            'activos_corrientes': float(activos_corrientes),
            'activos_no_corrientes': float(activos_no_corrientes),
            'total_activos': float(total_activos),
            'pasivos_corrientes': float(pasivos_corrientes),
            'pasivos_no_corrientes': float(pasivos_no_corrientes),
            'total_pasivos': float(total_pasivos),
            'total_capital': float(total_capital),
            
            # RATIOS FINANCIEROS NIIF
            'liquidez_corriente': (float(activos_corrientes) / float(pasivos_corrientes)) if float(pasivos_corrientes) > 0 else 0,
            'prueba_acida': ((float(activos_corrientes) - (float(ventas_mes) * 0.3)) / float(pasivos_corrientes)) if float(pasivos_corrientes) > 0 else 0,
            'endeudamiento_total': (float(total_pasivos) / float(total_activos)) if float(total_activos) > 0 else 0,
            'endeudamiento_patrimonio': (float(total_pasivos) / float(total_capital)) if float(total_capital) > 0 else 0,
            'apalancamiento': (float(total_activos) / float(total_capital)) if float(total_capital) > 0 else 0,
            
            # RATIOS DE RENTABILIDAD
            'roe': (utilidad_operacional / float(total_capital) * 100) if float(total_capital) > 0 else 0,
            'roa': (utilidad_operacional / float(total_activos) * 100) if float(total_activos) > 0 else 0,
            'margen_ebitda': ((utilidad_operacional + (float(gastos_mes) * 0.1)) / ventas_float * 100) if ventas_float > 0 else 0,
            
            # RATIOS DE EFICIENCIA
            'rotacion_activos': (ventas_float / float(total_activos)) if float(total_activos) > 0 else 0,
            'rotacion_inventario': (float(costo_ventas_mes) * 12 / (float(ventas_mes) * 0.3)) if float(ventas_mes) > 0 else 0,
            'ciclo_conversion_efectivo': 30,  # Aproximado
            
            # RATIOS DE ACTIVIDAD
            'ventas_por_empleado': float(ventas_mes) * 12 / 5,  # Asumiendo 5 empleados promedio
            'gastos_por_venta': (float(gastos_mes) / float(ventas_mes)) if float(ventas_mes) > 0 else 0,
            
            # FLUJO DE CAJA APROXIMADO
            'flujo_operativo_mes': utilidad_operacional + (float(gastos_mes) * 0.1),  # + Depreciación aproximada
            'flujo_libre_mes': utilidad_operacional - (float(ventas_mes) * 0.05),  # - Inversiones aproximadas
            
            # INDICADORES DE CRECIMIENTO
            'crecimiento_ventas': ((float(ventas_mes) * 3 / float(ventas_3m) - 1) * 100) if float(ventas_3m) > 0 else 0,
            'crecimiento_utilidad': 0,  # Se calculará con más datos históricos
            
            # INDICADORES DE RIESGO
            'cobertura_gastos_fijos': (utilidad_bruta / float(gastos_mes)) if float(gastos_mes) > 0 else 0,
            'punto_equilibrio': (float(gastos_mes) / (margen_bruto_niif / 100)) if margen_bruto_niif > 0 else 0,
            'dias_supervivencia': (float(total_activos) / (float(gastos_mes) / 30)) if float(gastos_mes) > 0 else 0,
            'fuente_costo': 'precio_unitario' if empresa.categoria == 'servicios' else 'cuenta_contable',
            'categoria': empresa.categoria,
            'ubicacion': empresa.ubicacion_completa or 'Ecuador'
        }
    
    def analizar_empresa(self, empresa):
        """Análisis principal de la empresa"""
        datos = self.obtener_datos_empresa(empresa)
        
        if self.provider == 'gemini':
            return self._analizar_con_gemini(empresa, datos)
        # elif self.provider == 'openai':
        #     return self._analizar_con_openai(empresa, datos)
        else:
            return self._analizar_local(empresa, datos)
    
    def _analizar_con_openai(self, empresa, datos):
        """Análisis usando OpenAI GPT"""
        try:
            prompt = f"""
            Eres un consultor financiero experto analizando una empresa ecuatoriana.
            
            DATOS DE LA EMPRESA:
            - Nombre: {empresa.nombre}
            - Sector: {datos['categoria']}
            - Ubicación: {datos['ubicacion']}
            - Ventas último mes: ${datos['ventas_mes']:,.2f}
            - Gastos último mes: ${datos['gastos_mes']:,.2f}
            - Utilidad último mes: ${datos['utilidad_mes']:,.2f}
            - Margen de utilidad: {datos['margen_mes']:.1f}%
            - Principales gastos: {datos['top_gastos']}
            
            Proporciona un análisis en formato JSON con:
            {{
                "resumen": "Análisis general en 2-3 líneas",
                "fortalezas": ["fortaleza1", "fortaleza2"],
                "debilidades": ["debilidad1", "debilidad2", "debilidad3"],
                "oportunidades": ["oportunidad1", "oportunidad2"],
                "acciones_inmediatas": ["acción1", "acción2"],
                "prediccion_proximo_mes": "Predicción específica",
                "recomendacion_principal": "La recomendación más importante"
            }}
            
            Sé específico, práctico y enfócate en el contexto ecuatoriano.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return self._analizar_local(empresa, datos)
    
    def _analizar_con_gemini(self, empresa, datos):
        """Análisis usando Google Gemini"""
        try:
            prompt = f"""
            Eres un consultor financiero experto analizando una empresa ecuatoriana.
            
            EMPRESA: {empresa.nombre}
            SECTOR: {datos['categoria']}
            UBICACIÓN: {datos['ubicacion']}
            
            DATOS FINANCIEROS REALES (CONTABLES):
            - Ventas último mes: ${datos['ventas_mes']:,.2f}
            - Costo de ventas: ${datos['costo_ventas_mes']:,.2f}
            - Gastos operativos: ${datos['gastos_mes']:,.2f}
            - Utilidad bruta: ${datos['utilidad_bruta_mes']:,.2f} (margen {datos['margen_bruto']:.1f}%)
            - Utilidad neta: ${datos['utilidad_mes']:,.2f} (margen {datos['margen_mes']:.1f}%)
            - Activos totales: ${datos['total_activos']:,.2f}
            - Pasivos totales: ${datos['total_pasivos']:,.2f}
            - Capital: ${datos['total_capital']:,.2f}
            - Liquidez: {datos['liquidez']:.2f}
            - Endeudamiento: {datos['endeudamiento']:.1%}
            - ROE: {datos['roe']:.1f}%
            - Principales gastos: {datos['top_gastos']}
            
            Analiza estos datos reales y responde EXACTAMENTE en este formato JSON (sin markdown, solo JSON puro):
            {{
                "resumen": "Análisis específico de 2-3 líneas usando los números exactos",
                "fortalezas": ["Fortaleza 1 basada en datos reales", "Fortaleza 2 específica"],
                "debilidades": ["Debilidad 1 con números", "Debilidad 2 específica", "Debilidad 3 accionable"],
                "oportunidades": ["Oportunidad 1 para este sector", "Oportunidad 2 en Ecuador"],
                "acciones_inmediatas": ["Acción 1 específica y medible", "Acción 2 inmediata"],
                "prediccion_proximo_mes": "Predicción basada en la tendencia de los datos",
                "recomendacion_principal": "La recomendación más importante con números específicos"
            }}
            """
            
            text = self._ai_provider.complete(prompt)
            
            return json.loads(text)
            
        except Exception as e:
            print(f"Error Gemini análisis: {e}")
            return self._analizar_local(empresa, datos)
    
    def _analizar_local(self, empresa, datos):
        """Análisis inteligente usando reglas locales"""
        analisis = {
            "resumen": f"{empresa.nombre} ({empresa.categoria}) generó ${datos['utilidad_mes']:,.2f} de utilidad con un margen del {datos['margen_mes']:.1f}% este mes.",
            "fortalezas": [],
            "debilidades": [],
            "oportunidades": [],
            "acciones_inmediatas": [],
            "prediccion_proximo_mes": "Mantener tendencia actual",
            "recomendacion_principal": "Optimizar estructura de costos"
        }
        
        # Análisis detallado de margen
        if datos['margen_mes'] > 25:
            analisis["fortalezas"].append(f"Excelente margen de utilidad del {datos['margen_mes']:.1f}% - muy por encima del promedio sectorial")
            analisis["prediccion_proximo_mes"] = f"Con este margen, podrías generar ~${datos['utilidad_mes'] * 1.1:,.2f} el próximo mes"
        elif datos['margen_mes'] > 15:
            analisis["fortalezas"].append(f"Buen margen de utilidad del {datos['margen_mes']:.1f}% - rentabilidad saludable")
        elif datos['margen_mes'] > 5:
            analisis["debilidades"].append(f"Margen bajo del {datos['margen_mes']:.1f}% - necesitas optimizar costos o aumentar precios")
            analisis["acciones_inmediatas"].append(f"Reducir gastos de ${datos['gastos_mes']:,.2f} en al menos 15%")
        else:
            analisis["debilidades"].append(f"Margen crítico del {datos['margen_mes']:.1f}% - empresa en riesgo financiero")
            analisis["acciones_inmediatas"].append("URGENTE: Revisar todos los gastos y aumentar precios")
        
        # Análisis de estructura de costos
        ratio_costos = (datos['costo_ventas_mes'] / datos['ventas_mes'] * 100) if datos['ventas_mes'] > 0 else 0
        ratio_gastos = (datos['gastos_mes'] / datos['ventas_mes'] * 100) if datos['ventas_mes'] > 0 else 0
        
        if ratio_costos > 70:
            analisis["debilidades"].append(f"Costos de ventas muy altos: {ratio_costos:.1f}% - revisar precios de compra")
        
        if ratio_gastos > 25:
            analisis["debilidades"].append(f"Gastos operativos excesivos: {ratio_gastos:.1f}% de las ventas")
            analisis["acciones_inmediatas"].append(f"Reducir gastos operativos en ${datos['gastos_mes'] * 0.2:,.2f}")
        elif ratio_gastos > 15:
            analisis["debilidades"].append(f"Gastos operativos altos: {ratio_gastos:.1f}% - hay espacio para optimizar")
        
        # Análisis de tendencia (comparando con 3 meses)
        if datos['ventas_3m'] > 0:
            crecimiento = ((datos['ventas_mes'] * 3) / datos['ventas_3m'] - 1) * 100
            if crecimiento > 10:
                analisis["fortalezas"].append(f"Crecimiento positivo en ventas del {crecimiento:.1f}%")
                analisis["prediccion_proximo_mes"] = f"Tendencia positiva: podrías alcanzar ${datos['ventas_mes'] * 1.1:,.2f} en ventas"
            elif crecimiento < -10:
                analisis["debilidades"].append(f"Declive en ventas del {crecimiento:.1f}% - necesitas reactivar")
                analisis["acciones_inmediatas"].append("Implementar estrategia de marketing urgente")
        
        # Análisis de gastos principales
        if datos['top_gastos']:
            gasto_mayor = datos['top_gastos'][0]
            porcentaje_gasto = (gasto_mayor['total'] / datos['gastos_mes'] * 100) if datos['gastos_mes'] > 0 else 0
            if porcentaje_gasto > 40:
                analisis["debilidades"].append(f"Gasto concentrado: '{gasto_mayor['descripcion']}' representa {porcentaje_gasto:.1f}% del total")
                analisis["acciones_inmediatas"].append(f"Revisar y optimizar el gasto en '{gasto_mayor['descripcion']}'")
        
        # Oportunidades específicas por sector
        if empresa.categoria == 'comercio':
            analisis["oportunidades"].append("Implementar ventas online para ampliar mercado")
            analisis["oportunidades"].append("Negociar mejores precios con proveedores")
        elif empresa.categoria == 'manufactura':
            analisis["oportunidades"].append("Optimizar procesos productivos para reducir costos")
            analisis["oportunidades"].append("Explorar mercados de exportación")
        else:
            analisis["oportunidades"].append("Diversificar servicios para aumentar ingresos")
            analisis["oportunidades"].append("Implementar precios premium por calidad")
        
        # Recomendación principal basada en datos
        if datos['margen_mes'] < 10:
            analisis["recomendacion_principal"] = f"PRIORIDAD: Aumentar margen del {datos['margen_mes']:.1f}% a mínimo 15% reduciendo gastos o aumentando precios"
        elif datos['utilidad_mes'] < 0:
            analisis["recomendacion_principal"] = f"URGENTE: Revertir pérdida de ${abs(datos['utilidad_mes']):,.2f} - revisar modelo de negocio"
        else:
            analisis["recomendacion_principal"] = f"Mantener utilidad de ${datos['utilidad_mes']:,.2f} y buscar crecimiento del 20% en ventas"
        
        return analisis
    
    def chat_con_usuario(self, empresa, pregunta):
        """Chat interactivo con el usuario"""
        datos = self.obtener_datos_empresa(empresa)
        
        print(f"DEBUG: Provider actual: {self.provider}")
        print(f"DEBUG: Datos empresa - Ventas: ${datos['ventas_mes']}, Gastos: ${datos['gastos_mes']}")
        
        if self.provider == 'gemini':
            return self._chat_gemini(empresa, datos, pregunta)
        else:
            print("DEBUG: Usando chat local inteligente")
            return self._chat_local(empresa, datos, pregunta)
    
    def _chat_openai(self, empresa, datos, pregunta):
        try:
            prompt = f"""
            Eres el asistente financiero de {empresa.nombre}.
            
            Contexto de la empresa:
            - Ventas mes: ${datos['ventas_mes']:,.2f}
            - Gastos mes: ${datos['gastos_mes']:,.2f}
            - Utilidad: ${datos['utilidad_mes']:,.2f}
            - Sector: {datos['categoria']}
            
            Pregunta del usuario: {pregunta}
            
            Responde de forma práctica y específica para esta empresa.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except:
            return self._chat_local(empresa, datos, pregunta)
    
    def _chat_gemini(self, empresa, datos, pregunta):
        try:
            # PRIMERO: Intentar procesar como comando de IA
            from empresa.services.ai_comandos_service import procesar_comando_ia
            from django.contrib.auth import get_user_model
            
            # Detectar si es un comando ejecutable - PRIORIDAD MÁXIMA
            comandos_clave = ['crear', 'añadir', 'agregar', 'vender', 'registrar', 'gasto', 'producto', 'cliente', 'venta', 'generar', 'generame']
            es_comando = any(palabra in pregunta.lower() for palabra in comandos_clave)
            
            # Detectar patrones específicos de creación - FORZAR DETECCIÓN
            patrones_creacion = [
                r'generar.*producto',
                r'generame.*producto',
                r'crear.*producto', 
                r'nuevo producto',
                r'producto.*llam',
                r'costo.*pvp',
                r'pvp.*costo',
                r'producto.*se.*llam'
            ]
            
            # FORZAR como comando si coincide con patrones
            for patron in patrones_creacion:
                if re.search(patron, pregunta.lower()):
                    es_comando = True
                    break
            
            # EJECUTAR COMANDO INMEDIATAMENTE SI SE DETECTA
            if es_comando:
                # Obtener usuario de la empresa
                Usuario = get_user_model()
                usuario = Usuario.objects.filter(empresa=empresa).first()
                
                if usuario:
                    resultado_comando = procesar_comando_ia(empresa, usuario, pregunta)
                    
                    if resultado_comando.get('success'):
                        respuesta_comando = f"{resultado_comando['mensaje']}"
                        
                        # Mostrar confirmación si existe
                        if 'confirmacion' in resultado_comando:
                            respuesta_comando += f"\n\n{resultado_comando['confirmacion']}"
                        
                        # Mostrar acción ejecutada
                        if 'accion_ejecutada' in resultado_comando:
                            respuesta_comando += f"\nAccion: {resultado_comando['accion_ejecutada']}"
                        
                        # Mostrar datos importantes
                        if 'datos' in resultado_comando:
                            datos_importantes = ['producto_id', 'venta_id', 'gasto_id', 'total', 'monto', 'verificado']
                            datos_mostrar = {k: v for k, v in resultado_comando['datos'].items() if k in datos_importantes}
                            
                            if datos_mostrar:
                                respuesta_comando += "\n\nDetalles:"
                                for key, value in datos_mostrar.items():
                                    respuesta_comando += f"\n- {key}: {value}"
                        
                        respuesta_comando += "\n\nNecesitas hacer algo mas?"
                        return respuesta_comando
            
            # SEGUNDO: Si no es comando o falló, usar análisis con Gemini
            gastos_texto = "Sin gastos registrados"
            if datos['top_gastos']:
                gastos_texto = ", ".join([f"{g['descripcion']}: ${g['total']:,.2f}" for g in datos['top_gastos'][:3]])
            
            productos_texto = "Sin productos registrados"
            if datos['top_productos']:
                productos_texto = ", ".join([f"{p['producto__nombre']}: ${p['total_vendido']:,.2f} ({p['cantidad_vendida']} unidades)" for p in datos['top_productos'][:3]])
            
            # Detectar si es comando ejecutable
            pregunta_lower = pregunta.lower()
            
            # Detectar modificaciones/correcciones
            es_modificacion = any(palabra in pregunta_lower for palabra in [
                'pero', 'en realidad', 'mejor', 'cambiar', 'corregir', 'modificar', 'actualizar'
            ]) and any(palabra in pregunta_lower for palabra in [
                'costo', 'precio', 'stock', 'unidades', 'cantidad'
            ])
            
            # Detectar comandos de acción
            es_comando = any(word in pregunta_lower for word in [
                'crear', 'generar', 'generame', 'añadir', 'agregar', 'vender', 'registrar', 'gasto', 'producto'
            ]) or any(patron in pregunta_lower for patron in [
                'nuevo producto', 'producto que se llame', 'costo', 'pvp'
            ]) or es_modificacion
            
            # DETECTAR SI ES COMANDO EJECUTABLE
            comandos_ejecutables = [
                'crear', 'generar', 'registrar', 'añadir', 'agregar', 'vender', 
                'comprar', 'gasto', 'producto', 'cliente', 'proveedor', 'venta'
            ]
            
            es_comando_ejecutable = any(cmd in pregunta_lower for cmd in comandos_ejecutables)
            
            if es_comando_ejecutable:
                # PROMPT PARA COMANDOS EJECUTABLES
                prompt = f"""
Eres el asistente ejecutivo de {empresa.nombre}.

DATOS ACTUALES:
- Ventas: ${datos['ventas_mes']:,.2f}
- Gastos: ${datos['gastos_mes']:,.2f}
- Margen: {datos['margen_mes']:.1f}%

COMANDO: "{pregunta}"

Si el usuario quiere EJECUTAR una acción (crear, registrar, vender, etc.):
1. Extrae los datos específicos
2. Responde EXACTAMENTE así:
"CONFIRMAR_ACCION: [tipo_accion]|[datos_extraidos]
¿Confirmas esta acción? Responde 'sí' para ejecutar."

Ejemplos:
- "crear producto laptop precio 800" → "CONFIRMAR_ACCION: crear_producto|nombre=laptop|precio=800\n¿Confirmas crear producto laptop por $800? Responde 'sí' para ejecutar."
- "registrar gasto alquiler 500" → "CONFIRMAR_ACCION: crear_gasto|descripcion=alquiler|monto=500\n¿Confirmas registrar gasto de alquiler por $500? Responde 'sí' para ejecutar."

Si NO es una acción ejecutable, responde normalmente en máximo 30 palabras.
                """
            else:
                # PROMPT PARA CONSULTAS NORMALES CON TODOS LOS KPIs
                prompt = f"""
Eres el consultor financiero experto de {empresa.nombre}.

DATOS FINANCIEROS COMPLETOS:

ESTADO DE RESULTADOS:
- Ventas: ${datos['ventas_mes']:,.2f}
- Utilidad Bruta: ${datos['utilidad_bruta_mes']:,.2f} (Margen: {datos['margen_bruto']:.1f}%)
- Utilidad Operacional: ${datos['utilidad_mes']:,.2f} (Margen: {datos['margen_mes']:.1f}%)

BALANCE GENERAL:
- Activos Totales: ${datos['total_activos']:,.2f}
- Pasivos Totales: ${datos['total_pasivos']:,.2f}
- Patrimonio: ${datos['total_capital']:,.2f}

RATIOS CLAVE:
- Liquidez: {datos['liquidez_corriente']:.2f} (¿Puede pagar deudas corto plazo?)
- ROE: {datos['roe']:.1f}% (Rentabilidad sobre patrimonio)
- ROA: {datos['roa']:.1f}% (Rentabilidad sobre activos)
- Endeudamiento: {datos['endeudamiento_total']:.1%} (¿Cuánto debe vs lo que tiene?)
- Punto Equilibrio: ${datos['punto_equilibrio']:,.2f} (Ventas mínimas para no perder)
- Días Supervivencia: {datos['dias_supervivencia']:.0f} días (¿Cuánto aguanta sin ventas?)

PREGUNTA: "{pregunta}"

INSTRUCCIONES:
1. Explica en LENGUAJE COMÚN (como si fuera un amigo empresario)
2. Usa los números exactos proporcionados
3. Si mencionas ratios técnicos, explica qué significan en la práctica
4. Máximo 60 palabras
5. Sin emojis

Ejemplo: "Tu liquidez de 1.5 significa que por cada dólar que debes, tienes $1.50 para pagarlo. Eso está bien."
                """
            
            print(f"DEBUG AI: Enviando prompt con datos reales para '{pregunta}'...")
            respuesta_texto = self._ai_provider.complete(prompt)
            print(f"DEBUG AI: Respuesta recibida exitosamente")
            
            # Si Gemini detectó un comando, ejecutarlo
            if respuesta_texto.startswith('EJECUTAR_COMANDO:'):
                comando_data = respuesta_texto.replace('EJECUTAR_COMANDO:', '').strip()
                
                # Parsear comando
                if 'crear_producto' in comando_data:
                    # Extraer datos del comando
                    partes = comando_data.split('|')
                    datos_comando = {}
                    
                    for parte in partes[1:]:  # Saltar 'crear_producto'
                        if '=' in parte:
                            key, value = parte.split('=', 1)
                            datos_comando[key] = value
                    
                    # Construir comando para el sistema
                    nombre = datos_comando.get('nombre', 'producto')
                    precio = datos_comando.get('precio', '15')
                    costo = datos_comando.get('costo', '')
                    
                    comando_sistema = f"crear producto {nombre} precio {precio}"
                    if costo:
                        comando_sistema += f" costo {costo}"
                    
                    # Ejecutar comando
                    Usuario = get_user_model()
                    usuario = Usuario.objects.filter(empresa=empresa).first()
                    
                    if usuario:
                        resultado_comando = procesar_comando_ia(empresa, usuario, comando_sistema)
                        
                        if resultado_comando.get('requiere_confirmacion'):
                            return f"CONFIRMACION REQUERIDA: {resultado_comando['mensaje']}\n\n{resultado_comando['instruccion']}"
                        elif resultado_comando.get('success'):
                            return f"COMANDO EJECUTADO: {resultado_comando['mensaje']}"
                        else:
                            return f"ERROR: {resultado_comando.get('error')}"
            
            # PROCESAR RESPUESTA DE GEMINI
            respuesta_limpia = respuesta_texto.encode('ascii', 'ignore').decode('ascii')
            
            # Si Gemini detectó un comando ejecutable
            if respuesta_limpia.startswith('CONFIRMAR_ACCION:'):
                return self._procesar_confirmacion_accion(respuesta_limpia, empresa, pregunta)
            
            return respuesta_limpia
            
        except Exception as e:
            print(f"DEBUG Gemini Error completo: {e}")
            print(f"DEBUG: Fallback a chat local")
            return self._chat_local(empresa, datos, pregunta)
    
    def _chat_local(self, empresa, datos, pregunta):
        """Chat inteligente y proactivo usando datos reales"""
        pregunta_lower = pregunta.lower()
        
        # DETECTAR CONFIRMACIONES
        if 'si confirmo' in pregunta_lower:
            return self._ejecutar_accion_confirmada(empresa)
        elif 'cancelar' in pregunta_lower:
            from django.core.cache import cache
            cache.delete(f"accion_pendiente_{empresa.id}")
            return "Accion cancelada correctamente."
        
        # RESPUESTAS CON KPIs EN LENGUAJE COMÚN
        if 'liquidez' in pregunta_lower:
            liquidez = datos['liquidez_corriente']
            if liquidez >= 2:
                estado = "excelente - puedes pagar todas tus deudas fácilmente"
            elif liquidez >= 1.5:
                estado = "buena - tienes suficiente para pagar lo que debes"
            elif liquidez >= 1:
                estado = "justa - puedes pagar pero sin margen de error"
            else:
                estado = "crítica - no tienes suficiente para pagar deudas"
            return f"Tu liquidez es {liquidez:.2f}. Esto significa que por cada dólar que debes, tienes ${liquidez:.2f} disponibles. Situación: {estado}."
        
        elif 'roe' in pregunta_lower or 'rentabilidad patrimonio' in pregunta_lower:
            roe = datos['roe']
            if roe > 15:
                estado = "excelente - tu dinero invertido está generando muy buena ganancia"
            elif roe > 10:
                estado = "buena - estás ganando bien con tu inversión"
            elif roe > 0:
                estado = "baja - podrías ganar más poniendo el dinero en otro lado"
            else:
                estado = "negativa - estás perdiendo tu inversión"
            return f"Tu ROE es {roe:.1f}%. Esto significa que por cada $100 que invertiste en tu negocio, ganaste ${roe:.1f}. Situación: {estado}."
        
        elif 'endeudamiento' in pregunta_lower:
            endeudamiento = datos['endeudamiento_total'] * 100
            if endeudamiento < 30:
                estado = "bajo - tienes pocas deudas, muy seguro"
            elif endeudamiento < 50:
                estado = "moderado - nivel normal de deudas"
            elif endeudamiento < 70:
                estado = "alto - cuidado con las deudas"
            else:
                estado = "muy alto - riesgo de quiebra"
            return f"Tu endeudamiento es {endeudamiento:.1f}%. Esto significa que {endeudamiento:.1f}% de todo lo que tienes lo debes. Situación: {estado}."
        
        elif 'punto equilibrio' in pregunta_lower or 'equilibrio' in pregunta_lower:
            equilibrio = datos['punto_equilibrio']
            ventas_actuales = datos['ventas_mes']
            if ventas_actuales > equilibrio:
                diferencia = ventas_actuales - equilibrio
                return f"Tu punto de equilibrio es ${equilibrio:,.2f}. Vendes ${ventas_actuales:,.2f}, o sea ${diferencia:,.2f} por encima. Estás ganando dinero."
            else:
                diferencia = equilibrio - ventas_actuales
                return f"Tu punto de equilibrio es ${equilibrio:,.2f}. Vendes ${ventas_actuales:,.2f}, te faltan ${diferencia:,.2f} para no perder dinero."
        
        elif 'supervivencia' in pregunta_lower or 'aguantar' in pregunta_lower:
            dias = datos['dias_supervivencia']
            if dias > 90:
                estado = "excelente - puedes aguantar más de 3 meses sin vender"
            elif dias > 30:
                estado = "buena - puedes aguantar más de un mes sin vender"
            elif dias > 15:
                estado = "justa - solo aguantas 2 semanas sin vender"
            else:
                estado = "crítica - menos de 2 semanas sin vender"
            return f"Puedes aguantar {dias:.0f} días sin vender nada antes de quedarte sin dinero. Situación: {estado}."
        
        # Respuestas básicas mejoradas
        elif 'ventas del mes' in pregunta_lower:
            transacciones = Venta.objects.filter(empresa=empresa, fecha__month=datetime.now().month).count()
            return f"Ventas: ${datos['ventas_mes']:,.2f} en {transacciones} transacciones. Margen operacional: {datos['margen_mes']:.1f}% (ganancia después de todos los gastos)."
        
        elif 'utilidad' in pregunta_lower:
            utilidad = datos['utilidad_mes']
            margen = datos['margen_mes']
            if margen > 15:
                estado = "excelente negocio"
            elif margen > 5:
                estado = "negocio rentable"
            elif margen > 0:
                estado = "apenas ganando"
            else:
                estado = "perdiendo dinero"
            return f"Utilidad operacional: ${utilidad:,.2f} con margen {margen:.1f}%. En palabras simples: de cada $100 que vendes, te quedan ${margen:.1f} de ganancia. Es un {estado}."
        
        # Análisis proactivo de problemas
        def detectar_problema_principal():
            if datos['utilidad_mes'] < 0:
                ratio_costos = (datos['costo_ventas_mes'] / datos['ventas_mes'] * 100) if datos['ventas_mes'] > 0 else 0
                ratio_gastos = (datos['gastos_mes'] / datos['ventas_mes'] * 100) if datos['ventas_mes'] > 0 else 0
                
                if ratio_costos > 80:
                    return "PROBLEMA CRÍTICO: Tus costos de ventas son excesivos"
                elif ratio_gastos > 30:
                    return "PROBLEMA CRÍTICO: Tus gastos operativos son muy altos"
                else:
                    return "PROBLEMA: Precios muy bajos para cubrir costos"
            return None
        
        # Respuestas específicas y proactivas
        if 'margen' in pregunta_lower and 'negativo' in pregunta_lower:
            problema = detectar_problema_principal()
            ratio_costos = (datos['costo_ventas_mes'] / datos['ventas_mes'] * 100) if datos['ventas_mes'] > 0 else 0
            ratio_gastos = (datos['gastos_mes'] / datos['ventas_mes'] * 100) if datos['ventas_mes'] > 0 else 0
            
            solucion = ""
            if ratio_costos > 80:
                solucion = f"🔍 DIAGNÓSTICO: Costos {ratio_costos:.1f}% vs ventas. ✅ SOLUCIÓN: 1) Ve a Inventario > Ver Productos, revisa precios de compra, 2) Negocia con proveedores descuentos del 10-15%, 3) Busca proveedores alternativos más baratos."
            elif ratio_gastos > 30:
                gasto_mayor = datos['top_gastos'][0]['descripcion'] if datos['top_gastos'] else "gastos operativos"
                solucion = f"🔍 DIAGNÓSTICO: Gastos {ratio_gastos:.1f}% vs ventas. ✅ SOLUCIÓN: 1) Reduce '{gasto_mayor}' inmediatamente, 2) Elimina gastos no esenciales, 3) Objetivo: bajar gastos a máximo 20% de ventas."
            else:
                precio_sugerido = (datos['costo_ventas_mes'] + datos['gastos_mes']) * 1.3 / (datos['ventas_mes'] / datos['costo_ventas_mes']) if datos['ventas_mes'] > 0 else 0
                solucion = f"🔍 DIAGNÓSTICO: Precios muy bajos. ✅ SOLUCIÓN: 1) Aumenta precios 25-30%, 2) Precio sugerido por unidad: ${precio_sugerido:.2f}, 3) Ve a Transacciones > Nueva Venta y ajusta precios."
            
            return f"{problema}. {solucion} 📊 Monitorea en Dashboard el impacto inmediato."
        
        elif 'precio' in pregunta_lower and ('incrementar' in pregunta_lower or 'aumentar' in pregunta_lower or 'subir' in pregunta_lower):
            ratio_costos = (datos['costo_ventas_mes'] / datos['ventas_mes'] * 100) if datos['ventas_mes'] > 0 else 0
            
            if ratio_costos > 85:
                return f"❌ NO subas precios aún. PRIMERO reduce costos ({ratio_costos:.1f}% de ventas). ✅ PLAN: 1) Ve a Inventario > Ver Productos, 2) Revisa costos unitarios, 3) Negocia con proveedores, 4) DESPUÉS aumenta precios 15-20%. Si subes precios ahora, podrías perder clientes sin resolver el problema de fondo."
            else:
                precio_actual = datos['ventas_mes'] / max(1, sum(p.get('cantidad_vendida', 1) for p in datos['top_productos']))
                precio_sugerido = precio_actual * 1.25
                return f"✅ SÍ, aumenta precios. 🎯 ESTRATEGIA: 1) Precio actual ~${precio_actual:.2f}, sube a ${precio_sugerido:.2f} (25%), 2) Ve a Inventario > Ver Productos > Editar precio, 3) Implementa gradualmente (2-3 productos por semana), 4) Monitorea ventas en Dashboard. Con este ajuste podrías generar ${datos['utilidad_mes'] + (precio_sugerido - precio_actual) * 10:.2f} más de utilidad."
        
        elif 'ventas' in pregunta_lower or 'vender' in pregunta_lower:
            if datos['ventas_mes'] > 0:
                if datos['margen_mes'] < 0:
                    return f"⚠️ ALERTA: Ventas ${datos['ventas_mes']:,.2f} pero PÉRDIDAS ${datos['utilidad_mes']:,.2f}. 🔍 PROBLEMA: Cada venta te genera pérdida. ✅ ACCIÓN INMEDIATA: 1) PARA de vender a pérdida, 2) Recalcula precios: costo + 30% mínimo, 3) Ve a Inventario > Ver Productos y ajusta precios YA. Mejor vender menos pero con ganancia."
                else:
                    return f"📈 Ventas: ${datos['ventas_mes']:,.2f} con margen {datos['margen_mes']:.1f}%. ✅ PARA CRECER: 1) Identifica tu producto estrella, 2) Promociona productos de mayor margen, 3) Implementa descuentos por volumen, 4) Meta: ${datos['ventas_mes'] * 1.3:,.2f} próximo mes."
            else:
                return "🚨 SIN VENTAS registradas. ✅ URGENTE: 1) Ve a Transacciones > + Nueva Venta y registra TODAS las ventas, 2) Configura productos en Inventario, 3) Establece precios rentables. Sin datos no puedo ayudarte a crecer."
        
        elif 'gastos' in pregunta_lower or 'costos' in pregunta_lower:
            if datos['gastos_mes'] > 0:
                ratio = (datos['gastos_mes'] / datos['ventas_mes'] * 100) if datos['ventas_mes'] > 0 else 100
                gasto_principal = datos['top_gastos'][0]['descripcion'] if datos['top_gastos'] else "No identificado"
                meta_reduccion = datos['gastos_mes'] * 0.3
                
                if ratio > 25:
                    return f"🔥 GASTOS CRÍTICOS: ${datos['gastos_mes']:,.2f} ({ratio:.1f}% de ventas). 🎯 FOCO: '{gasto_principal}' es tu mayor gasto. ✅ PLAN DE CHOQUE: 1) Reduce este gasto ${meta_reduccion:.2f} este mes, 2) Ve a Reportes > Estado de Resultados para ver detalle, 3) Elimina gastos no esenciales, 4) Objetivo: máximo 20% de ventas."
                else:
                    return f"✅ Gastos controlados: ${datos['gastos_mes']:,.2f} ({ratio:.1f}%). 💡 OPTIMIZACIÓN: 1) Revisa '{gasto_principal}' mensualmente, 2) Negocia mejores tarifas, 3) Automatiza procesos para reducir costos operativos."
            else:
                return "📝 Sin gastos registrados. ✅ IMPORTANTE: 1) Ve a Transacciones > + Nuevo Gasto, 2) Registra TODOS los gastos diarios, 3) Categoriza correctamente. Sin control de gastos no hay rentabilidad."
        
        elif 'utilidad' in pregunta_lower or 'ganancia' in pregunta_lower:
            if datos['utilidad_mes'] > 0:
                return f"💰 Utilidad: ${datos['utilidad_mes']:,.2f} (margen {datos['margen_mes']:.1f}%). {'🎉 EXCELENTE' if datos['margen_mes'] > 20 else '👍 BUENO' if datos['margen_mes'] > 10 else '⚠️ MEJORABLE'}. ✅ SIGUIENTE NIVEL: 1) {'Mantén este ritmo' if datos['margen_mes'] > 20 else 'Aumenta precios 10%'}, 2) Reinvierte ${datos['utilidad_mes'] * 0.3:.2f} en marketing, 3) Meta: ${datos['utilidad_mes'] * 1.5:.2f} próximo mes."
            elif datos['utilidad_mes'] < 0:
                dias_quiebra = abs(datos['total_capital'] / datos['utilidad_mes']) if datos['utilidad_mes'] < 0 and datos['total_capital'] > 0 else 0
                return f"🚨 PÉRDIDA: ${abs(datos['utilidad_mes']):,.2f}. {'⏰ CRÍTICO: Te quedan ~' + str(int(dias_quiebra)) + ' días' if dias_quiebra > 0 and dias_quiebra < 90 else ''}. ✅ PLAN DE RESCATE: 1) Aumenta precios 30% HOY, 2) Reduce gastos 50%, 3) Enfócate solo en productos rentables, 4) Ve a Dashboard cada día para monitorear. ¿Necesitas ayuda específica con precios?"
            else:
                return "⚖️ Punto de equilibrio (sin ganancia ni pérdida). ✅ PARA GENERAR UTILIDAD: 1) Aumenta ventas 20% O reduce gastos 15%, 2) Ajusta precios 10-15%, 3) Cualquier mejora te dará rentabilidad inmediata."
        
        else:
            # Mensaje inicial proactivo
            estado = "🎉 excelente" if datos['margen_mes'] > 15 else "⚠️ crítica" if datos['margen_mes'] < 0 else "👍 estable"
            accion_sugerida = "mantener el rumbo" if datos['margen_mes'] > 15 else "actuar inmediatamente" if datos['margen_mes'] < 0 else "optimizar operaciones"
            
            # Respuesta con datos reales para consultas generales
            if any(word in pregunta_lower for word in ['como', 'situacion', 'estado', 'resumen']):
                estado = "🎉 excelente" if datos['margen_mes'] > 15 else "⚠️ crítica" if datos['margen_mes'] < 0 else "👍 estable"
                return f"📄 RESUMEN FINANCIERO de {empresa.nombre}: Ventas ${datos['ventas_mes']:,.2f}, Gastos ${datos['gastos_mes']:,.2f}, Utilidad ${datos['utilidad_mes']:,.2f} (margen {datos['margen_mes']:.1f}%). Situación: {estado}."
            
            return f"Hola, soy tu consultor financiero de {empresa.nombre}. SITUACION ACTUAL: {estado} - Ventas ${datos['ventas_mes']:,.2f}, Utilidad ${datos['utilidad_mes']:,.2f} (margen {datos['margen_mes']:.1f}%). RECOMENDACION: {accion_sugerida}. Que quieres que analice de rentabilidad, costos o ventas?"
    
    def _procesar_confirmacion_accion(self, respuesta_gemini, empresa, pregunta_original):
        """Procesa confirmaciones de acciones ejecutables"""
        try:
            from django.core.cache import cache
            lineas = respuesta_gemini.split('\n')
            linea_accion = lineas[0].replace('CONFIRMAR_ACCION: ', '')
            mensaje_confirmacion = '\n'.join(lineas[1:]) if len(lineas) > 1 else 'Confirmas esta accion?'
            
            cache_key = f"accion_pendiente_{empresa.id}"
            cache.set(cache_key, {
                'accion': linea_accion,
                'pregunta_original': pregunta_original
            }, 300)
            
            return f"{mensaje_confirmacion}\n\nPara ejecutar, responde exactamente: 'si confirmo'\nPara cancelar, responde: 'cancelar'"
            
        except Exception as e:
            return f"Error procesando confirmacion: {str(e)}"
    
    def _ejecutar_accion_confirmada(self, empresa):
        """Ejecuta la accion confirmada por el usuario"""
        try:
            from django.core.cache import cache
            from empresa.services.ai_comandos_service import procesar_comando_ia
            from django.contrib.auth import get_user_model
            
            cache_key = f"accion_pendiente_{empresa.id}"
            accion_data = cache.get(cache_key)
            
            if not accion_data:
                return "No hay acciones pendientes para ejecutar."
            
            cache.delete(cache_key)
            
            Usuario = get_user_model()
            usuario = Usuario.objects.filter(empresa=empresa).first()
            
            if not usuario:
                return "Error: No se encontro usuario para ejecutar la accion."
            
            resultado = procesar_comando_ia(empresa, usuario, accion_data['pregunta_original'])
            
            if resultado.get('success'):
                return f"ACCION EJECUTADA: {resultado['mensaje']}"
            else:
                return f"Error ejecutando accion: {resultado.get('error', 'Error desconocido')}"
                
        except Exception as e:
            return f"Error ejecutando accion confirmada: {str(e)}"