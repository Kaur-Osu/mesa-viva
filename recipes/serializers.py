from rest_framework import serializers
from .models import Favorite

class RecipeQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, max_length=60, default="")

class FavoriteInputSerializer(serializers.Serializer):
    meal_id = serializers.RegexField(r"^[0-9]{1,12}$")

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ("meal_id", "recipe", "created_at")
