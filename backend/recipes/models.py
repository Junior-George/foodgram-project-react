from django.db import models
from users.models import User


class Ingredient(models.Model):
    name = models.CharField(
        max_length=100, verbose_name='Ингредиент'
    )
    measurement_unit = models.CharField(
        max_length=10, verbose_name='Единица измерения'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


class Tag(models.Model):
    name = models.CharField(
        max_length=10, unique=True, verbose_name='Имя тега'
    )
    color = models.CharField(
        max_length=7, unique=True, verbose_name='Цвет тега'
    )
    slug = models.SlugField(
        max_length=200, unique=True, verbose_name='Слаг тега'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class IngredientsInRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='ingredient'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self):
        return f'{self.ingredient.name} - {self.amount}'


class Recipe(models.Model):
    name = models.CharField(
        max_length=150, verbose_name='Название рецепта',
        unique=True
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='recipes', verbose_name='Автор'
    )
    image = models.ImageField(
        upload_to='static_back/recipes/imgs/', blank=True
    )
    ingredients = models.ManyToManyField(
        IngredientsInRecipe,
        verbose_name='Список ингредиентов'
    )
    text = models.TextField(max_length=250, verbose_name='Описания рецепта')
    tags = models.ManyToManyField(
        Tag, verbose_name='Список тегов',
        related_name='recipes'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления'
    )

    def __str__(self):
        return self.name[:72]

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorite',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='рецепт',
        related_name='favorite',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_favorite_recipe"
            )
        ]

    def __str__(self):
        return self.recipe.name


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='рецепт',
        related_name='shopping_cart',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart'
            ),
        )
