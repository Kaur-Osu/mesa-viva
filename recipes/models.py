from django.conf import settings
from django.db import models

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    meal_id = models.CharField(max_length=12)
    recipe = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "meal_id"], name="unique_user_recipe")]

    def __str__(self):
        return f"{self.user_id}: {self.meal_id}"
