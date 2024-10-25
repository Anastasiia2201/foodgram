import base64
import re

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CurrentUserDefault
from rest_framework.validators import UniqueValidator

from recipes.constants import MAX_LENGTH_EMAIL, MAX_LENGTH_USERNAME
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]

            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class SignupSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        required=True,
        max_length=MAX_LENGTH_USERNAME,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    email = serializers.EmailField(
        required=True,
        max_length=MAX_LENGTH_EMAIL,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    first_name = serializers.CharField(
        required=True, max_length=MAX_LENGTH_USERNAME
    )
    last_name = serializers.CharField(
        required=True, max_length=MAX_LENGTH_USERNAME
    )
    password = serializers.CharField(
        required=True, max_length=MAX_LENGTH_USERNAME
    )

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
        )

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(user.password)
        user.save()
        return user

    @staticmethod
    def validate_username(value):
        """Проверка имени пользователя."""
        if not re.match(r"^[\w.@+-]+\Z", value):
            raise serializers.ValidationError(
                f"Имя {value} не может содержать спецсимволы"
            )
        return value


class UserShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
        )


class TokenSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=True)
    email = serializers.CharField(required=True)

    class Meta:
        fields = ("password", "email")
        model = User


class UpdateAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ("avatar",)


class UserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "is_subscribed",
            "first_name",
            "last_name",
            "avatar",
        )


class RecepieIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели RecipeIngredient."""

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")

    def validate_amount(self, value):
        if value <= 0:
            raise ValidationError(
                {"amount": "Убедитесь, что это значение больше либо равно 1."}
            )
        return value


class RecepieIngredientInputSerializer(serializers.ModelSerializer):
    """Сериализатор для модели RecipeIngredient."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeInputSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""

    ingredients = RecepieIngredientInputSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField(required=True)
    author = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
            "author",
        )

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError("Введите ингредиенты!")
        ids = [ingredient.get("id") for ingredient in value]
        if len(set(ids)) < len(ids):
            raise ValidationError("Повторяющиеся ингредиенты!")
        return value

    def validate_tags(self, value):
        if not value:
            raise ValidationError("Введите теги!")
        if len(set(value)) < len(value):
            raise ValidationError("Повторяющиеся теги!")
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise ValidationError("Время меньше 1!")
        return value

    def to_representation(self, instance):
        serialiser = RecipeDisplaySerializer(instance, context=self.context)
        return serialiser.data

    def create_recipe_ingredient(self, ingredients, recipe):
        for ingredient in ingredients:
            RecipeIngredient.objects.update_or_create(
                recipe=recipe,
                ingredient=ingredient["id"],
                amount=ingredient["amount"],
            )

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        recipe = super().create(validated_data)
        self.create_recipe_ingredient(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients")
        instance.ingredients.clear()
        recipe = super().update(instance, validated_data)
        self.create_recipe_ingredient(ingredients, recipe)
        return recipe


class RecipeDisplaySerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""

    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = RecepieIngredientSerializer(
        source="recipeingredient_set", read_only=True, many=True
    )
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )


class RecipeShortDisplaySerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class UserSubsciptionsSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.BooleanField(default=True)
    recipes_count = serializers.IntegerField()
    recipes = serializers.SerializerMethodField(
        "user_recipes", allow_null=True
    )

    def user_recipes(self, instance):
        recipes_limit = int(self.context["recipes_limit"])
        serilizer = RecipeShortDisplaySerializer(
            Recipe.objects.filter(author=instance.id).order_by("id")[
                :recipes_limit
            ],
            many=True,
        )
        return serilizer.data

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "is_subscribed",
            "first_name",
            "last_name",
            "recipes",
            "recipes_count",
            "avatar",
        )
