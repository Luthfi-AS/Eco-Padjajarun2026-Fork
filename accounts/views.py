from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from .forms import RegisterForm
from .models import UserProfile
from tickets.models import Order
def register(request):
    if request.method=='POST':
        form=RegisterForm(request.POST)
        if form.is_valid():
            user=form.save(commit=False); user.email=form.cleaned_data['email']; user.is_active=True; user.save()
            profile=UserProfile.objects.create(user=user,phone=form.cleaned_data['phone'])
            verify_url=request.build_absolute_uri(reverse('verify_email',args=[profile.verification_token]))
            send_mail('Verifikasi Email Eco Padjadjarun 2026',f'Klik link berikut untuk verifikasi email Anda: {verify_url}',None,[user.email],fail_silently=True)
            login(request,user); messages.success(request,'Registrasi berhasil. Link verifikasi tampil di console/server email.'); return redirect('dashboard')
    else: form=RegisterForm()
    return render(request,'accounts/register.html',{'form':form})
def verify_email(request, token):
    try:
        profile=UserProfile.objects.get(verification_token=token); profile.is_email_verified=True; profile.save(); messages.success(request,'Email berhasil diverifikasi. Anda sudah bisa membeli tiket.')
    except UserProfile.DoesNotExist: messages.error(request,'Token verifikasi tidak valid.')
    return redirect('dashboard')
@login_required
def dashboard(request):
    return render(request,'accounts/dashboard.html',{'orders':Order.objects.filter(user=request.user).order_by('-created_at'),'profile':getattr(request.user,'userprofile',None)})
