from django_filters import rest_framework

from recipes.models import Recipe, Tag


class RecipeFilter(rest_framework.FilterSet):
    """Доступна фильтрация по избранному, автору, списку покупок и тегам."""

    CHOICES = (
        (0, False),
        (1, True),
    )

    tags = rest_framework.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
    )
    author = rest_framework.NumberFilter(
        field_name="author",
    )
    is_in_shopping_cart = rest_framework.ChoiceFilter(
        choices=CHOICES, method="filter_is_in_shopping_cart"
    )
    is_favorited = rest_framework.ChoiceFilter(
        choices=CHOICES, method="filter_is_favorited"
    )

    class Meta:
        fields = ("tags", "author", "is_favorited", "is_in_shopping_cart")
        model = Recipe

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value[0] == "1":
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value[0] == "1":
            return queryset.filter(shoppingcart__user=self.request.user)
        return queryset
