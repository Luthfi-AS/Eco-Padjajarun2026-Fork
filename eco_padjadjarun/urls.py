from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from core import views as core_views
urlpatterns=[path('admin/',admin.site.urls),path('',core_views.home,name='home'),path('about/',core_views.about,name='about'),path('sponsor/',core_views.sponsor,name='sponsor'),path('gis/',core_views.gis_map,name='gis'),path('accounts/',include('accounts.urls')),path('tickets/',include('tickets.urls')),path('news/',include('news.urls'))]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
