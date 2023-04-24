from django.contrib import admin

from users.models import Follow

from .models import (Favorite, Ingredient, IngredientsInRecipe, Recipe,
                     ShoppingCart, Tag)


class IngredientsInRecipeAdmin(admin.TabularInline):
    model = IngredientsInRecipe
    min_num = 1
    extra = 1


class IngredientsAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit',
    )
    list_filter = (
        'name',
    )
    search_fields = (
        'name',
    )
    empty_value_display = (
        '-пусто-'
    )


class TagsAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'color',
        'slug',
    )
    empty_value_display = (
        '-пусто-',
    )


#class RecipeAdmin(admin.ModelAdmin):
#    inlines = (IngredientsInRecipeAdmin,)
#    empty_value_display = ('пусто')


admin.site.register(Ingredient, IngredientsAdmin)
admin.site.register(Tag, TagsAdmin)
admin.site.register(Recipe)
admin.site.register(Favorite)
admin.site.register(Follow)
admin.site.register(ShoppingCart)
admin.site.register(IngredientsInRecipe)
