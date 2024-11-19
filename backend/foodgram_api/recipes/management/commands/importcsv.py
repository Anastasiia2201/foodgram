from django.contrib.auth import get_user_model
from django.core import management
from django.core.management.base import BaseCommand

from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeTag,
    Tag,
)

CSV_DIR = "../data/"

FILE_NAMES = {
    "ingredients": "ingredients.csv",
    "tags": "tags.csv",
    "users": "users.csv",
    "recipes": "recipes.csv",
}
IMAGE_EXAMPLE = "data:image/png;base64,iVBOR"
SUPERUSER_USERNAME_PASSWORD = "admin"
SUPERUSER_EMAIL = "admin@admin.com"

User = get_user_model()


def import_ingredients(file_path: str):
    """Импорт данных из cvs файла в модель."""
    with open(file_path, "r", encoding="utf-8") as file:
        for row in file:
            if '"' not in row:
                measurement_unit = row.split(",")[1].rstrip()
                name = row.split(",")[0]
            else:
                measurement_unit = row.split('",')[1].rstrip()
                name = row.split('",')[0].replace('"', "")
            Ingredient.objects.get_or_create(
                measurement_unit=measurement_unit, name=name
            )


def import_tags(file_path: str):
    """Импорт данных из cvs файла в модель."""
    with open(file_path, "r", encoding="utf-8") as file:
        for row in file:
            data = row.split(",")
            name = data[0]
            slug = data[1].rstrip()
            Tag.objects.get_or_create(name=name, slug=slug)


def import_users(file_path: str):
    """Импорт данных из cvs файла в модель."""
    with open(file_path, "r", encoding="utf-8") as file:
        for row in file:
            data = row.split(",")
            username = data[0]
            first_name = data[1]
            last_name = data[2]
            password = data[3]
            email = data[4].rstrip()
            user, _ = User.objects.get_or_create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
                email=email,
                avatar=IMAGE_EXAMPLE,
            )
            user.set_password(user.password)
            user.save()


def import_recipes(file_path: str):
    """Импорт данных из cvs файла в модель."""
    with open(file_path, "r", encoding="utf-8") as file:
        for row in file:
            data = row.split(",")
            author_id = data[0]
            tags = data[1]
            ingredients = data[2]
            name = data[3]
            cooking_time = data[4]
            text = data[5].rstrip()
            recipe, _ = Recipe.objects.get_or_create(
                author=User.objects.get(pk=author_id),
                name=name,
                cooking_time=cooking_time,
                text=text,
                image=IMAGE_EXAMPLE,
            )
            for tag in tags.split():
                RecipeTag.objects.get_or_create(
                    recipe=recipe, tag=Tag.objects.get(pk=int(tag))
                )
            for ingredient in ingredients.split():
                RecipeIngredient.objects.get_or_create(
                    recipe=recipe,
                    ingredient=Ingredient.objects.get(pk=int(ingredient)),
                )


class Command(BaseCommand):
    help = "import CSV Data into model Ingredient"

    management.call_command("migrate")
    User.objects.create_superuser(
        username="admin", password="admin", email="admin@admin.com"
    )

    def handle(self, *args, **options):
        import_ingredients(CSV_DIR + FILE_NAMES.get("ingredients"))
        import_tags(CSV_DIR + FILE_NAMES.get("tags"))
        import_users(CSV_DIR + FILE_NAMES.get("users"))
        import_recipes(CSV_DIR + FILE_NAMES.get("recipes"))
        self.stdout.write(self.style.SUCCESS("Данные добавлены"))
