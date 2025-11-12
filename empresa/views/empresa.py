from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from empresa.models import Empresa
from empresa.forms import EmpresaForm, EmpleadoEmpresaForm, EditarEmpresaForm
from django.http import JsonResponse
from empresa.models import Empresa, Usuario, PoderEmpleado
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from empresa.decorators import require_owner
import json


@login_required
def home(request):
    """
    Vista principal que siempre redirige al resumen financiero.
    """
    # Verificar que el usuario tenga una empresa
    if not request.user.empresa:
        messages.warning(request, 'No tienes una empresa asociada.')
        return redirect('empresa:crear_empresa')
    
    # Siempre redirigir al resumen financiero
    return redirect('empresa:resumen_financiero')


@login_required
def crear_empresa(request):
    # Verificar si el usuario ya tiene una empresa
    if request.user.empresa:
        messages.warning(request, 'Ya tienes una empresa asociada.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save()
            # Asignar la empresa al usuario
            request.user.empresa = empresa
            request.user.save()
            messages.success(request, 'Empresa creada y asociada exitosamente.')
            return redirect('empresa:dashboard')
    else:
        form = EmpresaForm()
    return render(request, 'empresa/crear_empresa.html', {'form': form})


@login_required
@require_owner
def listar_empresas(request):
    # Solo mostrar la empresa del usuario actual
    if not request.user.empresa:
        messages.warning(request, 'No tienes una empresa asociada.')
        return redirect('empresa:crear_empresa')
    
    # Precargar la empresa con sus empleados (incluyendo al dueño)
    empresa = Empresa.objects.prefetch_related('usuarios').get(id=request.user.empresa.id)
    # Mostrar todos los usuarios de la empresa
    empleados = empresa.usuarios.all()
    
    # Datos adicionales para vista empresarial
    from django.db.models import Sum, Count
    from datetime import datetime, timedelta
    
    # Estadísticas básicas
    stats = {
        'total_empleados': empleados.count(),
        'total_productos': empresa.producto_set.count(),
        'ventas_mes': empresa.venta_set.filter(
            fecha__month=datetime.now().month,
            fecha__year=datetime.now().year
        ).aggregate(total=Sum('monto'))['total'] or 0,
        'gastos_mes': empresa.gasto_set.filter(
            fecha__month=datetime.now().month,
            fecha__year=datetime.now().year
        ).aggregate(total=Sum('monto'))['total'] or 0,
    }
    
    return render(request, 'empresa/mi_empresa.html', {
        'empresa': empresa,
        'empleados': empleados,
        'stats': stats
    })


@login_required
@require_owner
def crear_empleado(request):
    # Verificar que el usuario tenga una empresa
    if not request.user.empresa:
        messages.warning(request, 'No tienes una empresa asociada.')
        return redirect('empresa:crear_empresa')
    
    if request.method == 'POST':
        form = EmpleadoEmpresaForm(request.POST, empresa=request.user.empresa)
        if form.is_valid():
            try:
                empleado = form.save()
                messages.success(request, f'Empleado {empleado.get_full_name()} creado exitosamente.')
                return redirect('empresa:listar_empresas')
            except Exception as e:
                if 'username' in str(e) and 'unique' in str(e).lower():
                    messages.error(request, 'Ya existe un usuario con ese nombre. Elige otro nombre de usuario.')
                else:
                    messages.error(request, f'Error al crear empleado: {e}')
        else:
            messages.error(request, 'Error al crear el empleado. Revisa los datos.')
    else:
        form = EmpleadoEmpresaForm(empresa=request.user.empresa)
    
    return render(request, 'empresa/crear_empleado.html', {'form': form})


@login_required
@require_http_methods(["GET", "POST"])
def gestion_poderes_empleado(request, empresa_id, empleado_id):
    try:
        empresa = Empresa.objects.get(id=empresa_id)
        empleado = Usuario.objects.get(id=empleado_id, empresa=empresa)
        
        # Verificar que el usuario actual sea el dueño de la empresa
        if request.user.empresa != empresa:
            return JsonResponse({'error': 'No tienes permisos para gestionar esta empresa.'}, status=403)
        
        # Verificar que el usuario actual sea el dueño (primer usuario de la empresa)
        dueño = empresa.usuarios.first()
        if request.user.id != dueño.id:
            return JsonResponse({'error': 'Solo el dueño de la empresa puede gestionar poderes.'}, status=403)
            
    except (Empresa.DoesNotExist, Usuario.DoesNotExist):
        return JsonResponse({'error': 'Empresa o empleado no encontrado.'}, status=404)

    if request.method == 'GET':
        poderes, _ = PoderEmpleado.objects.get_or_create(empleado=empleado, empresa=empresa)
        data = {
            'puede_ver_reportes': poderes.puede_ver_reportes,
            'puede_registrar_ventas': poderes.puede_registrar_ventas,
            'puede_editar_productos': poderes.puede_editar_productos,
            'puede_gestionar_cuentas': poderes.puede_gestionar_cuentas,
            'puede_registrar_gastos': poderes.puede_registrar_gastos,
            'puede_gestionar_inventario': poderes.puede_gestionar_inventario,
            'puede_gestionar_metas': poderes.puede_gestionar_metas,
        }
        return JsonResponse(data)

    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'error': 'JSON inválido.'}, status=400)
        poderes, _ = PoderEmpleado.objects.get_or_create(empleado=empleado, empresa=empresa)
        poderes.puede_ver_reportes = body.get('puede_ver_reportes', False)
        poderes.puede_registrar_ventas = body.get('puede_registrar_ventas', False)
        poderes.puede_editar_productos = body.get('puede_editar_productos', False)
        poderes.puede_gestionar_cuentas = body.get('puede_gestionar_cuentas', False)
        poderes.puede_registrar_gastos = body.get('puede_registrar_gastos', False)
        poderes.puede_gestionar_inventario = body.get('puede_gestionar_inventario', False)
        poderes.puede_gestionar_metas = body.get('puede_gestionar_metas', False)
        poderes.save()
        return JsonResponse({'success': True})


@login_required
@require_owner
@require_http_methods(["POST"])
def eliminar_empleado(request, empleado_id):
    try:
        empleado = Usuario.objects.get(id=empleado_id, empresa=request.user.empresa)
        
        # Verificar que no sea el propietario
        if empleado == request.user.empresa.usuarios.first():
            return JsonResponse({'error': 'No puedes eliminar al propietario de la empresa.'}, status=400)
        
        # Eliminar poderes asociados
        PoderEmpleado.objects.filter(empleado=empleado).delete()
        
        # Desactivar usuario en lugar de eliminarlo (preserva historial)
        empleado.is_active = False
        empleado.username = f"ELIMINADO_{empleado.id}_{empleado.username}"
        empleado.save()
        
        return JsonResponse({'success': True})
        
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Empleado no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_owner
@require_http_methods(["POST"])
def editar_empresa(request):
    if not request.user.empresa:
        return JsonResponse({'error': 'No tienes una empresa asociada.'}, status=400)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Datos inválidos.'}, status=400)
    
    empresa = request.user.empresa
    
    # Validaciones básicas
    if not data.get('nombre') or not data.get('ruc') or not data.get('direccion'):
        return JsonResponse({'error': 'Nombre, RUC y dirección son obligatorios.'}, status=400)
    
    # Actualizar campos
    empresa.nombre = data.get('nombre')
    empresa.ruc = data.get('ruc')
    empresa.direccion = data.get('direccion')
    empresa.categoria = data.get('categoria', empresa.categoria)
    empresa.provincia = data.get('provincia', '')
    empresa.ciudad = data.get('ciudad', '')
    empresa.telefono_whatsapp = data.get('telefono_whatsapp', '')
    empresa.tipo_negocio = data.get('tipo_negocio', '')
    
    try:
        empresa.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def editar_usuario(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Datos inválidos.'}, status=400)
    
    usuario = request.user
    
    # Validaciones básicas
    if not data.get('first_name') or not data.get('last_name'):
        return JsonResponse({'error': 'Nombre y apellido son obligatorios.'}, status=400)
    
    # Actualizar campos del usuario
    usuario.first_name = data.get('first_name').strip()
    usuario.last_name = data.get('last_name').strip()
    usuario.email = data.get('email', '').strip()
    
    try:
        usuario.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


