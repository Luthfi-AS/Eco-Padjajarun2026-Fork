from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=30, required=True, label="Nomor HP")

    class Meta:
        model = User
        fields = ["username", "email", "phone", "password1", "password2"]
