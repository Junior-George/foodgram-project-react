import djoser
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, IngredientsInRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from users.models import Follow, User

from .filters import RecipeFilter
from .pagination import SubscriptionPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (CustomUserCreateSerializer, CustomUserSerializer,
                          FollowListSerializer, FollowSerializer,
                          GetRecipeSerializer, IngredientSerializer,
                          RecipeSerializer, ShopingCartCreateSerializer,
                          TagSerializer)


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    pagination_class = SubscriptionPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ('subscribe'):
            return FollowSerializer
        elif self.action == 'subscriptions':
            return FollowListSerializer
        elif self.action == "set_password":
            return djoser.serializers.SetPasswordSerializer
        elif self.action == "create":
            return CustomUserCreateSerializer
        else:
            return CustomUserSerializer

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
                status=status.HTTP_404_BAD_REQUEST
            )

    def list(self, request):
        queryset = User.objects.all()
        serializer = CustomUserSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=False)
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

    def get_serializer_class(self):
        if self.action in ('favorite'):
            return ShopingCartCreateSerializer
        elif self.action in ('shopping_cart'):
            return ShopingCartCreateSerializer
        elif self.action in ('get', 'list'):
            return GetRecipeSerializer
        else:
            return RecipeSerializer

    def retrieve(self, request, pk=None):
        queryset = Recipe.objects.all()
        recipe = get_object_or_404(queryset, pk=pk)
        serializer = GetRecipeSerializer(recipe, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        if request.method == 'POST':
            Favorite.objects.create(user=user, recipe=recipe)
            queryset = Recipe.objects.get(pk=pk)
            serializer = self.get_serializer_class()(queryset, many=False)
            return Response(serializer.data)
        else:
            Favorite.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            ShoppingCart.objects.create(user=user, recipe=recipe)
            queryset = Recipe.objects.get(pk=pk)
            serializer = self.get_serializer_class()(queryset, many=False)
            return Response(serializer.data)
        else:
            ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

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


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
