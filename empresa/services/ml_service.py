"""
Servicio de Machine Learning Local para CONTAFY
"""
try:
    import numpy as np
except Exception:
    np = None
try:
    import pandas as pd
except Exception:
    pd = None
from datetime import datetime, timedelta, date
from django.db.models import Sum, Avg, Count
from empresa.models import Venta, Gasto, Producto, Empresa
import pickle
import os
from django.conf import settings

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class MLService:
    """Servicio de Machine Learning para predicciones empresariales"""
    
    def __init__(self, empresa):
        self.empresa = empresa
        self.models_path = os.path.join(settings.BASE_DIR, 'ml_models', str(empresa.id))
        os.makedirs(self.models_path, exist_ok=True)
        
        # Modelos disponibles
        self.modelo_ventas = None
        self.modelo_gastos = None
        self.scaler = StandardScaler()
        
    def entrenar_modelo_ventas(self):
        """Entrena modelo de predicción de ventas"""
        if not SKLEARN_AVAILABLE:
            return self._prediccion_simple_ventas()
        
        try:
            # Obtener datos históricos
            datos = self._obtener_datos_historicos_ventas()
            
            if len(datos) < 10 or np is None:  # Mínimo 10 registros o numpy no disponible
                return self._prediccion_simple_ventas()
            
            # Preparar features
            X, y = self._preparar_features_ventas(datos)
            if np is None:
                return self._prediccion_simple_ventas()
            
            if len(X) < 5:
                return self._prediccion_simple_ventas()
            
            # Dividir datos
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Escalar features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Entrenar modelo
            self.modelo_ventas = RandomForestRegressor(
                n_estimators=50,
                random_state=42,
                max_depth=10
            )
            self.modelo_ventas.fit(X_train_scaled, y_train)
            
            # Evaluar modelo
            y_pred = self.modelo_ventas.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Guardar modelo
            self._guardar_modelo('ventas')
            
            return {
                'success': True,
                'modelo': 'RandomForest',
                'mae': float(mae),
                'r2_score': float(r2),
                'datos_entrenamiento': len(X_train),
                'precision': 'Alta' if r2 > 0.7 else 'Media' if r2 > 0.4 else 'Baja'
            }
            
        except Exception as e:
            print(f"Error entrenando modelo ML: {e}")
            return self._prediccion_simple_ventas()
    
    def predecir_ventas_mes_siguiente(self):
        """Predice ventas del próximo mes"""
        if not SKLEARN_AVAILABLE or not self.modelo_ventas or np is None:
            return self._prediccion_simple_ventas()
        
        try:
            # Cargar modelo si existe
            if not self.modelo_ventas:
                self._cargar_modelo('ventas')
            
            if not self.modelo_ventas:
                return self._prediccion_simple_ventas()
            
            # Preparar features para predicción
            features_actuales = self._obtener_features_actuales()
            features_scaled = self.scaler.transform([features_actuales])
            
            # Hacer predicción
            prediccion = self.modelo_ventas.predict(features_scaled)[0]
            
            # Calcular intervalo de confianza (aproximado)
            datos_historicos = self._obtener_datos_historicos_ventas()
            std_historica = np.std([d['ventas_mes'] for d in datos_historicos])
            
            return {
                'prediccion_ventas': float(max(0, prediccion)),
                'rango_minimo': float(max(0, prediccion - std_historica)),
                'rango_maximo': float(prediccion + std_historica),
                'confianza': 'Alta' if len(datos_historicos) > 20 else 'Media',
                'metodo': 'Machine Learning',
                'factores_clave': self._obtener_factores_importantes()
            }
            
        except Exception as e:
            print(f"Error en predicción ML: {e}")
            return self._prediccion_simple_ventas()
    
    def detectar_patrones_ventas(self):
        """Detecta patrones en las ventas usando ML"""
        try:
            datos = self._obtener_datos_historicos_ventas()
            
            if len(datos) < 15:
                return {'patrones': ['Datos insuficientes para análisis de patrones']}
            
            # Análisis de tendencias
            ventas_por_mes = [d['ventas_mes'] for d in datos[-12:]]  # Últimos 12 meses
            
            patrones = []
            
            # Tendencia general
            if len(ventas_por_mes) >= 3 and np is not None:
                try:
                    tendencia = np.polyfit(range(len(ventas_por_mes)), ventas_por_mes, 1)[0]
                except Exception:
                    tendencia = 0
                if tendencia > 100:
                    patrones.append(f"Tendencia de crecimiento: +${tendencia:.0f}/mes")
                elif tendencia < -100:
                    patrones.append(f"Tendencia de declive: ${tendencia:.0f}/mes")
                else:
                    patrones.append("Ventas estables sin tendencia clara")
            
            # Estacionalidad
            if len(ventas_por_mes) >= 6 and np is not None:
                try:
                    variabilidad = np.std(ventas_por_mes) / np.mean(ventas_por_mes)
                except Exception:
                    variabilidad = 0
                if variabilidad > 0.3:
                    patrones.append("Alta variabilidad estacional detectada")
                    
                    # Encontrar mejor y peor mes
                    mejor_mes = np.argmax(ventas_por_mes) + 1
                    peor_mes = np.argmin(ventas_por_mes) + 1
                    patrones.append(f"Mejor rendimiento: mes {mejor_mes}")
                    patrones.append(f"Menor rendimiento: mes {peor_mes}")
            
            # Productos más vendidos
            productos_top = self._obtener_productos_top_ml()
            if productos_top:
                patrones.append(f"Producto estrella: {productos_top[0]['nombre']}")
            
            return {
                'patrones': patrones,
                'datos_analizados': len(datos),
                'periodo_analisis': f"Últimos {len(ventas_por_mes)} meses"
            }
            
        except Exception as e:
            return {'patrones': [f'Error en análisis: {str(e)}']}
    
    def optimizar_precios_ml(self):
        """Optimiza precios usando ML"""
        try:
            # Obtener datos de productos y ventas
            productos = Producto.objects.filter(empresa=self.empresa)
            optimizaciones = []
            
            for producto in productos[:10]:  # Limitar a 10 productos
                ventas_producto = Venta.objects.filter(
                    empresa=self.empresa,
                    producto=producto
                ).values('precio_unitario', 'cantidad', 'fecha')
                
                if len(ventas_producto) >= 5:
                    # Análisis simple de elasticidad precio-demanda
                    precios = [v['precio_unitario'] for v in ventas_producto]
                    cantidades = [v['cantidad'] for v in ventas_producto]
                    
                    if len(set(precios)) > 1:  # Hay variación de precios
                        correlacion = np.corrcoef(precios, cantidades)[0, 1]
                        
                        precio_actual = float(producto.pvp or producto.precio_unitario)
                        precio_promedio = np.mean(precios)
                        
                        if correlacion < -0.3:  # Elasticidad negativa fuerte
                            if precio_actual > precio_promedio * 1.1:
                                optimizaciones.append({
                                    'producto': producto.nombre,
                                    'accion': 'Reducir precio',
                                    'precio_actual': precio_actual,
                                    'precio_sugerido': precio_promedio * 0.95,
                                    'razon': 'Alta sensibilidad al precio'
                                })
                        elif correlacion > -0.1:  # Baja elasticidad
                            optimizaciones.append({
                                'producto': producto.nombre,
                                'accion': 'Aumentar precio',
                                'precio_actual': precio_actual,
                                'precio_sugerido': precio_actual * 1.1,
                                'razon': 'Baja sensibilidad al precio'
                            })
            
            return {
                'optimizaciones': optimizaciones,
                'productos_analizados': len([o for o in optimizaciones])
            }
            
        except Exception as e:
            return {'optimizaciones': [], 'error': str(e)}
    
    def _obtener_datos_historicos_ventas(self):
        """Obtiene datos históricos para entrenamiento"""
        # Obtener ventas por mes de los últimos 24 meses
        fecha_inicio = datetime.now() - timedelta(days=730)
        
        ventas_por_mes = []
        fecha_actual = fecha_inicio
        
        while fecha_actual < datetime.now():
            ventas_mes = Venta.objects.filter(
                empresa=self.empresa,
                fecha__year=fecha_actual.year,
                fecha__month=fecha_actual.month
            ).aggregate(
                total=Sum('monto'),
                cantidad=Count('id')
            )
            
            gastos_mes = Gasto.objects.filter(
                empresa=self.empresa,
                fecha__year=fecha_actual.year,
                fecha__month=fecha_actual.month
            ).aggregate(total=Sum('monto'))
            
            ventas_por_mes.append({
                'año': fecha_actual.year,
                'mes': fecha_actual.month,
                'ventas_mes': float(ventas_mes['total'] or 0),
                'cantidad_ventas': ventas_mes['cantidad'] or 0,
                'gastos_mes': float(gastos_mes['total'] or 0),
                'dia_semana_inicio': fecha_actual.weekday(),
                'es_inicio_año': 1 if fecha_actual.month == 1 else 0
            })
            
            # Siguiente mes
            if fecha_actual.month == 12:
                fecha_actual = fecha_actual.replace(year=fecha_actual.year + 1, month=1)
            else:
                fecha_actual = fecha_actual.replace(month=fecha_actual.month + 1)
        
        return ventas_por_mes
    
    def _preparar_features_ventas(self, datos):
        """Prepara features para el modelo de ventas"""
        X = []
        y = []
        
        for i, dato in enumerate(datos):
            if i < 2:  # Necesitamos al menos 2 meses previos
                continue
                
            # Features: datos de los 2 meses anteriores
            features = [
                datos[i-1]['ventas_mes'],  # Ventas mes anterior
                datos[i-2]['ventas_mes'],  # Ventas 2 meses atrás
                datos[i-1]['gastos_mes'],  # Gastos mes anterior
                dato['mes'],  # Mes del año (estacionalidad)
                dato['dia_semana_inicio'],  # Día de la semana que inicia el mes
                dato['es_inicio_año']  # Si es enero
            ]
            
            X.append(features)
            y.append(dato['ventas_mes'])
        
        return np.array(X), np.array(y)
    
    def _obtener_features_actuales(self):
        """Obtiene features actuales para predicción"""
        # Ventas del mes actual y anterior
        hoy = date.today()
        
        # Mes anterior
        if hoy.month == 1:
            mes_anterior = 12
            año_anterior = hoy.year - 1
        else:
            mes_anterior = hoy.month - 1
            año_anterior = hoy.year
        
        ventas_mes_anterior = Venta.objects.filter(
            empresa=self.empresa,
            fecha__year=año_anterior,
            fecha__month=mes_anterior
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        # 2 meses atrás
        if mes_anterior == 1:
            mes_2_atras = 12
            año_2_atras = año_anterior - 1
        else:
            mes_2_atras = mes_anterior - 1
            año_2_atras = año_anterior
        
        ventas_2_meses = Venta.objects.filter(
            empresa=self.empresa,
            fecha__year=año_2_atras,
            fecha__month=mes_2_atras
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        gastos_mes_anterior = Gasto.objects.filter(
            empresa=self.empresa,
            fecha__year=año_anterior,
            fecha__month=mes_anterior
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        return [
            float(ventas_mes_anterior),
            float(ventas_2_meses),
            float(gastos_mes_anterior),
            hoy.month,
            hoy.weekday(),
            1 if hoy.month == 1 else 0
        ]
    
    def _prediccion_simple_ventas(self):
        """Predicción simple sin ML"""
        # Promedio de los últimos 3 meses
        ventas_recientes = Venta.objects.filter(
            empresa=self.empresa,
            fecha__gte=datetime.now() - timedelta(days=90)
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        prediccion = ventas_recientes / 3  # Promedio mensual
        
        return {
            'prediccion_ventas': float(prediccion),
            'rango_minimo': float(prediccion * 0.8),
            'rango_maximo': float(prediccion * 1.2),
            'confianza': 'Media',
            'metodo': 'Promedio histórico',
            'factores_clave': ['Promedio últimos 3 meses']
        }
    
    def _obtener_factores_importantes(self):
        """Obtiene factores importantes para la predicción"""
        if not SKLEARN_AVAILABLE or not self.modelo_ventas:
            return ['Datos históricos', 'Tendencia general']
        
        try:
            # Feature importance del Random Forest
            importancias = self.modelo_ventas.feature_importances_
            nombres_features = [
                'Ventas mes anterior',
                'Ventas 2 meses atrás', 
                'Gastos mes anterior',
                'Mes del año',
                'Día inicio mes',
                'Es enero'
            ]
            
            # Ordenar por importancia
            indices_ordenados = np.argsort(importancias)[::-1]
            
            factores = []
            for i in indices_ordenados[:3]:  # Top 3
                if importancias[i] > 0.1:  # Solo si es significativo
                    factores.append(nombres_features[i])
            
            return factores if factores else ['Tendencia histórica']
            
        except:
            return ['Tendencia histórica']
    
    def _obtener_productos_top_ml(self):
        """Obtiene productos top usando análisis ML"""
        productos = Producto.objects.filter(empresa=self.empresa)
        productos_analisis = []
        
        for producto in productos:
            ventas = Venta.objects.filter(
                empresa=self.empresa,
                producto=producto,
                fecha__gte=datetime.now() - timedelta(days=90)
            ).aggregate(
                total=Sum('monto'),
                cantidad=Sum('cantidad')
            )
            
            if ventas['total']:
                productos_analisis.append({
                    'nombre': producto.nombre,
                    'ventas_total': float(ventas['total']),
                    'cantidad_vendida': ventas['cantidad'] or 0
                })
        
        # Ordenar por ventas
        productos_analisis.sort(key=lambda x: x['ventas_total'], reverse=True)
        
        return productos_analisis[:5]
    
    def _guardar_modelo(self, tipo):
        """Guarda modelo entrenado"""
        try:
            if tipo == 'ventas' and self.modelo_ventas:
                modelo_path = os.path.join(self.models_path, 'modelo_ventas.pkl')
                scaler_path = os.path.join(self.models_path, 'scaler_ventas.pkl')
                
                with open(modelo_path, 'wb') as f:
                    pickle.dump(self.modelo_ventas, f)
                
                with open(scaler_path, 'wb') as f:
                    pickle.dump(self.scaler, f)
                    
        except Exception as e:
            print(f"Error guardando modelo: {e}")
    
    def _cargar_modelo(self, tipo):
        """Carga modelo guardado"""
        try:
            if tipo == 'ventas':
                modelo_path = os.path.join(self.models_path, 'modelo_ventas.pkl')
                scaler_path = os.path.join(self.models_path, 'scaler_ventas.pkl')
                
                if os.path.exists(modelo_path) and os.path.exists(scaler_path):
                    with open(modelo_path, 'rb') as f:
                        self.modelo_ventas = pickle.load(f)
                    
                    with open(scaler_path, 'rb') as f:
                        self.scaler = pickle.load(f)
                        
        except Exception as e:
            print(f"Error cargando modelo: {e}")

# Función helper para usar en views
def obtener_predicciones_ml(empresa):
    """Obtiene predicciones ML para una empresa"""
    ml_service = MLService(empresa)
    
    # Entrenar modelo si es necesario
    resultado_entrenamiento = ml_service.entrenar_modelo_ventas()
    
    # Hacer predicciones
    prediccion_ventas = ml_service.predecir_ventas_mes_siguiente()
    patrones = ml_service.detectar_patrones_ventas()
    optimizacion_precios = ml_service.optimizar_precios_ml()
    
    return {
        'entrenamiento': resultado_entrenamiento,
        'prediccion_ventas': prediccion_ventas,
        'patrones_detectados': patrones,
        'optimizacion_precios': optimizacion_precios,
        'ml_disponible': SKLEARN_AVAILABLE
    }