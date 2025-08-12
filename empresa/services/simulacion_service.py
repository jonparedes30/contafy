from django.utils import timezone
from decimal import Decimal
import json
from empresa.models_simulaciones import TipoSimulacion, SimulacionUsuario, EscenarioSimulacion
from empresa.services.gamificacion_service import GamificacionService

class SimulacionService:
    
    @staticmethod
    def iniciar_simulacion(usuario, tipo_simulacion_id, leccion=None):
        """Inicia una nueva simulación para el usuario"""
        tipo_simulacion = TipoSimulacion.objects.get(id=tipo_simulacion_id)
        
        simulacion = SimulacionUsuario.objects.create(
            usuario=usuario,
            tipo_simulacion=tipo_simulacion,
            leccion=leccion,
            estado='iniciada'
        )
        
        return simulacion
    
    @staticmethod
    def procesar_simulacion_venta(simulacion, datos_usuario):
        """Procesa una simulación de venta (para comercio)"""
        try:
            # Extraer datos del usuario
            producto = datos_usuario.get('producto', '')
            cantidad = int(datos_usuario.get('cantidad', 0))
            precio_unitario = float(datos_usuario.get('precio_unitario', 0))
            cliente = datos_usuario.get('cliente', '')
            
            # Validaciones básicas
            errores = []
            if not producto:
                errores.append("Debe seleccionar un producto")
            if cantidad <= 0:
                errores.append("La cantidad debe ser mayor a 0")
            if precio_unitario <= 0:
                errores.append("El precio debe ser mayor a 0")
            
            if errores:
                return {
                    'exito': False,
                    'errores': errores,
                    'puntuacion': 0
                }
            
            # Calcular totales
            subtotal = cantidad * precio_unitario
            iva = subtotal * 0.12  # 12% IVA Ecuador
            total = subtotal + iva
            
            # Evaluar respuesta
            puntuacion = 100
            feedback = []
            
            # Verificar cálculos
            if abs(datos_usuario.get('subtotal', 0) - subtotal) > 0.01:
                puntuacion -= 20
                feedback.append("El subtotal no es correcto")
            
            if abs(datos_usuario.get('iva', 0) - iva) > 0.01:
                puntuacion -= 20
                feedback.append("El IVA no es correcto")
            
            if abs(datos_usuario.get('total', 0) - total) > 0.01:
                puntuacion -= 20
                feedback.append("El total no es correcto")
            
            # Verificar datos del cliente
            if not cliente:
                puntuacion -= 10
                feedback.append("Es recomendable registrar el cliente")
            
            # Guardar resultado
            resultado = {
                'subtotal_correcto': subtotal,
                'iva_correcto': iva,
                'total_correcto': total,
                'puntuacion': max(puntuacion, 0),
                'feedback': feedback,
                'exito': puntuacion >= 60
            }
            
            simulacion.datos_entrada = datos_usuario
            simulacion.resultado = resultado
            simulacion.puntuacion = max(puntuacion, 0)
            simulacion.estado = 'completada' if puntuacion >= 60 else 'fallida'
            simulacion.fecha_completado = timezone.now()
            simulacion.save()
            
            # Otorgar XP si fue exitosa
            if puntuacion >= 60:
                xp_otorgada = int(puntuacion / 10)  # 10 puntos = 1 XP
                GamificacionService.otorgar_xp(
                    simulacion.usuario, 
                    xp_otorgada, 
                    "Simulación de venta completada"
                )
                resultado['xp_otorgada'] = xp_otorgada
            
            return resultado
            
        except Exception as e:
            return {
                'exito': False,
                'errores': [f"Error procesando simulación: {str(e)}"],
                'puntuacion': 0
            }
    
    @staticmethod
    def procesar_simulacion_receta(simulacion, datos_usuario):
        """Procesa una simulación de receta (para manufactura)"""
        try:
            # Extraer datos del usuario
            producto_nombre = datos_usuario.get('producto_nombre', '')
            ingredientes = datos_usuario.get('ingredientes', [])
            
            # Validaciones básicas
            errores = []
            if not producto_nombre:
                errores.append("Debe ingresar el nombre del producto")
            if len(ingredientes) < 2:
                errores.append("Debe agregar al menos 2 ingredientes")
            
            if errores:
                return {
                    'exito': False,
                    'errores': errores,
                    'puntuacion': 0
                }
            
            # Calcular costo total
            costo_total = 0
            for ingrediente in ingredientes:
                cantidad = float(ingrediente.get('cantidad', 0))
                precio_unitario = float(ingrediente.get('precio_unitario', 0))
                costo_total += cantidad * precio_unitario
            
            # Evaluar respuesta
            puntuacion = 100
            feedback = []
            
            # Verificar costo calculado por usuario
            costo_usuario = float(datos_usuario.get('costo_total', 0))
            if abs(costo_usuario - costo_total) > 0.01:
                puntuacion -= 30
                feedback.append("El costo total no es correcto")
            
            # Verificar precio de venta sugerido
            precio_venta = float(datos_usuario.get('precio_venta', 0))
            margen_minimo = costo_total * 1.3  # 30% margen mínimo
            
            if precio_venta < margen_minimo:
                puntuacion -= 20
                feedback.append("El precio de venta es muy bajo, considera un margen mayor")
            
            # Guardar resultado
            resultado = {
                'costo_total_correcto': costo_total,
                'margen_minimo_sugerido': margen_minimo,
                'puntuacion': max(puntuacion, 0),
                'feedback': feedback,
                'exito': puntuacion >= 60
            }
            
            simulacion.datos_entrada = datos_usuario
            simulacion.resultado = resultado
            simulacion.puntuacion = max(puntuacion, 0)
            simulacion.estado = 'completada' if puntuacion >= 60 else 'fallida'
            simulacion.fecha_completado = timezone.now()
            simulacion.save()
            
            # Otorgar XP si fue exitosa
            if puntuacion >= 60:
                xp_otorgada = int(puntuacion / 10)
                GamificacionService.otorgar_xp(
                    simulacion.usuario, 
                    xp_otorgada, 
                    "Simulación de receta completada"
                )
                resultado['xp_otorgada'] = xp_otorgada
            
            return resultado
            
        except Exception as e:
            return {
                'exito': False,
                'errores': [f"Error procesando simulación: {str(e)}"],
                'puntuacion': 0
            }
    
    @staticmethod
    def procesar_simulacion_servicio(simulacion, datos_usuario):
        """Procesa una simulación de facturación de servicio"""
        try:
            # Extraer datos del usuario
            tipo_servicio = datos_usuario.get('tipo_servicio', '')
            horas_trabajadas = float(datos_usuario.get('horas_trabajadas', 0))
            tarifa_hora = float(datos_usuario.get('tarifa_hora', 0))
            gastos_adicionales = float(datos_usuario.get('gastos_adicionales', 0))
            
            # Validaciones básicas
            errores = []
            if not tipo_servicio:
                errores.append("Debe especificar el tipo de servicio")
            if horas_trabajadas <= 0:
                errores.append("Las horas trabajadas deben ser mayor a 0")
            if tarifa_hora <= 0:
                errores.append("La tarifa por hora debe ser mayor a 0")
            
            if errores:
                return {
                    'exito': False,
                    'errores': errores,
                    'puntuacion': 0
                }
            
            # Calcular totales
            subtotal_servicio = horas_trabajadas * tarifa_hora
            subtotal_total = subtotal_servicio + gastos_adicionales
            iva = subtotal_total * 0.12
            total = subtotal_total + iva
            
            # Evaluar respuesta
            puntuacion = 100
            feedback = []
            
            # Verificar cálculos
            if abs(datos_usuario.get('subtotal', 0) - subtotal_total) > 0.01:
                puntuacion -= 25
                feedback.append("El subtotal no es correcto")
            
            if abs(datos_usuario.get('iva', 0) - iva) > 0.01:
                puntuacion -= 25
                feedback.append("El IVA no es correcto")
            
            if abs(datos_usuario.get('total', 0) - total) > 0.01:
                puntuacion -= 25
                feedback.append("El total no es correcto")
            
            # Verificar tarifa competitiva
            if tarifa_hora < 10:
                puntuacion -= 10
                feedback.append("La tarifa por hora parece muy baja")
            
            # Guardar resultado
            resultado = {
                'subtotal_correcto': subtotal_total,
                'iva_correcto': iva,
                'total_correcto': total,
                'puntuacion': max(puntuacion, 0),
                'feedback': feedback,
                'exito': puntuacion >= 60
            }
            
            simulacion.datos_entrada = datos_usuario
            simulacion.resultado = resultado
            simulacion.puntuacion = max(puntuacion, 0)
            simulacion.estado = 'completada' if puntuacion >= 60 else 'fallida'
            simulacion.fecha_completado = timezone.now()
            simulacion.save()
            
            # Otorgar XP si fue exitosa
            if puntuacion >= 60:
                xp_otorgada = int(puntuacion / 10)
                GamificacionService.otorgar_xp(
                    simulacion.usuario, 
                    xp_otorgada, 
                    "Simulación de servicio completada"
                )
                resultado['xp_otorgada'] = xp_otorgada
            
            return resultado
            
        except Exception as e:
            return {
                'exito': False,
                'errores': [f"Error procesando simulación: {str(e)}"],
                'puntuacion': 0
            }