from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q

from recipes.constants import (AMOUNT_MAX, AMOUNT_MIN, CHAR_FIELD_MAX_LENGTH,
                               RECIPE_DIR)

User = get_user_model()


class Tag(models.Model):
    """Теги."""

    name = models.CharField(
        verbose_name="Название тега",
        max_length=CHAR_FIELD_MAX_LENGTH,
    )
    slug = models.SlugField(
        unique=True,
        verbose_name="Уникальный ключ",
    )

    class Meta:
        verbose_name = "тег"
        verbose_name_plural = "Теги"
        ordering = ("slug",)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ингредиенты."""

    name = models.CharField(
        verbose_name="Название", max_length=CHAR_FIELD_MAX_LENGTH
    )
    measurement_unit = models.CharField(
        verbose_name="Единица измерения",
        max_length=CHAR_FIELD_MAX_LENGTH,
        default=None,
    )

    class Meta:
        verbose_name = "ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Рецепты."""

    name = models.CharField(
        verbose_name="Название", max_length=CHAR_FIELD_MAX_LENGTH
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время готовки в мин.",
        validators=[
            MinValueValidator(
                AMOUNT_MIN,
                message=f"Время не может быть меньше {AMOUNT_MIN}.",
            ),
            MaxValueValidator(
                AMOUNT_MAX,
                message=f"Время не может быть больше {AMOUNT_MAX}.",
            ),
        ],
    )
    text = models.TextField(verbose_name="Текст")
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="recipes",
    )
    image = models.ImageField(
        upload_to=RECIPE_DIR,
        verbose_name="Картинка",
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Тег",
        through="RecipeTag",
        blank=False,
        related_name="recipes",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name="Ингредиент",
        through="RecipeIngredient",
        related_name="recipes",
    )

    class Meta:
        verbose_name = "рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("name",)

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    """Связь тегов с рецептами."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, verbose_name="Тег"
    )

    def __str__(self):
        return f"{self.recipe} {self.tag}"

    class Meta:
        verbose_name = "Тег рецепта"
        verbose_name_plural = "Теги рецепта"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "tag"], name="one_tag_per_recipe"
            )
        ]


class RecipeIngredient(models.Model):
    """Связь ингредиентов с рецептами."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Количество ингредиента",
        validators=[
            MinValueValidator(
                AMOUNT_MIN,
                message=f"Количество не может быть меньше {AMOUNT_MIN}.",
            ),
            MaxValueValidator(
                AMOUNT_MAX,
                message=f"Количество не может быть больше {AMOUNT_MAX}.",
            ),
        ],
    )

    def __str__(self):
        return f"{self.recipe} {self.ingredient}"

    class Meta:
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецепта"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="one_ingredient_per_recipe",
            )
        ]


class BaseCartFavoriteSubscription(models.Model):
    """Абстрактная модель для моделей ShoppingCarts, Favorites."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )

    class Meta:
        abstract = True
        ordering = ("user",)


class ShoppingCart(BaseCartFavoriteSubscription):
    """Модель ShoppingCarts (Список покупок)."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="in_cart",
        verbose_name="Рецепт",
    )

    def __str__(self):
        return f"{self.recipe} {self.user}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="in_cart_once_per_user",
            )
        ]
        verbose_name = "корзину"
        verbose_name_plural = "Корзины"


class Favorite(BaseCartFavoriteSubscription):
    """Избранное."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Рецепт",
    )

    def __str__(self):
        return f"{self.recipe} {self.user}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "user"],
                name="favorite_once_per_user",
            )
        ]
        verbose_name = "избранное"
        verbose_name_plural = "Избранное"


class Subscription(BaseCartFavoriteSubscription):
    """Подписки."""

    subscribee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscribers",
        verbose_name="Подписчик",
    )

    def __str__(self):
        return f"{self.subscribee} {self.user}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subscribee", "user"], name="subscribe_once"
            ),
            models.CheckConstraint(
                name="cant_self_subscribe",
                check=~Q(user=F("subscribee")),
            ),
        ]
        verbose_name = "подписку"
        verbose_name_plural = "Подписки"
