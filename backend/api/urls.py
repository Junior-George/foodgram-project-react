from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (FavoriteViewSet, FollowListViewSet, FollowViewSet,
                    IngredientViewSet, RecipeViewSet, ShoppingCartViewSet,
                    TagViewSet, UserViewSet)

router = DefaultRouter()

router.register('users', FollowListViewSet, basename='subscribtions')
router.register('users', UserViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('recipes', RecipeViewSet)
router.register('users', FollowViewSet, basename='subscribe')

urlpatterns = [
     path(
          'recipes/<int:recipe_id>/favorite/',
          FavoriteViewSet.as_view(),
          name='favorite_recipe'),
     path(
          'recipes/<int:recipe_id>/shopping_cart/',
          ShoppingCartViewSet.as_view(),
          name='shopping_cart'),
     path('', include(router.urls)),
     path('', include('djoser.urls')),
     path('auth/', include('djoser.urls.authtoken')),
]
