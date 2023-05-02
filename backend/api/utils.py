from django.shortcuts import get_object_or_404
from recipes.models import Ingredient, IngredientsInRecipe


def add_ingredients(ingredients, obj):
    for ingredient in ingredients:
        c_ing = get_object_or_404(
            Ingredient, pk=ingredient['ingredient']['id']
        )
        ing_rec, status = IngredientsInRecipe.objects.get_or_create(
            amount=ingredient['amount'],
            ingredient=c_ing
        )
        obj.ingredients.add(ing_rec.id)
    return obj
