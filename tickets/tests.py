from django.test import TestCase
from django.urls import reverse
from django.db.models import ProtectedError
from django.contrib.auth.models import User
from .models import TicketCategory, Order

class CheckinBlackBoxTests(TestCase):
    def setUp(self):

        self.staff_user = User.objects.create_user(username='staff', password='password', is_staff=True)
        self.normal_user = User.objects.create_user(username='user', password='password')


        self.ticket_category = TicketCategory.objects.create(
            name="General Admission", price=100000, quota=100
        )

        self.order_paid = Order.objects.create(
            user=self.normal_user,
            ticket=self.ticket_category,
            participant_name="Test User",
            participant_email="test@example.com",
            participant_phone="08123456789",
            payment_status="PAID"
        )

        self.order_pending = Order.objects.create(
            user=self.normal_user,
            ticket=self.ticket_category,
            participant_name="Pending User",
            participant_email="pending@example.com",
            participant_phone="08123456789",
            payment_status="PENDING"
        )

    def test_bbchk01_checkin_by_staff_paid(self):
        """BBCHK01: Check-in oleh staff, order PAID"""
        self.client.login(username='staff', password='password')
        url = reverse('checkin', args=[self.order_paid.order_code])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        

        self.order_paid.refresh_from_db()
        self.assertTrue(self.order_paid.checked_in)
        

        messages = list(response.context['messages'])
        self.assertTrue(any("Check-in berhasil" in str(m) for m in messages))
        print("\n[BBCHK01] Input: user staff, order sudah PAID | Hasil Aktual: checked_in=True, pesan sukses | Status: SUKSES")

    def test_bbchk02_checkin_by_non_staff(self):
        """BBCHK02: Check-in oleh non-staff"""
        self.client.login(username='user', password='password')
        url = reverse('checkin', args=[self.order_paid.order_code])
        response = self.client.get(url)
        

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))
        print("\n[BBCHK02] Input: user biasa | Hasil Aktual: Ditolak -> redirect login | Status: SUKSES")

    def test_bbchk03_checkin_order_pending(self):
        """BBCHK03: Check-in order belum dibayar"""
        self.client.login(username='staff', password='password')
        url = reverse('checkin', args=[self.order_pending.order_code])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        

        self.order_pending.refresh_from_db()
        self.assertFalse(self.order_pending.checked_in)
        

        messages = list(response.context['messages'])
        self.assertTrue(any("Tiket belum dibayar" in str(m) for m in messages))
        print("\n[BBCHK03] Input: order PENDING | Hasil Aktual: Pesan 'Tiket belum dibayar', tidak check-in | Status: SUKSES")

    def test_bbchk04_checkin_ganda(self):
        """BBCHK04: Check-in ganda (idempoten)"""

        self.order_paid.checked_in = True
        self.order_paid.save()

        self.client.login(username='staff', password='password')
        url = reverse('checkin', args=[self.order_paid.order_code])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        

        self.order_paid.refresh_from_db()
        self.assertTrue(self.order_paid.checked_in)
        

        messages = list(response.context['messages'])
        self.assertTrue(any("Check-in berhasil" in str(m) for m in messages))
        print("\n[BBCHK04] Input: order yang sudah checked_in | Hasil Aktual: Tetap sukses (idempoten) | Status: SUKSES")

class OrderUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.category = TicketCategory.objects.create(name="VIP", price=500000)

    def test_ut_ord_01_save_new(self):
        """UT-ORD-01: save() order baru tanpa order_code"""
        order = Order.objects.create(
            user=self.user, ticket=self.category, participant_name="A"
        )
        self.assertTrue(order.order_code.startswith("ECO-"))
        self.assertEqual(len(order.order_code), 14)
        print("\n[UT-ORD-01] Input: order baru tanpa order_code | Output Aktual: order_code terisi, diawali ECO-, panjang 14 | Status: SUKSES")

    def test_ut_ord_02_save_ulang(self):
        """UT-ORD-02: save() order disimpan ulang"""
        order = Order.objects.create(
            user=self.user, ticket=self.category, participant_name="A"
        )
        initial_code = order.order_code
        order.participant_name = "B"
        order.save()
        self.assertEqual(order.order_code, initial_code)
        print("\n[UT-ORD-02] Input: order disimpan ulang | Output Aktual: save() kedua kali -> order_code TIDAK berubah | Status: SUKSES")

    def test_ut_ord_03_order_code_unik(self):
        """UT-ORD-03: order_code unik"""
        order1 = Order.objects.create(user=self.user, ticket=self.category)
        order2 = Order.objects.create(user=self.user, ticket=self.category)
        self.assertNotEqual(order1.order_code, order2.order_code)
        print("\n[UT-ORD-03] Input: dua order dibuat | Output Aktual: kedua order_code berbeda | Status: SUKSES")

    def test_ut_ord_04_default_payment_status(self):
        """UT-ORD-04: Default payment_status"""
        order = Order.objects.create(user=self.user, ticket=self.category)
        self.assertEqual(order.payment_status, "PENDING")
        print("\n[UT-ORD-04] Input: order baru | Output Aktual: status = 'PENDING' | Status: SUKSES")

    def test_ut_ord_05_default_checked_in(self):
        """UT-ORD-05: Default checked_in"""
        order = Order.objects.create(user=self.user, ticket=self.category)
        self.assertFalse(order.checked_in)
        print("\n[UT-ORD-05] Input: order baru | Output Aktual: checked_in = False | Status: SUKSES")

    def test_ut_ord_06_proteksi_fk(self):
        """UT-ORD-06: Proteksi FK ticket"""
        Order.objects.create(user=self.user, ticket=self.category)
        with self.assertRaises(ProtectedError):
            self.category.delete()
        print("\n[UT-ORD-06] Input: hapus TicketCategory yang punya order | Output Aktual: delete() -> Ditolak (on_delete=PROTECT) | Status: SUKSES")

class TicketCategoryUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.category = TicketCategory.objects.create(name="Reguler", price=100000, quota=100)

    def test_ut_tix_01_sold_with_paid(self):
        """UT-TIX-01: sold 2 PAID + 1 PENDING"""
        Order.objects.create(user=self.user, ticket=self.category, payment_status="PAID")
        Order.objects.create(user=self.user, ticket=self.category, payment_status="PAID")
        Order.objects.create(user=self.user, ticket=self.category, payment_status="PENDING")
        self.assertEqual(self.category.sold, 2)
        print("\n[UT-TIX-01] Input: ada 2 order PAID + 1 PENDING | Output Aktual: hitung sold = 2 | Status: SUKSES")

    def test_ut_tix_02_sold_without_paid(self):
        """UT-TIX-02: sold tanpa order PAID"""
        Order.objects.create(user=self.user, ticket=self.category, payment_status="PENDING")
        self.assertEqual(self.category.sold, 0)
        print("\n[UT-TIX-02] Input: tanpa order PAID | Output Aktual: hitung sold = 0 | Status: SUKSES")

    def test_ut_tix_03_remaining(self):
        """UT-TIX-03: remaining quota=100, sold=10"""
        for _ in range(10):
            Order.objects.create(user=self.user, ticket=self.category, payment_status="PAID")
        self.assertEqual(self.category.remaining, 90)
        print("\n[UT-TIX-03] Input: quota=100, sold=10 | Output Aktual: hitung remaining = 90 | Status: SUKSES")

    def test_ut_tix_04_remaining_sold_gt_quota(self):
        """UT-TIX-04: remaining sold > quota"""
        self.category.quota = 2
        self.category.save()
        for _ in range(3):
            Order.objects.create(user=self.user, ticket=self.category, payment_status="PAID")

        self.assertEqual(self.category.remaining, 0)
        print("\n[UT-TIX-04] Input: sold > quota | Output Aktual: hitung remaining = 0 | Status: SUKSES")
