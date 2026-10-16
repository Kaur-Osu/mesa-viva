import hashlib
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import IntegrityError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from .forms import EmailAuthenticationForm, RegistrationForm


def home(request):
    return render(request, "home.html")

def recipes(request):
    return render(request, "recipes.html")

def detail(request, meal_id):
    return render(request, "detail.html", {"meal_id": meal_id})

@login_required
def favorites(request):
    return render(request, "favorites.html")

def privacy(request):
    return render(request, "privacy.html")

def limited(request, action):
    # REMOTE_ADDR se usa directamente: no se confía en cabeceras enviadas por el cliente.
    ip = request.META.get("REMOTE_ADDR", "unknown")
    key = f"auth:{action}:" + hashlib.sha256(ip.encode()).hexdigest()
    cache.add(key, 0, 300)
    count = cache.incr(key)
    return count > (10 if action == "login" else 5)

def register(request):
    if request.user.is_authenticated:
        return redirect("favorites")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST":
        if limited(request, "register"):
            form = RegistrationForm()
            messages.error(request, "Demasiados intentos. Espera 5 minutos antes de intentar de nuevo.")
            return render(request, "register.html", {"form": form}, status=429)
        if form.is_valid():
            try:
                user = form.save()
            except IntegrityError:
                form.add_error("email", "Ya existe una cuenta con este correo.")
            else:
                login(request, user)
                messages.success(request, "¡Tu cuenta está lista! Ya puedes guardar tus recetas favoritas.")
                return redirect("favorites")
    return render(request, "register.html", {"form": form})

def signin(request):
    if request.user.is_authenticated:
        return redirect("favorites")
    form = EmailAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        if limited(request, "login"):
            form = EmailAuthenticationForm(request)
            messages.error(request, "Demasiados intentos. Espera 5 minutos antes de intentar de nuevo.")
            return render(request, "login.html", {"form": form}, status=429)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("favorites")
    return render(request, "login.html", {"form": form})

@require_POST
def signout(request):
    logout(request)
    messages.success(request, "Cerraste sesión correctamente.")
    return redirect("home")
