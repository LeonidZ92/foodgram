from django.contrib import admin
from recipes.models import Ingredient, Recipe, Tag

from foodgram import constants


class RecipeIngredientsInLine(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = constants.INLINE_EXTRA


class RecipeTagsInLine(admin.TabularInline):
    model = Recipe.tags.through
    extra = constants.INLINE_EXTRA


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    search_fields = ("name",)
    empty_value_display = "-пусто-"


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("author", "name", "text")
    list_display_links = ("author", "name")
    list_filter = ("tags", "author")
    inlines = (RecipeIngredientsInLine, RecipeTagsInLine)
    empty_value_display = "-пусто-"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return (
            queryset
            .select_related("author")
            .prefetch_related("tags")
            .prefetch_related("ingredient_list__ingredient")
        )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name",)
    empty_value_display = "-пусто-"
