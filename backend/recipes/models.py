from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from users.models import User

from foodgram import constants


class Ingredient(models.Model):
    """Модель для хранения информации об ингредиентах."""

    name = models.CharField(
        max_length=constants.INGREDIENT_NAME_MAX_LENGTH,
        unique=True,
        verbose_name="Название ингредиента",
    )
    measurement_unit = models.CharField(
        max_length=constants.MEASUREMENT_UNIT_MAX_LENGTH,
        verbose_name="Единица измерения",
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = (
            models.UniqueConstraint(
                fields=("name", "measurement_unit"),
                name="unique_ingredient",
            ),
        )

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Tag(models.Model):
    """Модель для тегов, которые используются для классификации рецептов."""

    name = models.CharField(
        max_length=constants.TAG_NAME_MAX_LENGTH,
        verbose_name="Название тега",
    )
    slug = models.SlugField(
        max_length=constants.TAG_SLUG_MAX_LENGTH,
        unique=True,
        verbose_name="Идентификатор",
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель для хранения рецептов."""

    name = models.CharField(
        max_length=constants.RECIPE_NAME_MAX_LENGTH,
        verbose_name="Название рецепта",
    )
    text = models.TextField(
        verbose_name="Описание рецепта",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name="Ингредиенты рецепта",
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(
                constants.COOKING_TIME_MIN,
                f"Не может быть меньше {constants.COOKING_TIME_MIN} минут(ы)",
            ),
            MaxValueValidator(
                constants.COOKING_TIME_MAX,
                f'Не может быть больше {constants.COOKING_TIME_MAX} минут(ы)'
            ),
        ),
        verbose_name="Время приготовления (минут)",
    )
    image = models.ImageField(
        verbose_name="Изображение рецепта",
        upload_to="media/recipes/",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор рецепта",
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="recipes",
        verbose_name="Теги рецепта",
    )

    class Meta:
        ordering = ("-id",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи рецептов с ингредиентами."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredient_list",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="ingredient_recipe",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(
                constants.INGREDIENT_AMOUNT_MIN,
                f"Минимальное количество — {constants.INGREDIENT_AMOUNT_MIN}",
            ),
            MaxValueValidator(
                constants.INGREDIENT_AMOUNT_MAX,
                f'Максимальное количество — {constants.INGREDIENT_AMOUNT_MAX}'
            ),
        ),
        verbose_name="Количество",
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Количество ингредиента"
        verbose_name_plural = "Количество ингредиентов"
        constraints = (
            models.UniqueConstraint(
                fields=("ingredient", "recipe"),
                name="unique_recipe_ingredient",
            ),
        )

    def __str__(self):
        return f"Рецепт {self.recipe} содержит ингредиент {self.ingredient}"


class Favorite(models.Model):
    """Модель для хранения информации о рецептах в избранном."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorite",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorite",
        verbose_name="Рецепт",
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные рецепты"

        constraints = (
            models.UniqueConstraint(
                fields=("user", "recipe"), name="unique_favorite_recipe"
            ),
        )

    def __str__(self):
        return f'Рецепт "{self.recipe}" в избранном у пользователя {self.user}'


class ShoppingList(models.Model):
    """Модель для хранения списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_list",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_list",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"

        constraints = (
            models.UniqueConstraint(
                fields=("user", "recipe"), name="unique_shopping_list_recipe"
            ),
        )

    def __str__(self):
        return (
            f"Пользователь {self.user} добавил {self.recipe} в список покупок"
        )
