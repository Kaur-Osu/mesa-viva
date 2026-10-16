import hashlib
import json
from urllib.parse import urlparse
import requests
from django.conf import settings
from django.core.cache import cache

class RecipeServiceError(Exception):
    pass

def safe_url(value, image=False):
    value = value or ""
    parsed = urlparse(value)
    allowed = {"www.themealdb.com", "themealdb.com"} if image else {"www.youtube.com", "youtube.com", "youtu.be"}
    return value if parsed.scheme == "https" and parsed.hostname in allowed else ""

def normalize(meal):
    return {
        "id": meal["idMeal"], "name": meal.get("strMeal") or "Receta",
        "category": meal.get("strCategory") or "Sin categoría", "area": meal.get("strArea") or "Internacional",
        "image": safe_url(meal.get("strMealThumb"), image=True),
        "instructions": meal.get("strInstructions") or "Sin instrucciones disponibles.",
        "ingredients": [{"name": str(meal.get(f"strIngredient{i}") or "").strip(),
            "measure": str(meal.get(f"strMeasure{i}") or "").strip()}
            for i in range(1, 21) if str(meal.get(f"strIngredient{i}") or "").strip()],
        "video": safe_url(meal.get("strYoutube")),
    }

def fetch_meals(endpoint, params):
    if not settings.THEMEALDB_API_KEY:
        raise RecipeServiceError("La API no está configurada. Revisa THEMEALDB_API_KEY en .env.")
    cache_key = "mealdb:" + hashlib.sha256(json.dumps([endpoint, params], sort_keys=True).encode()).hexdigest()
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        response = requests.get(f"https://www.themealdb.com/api/json/v1/{settings.THEMEALDB_API_KEY}/{endpoint}", params=params, timeout=(4, 12))
        response.raise_for_status()
        data = response.json()
        meals = data.get("meals")
        if meals is not None and not isinstance(meals, list):
            raise ValueError("Formato inesperado")
        result = [normalize(meal) for meal in (meals or [])]
    except (requests.RequestException, ValueError, TypeError, KeyError, AttributeError):
        raise RecipeServiceError("No pudimos conectar con el recetario. Inténtalo de nuevo en unos momentos.") from None
    cache.set(cache_key, result, 300)
    return result

def search_meals(query):
    return fetch_meals("search.php", {"s": query})

def get_meal(meal_id):
    meals = fetch_meals("lookup.php", {"i": meal_id})
    return meals[0] if meals else None
