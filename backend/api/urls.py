from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (FavoriteViewSet, FollowViewSet, IngredientViewSet,
                    RecipeViewSet, ShoppingCartViewSet, TagViewSet,
                    UserViewSet, FollowListViewSet)


router = DefaultRouter()

router.register('users', FollowListViewSet, basename='subscribtions')
#router.register('recipes/download_shopping_cart/', DownloadShopingCart, basename='download_sh_ct')
router.register('users', UserViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('recipes', RecipeViewSet)
#router.register(r'recipes/(?P<recipe_id>\d+)/favorite/', FavoriteViewSet, basename='favorite')
#router.register(r'recipes/(?P<recipe_id>\d+)/shopping_cart/', ShoppingCartViewSet, basename='shopping_cart')
router.register('users', FollowViewSet, basename='subscribe')

#router.register('users',
#                FollowViewSet,
#                basename='subscriptions')

urlpatterns = [
     #path(
     #     'users/<int:user_id>/subscribe/',
     #     FollowViewSet.as_view(),
     #     name='subscribe'),
     #path(
     #     'users/subscriptions',
     #     FollowListViewSet.as_view(),
     #     name='subscriptions'
     #),
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

#router = DefaultRouter()
#router.register('recipes',
#                ShoppingCartViewSet,
#                basename='download_shopping_cart')
#router.register('recipes',
#                RecipeViewSet,
#                basename='recipes')
#router.register(r'recipes/(?P<recipe_id>\d+)/favorite',
#                FavoriteViewSet,
#                basename='favorite')
#router.register(r'recipes/(?P<recipe_id>\d+)/shopping_cart',
#                ShoppingCartViewSet,
#                basename='shopping_cart')
#router.register('ingredients',
#                IngredientViewSet,
#                basename='ingredients')
#router.register('tags',
#                TagViewSet,
#                basename='tags')
#router.register('users',
#                UserViewSet,
#                basename='users')
#router.register('users',
#                FollowViewSet,
#                basename='subscriptions')
#
#router.register('users',
#                FollowViewSet,
#                basename='subscribe')
#
#urlpatterns = [
#    path('', include(router.urls)),
#]
