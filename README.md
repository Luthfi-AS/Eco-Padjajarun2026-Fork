# Eco Padjadjarun 2026 — Django Ticketing System

Website ticketing system berbasis Python Django untuk event **Padjadjaran Indoor Hockey Festival & Eco Run 2026**.

## Fitur Utama
- Home page dengan event profile sebagai halaman pertama
- Countdown menuju 25 Juli 2026
- Register, login, logout
- Email verification sederhana via token
- Ticketing system
- QR Code e-ticket
- Payment status manual: Pending / Paid / Failed / Expired / Refunded
- Admin dashboard bawaan Django
- News page
- Sponsor page
- Web GIS dengan Leaflet.js
- Geolocation tombol “Gunakan Lokasi Saya”
- Sustainability impact section
- Entertainment lineup
- Responsive design

## Jalankan Local
```bash
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```
Buka: http://127.0.0.1:8000
Admin: http://127.0.0.1:8000/admin
