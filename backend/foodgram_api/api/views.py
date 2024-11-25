from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import BooleanField, Count, ExpressionWrapper, Q
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django_url_shortener.utils import shorten_url
from djoser.serializers import SetPasswordSerializer
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from recipes.constants import RECIPES_LIMIT
from recipes.models import (Favorite, Ingredient, Recipe, ShoppingCart,
                            Subscription, Tag)

from .filters import RecipeFilter
from .permissions import IsAuthorOrAdmin
from .serializers import (IngredientSerializer, RecipeDisplaySerializer,
                          RecipeInputSerializer, RecipeShortDisplaySerializer,
                          SignupSerializer, TagSerializer,
                          UpdateAvatarSerializer, UserSerializer,
                          UserShortSerializer, UserSubsciptionsSerializer)

User = get_user_model()


def output_ingredients(ingredients):
    """Данные для файла с ингредиентами."""
    ingredients_list: dict[str:[str, int]] = {}
    for ingredient in ingredients:
        name = ingredient[1]
        amount = ingredient[0]
        measurement_unit = ingredient[2]
        if name in ingredients_list:
            amount += ingredients_list[name][1]
        ingredients_list[name] = [measurement_unit, amount]
    ingredients = ""
    for (
        ingredient_name,
        ingredient_measurement,
    ) in ingredients_list.items():
        ingredients += (f"{ingredient_name} "
                        f"({ingredient_measurement[0]}) — "
                        f"{str(ingredient_measurement[1])}\n")
    return ingredients


class TagViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """Вьюсет для модели Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """Вьюсет для модели Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name"]


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели User."""

    serializer_class = UserSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        users = User.objects.annotate(
            is_subscribed=ExpressionWrapper(
                Q(
                    id__in=Subscription.objects.filter(
                        user=self.request.user.id
                    ).values("subscribee")
                ),
                output_field=BooleanField(),
            ),
            recipes_count=Count("recipes"),
        )
        return users

    def create(self, request):
        """Регистрация пользователя."""
        context = {"request": self.request}
        serializer = SignupSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        new_user = serializer.save()
        serializer = UserShortSerializer(new_user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[IsAuthenticated],
        url_path="me",
    )
    def me(self, request):
        """Текущий пользователь."""
        serializer = UserSerializer(request.user)
        data = serializer.data.copy()
        return Response(data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["PUT", "DELETE"],
        permission_classes=[IsAuthenticated],
        url_path="me/avatar",
    )
    def update_avatar(self, request):
        """Добавление и удаление аватара текущего пользователя."""
        if request.method == "PUT":
            serializer = UpdateAvatarSerializer(
                request.user, data=request.data
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[IsAuthenticated],
        url_path="subscriptions",
    )
    def subscriptions(self, request):
        """Возвращает пользователей, на которых подписан текущий."""
        user = request.user
        recipes_limit = request.GET.get("recipes_limit", RECIPES_LIMIT)
        context = {"recipes_limit": recipes_limit}
        queryset = self.get_queryset().filter(
            pk__in=user.subscription_set.values_list("subscribee", flat=True)
        )
        page = self.paginate_queryset(queryset)
        serializer = UserSubsciptionsSerializer(
            page, context=context, many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["POST", "DELETE"],
        permission_classes=[IsAuthenticated],
        url_path=r"(?P<id>\d+)/subscribe",
    )
    def subscribe(self, request, id):
        """Подписаться на пользователя."""
        user = request.user
        recipes_limit = request.GET.get("recipes_limit", RECIPES_LIMIT)
        subscribee = get_object_or_404(self.get_queryset(), pk=id)
        context = {
            "recipes_limit": recipes_limit,
        }
        if request.method == "POST":
            if Subscription.objects.filter(
                subscribee=subscribee.id, user=user
            ).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = UserSubsciptionsSerializer(
                subscribee, context=context
            )
            if subscribee.id != user.id:
                Subscription.objects.create(subscribee=subscribee, user=user)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            return Response(
                "Нельзя подписаться на самого себя!",
                status=status.HTTP_400_BAD_REQUEST,
            )
        deleted, _ = Subscription.objects.filter(
            subscribee=subscribee.id, user=user.id
        ).delete()
        if deleted > 0:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["POST"],
        permission_classes=[IsAuthenticated],
        url_path="set_password",
    )
    def set_password(self, request):
        """Изменение пароля текущего пользователя."""
        context = {"request": self.request}
        serializer = SetPasswordSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data["new_password"])
        self.request.user.save()
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Recipe."""

    serializer_class = RecipeDisplaySerializer
    pagination_class = PageNumberPagination
    filter_backends = [
        DjangoFilterBackend,
    ]
    permission_classes = [
        IsAuthorOrAdmin,
        IsAuthenticatedOrReadOnly,
    ]
    filterset_class = RecipeFilter

    def get_queryset(self):
        recipes = Recipe.objects.select_related("author").prefetch_related(
            "tags", "ingredients"
        )
        recipes = recipes.annotate(
            is_favorited=ExpressionWrapper(
                Q(
                    id__in=Favorite.objects.filter(
                        user=self.request.user.id
                    ).values("recipe")
                ),
                output_field=BooleanField(),
            )
        )
        recipes = recipes.annotate(
            is_in_shopping_cart=ExpressionWrapper(
                Q(
                    id__in=ShoppingCart.objects.filter(
                        user=self.request.user.id
                    ).values("recipe")
                ),
                output_field=BooleanField(),
            )
        )
        return recipes

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            self.permission_classes = [IsAuthenticated, IsAuthorOrAdmin]
        else:
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super(self.__class__, self).get_permissions()

    def create(self, request):
        """Создание рецепта."""
        serializer = RecipeInputSerializer(
            data=request.data, context={"request": self.request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        """Обновление рецепта."""
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = RecipeInputSerializer(
            recipe, data=request.data, context={"request": self.request}
        )
        serializer.is_valid(raise_exception=True)
        self.check_object_permissions(self.request, recipe)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
        url_path=r"(?P<id>\d+)/get-link",
    )
    def get_link(self, request, id):
        """Получить короткую ссылку на рецепт."""
        created, short_url = shorten_url(
            settings.BASE_URL + request.path[4:-9]
        )
        return Response({"short-link": short_url}, status=status.HTTP_200_OK)

    def recipe_add(self, request, id, model):
        """Добавление рецепта в избранное или корзину."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=id)
        entry = model.objects.filter(user=user, recipe=recipe).first()
        if entry:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = RecipeShortDisplaySerializer(recipe)
        model.objects.create(user=user, recipe=recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def recipe_delete(self, request, id, model):
        """Удаление рецепта из избранного или корзины."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=id)
        deleted, *_ = model.objects.filter(user=user, recipe=recipe).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["POST", "DELETE"],
        permission_classes=[IsAuthenticated],
        url_path=r"(?P<id>\d+)/shopping_cart",
    )
    def shopping_cart(self, request, id):
        """Добавить рецепт в список покупок или удалить из него."""
        if request.method == "POST":
            return self.recipe_add(request, id, ShoppingCart)
        return self.recipe_delete(request, id, ShoppingCart)

    @action(
        detail=False,
        methods=["POST", "DELETE"],
        permission_classes=[IsAuthenticated],
        url_path=r"(?P<id>\d+)/favorite",
    )
    def favorite(self, request, id):
        """Добавить рецепт в избранное или удалить из него."""
        if request.method == "POST":
            return self.recipe_add(request, id, Favorite)
        return self.recipe_delete(request, id, Favorite)

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[IsAuthenticated],
        url_path="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок."""
        user = request.user
        response = HttpResponse(content_type="text/plain")
        response["Content-Disposition"] = (
            "attachment; filename='shopping_cart.txt'"
        )
        ingredients = Ingredient.objects.filter(
            recipes__in=ShoppingCart.objects.filter(user=user).values_list(
                "recipe", flat=True
            )
        )
        ingredients = output_ingredients(ingredients.values_list())
        response.write(ingredients)
        return response
