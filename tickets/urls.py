from django.urls import path
from . import views
urlpatterns=[path('',views.ticket_list,name='ticket_list'),path('buy/',views.buy_ticket,name='buy_ticket'),path('order/<str:order_code>/',views.order_detail,name='order_detail'),path('simulate-payment/<str:order_code>/',views.simulate_payment,name='simulate_payment'),path('checkin/<str:order_code>/',views.checkin,name='checkin')]
