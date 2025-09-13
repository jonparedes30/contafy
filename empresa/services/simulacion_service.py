from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import json
from empresa.models_simulaciones import TipoSimulacion, SimulacionUsuario, EscenarioSimulacion
from empresa.services.gamificacion_service import GamificacionService
from empresa.sandbox_mode import enable as enable_sandbox, disable as disable_sandbox
# Importar patches para bloquear side-effects
import empresa.sandbox_patches

class SimulacionService:
    
    @staticmethod
    def iniciar_simulacion(usuario, tipo_simulacion_id, leccion=None, modo_sandbox=False):
        """Inicia una nueva simulación para el usuario"""
        tipo_simulacion = TipoSimulacion.objects.get(id=tipo_simulacion_id)
        
        simulacion = SimulacionUsuario.objects.create(
            usuario=usuario,
            tipo_simulacion=tipo_simulacion,
            leccion=leccion,
            estado='iniciada'
        )
        # Marcar en memoria que es sandbox para que llamadas posteriores
        # o handlers asíncronos puedan detectarlo sin necesidad de migraciones
        if modo_sandbox:
            # Guardar de forma persistente el flag es_sandbox (modelo actualizado)
            try:
                simulacion.es_sandbox = True
                simulacion.save()
            except Exception:
                # Fallback a atributo de instancia si algo falla
                setattr(simulacion, '_es_sandbox', True)

        return simulacion
    
    @staticmethod
    def procesar_simulacion_venta(simulacion, datos_usuario, modo_sandbox=True):
        """Procesa una simulación de venta (para comercio)"""
        try:
            # Extraer datos del usuario y normalizar
            producto = datos_usuario.get('producto', '')
            try:
                cantidad = int(datos_usuario.get('cantidad', 0))
            except Exception:
                cantidad = 0
            try:
                precio_unitario = float(datos_usuario.get('precio_unitario', 0))
            except Exception:
                # Compatibilidad con campo 'precio' usado en UI
                try:
                    precio_unitario = float(datos_usuario.get('precio', 0))
                except Exception:
                    precio_unitario = 0.0
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
                simulacion.datos_entrada = datos_usuario
                simulacion.resultado = {'errores': errores, 'puntuacion': 0}
                simulacion.puntuacion = 0
                simulacion.estado = 'fallida'
                simulacion.fecha_completado = timezone.now()
                simulacion.save()
                return {
                    'exito': False,
                    'errores': errores,
                    'puntuacion': 0
                }

            # Calcular totales
            subtotal = cantidad * precio_unitario
            iva = round(subtotal * 0.12, 2)
            total = round(subtotal + iva, 2)

            # Normalizar valores numéricos proporcionados por el usuario
            try:
                user_subtotal = float(datos_usuario.get('subtotal', 0) or 0)
            except Exception:
                user_subtotal = 0.0
            try:
                user_iva = float(datos_usuario.get('iva', 0) or 0)
            except Exception:
                user_iva = 0.0
            try:
                user_total = float(datos_usuario.get('total', 0) or 0)
            except Exception:
                user_total = 0.0

            # Evaluar respuesta
            puntuacion = 100
            feedback = []

            if abs(user_subtotal - subtotal) > 0.01:
                puntuacion -= 20
                feedback.append("El subtotal no es correcto")

            if abs(user_iva - iva) > 0.01:
                puntuacion -= 20
                feedback.append("El IVA no es correcto")

            if abs(user_total - total) > 0.01:
                puntuacion -= 20
                feedback.append("El total no es correcto")

            if not cliente:
                puntuacion -= 10
                feedback.append("Es recomendable registrar el cliente")

            resultado = {
                'subtotal_correcto': subtotal,
                'iva_correcto': iva,
                'total_correcto': total,
                'puntuacion': max(puntuacion, 0),
                'feedback': feedback,
                'exito': puntuacion >= 60
            }

            # Ejecutar side-effects en savepoint si es sandbox
            if modo_sandbox:
                with transaction.atomic():
                    sp = transaction.savepoint()
                    try:
                        enable_sandbox()
                        # Simular creación de venta y asientos contables
                        from empresa.services.contabilidad_service import ContabilidadService
                        from decimal import Decimal
                        
                        # Crear asientos de prueba para validar balance
                        asientos_test = [
                            {
                                'cuenta': 'Caja',
                                'tipo_cuenta': 'activo',
                                'tipo_movimiento': 'debito',
                                'monto': Decimal(str(total)),
                                'descripcion': f'Venta sandbox {producto}'
                            },
                            {
                                'cuenta': 'Ventas',
                                'tipo_cuenta': 'ingreso', 
                                'tipo_movimiento': 'credito',
                                'monto': Decimal(str(subtotal)),
                                'descripcion': f'Venta sandbox {producto}'
                            },
                            {
                                'cuenta': 'IVA por Pagar',
                                'tipo_cuenta': 'pasivo',
                                'tipo_movimiento': 'credito', 
                                'monto': Decimal(str(iva)),
                                'descripcion': f'IVA sandbox {producto}'
                            }
                        ]
                        
                        # Crear AsientoAudit en lugar de transacción real
                        from empresa.models_audit import AsientoAudit
                        transaccion_id = f"sandbox_{simulacion.id}"
                        
                        AsientoAudit.crear_desde_asientos(
                            simulacion,
                            asientos_test,
                            transaccion_id
                        )
                        
                        # Validar balance en audit
                        balance = AsientoAudit.validar_balance(simulacion)
                        if not balance['balanceado']:
                            raise ValueError(f"Asientos desbalanceados: {balance['diferencia']}")
                        
                        resultado['balance_audit'] = balance
                        
                    except Exception as e:
                        resultado['sandbox_error'] = str(e)
                    finally:
                        disable_sandbox()
                        transaction.savepoint_rollback(sp)

            # Persistir metadatos de la simulación
            simulacion.datos_entrada = datos_usuario
            simulacion.resultado = resultado
            simulacion.puntuacion = max(puntuacion, 0)
            simulacion.estado = 'completada' if puntuacion >= 60 else 'fallida'
            simulacion.fecha_completado = timezone.now()
            simulacion.save()

            # Otorgar XP si aplica
            if puntuacion >= 60:
                xp_otorgada = int(puntuacion / 10)
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
    def procesar_simulacion_receta(simulacion, datos_usuario, modo_sandbox=True):
        """Procesa una simulación de receta (para manufactura)"""
        try:
            # Extraer datos del usuario
            producto_nombre = datos_usuario.get('producto_nombre', '')
            ingredientes = datos_usuario.get('ingredientes', [])
            # Si ingredientes se envía como JSON-string (desde form), intentar parsear
            if isinstance(ingredientes, str):
                try:
                    ingredientes = json.loads(ingredientes)
                except Exception:
                    ingredientes = []
            
            # Validaciones básicas
            errores = []
            if not producto_nombre:
                errores.append("Debe ingresar el nombre del producto")
            if len(ingredientes) < 2:
                errores.append("Debe agregar al menos 2 ingredientes")
            
            if errores:
                simulacion.datos_entrada = datos_usuario
                simulacion.resultado = {'errores': errores, 'puntuacion': 0}
                simulacion.puntuacion = 0
                simulacion.estado = 'fallida'
                simulacion.fecha_completado = timezone.now()
                simulacion.save()
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
            # Sandbox execution pattern: validar contabilidad sin persistir
            if modo_sandbox:
                with transaction.atomic():
                    sp = transaction.savepoint()
                    try:
                        enable_sandbox()
                        # Validar cálculos de costos en sandbox
                        from decimal import Decimal
                        costo_decimal = Decimal(str(costo_total))
                        if costo_decimal <= 0:
                            raise ValueError("Costo total debe ser mayor a 0")
                    except Exception as e:
                        resultado['sandbox_error'] = str(e)
                    finally:
                        disable_sandbox()
                        transaction.savepoint_rollback(sp)

            simulacion.datos_entrada = datos_usuario
            simulacion.resultado = resultado
            simulacion.puntuacion = max(puntuacion, 0)
            simulacion.estado = 'completada' if puntuacion >= 60 else 'fallida'
            simulacion.fecha_completado = timezone.now()
            simulacion.save()

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
    def procesar_simulacion_servicio(simulacion, datos_usuario, modo_sandbox=True):
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
                simulacion.datos_entrada = datos_usuario
                simulacion.resultado = {'errores': errores, 'puntuacion': 0}
                simulacion.puntuacion = 0
                simulacion.estado = 'fallida'
                simulacion.fecha_completado = timezone.now()
                simulacion.save()
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
            # Sandbox execution: validar cálculos de servicios
            if modo_sandbox:
                with transaction.atomic():
                    sp = transaction.savepoint()
                    try:
                        enable_sandbox()
                        # Validar cálculos con Decimal para precisión
                        from decimal import Decimal
                        subtotal_d = Decimal(str(subtotal_total))
                        iva_d = Decimal(str(iva))
                        total_d = Decimal(str(total))
                        
                        if abs(subtotal_d + iva_d - total_d) > Decimal('0.01'):
                            raise ValueError("Error en cálculos de servicio")
                    except Exception as e:
                        resultado['sandbox_error'] = str(e)
                    finally:
                        disable_sandbox()
                        transaction.savepoint_rollback(sp)

            simulacion.datos_entrada = datos_usuario
            simulacion.resultado = resultado
            simulacion.puntuacion = max(puntuacion, 0)
            simulacion.estado = 'completada' if puntuacion >= 60 else 'fallida'
            simulacion.fecha_completado = timezone.now()
            simulacion.save()

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