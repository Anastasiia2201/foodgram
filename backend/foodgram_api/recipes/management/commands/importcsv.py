import csv

from django.contrib.auth import get_user_model
from django.core import management
from django.core.management.base import BaseCommand
from django.db import models

from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeTag,
    Subscription,
    Favorite,
    Tag,
)

User = get_user_model()

CSV_DIR = "../data/"
IMAGE_EXAMPLE = "data:image/png;base64,iVBOR"
MODEL_FILES = {
    Tag: "tags.csv",
    Ingredient: "ingredients.csv",
    User: "users.csv",
    Recipe: "recipes.csv",
    Favorite: "favorites.csv",
    Subscription: "subscriptions.csv",
}

def import_model(file_path: str, model: models.Model):
    """Импорт данных из cvs файла в модель."""
    id = 0
    if model == User:
        id = 1
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            id += 1
            entity, _ = model.objects.get_or_create(id=id, defaults=row)
            if model == User:
                entity.set_password(entity.password)
                entity.save()

def import_recipe(file_path):
    id = 0
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            id += 1
            tags = map(int, row.pop("tags").split(" "))
            ingredients = map(int, row.pop("ingredients").split(" "))
            author = row.pop("author")
            recipe, _ = Recipe.objects.get_or_create(
                id=id,
                defaults=row,
                author=User.objects.get(pk=author))
            for tag in tags:
                RecipeTag.objects.get_or_create(
                    recipe=recipe, tag=Tag.objects.get(pk=tag)
                )
            for ingredient in ingredients:
                RecipeIngredient.objects.get_or_create(
                    recipe=recipe, ingredient=Ingredient.objects.get(pk=ingredient)
                )

def import_favorite(file_path):
    id = 0
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            id += 1
            Favorite.objects.get_or_create(
                id=id,
                user=User.objects.get(pk=row["user"]),
                recipe=Recipe.objects.get(pk=row["recipe"]))

def import_subscriptions(file_path):
    id = 0
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            id += 1
            Subscription.objects.get_or_create(
                id=id,
                user=User.objects.get(pk=row["user"]),
                subscribee=User.objects.get(pk=row["subscribee"]))


class Command(BaseCommand):
    help = "import CSV Data into model Ingredient"

    management.call_command("migrate")
    User.objects.create_superuser(
        username="admin", password="admin", email="admin@admin.com",
        first_name="Имя", last_name="Фамилия"
    )

    def handle(self, *args, **options):
        models = [Ingredient, Tag, User]
        for model in models:
            import_model(CSV_DIR + MODEL_FILES[model], model)
        import_recipe(CSV_DIR + MODEL_FILES[Recipe])
        import_favorite(CSV_DIR + MODEL_FILES[Favorite])
        import_subscriptions(CSV_DIR + MODEL_FILES[Subscription])
        self.stdout.write(self.style.SUCCESS("Данные добавлены"))
