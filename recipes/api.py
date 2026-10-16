from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from . import services
from .models import Favorite
from .serializers import FavoriteInputSerializer, FavoriteSerializer, RecipeQuerySerializer

@api_view(["GET"])
@permission_classes([AllowAny])
def recipes_list(request):
    query = RecipeQuerySerializer(data=request.query_params)
    query.is_valid(raise_exception=True)
    try:
        meals = services.search_meals(query.validated_data["q"])
    except services.RecipeServiceError as exc:
        return Response({"detail": str(exc)}, status=503)
    return Response({"source": "TheMealDB", "count": len(meals), "results": meals})

@api_view(["GET"])
@permission_classes([AllowAny])
def recipe_detail(request, meal_id):
    try:
        meal = services.get_meal(meal_id)
    except services.RecipeServiceError as exc:
        return Response({"detail": str(exc)}, status=503)
    if meal is None:
        return Response({"detail": "No encontramos esta receta."}, status=404)
    return Response(meal)

@api_view(["GET", "POST"])
def favorites_list(request):
    if request.method == "GET":
        items = Favorite.objects.filter(user=request.user)
        return Response({"results": FavoriteSerializer(items, many=True).data})
    serializer = FavoriteInputSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    meal_id = serializer.validated_data["meal_id"]
    existing = Favorite.objects.filter(user=request.user, meal_id=meal_id).first()
    if existing:
        return Response(FavoriteSerializer(existing).data, status=200)
    try:
        meal = services.get_meal(meal_id)
    except services.RecipeServiceError as exc:
        return Response({"detail": str(exc)}, status=503)
    if not meal:
        return Response({"detail": "Esta receta no existe."}, status=404)
    favorite, created = Favorite.objects.get_or_create(user=request.user, meal_id=meal_id, defaults={"recipe": meal})
    return Response(FavoriteSerializer(favorite).data, status=201 if created else 200)

@api_view(["DELETE"])
def favorite_delete(request, meal_id):
    deleted, _ = Favorite.objects.filter(user=request.user, meal_id=meal_id).delete()
    if not deleted:
        return Response({"detail": "No encontramos este favorito en tu cuenta."}, status=404)
    return Response(status=204)
