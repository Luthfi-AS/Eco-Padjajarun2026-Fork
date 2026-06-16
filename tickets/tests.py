"""
Test suite untuk app tickets — Eco Padjadjarun 2026
Mencakup:
  - Unit Testing Form OrderForm (UTFORM-05, UTFORM-06)
  - Black Box view access tests terkait tickets
"""

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import UserProfile
from .forms import OrderForm
from .models import Order, TicketCategory

def _create_ticket_category(**overrides):
    """Create a test TicketCategory."""
    defaults = {
        "name": "Eco Run 5K",
        "description": "Kategori lari 5 kilometer",
        "price": 75000,
        "quota": 100,
        "is_active": True,
    }
    defaults.update(overrides)
    return TicketCategory.objects.create(**defaults)


def _create_user_with_profile(username="ticketuser", verified=True):
    """Create a user with a verified profile."""
    user = User.objects.create_user(username, f"{username}@e.com", "Padjadjaran#2026")
    profile = UserProfile.objects.create(
        user=user,
        phone="081234567890",
        is_email_verified=verified,
    )
    return user, profile

class UnitTestOrderFormTests(TestCase):
    """UTFORM-05 dan UTFORM-06"""

    def setUp(self):
        self.ticket = _create_ticket_category()

    # UTFORM-05  OrderForm valid
    def test_utform_05_order_form_valid(self):
        form = OrderForm(data={
            "ticket": self.ticket.pk,
            "participant_name": "Luthfi AS",
            "participant_email": "luthfi@example.com",
            "participant_phone": "081234567890",
        })
        self.assertTrue(form.is_valid(), form.errors)

    # UTFORM-06  OrderForm email salah
    def test_utform_06_order_form_email_salah(self):
        form = OrderForm(data={
            "ticket": self.ticket.pk,
            "participant_name": "Luthfi AS",
            "participant_email": "x",
            "participant_phone": "081234567890",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("participant_email", form.errors)

class TicketViewsAccessTests(TestCase):
    """Tests terkait akses view tickets yang tercakup dalam BB-LOGIN test cases."""

    def setUp(self):
        self.client = Client()
        self.ticket = _create_ticket_category()
        self.user, self.profile = _create_user_with_profile()

    def test_buy_ticket_requires_login(self):
        resp = self.client.get(reverse("buy_ticket"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    def test_buy_ticket_unverified_email_redirects(self):
        """User dengan email belum verified → redirect ke dashboard."""
        user2, _ = _create_user_with_profile("unverified", verified=False)
        self.client.login(username="unverified", password="Padjadjaran#2026")
        resp = self.client.get(reverse("buy_ticket"), follow=True)
        # Harus ada pesan warning tentang verifikasi
        messages_list = list(resp.context["messages"])
        self.assertTrue(
            any("erifikasi" in str(m) for m in messages_list),
            "Seharusnya ada pesan warning verifikasi email"
        )

    def test_buy_ticket_verified_email_can_access(self):
        """User dengan email sudah verified → bisa akses form."""
        self.client.login(username="ticketuser", password="Padjadjaran#2026")
        resp = self.client.get(reverse("buy_ticket"))
        self.assertEqual(resp.status_code, 200)

    def test_create_order_success(self):
        """Order berhasil dibuat oleh user terverifikasi."""
        self.client.login(username="ticketuser", password="Padjadjaran#2026")
        resp = self.client.post(reverse("buy_ticket"), {
            "ticket": self.ticket.pk,
            "participant_name": "Luthfi AS",
            "participant_email": "luthfi@example.com",
            "participant_phone": "081234567890",
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Order.objects.filter(user=self.user).exists())

    def test_order_detail_requires_login(self):
        resp = self.client.get(reverse("order_detail", args=["ECO-ABC1234567"]))
        self.assertEqual(resp.status_code, 302)

    def test_order_detail_only_owner(self):
        """User hanya bisa lihat order miliknya sendiri."""
        self.client.login(username="ticketuser", password="Padjadjaran#2026")
        order = Order.objects.create(
            user=self.user,
            ticket=self.ticket,
            participant_name="Luthfi",
            participant_email="luthfi@example.com",
            participant_phone="08123",
        )
        # Owner bisa akses
        resp = self.client.get(reverse("order_detail", args=[order.order_code]))
        self.assertEqual(resp.status_code, 200)

        # User lain tidak bisa akses
        user2, _ = _create_user_with_profile("otheruser")
        self.client.login(username="otheruser", password="Padjadjaran#2026")
        resp = self.client.get(reverse("order_detail", args=[order.order_code]))
        self.assertEqual(resp.status_code, 404)

    def test_checkin_requires_staff(self):
        """Non-staff tidak bisa akses checkin."""
        self.client.login(username="ticketuser", password="Padjadjaran#2026")
        resp = self.client.get(reverse("checkin", args=["ECO-ABC1234567"]))
        self.assertEqual(resp.status_code, 302)

    def test_checkin_staff_can_access(self):
        """Staff bisa akses checkin."""
        staff_user = User.objects.create_user(
            "staffuser", "staff@e.com", "Padjadjaran#2026", is_staff=True
        )
        order = Order.objects.create(
            user=self.user,
            ticket=self.ticket,
            participant_name="Luthfi",
            participant_email="luthfi@example.com",
            participant_phone="08123",
            payment_status="PAID",
        )
        self.client.login(username="staffuser", password="Padjadjaran#2026")
        resp = self.client.get(reverse("checkin", args=[order.order_code]))
        self.assertEqual(resp.status_code, 200)

    def test_simulate_payment(self):
        """Simulasi pembayaran mengubah status ke PAID dan membuat QR."""
        self.client.login(username="ticketuser", password="Padjadjaran#2026")
        order = Order.objects.create(
            user=self.user,
            ticket=self.ticket,
            participant_name="Luthfi",
            participant_email="luthfi@example.com",
            participant_phone="08123",
        )
        self.assertEqual(order.payment_status, "PENDING")
        resp = self.client.get(
            reverse("simulate_payment", args=[order.order_code]),
            follow=True,
        )
        order.refresh_from_db()
        self.assertEqual(order.payment_status, "PAID")
        self.assertTrue(order.qr_code)

    def test_checkin_unpaid_order(self):
        """Check-in tiket belum bayar → error message."""
        staff_user = User.objects.create_user(
            "staffuser2", "staff2@e.com", "Padjadjaran#2026", is_staff=True
        )
        order = Order.objects.create(
            user=self.user,
            ticket=self.ticket,
            participant_name="Luthfi",
            participant_email="luthfi@example.com",
            participant_phone="08123",
            payment_status="PENDING",
        )
        self.client.login(username="staffuser2", password="Padjadjaran#2026")
        resp = self.client.get(reverse("checkin", args=[order.order_code]))
        messages_list = list(resp.context["messages"])
        self.assertTrue(any("belum dibayar" in str(m) for m in messages_list))

    def test_checkin_paid_order(self):
        """Check-in tiket sudah bayar → berhasil."""
        staff_user = User.objects.create_user(
            "staffuser3", "staff3@e.com", "Padjadjaran#2026", is_staff=True
        )
        order = Order.objects.create(
            user=self.user,
            ticket=self.ticket,
            participant_name="Luthfi",
            participant_email="luthfi@example.com",
            participant_phone="08123",
            payment_status="PAID",
        )
        self.client.login(username="staffuser3", password="Padjadjaran#2026")
        resp = self.client.get(reverse("checkin", args=[order.order_code]))
        order.refresh_from_db()
        self.assertTrue(order.checked_in)

class TicketModelTests(TestCase):
    """Test model TicketCategory dan Order."""

    def test_order_code_auto_generated(self):
        user = User.objects.create_user("u1", "u@e.com", "Pwd12345!")
        ticket = _create_ticket_category()
        order = Order.objects.create(
            user=user,
            ticket=ticket,
            participant_name="Test",
            participant_email="t@e.com",
            participant_phone="08123",
        )
        self.assertTrue(order.order_code.startswith("ECO-"))
        self.assertEqual(len(order.order_code), 14)  # ECO- + 10 hex chars

    def test_ticket_sold_count(self):
        user = User.objects.create_user("u2", "u2@e.com", "Pwd12345!")
        ticket = _create_ticket_category(quota=10)
        # Buat 3 order PAID
        for i in range(3):
            Order.objects.create(
                user=user,
                ticket=ticket,
                participant_name=f"P{i}",
                participant_email=f"p{i}@e.com",
                participant_phone="08123",
                payment_status="PAID",
            )
        # Buat 1 order PENDING (tidak terhitung sold)
        Order.objects.create(
            user=user,
            ticket=ticket,
            participant_name="Pending",
            participant_email="pending@e.com",
            participant_phone="08123",
            payment_status="PENDING",
        )
        self.assertEqual(ticket.sold, 3)
        self.assertEqual(ticket.remaining, 7)

    def test_order_str(self):
        user = User.objects.create_user("u3", "u3@e.com", "Pwd12345!")
        ticket = _create_ticket_category()
        order = Order.objects.create(
            user=user,
            ticket=ticket,
            participant_name="Test",
            participant_email="t@e.com",
            participant_phone="08123",
        )
        self.assertEqual(str(order), order.order_code)

    def test_ticket_category_str(self):
        ticket = _create_ticket_category(name="Eco Run 10K")
        self.assertEqual(str(ticket), "Eco Run 10K")
