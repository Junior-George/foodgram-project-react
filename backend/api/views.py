import djoser
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, IngredientsInRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import Follow, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import SubscriptionPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (CustomUserCreateSerializer, CustomUserSerializer,
                          FollowListSerializer, FollowSerializer,
                          GetRecipeSerializer, IngredientSerializer,
                          RecipeSerializer, RecipesParamsSerializer,
                          ShopingCartCreateSerializer, TagSerializer)


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.action == "set_password":
            return djoser.serializers.SetPasswordSerializer
        elif self.action == "create":
            return CustomUserCreateSerializer
        else:
            return CustomUserSerializer

    def list(self, request):
        queryset = User.objects.all()
        serializer = CustomUserSerializer(queryset, many=True)
        return Response(serializer.data)


class FollowViewSet(UserViewSet):
    queryset = User.objects.all()
    pagination_class = SubscriptionPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ('subscribe'):
            return FollowSerializer
        elif self.action == 'subscriptions':
            return FollowListSerializer

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, pk=id)
        if user == author:
            return Response(
                {"errors": "На себя подписываться нельзя"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            Follow.objects.create(user=user, author=author)
            queryset = User.objects.get(pk=id)
            serializer = self.get_serializer_class()(queryset, many=False)
            return Response(serializer.data)
        else:
            if Follow.objects.filter(user=user, author=author).exists():
                Follow.objects.filter(user=user, author=author).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"detail": "Страница не найдена"},
                status=status.HTTP_400_BAD_REQUEST
            )


class FollowListViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = FollowListSerializer

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=self.request.user).all()
        page = self.paginate_queryset(queryset)
        serializer = FollowListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('get', 'list'):
            return GetRecipeSerializer
        else:
            return RecipeSerializer

    def retrieve(self, request, pk=None):
        queryset = Recipe.objects.all()
        recipe = get_object_or_404(queryset, pk=pk)
        serializer = GetRecipeSerializer(recipe, context={'request': request})
        return Response(serializer.data)

    def get_serializer_context(self):
        """Возвращает контекст сериализатора."""
        context = super().get_serializer_context()
        query = RecipesParamsSerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        query_params = query.validated_data
        context['is_favorited'] = query_params.get(
            'is_favorited'
        )
        context['is_in_shopping_cart'] = query_params.get(
            'is_in_shopping_cart'
        )
        author = query_params.get('author')
        context['author'] = author.pk if author else None
        tags_slug = query_params.get('tags')
        context['tags'] = (
            [slug.pk for slug in tags_slug] if tags_slug else None
        )
        return context

    def send_message(self, ingredients):
        shopping_list = ''
        for ingredient in ingredients:
            shopping_list += (
                f"\n{ingredient['ingredient__name']} "
                f"{ingredient['ingredient__measurement_unit']} "
                f"{ingredient['amount']}"
            )
        file = 'shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{file}"'
        return response

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        ings = IngredientsInRecipe.objects.select_related(
            'recipe', 'ingredient'
        )
        if request.user.is_authenticated:
            ings = ings.filter(
                recipe__shopping_cart__user=request.user
            ).order_by("ingredient__name")
        else:
            ings = ings.filter(
                recipe_id__in=request.session['purchases']
            )
        ingredients = ings.values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            amount=Sum('amount')
        )
        return self.send_message(ingredients)

    def get_queryset(self):
        """Возвращает выборку данных по рецептам."""
        queryset = super().get_queryset()
        context = self.get_serializer_context()
        user = self.request.user
        if context['is_favorited']:
            queryset = queryset.filter(favorite__user=user)
        if context['is_in_shopping_cart']:
            queryset = queryset.filter(shopping_cart__user=user)
        if context['author']:
            queryset = queryset.filter(author__id=context['author'])
        if context['tags']:
            queryset = queryset.filter(tags__id__in=context['tags']).distinct()
        return queryset


class FavoriteViewSet(
        generics.DestroyAPIView,
        generics.ListCreateAPIView):
    """Добавление и удаление рецепта в/из избранных."""

    serializer_class = ShopingCartCreateSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        recipe_id = self.kwargs.get('recipe_id')
        queryset = Favorite.objects.filter(
            pk=recipe_id, user=self.request.user
        )
        return queryset

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        Favorite.objects.create(user=self.request.user, recipe=recipe)
        serializer = ShopingCartCreateSerializer(recipe, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        Favorite.objects.filter(user=self.request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(
                         generics.DestroyAPIView,
                         generics.ListCreateAPIView):

    serializer_class = ShopingCartCreateSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        return Recipe.shopping_carts.through.objects.filter(
            customuser_id=self.request.user.pk
        )

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        ShoppingCart.objects.create(user=self.request.user, recipe=recipe)
        serializer = ShopingCartCreateSerializer(recipe, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        ShoppingCart.objects.filter(
            user=self.request.user, recipe=recipe
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
