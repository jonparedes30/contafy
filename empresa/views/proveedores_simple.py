from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from empresa.models import Proveedor

@login_required
def listar_proveedores_simple(request):
    """Lista simple de proveedores"""
    empresa = request.user.empresa
    proveedores = Proveedor.objects.filter(empresa=empresa, activo=True).order_by('nombre')
    
    return render(request, 'empresa/manufactura/listar_proveedores.html', {
        'proveedores': proveedores
    })