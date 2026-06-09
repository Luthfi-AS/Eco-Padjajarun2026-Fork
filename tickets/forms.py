from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "ticket",
            "participant_name",
            "participant_email",
            "participant_phone",
        ]
        labels = {
            "ticket": "Kategori Tiket",
            "participant_name": "Nama Peserta",
            "participant_email": "Email Peserta",
            "participant_phone": "Nomor HP",
        }
