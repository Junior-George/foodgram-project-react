from djoser.serializers import UserCreateSerializer
from drf_base64.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, IngredientsInRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from rest_framework.validators import UniqueTogetherValidator
from users.models import Follow, User

from .utils import add_ingredients


class GetIsSubscribedMixin:

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return user.follower.filter(author=obj).exists()


class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
        )

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance


class CustomUserSerializer(GetIsSubscribedMixin,
                           serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'id',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=request.user, author=obj
        ).exists()


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.CharField(
        source='ingredient.id'
    )
    name = serializers.CharField(
        source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)

    class Meta:
        model = IngredientsInRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(
            slug_field='username',
            read_only=True,
            default=serializers.CurrentUserDefault()
        )
    ingredients = IngredientInRecipeSerializer(
        many=True
    )
    image = Base64ImageField(
        max_length=None,
        use_url=True)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        add_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        ingredients = validated_data.pop('ingredients')
        add_ingredients(ingredients, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        instance = GetRecipeSerializer(instance).data
        return instance

    class Meta:
        model = Recipe
        fields = (
            'name',
            'author',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time'
        )


class GetRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    author = CustomUserSerializer(many=False)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'author',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def is_object_exists(self, model, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return model.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_favorited(self, obj):
        return self.is_object_exists(Favorite, obj)

    def get_is_in_shopping_cart(self, obj):
        return self.is_object_exists(ShoppingCart, obj)

    def get_ingredients(self, obj):
        ings = IngredientsInRecipe.objects.filter(recipe=obj).all()
        return IngredientInRecipeSerializer(ings, many=True).data


class FollowSerializer(serializers.ModelSerializer):
    following = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all()
    )
    user = serializers.SlugRelatedField(
        read_only=True, slug_field='username',
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        fields = ('user', 'following')
        model = Follow
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following')
            )
        ]

    def to_representation(self, instance):
        instance = FollowListSerializer(instance).data
        return instance


class RecipeInFollowList(serializers.ModelSerializer):

    class Meta:
        fields = (
            'id', 'name', 'image', 'cooking_time'
        )
        model = Recipe


class FollowListSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    recipes = serializers.SerializerMethodField()

    class Meta:
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed', 'recipes',
                  'recipes_count'
                  )
        model = User

    def get_recipes(self, user):

        recipes = user.recipes.all()
        recipes = recipes[0:3]
        return RecipeInFollowList(
            instance=recipes,
            many=True,
            context=self.context
        ).data

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            author=obj
        ).exists()

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(
            author=obj
        ).count()


class ShopingCartSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('user', 'recipe')
        model = ShoppingCart


class ShopingCartCreateSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipe


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ()
        model = Favorite


class RecipesParamsSerializer(serializers.Serializer):
    is_favorited = serializers.ChoiceField(
        required=False, choices=[0, 1]
    )
    is_in_shopping_cart = serializers.ChoiceField(
        required=False, choices=[0, 1]
    )
    author = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=User.objects.all()
    )
    tags = serializers.SlugRelatedField(
        required=False,
        many=True,
        queryset=Tag.objects.all(),
        slug_field='slug'
    )
