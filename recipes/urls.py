from django.urls import path
from . import api, views

urlpatterns = [
    path("", views.home, name="home"),
    path("recetas/", views.recipes, name="recipes"),
    path("recetas/<int:meal_id>/", views.detail, name="detail"),
    path("registro/", views.register, name="register"),
    path("ingresar/", views.signin, name="login"),
    path("salir/", views.signout, name="logout"),
    path("favoritos/", views.favorites, name="favorites"),
    path("privacidad/", views.privacy, name="privacy"),
    path("api/recetas/", api.recipes_list, name="api-recipes"),
    path("api/recetas/<int:meal_id>/", api.recipe_detail, name="api-detail"),
    path("api/favoritos/", api.favorites_list, name="api-favorites"),
    path("api/favoritos/<int:meal_id>/", api.favorite_delete, name="api-favorite-delete"),
]
