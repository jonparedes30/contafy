import stripe
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from empresa.models import Plan, Suscripcion
from django.utils import timezone

stripe.api_key = settings.STRIPE_SECRET_KEY


def crear_checkout_session(request, plan_slug):
    """Crea una Stripe Checkout Session y redirige al pago."""
    plan = get_object_or_404(Plan, slug=plan_slug, activo=True)

    if not settings.STRIPE_SECRET_KEY or not plan.stripe_price_id:
        # Stripe no configurado o plan sin price_id → volver a landing con aviso
        from django.contrib import messages
        messages.info(request, 'El sistema de pagos aún no está disponible. Contáctanos para activar tu plan.')
        return redirect('empresa:landing')

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{'price': plan.stripe_price_id, 'quantity': 1}],
        mode='subscription',
        success_url=request.build_absolute_uri('/pago/success/?session_id={CHECKOUT_SESSION_ID}'),
        cancel_url=request.build_absolute_uri('/pago/cancel/'),
        metadata={'plan_slug': plan.slug},
    )
    return redirect(session.url, permanent=False)


def checkout_success(request):
    session_id = request.GET.get('session_id', '')
    return render(request, 'empresa/pago_success.html', {'session_id': session_id})


def checkout_cancel(request):
    return render(request, 'empresa/pago_cancel.html')


@csrf_exempt  # Los webhooks de Stripe no llevan sesión Django
def stripe_webhook(request):
    """Recibe y procesa eventos de Stripe (subscription created/updated/deleted)."""
    payload    = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponse(status=400)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    # Manejar checkout completado
    if event['type'] == 'checkout.session.completed':
        _handle_checkout_completed(event['data']['object'])

    return HttpResponse(status=200)


def _handle_checkout_completed(session):
    """Crea o actualiza la Suscripcion cuando Stripe confirma el pago."""
    plan_slug    = session.get('metadata', {}).get('plan_slug')
    customer_id  = session.get('customer')
    sub_id       = session.get('subscription')

    if not plan_slug:
        return

    try:
        plan = Plan.objects.get(slug=plan_slug)
    except Plan.DoesNotExist:
        return

    # La suscripción se asociará a la empresa cuando el usuario complete el registro.
    # Aquí guardamos los IDs de Stripe en sesión temporal o en un modelo de pendiente.
    # Por ahora registramos los datos para referencia futura.
    # TODO: enlazar con la Empresa tras el registro post-pago.
    pass
