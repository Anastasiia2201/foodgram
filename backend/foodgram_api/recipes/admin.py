from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe,
                     RecipeIngredient, RecipeTag, Tag)


class TagInline(admin.TabularInline):
    model = RecipeTag
    extra = 0


class IngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0


class RecipeAdmin(admin.ModelAdmin):

    inlines = [TagInline, IngredientInline]
    search_fields = ("author__username", "name")
    list_display = ("name", "author", "get_favorites")
    list_filter = ("tags__name",)
    filter_horizontal = ("tags",)

    @admin.display(description="Число добавлений рецепта в избранное")
    def get_favorites(self, obj):
        return len(Favorite.objects.get(recipe=obj.id))


class IngredientAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "measurement_unit")


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
