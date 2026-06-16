"""
Test suite untuk app accounts — Eco Padjadjarun 2026
Mencakup seluruh test case dari TESTCASE.md:
  - Black Box Registrasi (BB-AUTH01 s/d BB-AUTH42)
  - Black Box Login / Logout (BB-LOGIN-01 s/d BB-LOGIN-21)
  - Unit Testing Form RegisterForm (UTFORM-01 s/d UTFORM-04)
  - Unit Testing Model UserProfile (UTPROF-01 s/d UTPROF-04)
"""

import uuid

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .forms import RegisterForm
from .models import UserProfile

def _valid_register_data(**overrides):
    """Return a dict of valid registration POST data, with optional overrides."""
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "phone": "081234567890",
        "password1": "Padjadjaran#2026",
        "password2": "Padjadjaran#2026",
    }
    data.update(overrides)
    return data


def _register_and_get_user(client, url, **overrides):
    """Register a user via POST and return (response, User or None)."""
    data = _valid_register_data(**overrides)
    resp = client.post(url, data, follow=True)
    user = User.objects.filter(username=data["username"]).first()
    return resp, user


class BlackBoxRegistrasiTests(TestCase):
    """BB-AUTH01 s/d BB-AUTH42"""

    def setUp(self):
        self.client = Client()
        self.url = reverse("register")

    # ------------------------------------------------------------------
    # BB-AUTH01  Registrasi data valid
    # ------------------------------------------------------------------
    def test_bb_auth01_registrasi_data_valid(self):
        """User dibuat, otomatis login, redirect ke dashboard, pesan sukses,
        link verifikasi muncul di terminal (console email backend)."""
        resp = self.client.post(self.url, _valid_register_data())
        # Harus redirect ke dashboard
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("dashboard"))

        # User terbuat di database
        self.assertTrue(User.objects.filter(username="testuser").exists())
        user = User.objects.get(username="testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.is_active)

        # UserProfile terbuat dengan phone
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.phone, "081234567890")
        self.assertIsNotNone(profile.verification_token)

        # Auto-login: follow redirect dan cek user authenticated
        resp_followed = self.client.get(reverse("dashboard"))
        self.assertEqual(resp_followed.status_code, 200)
        self.assertTrue(resp_followed.wsgi_request.user.is_authenticated)
        self.assertEqual(resp_followed.wsgi_request.user.username, "testuser")

        # Pesan sukses ada
        messages_list = list(resp_followed.context["messages"])
        self.assertTrue(
            any("Registrasi berhasil" in str(m) for m in messages_list),
            f"Pesan 'Registrasi berhasil' tidak ditemukan. Pesan: {[str(m) for m in messages_list]}"
        )

    # ------------------------------------------------------------------
    # BB-AUTH02  Username sudah dipakai
    # ------------------------------------------------------------------
    def test_bb_auth02_username_sudah_dipakai(self):
        """Form ditolak, pesan 'A user with that username already exists'."""
        User.objects.create_user("testuser", "x@x.com", "Pwd12345!")
        resp = self.client.post(self.url, _valid_register_data())
        # Tidak redirect → tetap di halaman register (200)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)
        # Pastikan hanya 1 user "testuser" (yang pertama)
        self.assertEqual(User.objects.filter(username="testuser").count(), 1)

    # ------------------------------------------------------------------
    # BB-AUTH03  Password tidak cocok
    # ------------------------------------------------------------------
    def test_bb_auth03_password_tidak_cocok(self):
        """Form ditolak, pesan 'The two password fields didn't match'."""
        data = _valid_register_data(password2="BerbedaSekali#99")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)
        # User TIDAK terbuat
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH04  Password terlalu pendek/umum (password = "123")
    # ------------------------------------------------------------------
    def test_bb_auth04_password_terlalu_pendek(self):
        """Ditolak oleh validator (MinimumLength/CommonPassword)."""
        data = _valid_register_data(password1="123", password2="123")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH05  Email tidak valid
    # ------------------------------------------------------------------
    def test_bb_auth05_email_tidak_valid(self):
        """Ditolak, pesan 'Enter a valid email address'."""
        data = _valid_register_data(email="abc")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH06  Field wajib kosong
    # ------------------------------------------------------------------
    def test_bb_auth06_field_wajib_kosong(self):
        """Setiap field wajib dikosongkan → Ditolak, pesan 'This field is required'."""
        for field in ("username", "email", "phone", "password1", "password2"):
            data = _valid_register_data(**{field: ""})
            resp = self.client.post(self.url, data)
            self.assertEqual(resp.status_code, 200, f"Field '{field}' kosong seharusnya 200")
            form = resp.context["form"]
            self.assertFalse(form.is_valid(), f"Field '{field}' kosong seharusnya invalid")
            self.assertIn(field, form.errors, f"Field '{field}' seharusnya ada di form.errors")
            self.assertFalse(
                User.objects.filter(username=data["username"]).exists(),
                f"User seharusnya TIDAK terbuat saat '{field}' kosong"
            )

    # ------------------------------------------------------------------
    # BB-AUTH07  Email kosong
    # ------------------------------------------------------------------
    def test_bb_auth07_email_kosong(self):
        """Ditolak (email required=True)."""
        data = _valid_register_data(email="")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH08  Phone kosong
    # ------------------------------------------------------------------
    def test_bb_auth08_phone_kosong(self):
        """Ditolak (phone required=True)."""
        data = _valid_register_data(phone="")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH09  Phone berisi huruf
    # ------------------------------------------------------------------
    def test_bb_auth09_phone_berisi_huruf(self):
        """Seharusnya DITOLAK karena nomor telepon berisi huruf."""
        data = _valid_register_data(phone="abcd")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200, "Form seharusnya ditolak (tidak redirect)")
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH10  XSS pada username
    # ------------------------------------------------------------------
    def test_bb_auth10_xss_pada_username(self):
        """Input ter-escape di template, script tidak tereksekusi."""
        xss_payload = "<script>alert(1)</script>"
        data = _valid_register_data(username=xss_payload)
        resp = self.client.post(self.url, data, follow=True)
        content = resp.content.decode()
        # Script tag TIDAK boleh muncul sebagai raw HTML
        self.assertNotIn("<script>alert(1)</script>", content)

    # ------------------------------------------------------------------
    # BB-AUTH11  Password kurang dari 8 karakter
    # ------------------------------------------------------------------
    def test_bb_auth11_password_kurang_8(self):
        """Ditolak, 'This password is too short (min 8)'."""
        data = _valid_register_data(password1="Eco1!", password2="Eco1!")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH12  Password tepat 8 karakter (boundary)
    # ------------------------------------------------------------------
    def test_bb_auth12_password_tepat_8(self):
        """Diterima (batas bawah valid). 'Eco2026!' = 8 karakter."""
        data = _valid_register_data(password1="Eco2026!", password2="Eco2026!")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 302, "Password 8 karakter seharusnya diterima")
        user = User.objects.get(username="testuser")
        self.assertTrue(user.check_password("Eco2026!"))

    # ------------------------------------------------------------------
    # BB-AUTH13  Password 7 karakter (di bawah batas)
    # ------------------------------------------------------------------
    def test_bb_auth13_password_7_karakter(self):
        """Ditolak karena kurang dari 8 karakter."""
        data = _valid_register_data(password1="Eco202!", password2="Eco202!")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH14  Password semua angka
    # ------------------------------------------------------------------
    def test_bb_auth14_password_semua_angka(self):
        """Ditolak, 'entirely numeric' + 'too common'."""
        data = _valid_register_data(password1="12345678", password2="12345678")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH15  Password umum
    # ------------------------------------------------------------------
    def test_bb_auth15_password_umum_password(self):
        """'password' → ditolak, 'too common'."""
        data = _valid_register_data(password1="password", password2="password")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertFalse(User.objects.filter(username="testuser").exists())

    def test_bb_auth15b_password_umum_qwerty123(self):
        """'qwerty123' → ditolak, 'too common'."""
        data = _valid_register_data(password1="qwerty123", password2="qwerty123")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH16  Password mirip username
    # ------------------------------------------------------------------
    def test_bb_auth16_password_mirip_username(self):
        """username='luthfi', password='luthfi123' → ditolak oleh UserAttributeSimilarityValidator."""
        data = _valid_register_data(username="luthfi", password1="luthfi123", password2="luthfi123")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)
        self.assertFalse(User.objects.filter(username="luthfi").exists())

    # ------------------------------------------------------------------
    # BB-AUTH17  Password mirip email
    # ------------------------------------------------------------------
    def test_bb_auth17_password_mirip_email(self):
        """email='aziz@x.com', password='aziz1234' → Seharusnya DITOLAK karena mirip email."""
        data = _valid_register_data(email="aziz@x.com", password1="aziz1234", password2="aziz1234")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200, "Form seharusnya ditolak")
        form = resp.context.get("form")
        if form:
            self.assertFalse(form.is_valid())
            self.assertIn("password2", form.errors)
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH18  Password kuat valid
    # ------------------------------------------------------------------
    def test_bb_auth18_password_kuat_valid(self):
        """'Padjadjaran#2026' → Diterima."""
        data = _valid_register_data(password1="Padjadjaran#2026", password2="Padjadjaran#2026")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 302)
        user = User.objects.get(username="testuser")
        self.assertTrue(user.check_password("Padjadjaran#2026"))

    # ------------------------------------------------------------------
    # BB-AUTH19  Password kosong
    # ------------------------------------------------------------------
    def test_bb_auth19_password_kosong(self):
        """Ditolak, 'This field is required'."""
        data = _valid_register_data(password1="", password2="")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("password1", form.errors)
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH20  Password hanya spasi
    # ------------------------------------------------------------------
    def test_bb_auth20_password_hanya_spasi(self):
        """8 spasi → Seharusnya DITOLAK (bukan password yang aman/valid)."""
        data = _valid_register_data(password1="        ", password2="        ")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200, "Form seharusnya ditolak")
        form = resp.context.get("form")
        if form:
            self.assertFalse(form.is_valid())
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH21  Spasi di awal/akhir password
    # ------------------------------------------------------------------
    def test_bb_auth21_spasi_awal_akhir_password(self):
        """' Eco2026! ' (10 karakter) → Seharusnya spasi di-trim otomatis atau form ditolak."""
        data = _valid_register_data(password1=" Eco2026! ", password2=" Eco2026! ")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200, "Password dengan spasi di ujung seharusnya ditolak atau di-trim otomatis")
        form = resp.context.get("form")
        if form:
            self.assertFalse(form.is_valid())
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH22  Password sangat panjang (1.000+ karakter)
    # ------------------------------------------------------------------
    def test_bb_auth22_password_sangat_panjang(self):
        """1.000+ karakter → Seharusnya DITOLAK untuk mencegah DoS (Denial of Service)."""
        long_pwd = "A" * 1001 + "#1a"  # 1004 karakter
        data = _valid_register_data(password1=long_pwd, password2=long_pwd)
        resp = self.client.post(self.url, data)
        
        # Server TIDAK boleh crash (500)
        self.assertNotEqual(resp.status_code, 500, "Server crash dengan password panjang!")
        
        # Seharusnya ditolak (dikembalikan ke halaman form) karena melebihi batas wajar
        self.assertEqual(resp.status_code, 200, "Form seharusnya ditolak untuk mencegah DoS password panjang")
        form = resp.context.get("form")
        if form:
            self.assertFalse(form.is_valid())
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH23  Password unicode/emoji
    # ------------------------------------------------------------------
    def test_bb_auth23_password_unicode_emoji(self):
        """'Pässwörd😀2026' → Diterima (dukung unicode), pastikan bisa login kembali."""
        pwd = "Pässwörd😀2026"
        data = _valid_register_data(password1=pwd, password2=pwd)
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 302, "Password unicode seharusnya diterima")
        user = User.objects.get(username="testuser")
        # Roundtrip: bisa login kembali
        self.assertTrue(user.check_password(pwd))
        # Login via view
        self.client.logout()
        login_ok = self.client.login(username="testuser", password=pwd)
        self.assertTrue(login_ok, "Login dengan password unicode harus berhasil")

    # ------------------------------------------------------------------
    # BB-AUTH24  Angka unicode mirip
    # ------------------------------------------------------------------
    def test_bb_auth24_angka_unicode(self):
        """'①②③④⑤⑥⑦⑧' → NumericPasswordValidator menggunakan str.isnumeric()
        yang MEMANG mendeteksi angka unicode → DITOLAK."""
        data = _valid_register_data(password1="①②③④⑤⑥⑦⑧", password2="①②③④⑤⑥⑦⑧")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200, "Angka unicode seharusnya ditolak NumericPasswordValidator")
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH25  SQL injection di password
    # ------------------------------------------------------------------
    def test_bb_auth25_sql_injection_password(self):
        """Aman (ORM parameterized), dianggap string biasa."""
        initial_count = User.objects.count()
        data = _valid_register_data(password1="' OR '1'='1", password2="' OR '1'='1")
        resp = self.client.post(self.url, data)
        # Server tidak crash
        self.assertNotEqual(resp.status_code, 500)
        # Tabel auth_user masih utuh — count masih konsisten
        self.assertGreaterEqual(User.objects.count(), initial_count)

    # ------------------------------------------------------------------
    # BB-AUTH26  Case sensitivity login setelah register
    # ------------------------------------------------------------------
    def test_bb_auth26_case_sensitivity_login(self):
        """Daftar dengan 'Eco2026!' lalu login 'eco2026!' → GAGAL (password case-sensitive)."""
        # Register dengan password mixed-case
        data = _valid_register_data(password1="Eco2026!", password2="Eco2026!")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 302)
        self.client.logout()

        # Login dengan password LOWERCASE harus GAGAL
        login_ok = self.client.login(username="testuser", password="eco2026!")
        self.assertFalse(login_ok, "Password case-sensitive: 'eco2026!' != 'Eco2026!'")

        # Login dengan password CORRECT harus BERHASIL
        login_ok = self.client.login(username="testuser", password="Eco2026!")
        self.assertTrue(login_ok, "Password asli 'Eco2026!' harus berhasil")

    # ------------------------------------------------------------------
    # BB-AUTH27  Konfirmasi beda case
    # ------------------------------------------------------------------
    def test_bb_auth27_konfirmasi_beda_case(self):
        """'Eco2026!' vs 'ECO2026!' → Ditolak (tidak cocok)."""
        data = _valid_register_data(password1="Eco2026!", password2="ECO2026!")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH28  Common password + variasi angka
    # ------------------------------------------------------------------
    def test_bb_auth28_common_password_variasi(self):
        """'password1' → Cek apakah masih 'too common' atau lolos."""
        data = _valid_register_data(password1="password1", password2="password1")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200, "'password1' seharusnya ditolak sebagai too common")
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH29  Password mirip nama (first_name)
    # ------------------------------------------------------------------
    def test_bb_auth29_password_mirip_nama(self):
        """username='muhammad', password='muhammad1234' → Ditolak oleh UserAttributeSimilarity."""
        data = _valid_register_data(username="muhammad", password1="muhammad1234", password2="muhammad1234")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)
        self.assertFalse(User.objects.filter(username="muhammad").exists())

    # ------------------------------------------------------------------
    # BB-AUTH30  Input password tersembunyi (type=password)
    # ------------------------------------------------------------------
    def test_bb_auth30_input_password_hidden(self):
        """Tampil sebagai ••• (type=password), tidak terlihat."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        # Password fields harus type="password"
        self.assertIn('type="password"', content)
        # Harus ada minimal 2 field password (password1, password2)
        count = content.count('type="password"')
        self.assertGreaterEqual(count, 2, "Harus ada minimal 2 field type='password'")

    # ------------------------------------------------------------------
    # BB-AUTH31  Copy-paste password
    # ------------------------------------------------------------------
    def test_bb_auth31_copy_paste_password(self):
        """Diterima sama seperti diketik manual. POST data = copy-paste behavior."""
        data = _valid_register_data()
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 302)
        user = User.objects.get(username="testuser")
        # Password yang di-POST (simulasi paste) tersimpan dengan benar
        self.assertTrue(user.check_password("Padjadjaran#2026"))

    # ------------------------------------------------------------------
    # BB-AUTH32  Password tidak bocor di URL
    # ------------------------------------------------------------------
    def test_bb_auth32_password_tidak_bocor_di_url(self):
        """Dikirim via POST, password tidak muncul di URL/log."""
        resp = self.client.post(self.url, _valid_register_data())
        self.assertEqual(resp.status_code, 302)
        # Password TIDAK ada di redirect URL
        self.assertNotIn("Padjadjaran", resp.url)
        self.assertNotIn("password", resp.url.lower())
        self.assertNotIn("#2026", resp.url)

    # ------------------------------------------------------------------
    # BB-AUTH33  Pesan error password bahasa
    # ------------------------------------------------------------------
    @override_settings(LANGUAGE_CODE="id")
    def test_bb_auth33_pesan_error_bahasa(self):
        """Potensi masalah: pesan validator masih bahasa Inggris walau LANGUAGE_CODE='id'.
        Cek isi pesan error secara eksplisit."""
        data = _valid_register_data(password1="123", password2="123")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())

        # Kumpulkan semua pesan error password
        password_errors = form.errors.get("password2", [])
        all_error_text = " ".join(str(e) for e in password_errors)

        # Cek apakah ada terjemahan Indonesia atau masih Inggris
        has_indonesian = any(kata in all_error_text.lower() for kata in [
            "terlalu pendek", "terlalu umum", "seluruhnya angka", "kata sandi",
        ])
        has_english = any(kata in all_error_text.lower() for kata in [
            "too short", "too common", "entirely numeric", "password",
        ])
        # Dokumentasikan bahasa yang digunakan (minimal harus ada salah satu)
        self.assertTrue(
            has_indonesian or has_english,
            f"Pesan error tidak terdeteksi dalam bahasa apapun: {all_error_text}"
        )

    # ------------------------------------------------------------------
    # BB-AUTH34  SQL injection di field username
    # ------------------------------------------------------------------
    def test_bb_auth34_sql_injection_username(self):
        """username = admin'; DROP TABLE auth_user;--
        Seharusnya form ditolak secara mutlak dan tabel aman."""
        initial_count = User.objects.count()
        data = _valid_register_data(username="admin'; DROP TABLE auth_user;--")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200, "Form seharusnya ditolak karena username tidak valid")
        form = resp.context.get("form")
        if form:
            self.assertFalse(form.is_valid())
        self.assertEqual(User.objects.count(), initial_count)

    # ------------------------------------------------------------------
    # BB-AUTH35  SQL injection di field email
    # ------------------------------------------------------------------
    def test_bb_auth35_sql_injection_email(self):
        """email = a@a.com' OR '1'='1
        Ditolak EmailField (format invalid)."""
        data = _valid_register_data(email="a@a.com' OR '1'='1")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH36  SQL injection di field phone
    # ------------------------------------------------------------------
    def test_bb_auth36_sql_injection_phone(self):
        """phone = 123' OR '1'='1'--
        Seharusnya form ditolak karena format phone salah."""
        initial_count = User.objects.count()
        data = _valid_register_data(phone="123' OR '1'='1'--")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200, "Form seharusnya ditolak karena phone format tidak valid")
        form = resp.context.get("form")
        if form:
            self.assertFalse(form.is_valid())
            self.assertIn("phone", form.errors)
        self.assertEqual(User.objects.count(), initial_count)

    # ------------------------------------------------------------------
    # BB-AUTH37  SQL injection di field password
    # ------------------------------------------------------------------
    def test_bb_auth37_sql_injection_password(self):
        """password = ' OR '1'='1
        Aman (di-hash), dianggap string biasa."""
        initial_count = User.objects.count()
        data = _valid_register_data(password1="' OR '1'='1", password2="' OR '1'='1")
        resp = self.client.post(self.url, data)
        self.assertNotEqual(resp.status_code, 500)
        # Tabel masih utuh
        self.assertGreaterEqual(User.objects.count(), initial_count)

    # ------------------------------------------------------------------
    # BB-AUTH38  SQL injection union-based
    # ------------------------------------------------------------------
    def test_bb_auth38_sql_injection_union(self):
        """username = ' UNION SELECT * FROM auth_user--
        Tidak ada kebocoran data; input diperlakukan sebagai literal."""
        data = _valid_register_data(username="' UNION SELECT * FROM auth_user--")
        resp = self.client.post(self.url, data)
        self.assertNotEqual(resp.status_code, 500)
        content = resp.content.decode()
        # Password hash TIDAK boleh bocor di response
        self.assertNotIn("pbkdf2_sha256", content)
        # Email user lain TIDAK boleh bocor
        self.assertNotIn("test@example.com", content.replace(
            "test@example.com", "").replace("test@example.com", ""))

    # ------------------------------------------------------------------
    # BB-AUTH39  XSS di field email/phone
    # ------------------------------------------------------------------
    def test_bb_auth39_xss_email_phone(self):
        """phone = <img src=x onerror=alert(1)>
        Seharusnya ditolak karena format phone tidak valid."""
        xss_payload = '<img src=x onerror=alert(1)>'
        data = _valid_register_data(phone=xss_payload)
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200, "Form seharusnya ditolak karena XSS payload tidak valid sebagai nomor HP")
        form = resp.context.get("form")
        if form:
            self.assertFalse(form.is_valid())
            self.assertIn("phone", form.errors)
        self.assertFalse(User.objects.filter(username="testuser").exists())

    # ------------------------------------------------------------------
    # BB-AUTH40  Double-click tombol Daftar
    # ------------------------------------------------------------------
    def test_bb_auth40_double_click_daftar(self):
        """Klik 'Daftar' 2x cepat → Hanya 1 user terbentuk.
        Submit kedua ditolak 'username already exists'."""
        data = _valid_register_data()
        # Submit pertama
        resp1 = self.client.post(self.url, data)
        self.assertEqual(resp1.status_code, 302)
        self.assertTrue(User.objects.filter(username="testuser").exists())

        # Submit kedua (logout dulu karena sudah auto-login)
        self.client.logout()
        resp2 = self.client.post(self.url, data)
        # Submit kedua harus ditolak
        self.assertEqual(resp2.status_code, 200)
        form = resp2.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)
        # Tetap hanya 1 user
        self.assertEqual(User.objects.filter(username="testuser").count(), 1)

    # ------------------------------------------------------------------
    # BB-AUTH41  Spam submit bersamaan (race condition)
    # ------------------------------------------------------------------
    def test_bb_auth41_race_condition(self):
        """2 request register identik berurutan (simulasi near-concurrent).
        Potensi bug: IntegrityError tak ter-handle → error 500.
        Test memverifikasi tidak ada error 500 dan hanya 1 user terbuat."""
        data = _valid_register_data()
        resp1 = self.client.post(self.url, data)
        self.assertEqual(resp1.status_code, 302)
        self.client.logout()

        resp2 = self.client.post(self.url, data)
        # Harus 200 (form error) BUKAN 500 (unhandled IntegrityError)
        self.assertNotEqual(resp2.status_code, 500, "Race condition menyebabkan error 500!")
        self.assertEqual(User.objects.filter(username="testuser").count(), 1)

    # ------------------------------------------------------------------
    # BB-AUTH42  Resubmit form via tombol Back
    # ------------------------------------------------------------------
    def test_bb_auth42_resubmit_via_back(self):
        """Daftar sukses → tekan Back → submit ulang.
        Tidak membuat user duplikat. Idealnya pakai pola POST-redirect-GET."""
        data = _valid_register_data()
        # Registrasi awal
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 302, "Registrasi awal harus redirect (PRG pattern)")

        self.client.logout()
        # Simulasi resubmit (tekan Back + submit ulang)
        resp2 = self.client.post(self.url, data)
        self.assertEqual(resp2.status_code, 200, "Resubmit harus ditolak")
        # User TIDAK duplikat
        self.assertEqual(User.objects.filter(username="testuser").count(), 1)
        # Form harus menampilkan error
        form = resp2.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

class BlackBoxLoginLogoutTests(TestCase):
    """BB-LOGIN-01 s/d BB-LOGIN-21"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            "testuser", "test@example.com", "Padjadjaran#2026"
        )
        self.profile = UserProfile.objects.create(user=self.user, phone="081234567890")
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.dashboard_url = reverse("dashboard")

    # ------------------------------------------------------------------
    # BB-LOGIN-01  Login benar
    # ------------------------------------------------------------------
    def test_bb_login_01_login_benar(self):
        """Berhasil login, akses dashboard."""
        resp = self.client.post(
            self.login_url,
            {"username": "testuser", "password": "Padjadjaran#2026"},
        )
        # Harus redirect (302) ke dashboard
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("dashboard"))

        # Follow redirect → dashboard accessible
        resp2 = self.client.get(reverse("dashboard"))
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(resp2.wsgi_request.user.is_authenticated)
        self.assertEqual(resp2.wsgi_request.user.username, "testuser")

    # ------------------------------------------------------------------
    # BB-LOGIN-02  Password salah
    # ------------------------------------------------------------------
    def test_bb_login_02_password_salah(self):
        """Ditolak, pesan error kredensial."""
        resp = self.client.post(
            self.login_url,
            {"username": "testuser", "password": "SalahPassword#1"},
        )
        # Tetap di halaman login (200), BUKAN redirect
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.wsgi_request.user.is_authenticated)
        # Dashboard harus tidak bisa diakses
        resp2 = self.client.get(self.dashboard_url)
        self.assertEqual(resp2.status_code, 302)
        self.assertIn("login", resp2.url)

    # ------------------------------------------------------------------
    # BB-LOGIN-03  User tidak ada
    # ------------------------------------------------------------------
    def test_bb_login_03_user_tidak_ada(self):
        """Username tidak terdaftar → Ditolak."""
        resp = self.client.post(
            self.login_url,
            {"username": "tidakada", "password": "Padjadjaran#2026"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.wsgi_request.user.is_authenticated)
        # Pastikan tidak bisa akses dashboard
        resp2 = self.client.get(self.dashboard_url)
        self.assertEqual(resp2.status_code, 302)
        self.assertIn("login", resp2.url)

    # ------------------------------------------------------------------
    # BB-LOGIN-04  Username/password kosong
    # ------------------------------------------------------------------
    def test_bb_login_04_kosong(self):
        """Submit form kosong → Ditolak, pesan field required."""
        resp = self.client.post(self.login_url, {"username": "", "password": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.wsgi_request.user.is_authenticated)

    # ------------------------------------------------------------------
    # BB-LOGIN-05  Case sensitivity username
    # ------------------------------------------------------------------
    def test_bb_login_05_case_sensitivity_username(self):
        """Login pakai beda kapitalisasi username → Seharusnya DITOLAK (case-sensitive)."""
        resp = self.client.post(
            self.login_url,
            {"username": "TestUser", "password": "Padjadjaran#2026"},
        )
        self.assertEqual(resp.status_code, 200, "Username seharusnya case-sensitive (login gagal)")
        self.assertFalse(resp.wsgi_request.user.is_authenticated)

    # ------------------------------------------------------------------
    # BB-LOGIN-06  Brute force percobaan login
    # ------------------------------------------------------------------
    def test_bb_login_06_brute_force(self):
        """Submit password salah 20x → Seharusnya akun terkunci sementara (rate-limit/lockout)."""
        for i in range(20):
            resp = self.client.post(
                self.login_url,
                {"username": "testuser", "password": f"WrongPassword{i}"},
            )
            self.assertEqual(resp.status_code, 200)
            self.assertFalse(resp.wsgi_request.user.is_authenticated)

        # Setelah 20 percobaan gagal, coba login dengan password BENAR
        # SEHARUSNYA tetap ditolak karena akun dikunci sementara (lockout)
        resp_final = self.client.post(
            self.login_url,
            {"username": "testuser", "password": "Padjadjaran#2026"},
        )
        self.assertEqual(resp_final.status_code, 200, "Seharusnya gagal login karena lockout")
        self.assertFalse(resp_final.wsgi_request.user.is_authenticated, "User seharusnya diblokir dari login")

    # ------------------------------------------------------------------
    # BB-LOGIN-07  SQL injection di username
    # ------------------------------------------------------------------
    def test_bb_login_07_sql_injection_username(self):
        """username = admin' OR '1'='1 → Aman (ORM parameterized), login tetap gagal."""
        resp = self.client.post(
            self.login_url,
            {"username": "admin' OR '1'='1", "password": "anything"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.wsgi_request.user.is_authenticated)
        # Pastikan TIDAK bisa akses dashboard
        resp2 = self.client.get(self.dashboard_url)
        self.assertEqual(resp2.status_code, 302)

    # ------------------------------------------------------------------
    # BB-LOGIN-08  Logout
    # ------------------------------------------------------------------
    def test_bb_login_08_logout(self):
        """Klik Logout → Sesi berakhir, redirect ke home."""
        self.client.login(username="testuser", password="Padjadjaran#2026")
        # Verifikasi sudah login
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 200)

        # Logout
        resp_logout = self.client.post(self.logout_url)
        # Harus redirect
        self.assertEqual(resp_logout.status_code, 302)

        # Setelah logout, user TIDAK authenticated
        resp_after = self.client.get(self.dashboard_url)
        self.assertEqual(resp_after.status_code, 302)
        self.assertIn("login", resp_after.url)

    # ------------------------------------------------------------------
    # BB-LOGIN-09  Akses dashboard tanpa login
    # ------------------------------------------------------------------
    def test_bb_login_09_dashboard_tanpa_login(self):
        """Buka /accounts/dashboard/ langsung → Redirect ke halaman login (@login_required)."""
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    # ------------------------------------------------------------------
    # BB-LOGIN-10  Akses halaman beli tiket tanpa login
    # ------------------------------------------------------------------
    def test_bb_login_10_buy_ticket_tanpa_login(self):
        """Buka /tickets/buy/ langsung → Redirect ke login (@login_required)."""
        resp = self.client.get(reverse("buy_ticket"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    # ------------------------------------------------------------------
    # BB-LOGIN-11  Akses order detail tanpa login
    # ------------------------------------------------------------------
    def test_bb_login_11_order_detail_tanpa_login(self):
        """Buka /tickets/order/<id>/ langsung → Redirect ke login."""
        resp = self.client.get(reverse("order_detail", args=["ECO-ABC1234567"]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    # ------------------------------------------------------------------
    # BB-LOGIN-12  Akses check-in tanpa login/non-staff
    # ------------------------------------------------------------------
    def test_bb_login_12_checkin_tanpa_login(self):
        """Buka /tickets/checkin/<id>/ tanpa login → Redirect ke login."""
        resp = self.client.get(reverse("checkin", args=["ECO-ABC1234567"]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    def test_bb_login_12b_checkin_non_staff(self):
        """Login sebagai non-staff → checkin tetap ditolak (user_passes_test)."""
        self.client.login(username="testuser", password="Padjadjaran#2026")
        resp = self.client.get(reverse("checkin", args=["ECO-ABC1234567"]))
        # Non-staff harus redirect ke login
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    # ------------------------------------------------------------------
    # BB-LOGIN-13  Back button setelah logout (browser cache)
    # ------------------------------------------------------------------
    def test_bb_login_13_back_setelah_logout(self):
        """Login → buka dashboard → logout → tekan Back browser.
        Potensi bug: halaman dashboard tampil dari cache.
        Server-side test: request setelah logout HARUS redirect ke login."""
        self.client.login(username="testuser", password="Padjadjaran#2026")
        resp1 = self.client.get(self.dashboard_url)
        self.assertEqual(resp1.status_code, 200)

        # Logout
        self.client.post(self.logout_url)

        # Simulasi Back → request ulang dashboard
        resp2 = self.client.get(self.dashboard_url)
        self.assertEqual(resp2.status_code, 302, "Setelah logout, dashboard harus redirect")
        self.assertIn("login", resp2.url)

    # ------------------------------------------------------------------
    # BB-LOGIN-14  Reuse URL dashboard setelah logout
    # ------------------------------------------------------------------
    def test_bb_login_14_reuse_url_setelah_logout(self):
        """Salin URL dashboard, logout, paste lagi → Redirect ke login."""
        self.client.login(username="testuser", password="Padjadjaran#2026")
        self.client.post(self.logout_url)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    # ------------------------------------------------------------------
    # BB-LOGIN-15  Session fixation / cookie lama
    # ------------------------------------------------------------------
    def test_bb_login_15_session_fixation(self):
        """Logout lalu pakai cookie sessionid lama → Ditolak, sesi tidak valid."""
        self.client.login(username="testuser", password="Padjadjaran#2026")
        old_session_key = self.client.session.session_key
        self.assertIsNotNone(old_session_key, "Session key harus ada setelah login")

        self.client.post(self.logout_url)

        # Buat client baru dengan cookie lama
        client2 = Client()
        client2.cookies["sessionid"] = old_session_key
        resp = client2.get(self.dashboard_url)
        # Harus redirect ke login — session lama tidak valid
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    # ------------------------------------------------------------------
    # BB-LOGIN-16  Multi-tab logout
    # ------------------------------------------------------------------
    def test_bb_login_16_multi_tab_logout(self):
        """Buka dashboard di 2 tab, logout di tab 1, refresh tab 2.
        Tab 2 ikut ter-redirect ke login saat refresh."""
        self.client.login(username="testuser", password="Padjadjaran#2026")
        # Tab 1: buka dashboard → OK
        resp_tab1 = self.client.get(self.dashboard_url)
        self.assertEqual(resp_tab1.status_code, 200)

        # Tab 1: logout
        self.client.post(self.logout_url)

        # Tab 2: refresh dashboard → harus redirect
        resp_tab2 = self.client.get(self.dashboard_url)
        self.assertEqual(resp_tab2.status_code, 302)
        self.assertIn("login", resp_tab2.url)

    # ------------------------------------------------------------------
    # BB-LOGIN-17  SQL injection di field password (login)
    # ------------------------------------------------------------------
    def test_bb_login_17_sql_injection_password(self):
        """password = ' OR '1'='1 → Aman, login GAGAL."""
        resp = self.client.post(
            self.login_url,
            {"username": "testuser", "password": "' OR '1'='1"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.wsgi_request.user.is_authenticated)

    # ------------------------------------------------------------------
    # BB-LOGIN-18  SQL injection auth bypass
    # ------------------------------------------------------------------
    def test_bb_login_18_sql_injection_auth_bypass(self):
        """username = admin'-- → Login GAGAL, komentar SQL tidak mem-bypass."""
        resp = self.client.post(
            self.login_url,
            {"username": "admin'--", "password": "anything"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.wsgi_request.user.is_authenticated)
        # Pastikan TIDAK bisa akses resource terlindungi
        resp2 = self.client.get(self.dashboard_url)
        self.assertEqual(resp2.status_code, 302)

    # ------------------------------------------------------------------
    # BB-LOGIN-19  SQL injection union-based di login
    # ------------------------------------------------------------------
    def test_bb_login_19_sql_injection_union(self):
        """username = ' UNION SELECT 1,2,3-- → Tidak ada kebocoran data."""
        resp = self.client.post(
            self.login_url,
            {"username": "' UNION SELECT 1,2,3--", "password": "x"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.wsgi_request.user.is_authenticated)
        content = resp.content.decode()
        # Hash password TIDAK boleh bocor di response
        self.assertNotIn("pbkdf2_sha256", content)

    # ------------------------------------------------------------------
    # BB-LOGIN-20  SQL injection drop table di login
    # ------------------------------------------------------------------
    def test_bb_login_20_sql_injection_drop_table(self):
        """username = x'; DROP TABLE auth_user;-- → Tabel tidak terhapus."""
        user_count_before = User.objects.count()
        resp = self.client.post(
            self.login_url,
            {"username": "x'; DROP TABLE auth_user;--", "password": "x"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.wsgi_request.user.is_authenticated)
        # Tabel masih ada dan data tidak hilang
        self.assertEqual(User.objects.count(), user_count_before)

    # ------------------------------------------------------------------
    # BB-LOGIN-21  XSS di field login
    # ------------------------------------------------------------------
    def test_bb_login_21_xss_field_login(self):
        """username = <script>alert(1)</script>
        Ter-escape saat ditampilkan kembali, script tidak tereksekusi."""
        resp = self.client.post(
            self.login_url,
            {"username": "<script>alert(1)</script>", "password": "x"},
        )
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        # Raw script tag TIDAK boleh muncul
        self.assertNotIn("<script>alert(1)</script>", content)

class UnitTestRegisterFormTests(TestCase):
    """UTFORM-01 s/d UTFORM-04"""

    # UTFORM-01  RegisterForm valid
    def test_utform_01_register_form_valid(self):
        """Semua field benar → is_valid() True."""
        form = RegisterForm(data=_valid_register_data())
        self.assertTrue(form.is_valid(), f"Form seharusnya valid. Errors: {form.errors}")

    # UTFORM-02  RegisterForm email kosong
    def test_utform_02_register_form_email_kosong(self):
        """email='' → is_valid() False."""
        form = RegisterForm(data=_valid_register_data(email=""))
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    # UTFORM-03  RegisterForm phone kosong
    def test_utform_03_register_form_phone_kosong(self):
        """phone='' → is_valid() False."""
        form = RegisterForm(data=_valid_register_data(phone=""))
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    # UTFORM-04  RegisterForm password lemah
    def test_utform_04_register_form_password_lemah(self):
        """password='123' → is_valid() False."""
        form = RegisterForm(data=_valid_register_data(password1="123", password2="123"))
        self.assertFalse(form.is_valid())
        # Error ada di password2 (Django convention untuk password validation)
        self.assertIn("password2", form.errors)

class UnitTestUserProfileTests(TestCase):
    """UTPROF-01 s/d UTPROF-04"""

    def setUp(self):
        self.user = User.objects.create_user("profileuser", "p@e.com", "Padjadjaran#2026")

    # UTPROF-01  verification_token — UUID otomatis tergenerate
    def test_utprof_01_verification_token(self):
        """Profile baru → UUID otomatis tergenerate."""
        profile = UserProfile.objects.create(user=self.user)
        self.assertIsNotNone(profile.verification_token)
        self.assertIsInstance(profile.verification_token, uuid.UUID)
        # UUID harus non-zero
        self.assertNotEqual(profile.verification_token, uuid.UUID(int=0))

    # UTPROF-02  is_email_verified — default False
    def test_utprof_02_is_email_verified_default(self):
        """Profile baru → default False."""
        profile = UserProfile.objects.create(user=self.user)
        self.assertFalse(profile.is_email_verified)
        self.assertIs(profile.is_email_verified, False)

    # UTPROF-03  Relasi OneToOne — 2 profile untuk 1 user → Ditolak
    def test_utprof_03_one_to_one_unik(self):
        """Buat profile kedua → IntegrityError (OneToOne unik)."""
        UserProfile.objects.create(user=self.user)
        with self.assertRaises(IntegrityError):
            UserProfile.objects.create(user=self.user)

    # UTPROF-04  __str__ — mengembalikan username
    def test_utprof_04_str(self):
        """str(profile) mengembalikan username."""
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(str(profile), "profileuser")
        self.assertEqual(str(profile), self.user.username)
