from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .validation import clean_person_name, validate_registration_email

User = get_user_model()

class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(label="Tu nombre", min_length=2, max_length=80,
        widget=forms.TextInput(attrs={"autocomplete": "given-name", "placeholder": "¿Cómo te llamas?"}))
    email = forms.EmailField(label="Correo electrónico", max_length=150,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "tu@correo.com"}))
    password1 = forms.CharField(label="Contraseña", strip=False, min_length=12, max_length=128,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "minlength": 12, "maxlength": 128}))
    password2 = forms.CharField(label="Confirma tu contraseña", strip=False, min_length=12, max_length=128,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "minlength": 12, "maxlength": 128}))
    consent = forms.BooleanField(label="He leído el aviso de privacidad y acepto crear mi cuenta.", error_messages={"required": "Debes aceptar el aviso de privacidad."})

    class Meta:
        model = User
        fields = ("first_name", "email", "password1", "password2")

    def clean_first_name(self):
        return clean_person_name(self.cleaned_data["first_name"])

    def clean_email(self):
        value = validate_registration_email(self.cleaned_data["email"].strip())
        if len(value) > 150:
            raise forms.ValidationError("El correo debe tener como máximo 150 caracteres.")
        if User.objects.filter(username__iexact=value).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo. Puedes iniciar sesión.")
        return value

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Correo electrónico", max_length=150,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "tu@correo.com"}))
    password = forms.CharField(label="Contraseña", strip=False, max_length=128,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()
