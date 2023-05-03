from django_filters import (BooleanFilter, CharFilter, FilterSet,
                            ModelMultipleChoiceFilter, NumberFilter)
from recipes.models import Recipe, Tag


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='istartswith')


class RecipeFilter(FilterSet):
    author = NumberFilter(
        field_name='author__id')
    tags = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'
    )

    is_favorited = BooleanFilter(
        method='get_is_favorited'
    )
    is_in_shopping_cart = BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    def get_is_favorited(self, queryset, name, value):

        if value:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset

    class Meta():
        model = Recipe
        fields = ('author', 'tags', 'is_in_shopping_cart', 'is_favorited')
