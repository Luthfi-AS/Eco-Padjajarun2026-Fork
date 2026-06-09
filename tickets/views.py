import io, qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, redirect, render
from .forms import OrderForm
from .models import TicketCategory, Order


def ticket_list(request):
    return render(
        request,
        "tickets/list.html",
        {"tickets": TicketCategory.objects.filter(is_active=True)},
    )


@login_required
def buy_ticket(request):
    profile = getattr(request.user, "userprofile", None)
    if profile and not profile.is_email_verified:
        messages.warning(request, "Verifikasi email dulu sebelum membeli tiket.")
        return redirect("dashboard")
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            messages.success(
                request, "Order berhasil dibuat. Silakan lanjutkan pembayaran."
            )
            return redirect("order_detail", order_code=order.order_code)
    else:
        form = OrderForm(
            initial={
                "participant_name": request.user.get_full_name()
                or request.user.username,
                "participant_email": request.user.email,
            }
        )
    return render(request, "tickets/buy.html", {"form": form})


@login_required
def order_detail(request, order_code):
    return render(
        request,
        "tickets/detail.html",
        {"order": get_object_or_404(Order, order_code=order_code, user=request.user)},
    )


@login_required
def simulate_payment(request, order_code):
    order = get_object_or_404(Order, order_code=order_code, user=request.user)
    order.payment_status = "PAID"
    img = qrcode.make(
        f"ECO PADJADJARUN 2026 | {order.order_code} | {order.participant_name} | {order.ticket.name}"
    )
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    order.qr_code.save(
        f"{order.order_code}.png", ContentFile(buffer.getvalue()), save=False
    )
    order.save()
    messages.success(request, "Simulasi pembayaran berhasil. QR e-ticket sudah dibuat.")
    return redirect("order_detail", order_code=order.order_code)


@user_passes_test(lambda u: u.is_staff)
def checkin(request, order_code):
    order = get_object_or_404(Order, order_code=order_code)
    if order.payment_status != "PAID":
        messages.error(request, "Tiket belum dibayar.")
    else:
        order.checked_in = True
        order.save()
        messages.success(request, f"Check-in berhasil untuk {order.participant_name}.")
    return render(request, "tickets/checkin.html", {"order": order})
