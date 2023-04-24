from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (FavoriteViewSet, IngredientViewSet, RecipeViewSet,
                    ShoppingCartViewSet, TagViewSet, UserViewSet, FollowViewSet)

router = DefaultRouter()
router.register('recipes',
                ShoppingCartViewSet,
                basename='download_shopping_cart')
router.register('recipes',
                RecipeViewSet,
                basename='recipes')
router.register(r'recipes/(?P<recipe_id>\d+)/favorite',
                FavoriteViewSet,
                basename='favorite')
router.register(r'recipes/(?P<recipe_id>\d+)/shopping_cart',
                ShoppingCartViewSet,
                basename='shopping_cart')
router.register('ingredients',
                IngredientViewSet,
                basename='ingredients')
router.register('tags',
                TagViewSet,
                basename='tags')
router.register('users',
                FollowViewSet,
                basename='subscriptions')
router.register('users',
                UserViewSet,
                basename='users')
router.register('users',
                FollowViewSet,
                basename='subscribe')

urlpatterns = [
    path('', include(router.urls)),
]
