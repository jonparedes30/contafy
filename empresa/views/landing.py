from django.shortcuts import render, redirect
from django.conf import settings
from empresa.models import Plan


def landing(request):
    """Página principal pública de Contafy."""
    if request.user.is_authenticated:
        return redirect('empresa:home')

    planes = Plan.objects.filter(activo=True).order_by('precio_mensual')
    return render(request, 'empresa/landing.html', {
        'planes': planes,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    })
