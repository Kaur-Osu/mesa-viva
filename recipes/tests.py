from unittest.mock import Mock, patch
import requests
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from .models import Favorite
from .services import RecipeServiceError, fetch_meals, normalize

User = get_user_model()
MEAL = {"id": "52771", "name": "Pasta", "category": "Pasta", "area": "Italian", "image": "", "instructions": "Cocinar.", "ingredients": [], "video": ""}

class AccountTests(TestCase):
    def setUp(self):
        cache.clear()
        domain_patch = patch("recipes.validation.check_email_domain")
        domain_patch.start()
        self.addCleanup(domain_patch.stop)
        self.data = {"first_name": "Lucía", "email": "lucia@example.com", "password1": "MesaBonita2026!", "password2": "MesaBonita2026!", "consent": "on"}

    def test_public_pages(self):
        for url in ("/", "/registro/", "/ingresar/", "/recetas/", "/recetas/52771/", "/privacidad/"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertContains(response, 'lang="es"')

    def test_registration_hashes_password_and_starts_session(self):
        response = self.client.post(reverse("register"), self.data)
        self.assertRedirects(response, reverse("favorites"))
        user = User.objects.get(username="lucia@example.com")
        self.assertTrue(user.check_password(self.data["password1"]))
        self.assertNotEqual(user.password, self.data["password1"])
        self.assertEqual(str(user.pk), self.client.session["_auth_user_id"])

    def test_invalid_registration_does_not_create_user(self):
        cases = [{"email": "incorrecto"}, {"first_name": "<script>"}, {"password2": "Distinta2026!"},
            {"password1": "12345678", "password2": "12345678"}, {"consent": ""}]
        for changes in cases:
            with self.subTest(changes=changes):
                response = self.client.post(reverse("register"), self.data | changes)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors)
                self.assertEqual(User.objects.count(), 0)

    def test_email_normalization_and_duplicate(self):
        self.client.post(reverse("register"), self.data | {"email": "LUCIA@EXAMPLE.COM"})
        self.client.logout()
        response = self.client.post(reverse("register"), self.data)
        self.assertIn("email", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_login_uses_email_and_logout_requires_post(self):
        User.objects.create_user(username="lucia@example.com", email="lucia@example.com", password="MesaBonita2026!")
        response = self.client.post(reverse("login"), {"username": "LUCIA@EXAMPLE.COM", "password": "MesaBonita2026!"})
        self.assertRedirects(response, reverse("favorites"))
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.client.post(reverse("logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_csrf_registration_and_login(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse("register"), self.data).status_code, 403)
        self.assertEqual(client.post(reverse("login"), {"username": "x@y.com", "password": "123"}).status_code, 403)
        client.get(reverse("register"))
        token = client.cookies["csrftoken"].value
        response = client.post(reverse("register"), self.data, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 302)

    def test_favorites_require_login(self):
        self.assertEqual(self.client.get(reverse("favorites")).status_code, 302)

    def test_security_headers(self):
        response = self.client.get("/")
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertIn("script-src 'self'", response["Content-Security-Policy"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(self.client.get("/registro/")["Cache-Control"], "no-store")

    def test_registration_attempt_limit(self):
        for _ in range(5):
            self.client.post(reverse("register"), {"email": "bad"})
        response = self.client.post(reverse("register"), self.data)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(User.objects.count(), 0)

class RecipeApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.api = APIClient()
        self.user = User.objects.create_user(username="ana@example.com", password="Example2026!")
        self.other = User.objects.create_user(username="otro@example.com", password="Example2026!")

    @patch("recipes.api.services.search_meals", return_value=[MEAL])
    def test_public_search(self, search):
        response = self.api.get("/api/recetas/", {"q": "pasta"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        search.assert_called_once_with("pasta")

    @patch("recipes.api.services.search_meals", return_value=[])
    def test_no_results(self, search):
        self.assertEqual(self.api.get("/api/recetas/?q=zzzz").json()["results"], [])

    def test_overlong_query_rejected(self):
        self.assertEqual(self.api.get("/api/recetas/", {"q": "a" * 61}).status_code, 400)

    @patch("recipes.api.services.search_meals", side_effect=RecipeServiceError("Servicio temporalmente no disponible"))
    def test_upstream_error_returns_503(self, search):
        response = self.api.get("/api/recetas/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "Servicio temporalmente no disponible")

    @patch("recipes.api.services.get_meal", return_value=None)
    def test_missing_meal(self, get_meal):
        self.assertEqual(self.api.get("/api/recetas/99999/").status_code, 404)

    def test_favorites_reject_anonymous(self):
        self.assertEqual(self.api.get("/api/favoritos/").status_code, 403)
        self.assertEqual(self.api.post("/api/favoritos/", {"meal_id": "52771"}).status_code, 403)

    @patch("recipes.api.services.get_meal", return_value=MEAL)
    def test_save_is_idempotent_and_private(self, get_meal):
        self.api.force_authenticate(self.user)
        self.assertEqual(self.api.post("/api/favoritos/", {"meal_id": "52771"}).status_code, 201)
        self.assertEqual(self.api.post("/api/favoritos/", {"meal_id": "52771"}).status_code, 200)
        self.assertEqual(Favorite.objects.count(), 1)
        self.assertEqual(len(self.api.get("/api/favoritos/").json()["results"]), 1)
        self.api.force_authenticate(self.other)
        self.assertEqual(self.api.get("/api/favoritos/").json()["results"], [])
        self.assertEqual(self.api.delete("/api/favoritos/52771/").status_code, 404)
        self.assertEqual(Favorite.objects.count(), 1)
        self.api.force_authenticate(self.user)
        self.assertEqual(self.api.delete("/api/favoritos/52771/").status_code, 204)
        self.assertEqual(Favorite.objects.count(), 0)

    def test_favorite_input_validation(self):
        self.api.force_authenticate(self.user)
        self.assertEqual(self.api.post("/api/favoritos/", {"meal_id": "<script>"}).status_code, 400)

    def test_authenticated_write_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post("/api/favoritos/", {"meal_id": "52771"})
        self.assertEqual(response.status_code, 403)

class ExternalServiceTests(TestCase):
    def setUp(self):
        cache.clear()

    @override_settings(THEMEALDB_API_KEY="test-key-not-public")
    @patch("recipes.services.requests.get")
    def test_external_key_stays_in_server_and_cache_reduces_calls(self, get):
        get.return_value = Mock(**{"json.return_value": {"meals": [{"idMeal": "52771", "strMeal": "Pasta"}]}})
        first = fetch_meals("search.php", {"s": "pasta"})
        second = fetch_meals("search.php", {"s": "pasta"})
        self.assertEqual(first, second)
        get.assert_called_once()
        self.assertIn("test-key-not-public", get.call_args.args[0])
        self.assertNotIn("test-key-not-public", str(first))
        self.assertEqual(get.call_args.kwargs["timeout"], (4, 12))

    @override_settings(THEMEALDB_API_KEY="1")
    @patch("recipes.services.requests.get", side_effect=requests.Timeout)
    def test_timeout_is_safe_error(self, get):
        with self.assertRaises(RecipeServiceError):
            fetch_meals("search.php", {"s": "pasta"})

    @override_settings(THEMEALDB_API_KEY="")
    def test_missing_key(self):
        with self.assertRaises(RecipeServiceError):
            fetch_meals("search.php", {"s": "pasta"})

    def test_untrusted_links_removed(self):
        meal = normalize({"idMeal": "1", "strMealThumb": "javascript:alert(1)", "strYoutube": "https://evil.example/video"})
        self.assertEqual(meal["image"], "")
        self.assertEqual(meal["video"], "")


class StrongRegistrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.data = {"first_name": "María José", "email": "maria@gmail.com", "password1": "HuertoVerde2026!", "password2": "HuertoVerde2026!", "consent": "on"}

    @patch("recipes.validation.check_email_domain")
    def test_valid_accented_name_and_email(self, domain):
        response = self.client.post("/registro/", self.data)
        self.assertEqual(response.status_code, 302)
        domain.assert_called_once_with("maria@gmail.com")

    @patch("recipes.validation.check_email_domain")
    def test_invalid_names(self, domain):
        from .forms import RegistrationForm
        for name in ("--", "A", "12", "María  José", "Ana--Luz", "-Ana", "Ana-", "Ana\u200b", "Ana<script>"):
            with self.subTest(name=name):
                form = RegistrationForm(self.data | {"first_name": name})
                self.assertFalse(form.is_valid())
                self.assertIn("first_name", form.errors)

    @patch("recipes.validation.check_email_domain")
    def test_password_rules_enforced_on_server(self, domain):
        from .forms import RegistrationForm
        for password in ("Corta2026!", "solominusculas2026", "SOLOMAYUSCULAS2026", "SinNumerosLarga!", "Huerto12345!Verde", "Huertooooo2026!", "Huerto\u200bVerde2026!", "A"*129):
            with self.subTest(password=password):
                form = RegistrationForm(self.data | {"password1": password, "password2": password})
                self.assertFalse(form.is_valid())
                self.assertTrue("password1" in form.errors or "password2" in form.errors)
        self.assertEqual(User.objects.count(), 0)

    @patch("recipes.validation.check_email_domain")
    def test_bad_email_syntax_is_rejected_before_dns(self, domain):
        from .forms import RegistrationForm
        for email in ("a..b@gmail.com", "a b@gmail.com", "a\u200bb@gmail.com", "a@localhost", "a@@gmail.com"):
            with self.subTest(email=email):
                form = RegistrationForm(self.data | {"email": email})
                self.assertFalse(form.is_valid())
                self.assertIn("email", form.errors)
        domain.assert_not_called()

    @patch("recipes.validation.validate_email")
    def test_nonexistent_domain_is_rejected(self, validate):
        from email_validator import EmailUndeliverableError
        from .validation import check_email_domain
        from django.core.exceptions import ValidationError
        validate.side_effect = EmailUndeliverableError("domain does not exist")
        with self.assertRaisesMessage(ValidationError, "El dominio de este correo no existe"):
            check_email_domain("sdasd@sexmail.xom")

    @patch("recipes.validation.validate_email")
    def test_dns_timeout_does_not_accept_unknown_domain(self, validate):
        from types import SimpleNamespace
        from .validation import check_email_domain
        from django.core.exceptions import ValidationError
        validate.return_value = SimpleNamespace()
        with self.assertRaisesMessage(ValidationError, "No pudimos verificar"):
            check_email_domain("ana@gmail.com")

    @patch("recipes.validation.check_email_domain")
    def test_domain_success_cached_without_storing_email(self, domain):
        from .validation import validate_registration_email
        self.assertEqual(validate_registration_email("ANA@GMAIL.COM"), "ana@gmail.com")
        self.assertEqual(validate_registration_email("otra@gmail.com"), "otra@gmail.com")
        domain.assert_called_once_with("ana@gmail.com")

    @patch("recipes.validation.check_email_domain")
    def test_domain_failure_prevents_account_creation(self, domain):
        from django.core.exceptions import ValidationError
        domain.side_effect = ValidationError("El dominio de este correo no existe.")
        response = self.client.post("/registro/", self.data | {"email": "sdasd@sexmail.xom"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El dominio de este correo no existe")
        self.assertEqual(User.objects.count(), 0)
