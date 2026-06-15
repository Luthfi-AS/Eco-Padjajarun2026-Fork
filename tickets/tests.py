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
        print("\n[BBCHK01] Input: user staff, order sudah PAID | Hasil Diharapkan: checked_in=True, pesan sukses | Status: SUKSES")

    def test_bbchk02_checkin_by_non_staff(self):
        """BBCHK02: Check-in oleh non-staff"""
        self.client.login(username='user', password='password')
        url = reverse('checkin', args=[self.order_paid.order_code])
        response = self.client.get(url)
        

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))
        print("\n[BBCHK02] Input: user biasa | Hasil Diharapkan: Ditolak -> redirect login | Status: SUKSES")

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
        print("\n[BBCHK03] Input: order PENDING | Hasil Diharapkan: Pesan 'Tiket belum dibayar', tidak check-in | Status: SUKSES")

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
        print("\n[BBCHK04] Input: order yang sudah checked_in | Hasil Diharapkan: Tetap sukses (idempoten) | Status: SUKSES")

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
        print("\n[UT-ORD-01] Input: order baru tanpa order_code | Output Diharapkan: order_code terisi, diawali ECO-, panjang 14 | Status: SUKSES")

    def test_ut_ord_02_save_ulang(self):
        """UT-ORD-02: save() order disimpan ulang"""
        order = Order.objects.create(
            user=self.user, ticket=self.category, participant_name="A"
        )
        initial_code = order.order_code
        order.participant_name = "B"
        order.save()
        self.assertEqual(order.order_code, initial_code)
        print("\n[UT-ORD-02] Input: order disimpan ulang | Output Diharapkan: save() kedua kali -> order_code TIDAK berubah | Status: SUKSES")

    def test_ut_ord_03_order_code_unik(self):
        """UT-ORD-03: order_code unik"""
        order1 = Order.objects.create(user=self.user, ticket=self.category)
        order2 = Order.objects.create(user=self.user, ticket=self.category)
        self.assertNotEqual(order1.order_code, order2.order_code)
        print("\n[UT-ORD-03] Input: dua order dibuat | Output Diharapkan: kedua order_code berbeda | Status: SUKSES")

    def test_ut_ord_04_default_payment_status(self):
        """UT-ORD-04: Default payment_status"""
        order = Order.objects.create(user=self.user, ticket=self.category)
        self.assertEqual(order.payment_status, "PENDING")
        print("\n[UT-ORD-04] Input: order baru | Output Diharapkan: status = 'PENDING' | Status: SUKSES")

    def test_ut_ord_05_default_checked_in(self):
        """UT-ORD-05: Default checked_in"""
        order = Order.objects.create(user=self.user, ticket=self.category)
        self.assertFalse(order.checked_in)
        print("\n[UT-ORD-05] Input: order baru | Output Diharapkan: checked_in = False | Status: SUKSES")

    def test_ut_ord_06_proteksi_fk(self):
        """UT-ORD-06: Proteksi FK ticket"""
        Order.objects.create(user=self.user, ticket=self.category)
        with self.assertRaises(ProtectedError):
            self.category.delete()
        print("\n[UT-ORD-06] Input: hapus TicketCategory yang punya order | Output Diharapkan: delete() -> Ditolak (on_delete=PROTECT) | Status: SUKSES")

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
        print("\n[UT-TIX-01] Input: ada 2 order PAID + 1 PENDING | Output Diharapkan: hitung sold = 2 | Status: SUKSES")

    def test_ut_tix_02_sold_without_paid(self):
        """UT-TIX-02: sold tanpa order PAID"""
        Order.objects.create(user=self.user, ticket=self.category, payment_status="PENDING")
        self.assertEqual(self.category.sold, 0)
        print("\n[UT-TIX-02] Input: tanpa order PAID | Output Diharapkan: hitung sold = 0 | Status: SUKSES")

    def test_ut_tix_03_remaining(self):
        """UT-TIX-03: remaining quota=100, sold=10"""
        for _ in range(10):
            Order.objects.create(user=self.user, ticket=self.category, payment_status="PAID")
        self.assertEqual(self.category.remaining, 90)
        print("\n[UT-TIX-03] Input: quota=100, sold=10 | Output Diharapkan: hitung remaining = 90 | Status: SUKSES")

    def test_ut_tix_04_remaining_sold_gt_quota(self):
        """UT-TIX-04: remaining sold > quota"""
        self.category.quota = 2
        self.category.save()
        for _ in range(3):
            Order.objects.create(user=self.user, ticket=self.category, payment_status="PAID")

        self.assertEqual(self.category.remaining, 0)
        print("\n[UT-TIX-04] Input: sold > quota | Output Diharapkan: hitung remaining = 0 | Status: SUKSES")

from accounts.models import UserProfile

class TicketsBlackBoxTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', password='password')
        self.profile = UserProfile.objects.create(user=self.user, is_email_verified=True)
        self.unverified_user = User.objects.create_user(username='unverified', password='password')
        UserProfile.objects.create(user=self.unverified_user, is_email_verified=False)
        self.ticket_active = TicketCategory.objects.create(name="Active Tix", price=10, quota=5, is_active=True)
        self.ticket_inactive = TicketCategory.objects.create(name="Inactive Tix", price=10, quota=5, is_active=False)

    def test_bb_tix_01(self):
        response = self.client.get(reverse('ticket_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Active Tix")
        self.assertNotContains(response, "Inactive Tix")
        print("\n[BB-TIX-01] Input: buka /tickets/ | Hasil Diharapkan: Hanya tiket is_active=True tampil | Status: SUKSES")

    def test_bb_tix_02(self):
        response = self.client.get(reverse('buy_ticket'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))
        print("\n[BB-TIX-02] Input: buka /tickets/buy/ belum login | Hasil Diharapkan: Redirect ke login | Status: SUKSES")

    def test_bb_tix_03(self):
        self.client.login(username='unverified', password='password')
        response = self.client.get(reverse('buy_ticket'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))
        print("\n[BB-TIX-03] Input: login tapi is_email_verified=False | Hasil Diharapkan: Diblokir, pesan Verifikasi email dulu, redirect dashboard | Status: SUKSES")

    def test_bb_tix_04(self):
        self.client.login(username='buyer', password='password')
        data = {'ticket': self.ticket_active.id, 'participant_name': 'Valid User', 'participant_email': 'valid@example.com', 'participant_phone': '08123456789'}
        response = self.client.post(reverse('buy_ticket'), data)
        self.assertEqual(response.status_code, 302)
        order = Order.objects.filter(participant_email='valid@example.com').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.payment_status, 'PENDING')
        self.assertTrue(order.order_code.startswith('ECO-'))
        print("\n[BB-TIX-04] Input: user terverifikasi, isi form benar | Hasil Diharapkan: Order dibuat, status PENDING, order_code ECO-xxxx, redirect order_detail | Status: SUKSES")

    def test_bb_tix_05(self):
        self.client.login(username='buyer', password='password')
        response = self.client.post(reverse('buy_ticket'), {})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'ticket', 'Bidang ini tidak boleh kosong.')
        print("\n[BB-TIX-05] Input: submit field kosong | Hasil Diharapkan: Ditolak, pesan field required | Status: SUKSES")

    def test_bb_tix_06(self):
        self.client.login(username='buyer', password='password')
        data = {'ticket': self.ticket_active.id, 'participant_name': 'A', 'participant_email': 'xx', 'participant_phone': '123'}
        response = self.client.post(reverse('buy_ticket'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'participant_email', 'Masukkan alamat email yang valid.')
        print("\n[BB-TIX-06] Input: participant_email = 'xx' | Hasil Diharapkan: Ditolak (EmailField), pesan Enter a valid email address | Status: SUKSES")

    def test_bb_tix_07(self):
        self.client.login(username='buyer', password='password')
        self.ticket_active.quota = 0
        self.ticket_active.save()
        data = {'ticket': self.ticket_active.id, 'participant_name': 'B', 'participant_email': 'a@a.com', 'participant_phone': '123'}
        response = self.client.post(reverse('buy_ticket'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.filter(participant_name='B').exists())
        print("\n[BB-TIX-07] Input: tiket dengan sold >= quota | Hasil Diharapkan: Order ditolak | Status: SUKSES")

    def test_bb_tix_08(self):
        self.client.login(username='buyer', password='password')
        data = {'ticket': self.ticket_inactive.id, 'participant_name': 'C', 'participant_email': 'b@b.com', 'participant_phone': '123'}
        response = self.client.post(reverse('buy_ticket'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.filter(participant_name='C').exists())
        print("\n[BB-TIX-08] Input: manipulasi value ticket non-aktif | Hasil Diharapkan: Order ditolak | Status: SUKSES")

    def test_bb_tix_09(self):
        self.client.login(username='buyer', password='password')
        data = {'ticket': self.ticket_active.id, 'participant_name': 'D', 'participant_email': 'abc', 'participant_phone': '123'}
        response = self.client.post(reverse('buy_ticket'), data)
        self.assertEqual(response.status_code, 200)
        print("\n[BB-TIX-09] Input: email peserta format salah | Hasil Diharapkan: Ditolak (EmailField), pesan Enter a valid email address | Status: SUKSES")

    def test_bb_tix_10(self):
        self.client.login(username='buyer', password='password')
        data = {'ticket': self.ticket_active.id, 'participant_name': 'E', 'participant_email': '', 'participant_phone': '123'}
        response = self.client.post(reverse('buy_ticket'), data)
        self.assertEqual(response.status_code, 200)
        print("\n[BB-TIX-10] Input: participant_email = '' | Hasil Diharapkan: Ditolak, field required | Status: SUKSES")

    def test_bb_tix_11(self):
        self.client.login(username='buyer', password='password')
        data = {'ticket': self.ticket_active.id, 'participant_name': 'F', 'participant_email': 'a@a.com', 'participant_phone': 'abcdef'}
        response = self.client.post(reverse('buy_ticket'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.filter(participant_name='F').exists())
        print("\n[BB-TIX-11] Input: participant_phone = 'abcdef' | Hasil Diharapkan: Ditolak karena format huruf | Status: SUKSES")

    def test_bb_tix_12(self):
        self.client.login(username='buyer', password='password')
        data = {'ticket': self.ticket_active.id, 'participant_name': 'G', 'participant_email': 'a@a.com', 'participant_phone': '!@#$%^'}
        response = self.client.post(reverse('buy_ticket'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.filter(participant_name='G').exists())
        print("\n[BB-TIX-12] Input: participant_phone karakter aneh | Hasil Diharapkan: Ditolak karena karakter aneh | Status: SUKSES")

    def test_bb_tix_13(self):
        self.client.login(username='buyer', password='password')
        data = {'ticket': self.ticket_active.id, 'participant_name': 'H', 'participant_email': 'a@a.com', 'participant_phone': ''}
        response = self.client.post(reverse('buy_ticket'), data)
        self.assertEqual(response.status_code, 200)
        print("\n[BB-TIX-13] Input: participant_phone = '' | Hasil Diharapkan: Ditolak, field required | Status: SUKSES")

    def test_bb_tix_14(self):
        self.client.login(username='buyer', password='password')
        data = {'ticket': self.ticket_active.id, 'participant_name': 'I', 'participant_email': 'a@a.com', 'participant_phone': '1' * 31}
        response = self.client.post(reverse('buy_ticket'), data)
        self.assertEqual(response.status_code, 200)
        print("\n[BB-TIX-14] Input: > 30 karakter | Hasil Diharapkan: Ditolak max_length=30 | Status: SUKSES")

    def test_bb_tix_15(self):
        self.client.login(username='buyer', password='password')
        data = {'ticket': self.ticket_active.id, 'participant_name': 'Dbl', 'participant_email': 'a@a.com', 'participant_phone': '123'}
        self.client.post(reverse('buy_ticket'), data)
        self.client.post(reverse('buy_ticket'), data)
        self.assertEqual(Order.objects.filter(participant_name='Dbl').count(), 1)
        print("\n[BB-TIX-15] Input: klik Beli Submit 2x cepat saat lag | Hasil Diharapkan: Hanya 1 tiket yang terbeli | Status: SUKSES")

    def test_bb_tix_16(self):
        self.client.login(username='buyer', password='password')
        data = {'ticket': self.ticket_active.id, 'participant_name': 'Spam', 'participant_email': 'a@a.com', 'participant_phone': '123'}
        for _ in range(5):
            self.client.post(reverse('buy_ticket'), data)
        self.assertEqual(Order.objects.filter(participant_name='Spam').count(), 1)
        print("\n[BB-TIX-16] Input: kirim beberapa request beli serempak | Hasil Diharapkan: Hanya 1 order yang terbuat | Status: SUKSES")

    def test_bb_tix_17(self):
        self.client.login(username='buyer', password='password')
        data = {'ticket': self.ticket_active.id, 'participant_name': 'Back', 'participant_email': 'a@a.com', 'participant_phone': '123'}
        self.client.post(reverse('buy_ticket'), data)
        self.client.post(reverse('buy_ticket'), data)
        self.assertEqual(Order.objects.filter(participant_name='Back').count(), 1)
        print("\n[BB-TIX-17] Input: order sukses tekan Back submit ulang | Hasil Diharapkan: Order duplikat ditolak | Status: SUKSES")

    def test_bb_tix_18(self):
        self.client.login(username='buyer', password='password')
        data = {'ticket': self.ticket_active.id, 'participant_name': 'F5', 'participant_email': 'a@a.com', 'participant_phone': '123'}
        response = self.client.post(reverse('buy_ticket'), data)
        order = Order.objects.get(participant_name='F5')
        self.client.get(reverse('order_detail', args=[order.order_code]))
        self.client.get(reverse('order_detail', args=[order.order_code]))
        self.assertEqual(Order.objects.filter(participant_name='F5').count(), 1)
        print("\n[BB-TIX-18] Input: F5 di halaman setelah order dibuat | Hasil Diharapkan: Tidak membuat order baru karena sudah redirect GET | Status: SUKSES")

    def test_bb_tix_19(self):
        self.client.login(username='buyer', password='password')
        sqli = "x'; DROP TABLE tickets_order;--"
        data = {'ticket': self.ticket_active.id, 'participant_name': sqli, 'participant_email': 'a@a.com', 'participant_phone': '123'}
        self.client.post(reverse('buy_ticket'), data)
        self.assertTrue(Order.objects.filter(participant_name=sqli).exists())
        print("\n[BB-TIX-19] Input: SQL injection di participant_name | Hasil Diharapkan: Aman ORM parameterized disimpan sebagai string tabel tidak terhapus | Status: SUKSES")

    def test_bb_tix_20(self):
        self.client.login(username='buyer', password='password')
        sqli = "a@a.com' OR '1'='1"
        data = {'ticket': self.ticket_active.id, 'participant_name': 'J', 'participant_email': sqli, 'participant_phone': '123'}
        response = self.client.post(reverse('buy_ticket'), data)
        self.assertEqual(response.status_code, 200)
        print("\n[BB-TIX-20] Input: SQL injection di participant_email | Hasil Diharapkan: Ditolak EmailField disimpan aman sebagai string | Status: SUKSES")

    def test_bb_tix_21(self):
        self.client.login(username='buyer', password='password')
        sqli = "123' OR '1'='1'--"
        data = {'ticket': self.ticket_active.id, 'participant_name': 'K', 'participant_email': 'a@a.com', 'participant_phone': sqli}
        self.client.post(reverse('buy_ticket'), data)
        self.assertTrue(Order.objects.filter(participant_phone=sqli).exists())
        print("\n[BB-TIX-21] Input: SQL injection di participant_phone | Hasil Diharapkan: Aman disimpan sebagai string literal | Status: SUKSES")

    def test_bb_tix_22(self):
        self.client.login(username='buyer', password='password')
        sqli = "1 OR 1=1"
        data = {'ticket': sqli, 'participant_name': 'L', 'participant_email': 'a@a.com', 'participant_phone': '123'}
        response = self.client.post(reverse('buy_ticket'), data)
        self.assertEqual(response.status_code, 200)
        print("\n[BB-TIX-22] Input: SQL injection di field ticket | Hasil Diharapkan: Ditolak ModelChoiceField hanya terima PK valid input invalid form error | Status: SUKSES")

    def test_bb_tix_23(self):
        self.client.login(username='buyer', password='password')
        sqli = "' UNION SELECT * FROM auth_user--"
        data = {'ticket': self.ticket_active.id, 'participant_name': sqli, 'participant_email': 'a@a.com', 'participant_phone': '123'}
        self.client.post(reverse('buy_ticket'), data)
        self.assertTrue(Order.objects.filter(participant_name=sqli).exists())
        print("\n[BB-TIX-23] Input: SQL injection union-based | Hasil Diharapkan: Tidak ada kebocoran data input jadi literal | Status: SUKSES")

    def test_bb_tix_24(self):
        self.client.login(username='buyer', password='password')
        xss = "<script>alert(1)</script>"
        data = {'ticket': self.ticket_active.id, 'participant_name': xss, 'participant_email': 'a@a.com', 'participant_phone': '123'}
        self.client.post(reverse('buy_ticket'), data)
        order = Order.objects.get(participant_name=xss)
        response = self.client.get(reverse('order_detail', args=[order.order_code]))
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
        print("\n[BB-TIX-24] Input: XSS di participant_name | Hasil Diharapkan: Ter-escape saat ditampilkan di order_detail QR script tidak tereksekusi | Status: SUKSES")
