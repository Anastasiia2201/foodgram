from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    ValidationError,
)
from django.db.models import Q, F

from recipes.constants import CHAR_FIELD_MAX_LENGTH, RECIPE_DIR, AMOUNT_MIN

User = get_user_model()


class Tag(models.Model):
    """Модель Tags (Теги)."""

    name = models.CharField(verbose_name='Название тега', max_length=CHAR_FIELD_MAX_LENGTH)
    slug = models.SlugField(unique=True, verbose_name='Уникальный ключ',)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('slug',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель Ingredients (Ингредиенты)."""

    name = models.CharField(verbose_name='Название', max_length=CHAR_FIELD_MAX_LENGTH)
    measurement_unit = models.CharField(verbose_name='Единица измерения',
                                        max_length=CHAR_FIELD_MAX_LENGTH, default=None)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель Recipes (Рецепты)."""

    name = models.CharField(verbose_name='Название', max_length=CHAR_FIELD_MAX_LENGTH)
    cooking_time = models.PositiveSmallIntegerField(verbose_name='Время готовки в мин.')
    text = models.TextField(verbose_name='Текст')
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
    )
    image = models.ImageField(
        upload_to=RECIPE_DIR, 
        null=True,  
        default=None,
        blank=True,
        verbose_name = 'Картинка'
    )
    tags = models.ManyToManyField(
        Tag, verbose_name='Тег', through='RecipeTag', blank=False
    )
    ingredients = models.ManyToManyField(
        Ingredient, verbose_name='Ингредиент', through='RecipeIngredient', blank=False
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('name',)

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    """Модель RecepiesTags (связь тегов с рецептами)."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, verbose_name='Тег')

    def __str__(self):
        return f'{self.recipe} {self.tag}'

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецепта'
        constraints = [
        models.UniqueConstraint(
            fields=['recipe', 'tag'], name='one_tag_per_recipe')
        ]       


class RecipeIngredient(models.Model):
    """Модель RecepiesIngredients (связь ингредиентов с рецептами)."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, verbose_name='Ингредиент')
    amount = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Количество ингредиента',
        validators=[
            MinValueValidator(
                AMOUNT_MIN,
                message=f'Количество ингредиента не может быть меньше {AMOUNT_MIN}.',
            ),
        ]
    )

    def __str__(self):
        return f'{self.recipe} {self.ingredient}'

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        constraints = [
        models.UniqueConstraint(
            fields=['recipe', 'ingredient'], name='one_ingredient_per_recipe')
        ]


class BaseCartFavoriteSubscription(models.Model):
    """Абстрактная модель для моделей ShoppingCarts, Favorites."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        abstract = True
        ordering = ('user',)


class ShoppingCart(BaseCartFavoriteSubscription):
    """Модель ShoppingCarts (Список покупок)."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        constraints = [
        models.UniqueConstraint(
            fields=['user', 'recipe'], name='in_cart_once_per_user')
        ]

class Favorite(BaseCartFavoriteSubscription):
    """Модель Favorites (Избранное)."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        constraints = [
        models.UniqueConstraint(
            fields=['recipe', 'user'], name='favorite_once_per_user')
        ]

class Subscription(BaseCartFavoriteSubscription):
    """Модель Subscriptions (Подписки)."""

    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscribers')

    class Meta:
        constraints = [
        models.UniqueConstraint(
            fields=['subscriber', 'user'],
            name='subscribe_once'),
        models.CheckConstraint(
            name='cant_self_subscribe',
            check=~Q(user=F('subscriber'))
        )
        ]
