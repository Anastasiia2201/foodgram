from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient, RecipeTag,
                     ShoppingCart, Subscription, Tag)


class TagInline(admin.TabularInline):
    model = RecipeTag
    extra = 0


class IngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [TagInline, IngredientInline]
    search_fields = ("author__username", "name")
    list_display = ("name", "author", "get_favorites")
    list_filter = ("tags__name",)
    filter_horizontal = ("tags",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("author").prefetch_related(
            "tags", "ingredients"
        )
        return qs

    @admin.display(
        description="Число добавлений рецепта в избранное"
    )
    def get_favorites(self, obj):
        return Favorite.objects.filter(recipe=obj.id).count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "measurement_unit")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    search_fields = ("user", "recipe")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("user", "recipe")
        return qs


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    search_fields = ("user", "recipe")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("user", "recipe")
        return qs


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "subscribee")
    search_fields = ("user", "subscribee")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("user", "subscribee")
        return qs
