from django.test import TestCase
from django.urls import reverse
from django.db.utils import IntegrityError
from .models import Article

class NewsBlackBoxTests(TestCase):
    def setUp(self):
        self.published_article = Article.objects.create(
            title="Published News",
            slug="published-news",
            is_published=True,
            body="Ini adalah konten berita yang di-publish."
        )
        self.unpublished_article = Article.objects.create(
            title="Unpublished News",
            slug="unpublished-news",
            is_published=False,
            body="Ini adalah konten berita yang belum di-publish."
        )

    def test_bbnews01_daftar_berita(self):
        """BBNEWS01: Hanya artikel is_published=True tampil di daftar berita"""
        response = self.client.get(reverse('news_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published_article.title)
        self.assertNotContains(response, self.unpublished_article.title)
        print("\n[BBNEWS01] Input: buka /news/ | Hasil Diharapkan: Hanya artikel is_published=True tampil | Status: SUKSES")

    def test_bbnews02_detail_berita_publish(self):
        """BBNEWS02: Detail berita publish tampil"""
        response = self.client.get(reverse('news_detail', args=[self.published_article.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published_article.title)
        print("\n[BBNEWS02] Input: buka slug valid | Hasil Diharapkan: Artikel tampil | Status: SUKSES")

    def test_bbnews03_detail_berita_unpublish(self):
        """BBNEWS03: Detail berita unpublish 404"""
        response = self.client.get(reverse('news_detail', args=[self.unpublished_article.slug]))
        self.assertEqual(response.status_code, 404)
        print("\n[BBNEWS03] Input: slug is_published=False | Hasil Diharapkan: 404 | Status: SUKSES")

    def test_bbnews04_slug_tidak_ada(self):
        """BBNEWS04: Slug tidak ada 404"""
        response = self.client.get(reverse('news_detail', args=['slug-acak-yang-tidak-ada']))
        self.assertEqual(response.status_code, 404)
        print("\n[BBNEWS04] Input: slug acak | Hasil Diharapkan: 404 | Status: SUKSES")

class ArticleUnitTests(TestCase):
    def test_ut_art_01_save_slug_kosong(self):
        """UT-ART-01: save() slug kosong -> otomatis slug"""
        article = Article(title="Eco Run 2026", body="Test")
        article.save()
        self.assertEqual(article.slug, "eco-run-2026")
        print("\n[UT-ART-01] Input: judul 'Eco Run 2026' | Output Diharapkan: slug = 'eco-run-2026' | Status: SUKSES")

    def test_ut_art_02_save_slug_sudah_ada(self):
        """UT-ART-02: save() slug sudah ada -> dipertahankan"""
        article = Article(title="Test", slug="manual-slug", body="Test")
        article.save()
        self.assertEqual(article.slug, "manual-slug")
        print("\n[UT-ART-02] Input: slug manual diisi | Output Diharapkan: slug manual dipertahankan | Status: SUKSES")

    def test_ut_art_03_get_absolute_url(self):
        """UT-ART-03: get_absolute_url()"""
        article = Article.objects.create(title="Testing URL", body="Test")
        expected_url = reverse('news_detail', args=[article.slug])
        self.assertEqual(article.get_absolute_url(), expected_url)
        print(f"\n[UT-ART-03] Input: artikel dengan slug | Output Diharapkan: URL {expected_url} | Status: SUKSES")

    def test_ut_art_04_slug_unik(self):
        """UT-ART-04: Slug unik"""
        Article.objects.create(title="Eco Run 2026", body="Test 1")
        with self.assertRaises(IntegrityError):
            Article.objects.create(title="Eco Run 2026", body="Test 2")
        print("\n[UT-ART-04] Input: dua judul sama | Output Diharapkan: IntegrityError (unique) | Status: SUKSES")

    def test_ut_art_05_default_ordering(self):
        """UT-ART-05: Default ordering"""
        a1 = Article.objects.create(title="First", body="First")
        a2 = Article.objects.create(title="Second", body="Second")
        articles = list(Article.objects.all())
        self.assertEqual(articles[0], a2)
        self.assertEqual(articles[1], a1)
        print("\n[UT-ART-05] Input: beberapa artikel | Output Diharapkan: urut -created_at (terbaru dulu) | Status: SUKSES")
