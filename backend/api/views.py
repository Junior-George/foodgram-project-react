import io

import djoser
from django.db.models import Sum
from django.db.models.expressions import Exists, OuterRef, Value
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
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
                          RecipeSerializer, ShopingCartCreateSerializer,
                          TagSerializer)

FILENAME = 'shoppingcart.pdf'


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    pagination_class = SubscriptionPagination
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
    pagination_class = SubscriptionPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = FollowListSerializer

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=self.request.user).all()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer_class()(page, many=True)
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = SubscriptionPagination
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        return Recipe.objects.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(
                    user=self.request.user, recipe=OuterRef('id'))),
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(
                    user=self.request.user,
                    recipe=OuterRef('id')))
        ).select_related('author').prefetch_related(
            'tags', 'ingredients', 'recipe',
            'shopping_cart', 'favorite_recipe'
        ) if self.request.user.is_authenticated else Recipe.objects.annotate(
            is_in_shopping_cart=Value(False),
            is_favorited=Value(False),
        ).select_related('author').prefetch_related(
            'tags', 'ingredients', 'recipe',
            'shopping_cart', 'favorite_recipe')

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


class FavoriteViewSet(
        generics.DestroyAPIView,
        generics.ListCreateAPIView):
    """Добавление и удаление рецепта в/из избранных."""

    serializer_class = ShopingCartCreateSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        recipe_id = self.kwargs.get('recipe_id')
        queryset = Favorite.objects.filter(
            pk=recipe_id
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
        recipe_id = self.kwargs.get('recipe_id')
        queryset = Favorite.objects.filter(
            pk=recipe_id
        )
        return queryset

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

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        """Качаем список с ингредиентами."""

        buffer = io.BytesIO()
        page = canvas.Canvas(buffer)
        pdfmetrics.registerFont(TTFont('Vera', 'Vera.ttf'))
        x_position, y_position = 50, 800
        shopping_cart = (
            request.user.shopping_cart.recipe.
            values(
                'ingredients__name',
                'ingredients__measurement_unit'
            ).annotate(amount=Sum('recipe__amount')).order_by())
        page.setFont('Vera', 14)
        if shopping_cart:
            indent = 20
            page.drawString(x_position, y_position, 'Cписок покупок:')
            for index, recipe in enumerate(shopping_cart, start=1):
                page.drawString(
                    x_position, y_position - indent,
                    f'{index}. {recipe["ingredients__name"]} - '
                    f'{recipe["amount"]} '
                    f'{recipe["ingredients__measurement_unit"]}.')
                y_position -= 15
                if y_position <= 50:
                    page.showPage()
                    y_position = 800
            page.save()
            buffer.seek(0)
            return FileResponse(
                buffer, as_attachment=True, filename=FILENAME)
        page.setFont('Vera', 24)
        page.drawString(
            x_position,
            y_position,
            'Cписок покупок пуст!')
        page.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=FILENAME)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    filterset_class = IngredientFilter
    serializer_class = IngredientSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
