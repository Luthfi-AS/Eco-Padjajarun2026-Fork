from django.core.management.base import BaseCommand
from tickets.models import TicketCategory
from news.models import Article


class Command(BaseCommand):
    help = "Seed initial Eco Padjadjarun data"

    def handle(self, *args, **options):
        tickets = [
            (
                "Eco Run 5K - Early Bird",
                "Tiket peserta Eco Run 5K termasuk race bib dan akses area Eco Village.",
                150000,
                1000,
            ),
            (
                "Eco Run 5K - Regular",
                "Tiket regular Eco Run 5K dengan race kit standar.",
                200000,
                3000,
            ),
            (
                "Festival Musik - Day 1",
                "Akses festival musik hari pertama.",
                100000,
                5000,
            ),
            (
                "Festival Musik - Day 2",
                "Akses festival musik hari kedua.",
                100000,
                5000,
            ),
            (
                "Full Access Pass",
                "Akses Eco Run, festival musik, dan area bazaar selama 2 hari.",
                350000,
                1500,
            ),
            (
                "Green Bazaar Tenant",
                "Registrasi booth tenant/UMKM Green Bazaar.",
                10000000,
                50,
            ),
            (
                "Indoor Hockey Participant",
                "Registrasi tim/peserta Indoor Hockey Tournament.",
                500000,
                100,
            ),
        ]
        for name, desc, price, quota in tickets:
            TicketCategory.objects.get_or_create(
                name=name,
                defaults={"description": desc, "price": price, "quota": quota},
            )
        articles = [
            (
                "Eco Padjadjarun 2026 Resmi Hadir",
                "Event sport dan sustainability terbesar di Padjadjaran.",
                "Eco Padjadjarun 2026 menghadirkan Indoor Hockey Festival, Eco Run 5K, Festival Musik, Green Bazaar, dan aksi lingkungan.",
            ),
            (
                "Gerakan 1 Runner 1 Tree",
                "Setiap partisipasi mendukung penghijauan.",
                "Sebagian biaya pendaftaran Eco Run dialokasikan untuk aksi penanaman pohon dan pengelolaan sampah berkelanjutan.",
            ),
            (
                "Web GIS dan Rute Eco Run 5K",
                "Peserta dapat melihat rute digital.",
                "Halaman GIS menyediakan rute Eco Run, titik start, finish, water station, parkir, dan titik penting acara.",
            ),
        ]
        for title, excerpt, body in articles:
            Article.objects.get_or_create(
                title=title, defaults={"excerpt": excerpt, "body": body}
            )
        self.stdout.write(self.style.SUCCESS("Seed data berhasil dibuat."))
