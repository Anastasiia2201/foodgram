from django.urls import path, include
from rest_framework import routers

from .views import (
    TagViewSet,
    IngredientViewSet,
    UserViewSet,
    RecipeViewSet,
    login,
    logout
)

router = routers.DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('users', UserViewSet, basename='users')
router.register('recipes', RecipeViewSet, basename='recipes')

authpatterns = [
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
]

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', include(authpatterns)),
]
