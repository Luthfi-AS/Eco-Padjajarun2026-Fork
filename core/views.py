from django.shortcuts import render
from tickets.models import TicketCategory
from news.models import Article
EVENT_DATA={'name':'Padjadjaran Indoor Hockey Festival & Eco Run 2026','short_name':'Eco Padjadjarun 2026','date':'25–26 Juli 2026','location':'Universitas Padjadjaran, Jatinangor','budget':'Rp2.200.950.000','participants':'500 atlet hockey, 5.000 peserta Eco Run, 5.000+ pengunjung harian','digital_reach':'Target 100.000+ impressions'}
def home(request):
    return render(request,'core/home.html',{'event':EVENT_DATA,'tickets':TicketCategory.objects.filter(is_active=True)[:6],'articles':Article.objects.filter(is_published=True)[:3]})
def about(request): return render(request,'core/about.html',{'event':EVENT_DATA})
def sponsor(request):
    packages=[{'name':'Title Sponsor','price':'Rp500.000.000','benefit':'Naming rights, branding 360°, gate start/finish, mainstage, website, slot runners.'},{'name':'Platinum Partner','price':'Rp300.000.000','benefit':'High visibility, booth utama, live streaming mention, website exposure.'},{'name':'Gold Partner','price':'Rp100.000.000','benefit':'Logo materi promosi, booth Eco-Village, ad-lips MC, thank you post.'},{'name':'Silver Partner','price':'Rp50.000.000','benefit':'Logo placement, sampling rights, Instagram story mention, website exposure.'},{'name':'Stand Exhibition UMKM','price':'Rp10.000.000','benefit':'Booth bazaar untuk tenant/UMKM.'}]
    return render(request,'core/sponsor.html',{'event':EVENT_DATA,'packages':packages})
def gis_map(request): return render(request,'core/gis.html',{'event':EVENT_DATA})
