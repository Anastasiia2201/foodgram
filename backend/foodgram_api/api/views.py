from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin )
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny)
from django_url_shortener.utils import shorten_url
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes

from .permissions import IsAdmin, IsAuthenticatedOrSafeMethod, IsAuthorOrAdmin
from .filters import RecipeFilter
from recipes.models import (
    Tag,
    Recipe,
    Ingredient,
    Favorite,
    ShoppingCart,
    Subscription,
    RecipeIngredient
)
from .serializers import (
    UserSerializer,
    SignupSerializer,
    UpdatePasswordSerializer,
    UpdateAvatarSerializer,
    IngredientSerializer,
    TagSerializer,
    RecipeDisplaySerializer,
    RecipeInputSerializer,
    RecipeShortDisplaySerializer,
    UserSubsciptionsSerializer,
    UserShortSerializer,
    TokenSerializer
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
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id', 'name']


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели User."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitOffsetPagination

    def create(self, request):
        """Регистрация пользователя."""
        serializer = SignupSerializer(data=request.data)
        print('dsadds466545')
        serializer.is_valid(raise_exception=True)
        new_user = User.objects.create(
            username=request.data['username'],
            email=request.data['email'],
            first_name=request.data['first_name'],
            last_name=request.data['last_name'],
            password=request.data['password'],
        )
        serializer = UserShortSerializer(new_user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        url_path='me',
    )
    def me(self, request):
        """Текущий пользователь."""
        serializer = UserSerializer(request.user)
        data = serializer.data.copy()
        return Response(data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['PUT', 'DELETE'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def update_avatar(self, request):
        """Добавление и удаление аватара текущего пользователя."""
        if request.method == 'PUT':
            serializer = UpdateAvatarSerializer(request.user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
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
        """Изменение пароля текущего пользователя."""
        context= {'request': self.request}
        serializer = UpdatePasswordSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        if serializer.data['current_password'] == request.user.password:
            request.user.password=serializer.data['new_password']
            request.user.save()
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        """Возвращает пользователей, на которых подписан текущий пользователь."""
        subscriber = request.user
        recipes_limit = request.GET.get('recipes_limit', 1000)
        context = {'recipes_limit': recipes_limit}
        subscribed_to = Subscription.objects.filter(subscriber=subscriber)
        queryset = User.objects.filter(pk__in=[user.user.id for user in subscribed_to])
        page = self.paginate_queryset(queryset)
        serializer = UserSubsciptionsSerializer(page, context=context, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
        url_path=r'(?P<id>\d+)/subscribe',
    )
    def subscribe(self, request, id):
        """Подписаться на пользователя."""
        subscriber = request.user
        recipes_limit = request.GET.get('recipes_limit', 1000)
        context = {'recipes_limit': recipes_limit}
        user = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            try:
                Subscription.objects.get(subscriber=subscriber, user=id)
                return Response(status=status.HTTP_400_BAD_REQUEST)
            except Subscription.DoesNotExist:
                serializer = UserSubsciptionsSerializer(user, context=context)
                if subscriber.id != user.id:
                    Subscription.objects.create(subscriber=subscriber, user=user)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                return Response('Нельзя подписаться на самого себя!', status=status.HTTP_400_BAD_REQUEST)
        try:
            sub = Subscription.objects.get(subscriber=subscriber, user=id)
            sub.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Subscription.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Recipe."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeDisplaySerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (IsAuthorOrAdmin, IsAuthenticatedOrReadOnly,)
    filterset_class = RecipeFilter
    

    def create(self, request):
        """Создание рецепта."""
        serializer = RecipeInputSerializer(data=request.data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        """Обновление рецепта."""
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = RecipeInputSerializer(recipe, data=request.data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        if recipe.author == request.user:
            serializer.save()
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['GET'],
        url_path=r'(?P<id>\d+)/get-link',
    )
    def get_link(self, request, id):
        """Получить короткую ссылку на рецепт."""
        created, short_url  = shorten_url(request.build_absolute_uri()[:-9])
        return Response({'short-link': short_url}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
        url_path=r'(?P<id>\d+)/shopping_cart',
    )
    def shopping_cart(self, request, id):
        """Добавить рецепт в список покупок или удалить из него."""
        user = request.user
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
        permission_classes=[IsAuthenticated],
        url_path=r'(?P<id>\d+)/favorite',
    )
    def favorite(self, request, id):
        """Добавить рецепт в избранное или удалить из него."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=id)
        if request.method == 'POST':
            serializer = RecipeShortDisplaySerializer(recipe)
            try:
                Favorite.objects.get(user=user, recipe=recipe)
                return Response(status=status.HTTP_400_BAD_REQUEST)
            except Favorite.DoesNotExist:
                Favorite.objects.create(user=user, recipe=recipe)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        try:
            entry = Favorite.objects.get(user=user, recipe=recipe)
            entry.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Favorite.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    
    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок."""
        response = HttpResponse(content_type='text/plain')  
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        ingredients_list: dict[str:[str, int]] = {}
        recipes_in_cart = ShoppingCart.objects.filter(user=request.user)
        for recipe in recipes_in_cart:
            ingredients = RecipeIngredient.objects.filter(recipe=recipe.recipe.id)
            for ingredient_in in ingredients:
                name = ingredient_in.ingredient.name
                amount = ingredient_in.amount
                measurement_unit = ingredient_in.ingredient.measurement_unit
                if name in ingredients_list:
                    amount += ingredients_list[name][1]
                ingredients_list[name] =  [measurement_unit, amount]
        
        for ingredient_name, ingredient_measurement in ingredients_list.items():
            ingredient = (ingredient_name + '(' + ingredient_measurement[0] +
                           ')' + ' — ' + str(ingredient_measurement[1]) + '\n')
            response.write(ingredient)
        return response


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Получить токен авторизации."""
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token, _ = Token.objects.get_or_create(user=get_object_or_404(User,
            password=request.data['password'],
            email=request.data['email'],)
    )
    return Response({'auth_token': f'{token.key}'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Удаляет токен текущего пользователя."""
    token = Token.objects.get(user=request.user)
    token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
