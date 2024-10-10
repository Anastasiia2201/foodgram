from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin )
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    SAFE_METHODS)
from django_url_shortener.utils import shorten_url
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, F
from recipes.models import (
    Tag,
    Recipe,
    Ingredient,
    Favorite,
    ShoppingCart,
    Subscription
)
from .serializers import (
    UserSerializer,
    SignupSerializer,
    UpdatePasswordSerializer,
    UpdateAvatarSerializer,
    IngredientSerializer,
    TagSerializer,
    RecipeDisplaySerializer,
    RecepieInputSerializer,
    RecipeShortDisplaySerializer,
    UserSubsciptionsSerializer,
)

User = get_user_model()


class TagViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """Вьюсет для модели Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """Вьюсет для модели Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели User."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        url_path='me',
    )
    def me(self, request):
        serializer = UserSerializer(request.user)
        data = serializer.data.copy()
        return Response(data)

    @action(
        detail=False,
        methods=['PUT', 'DELETE'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def update_avatar(self, request):
        if request.method == 'PUT':
            serializer = UpdateAvatarSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            request.user.avatar=serializer.data['avatar']
            request.user.save()
            return Response(serializer.data)
        request.user.avatar = None
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['POST'],
        permission_classes=[IsAuthenticated],
        url_path='set_password',
    )
    def set_password(self, request):
        serializer = UpdatePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.data['current_password'] == request.user.password:
            request.user.password=serializer.data['new_password']
            request.user.save()
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['GET'],
  
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        subscriber = User.objects.get(pk=2)
        subscribed_to = Subscription.objects.all().filter(subscriber=subscriber)
        queryset = User.objects.all().filter(pk__in=[user.user.id for user in subscribed_to])
        page = self.paginate_queryset(queryset)
        serializer = UserSubsciptionsSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['POST', 'DELETE'],
  
        url_path=r'(?P<id>\d+)/subscriptions',
    )
    def subscriptions(self, request, id):
        subscriber = User.objects.get(pk=2)
        user = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            try:
                Subscription.objects.get(subscriber=subscriber, user=id)
                return Response(status=status.HTTP_400_BAD_REQUEST)
            except:
                serializer = UserSubsciptionsSerializer(user)
                if subscriber.id != user.id:
                    Subscription.objects.create(subscriber=subscriber, user=user)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                return Response('Нельзя подписаться на самого себя!', status=status.HTTP_400_BAD_REQUEST)
        try:
            sub = Subscription.objects.get(subscriber=subscriber, user=id)
            sub.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Recipe."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeDisplaySerializer

    def get_serializer_class(self):
        if self.action in SAFE_METHODS:
            return RecipeDisplaySerializer
        return RecepieInputSerializer
    
    @action(
        detail=False,
        methods=['GET'],
        url_path=r'(?P<id>\d+)/get-link',
    )
    def get_link(self, request, id):
        created, short_url  = shorten_url(request.build_absolute_uri()[:-9])
        return Response({'short-link': short_url}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['POST', 'DELETE'],
 #       permission_classes=[IsAuthenticated],
        url_path=r'(?P<id>\d+)/shopping_cart',
    )
    def shopping_cart(self, request, id):
  #      user = request.user
        user = User.objects.get(pk=1)
        recipe = get_object_or_404(Recipe, pk=id)
        if request.method == 'POST':
            serializer = RecipeShortDisplaySerializer(recipe)
            try:
                ShoppingCart.objects.get(user=user, recipe=recipe)
                return Response(status=status.HTTP_400_BAD_REQUEST)
            except:
                ShoppingCart.objects.create(user=user, recipe=recipe)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        try:
            entry = ShoppingCart.objects.get(user=user, recipe=recipe)
            entry.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['POST', 'DELETE'],
 #       permission_classes=[IsAuthenticated],
        url_path=r'(?P<id>\d+)/favorite',
    )
    def favorite(self, request, id):
  #      user = request.user
        user = User.objects.get(pk=1)
        recipe = get_object_or_404(Recipe, pk=id)
        if request.method == 'POST':
            serializer = RecipeShortDisplaySerializer(recipe)
            try:
                Favorite.objects.get(user=user, recipe=recipe)
                return Response(status=status.HTTP_400_BAD_REQUEST)
            except:
                Favorite.objects.create(user=user, recipe=recipe)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        try:
            entry = Favorite.objects.get(user=user, recipe=recipe)
            entry.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)
