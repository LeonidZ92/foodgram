from django.core.validators import MinValueValidator
from django.db import models

from foodgram import constants
from users.models import User


class Ingredient(models.Model):
    """
    Модель для хранения информации об ингредиентах.
    """

    name = models.CharField(
        max_length=constants.INGREDIENT_NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Название ингредиента',
        help_text='Введите название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=constants.MEASUREMENT_UNIT_MAX_LENGTH,
        verbose_name='Единица измерения',
        help_text='Введите единицу измерения для ингредиента',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient',
            ),
        )

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Tag(models.Model):
    """
    Модель для тегов, которые используются для классификации рецептов.
    """

    name = models.CharField(
        max_length=constants.TAG_NAME_MAX_LENGTH,
        verbose_name='Название тега',
        help_text='Введите название тега',
    )
    slug = models.SlugField(
        max_length=constants.TAG_SLUG_MAX_LENGTH,
        unique=True,
        verbose_name='Идентификатор',
        help_text='Введите уникальный идентификатор для тега',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """
    Модель для хранения рецептов.
    """

    name = models.CharField(
        max_length=constants.RECIPE_NAME_MAX_LENGTH,
        verbose_name='Название рецепта',
        help_text='Введите название рецепта',
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
        help_text='Введите описание или пошаговые инструкции рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        blank=False,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты рецепта',
        help_text='Выберите или добавьте ингредиенты для рецепта',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(
            constants.COOKING_TIME_MIN,
            f'Не может быть меньше {constants.COOKING_TIME_MIN} минут(ы)'
        ),),
        verbose_name='Время приготовления (минут)',
        help_text='Укажите время приготовления в минутах',
    )
    image = models.ImageField(
        blank=False,
        verbose_name='Изображение рецепта',
        help_text='Загрузите изображение готового блюда',
        upload_to='media/recipes/',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
    )
    tags = models.ManyToManyField(
        Tag,
        blank=False,
        through='RecipeTags',
        related_name='recipes',
        verbose_name='Теги рецепта',
        help_text='Выберите теги для классификации рецепта',
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """
    Промежуточная модель для связи рецептов с ингредиентами.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_list',
        verbose_name='Рецепт',
        help_text='Рецепт, в котором используется ингредиент',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipe',
        verbose_name='Ингредиент',
        help_text='Ингредиент, который используется в рецепте',
    )
    amount = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(
            constants.INGREDIENT_AMOUNT_MIN,
            f'Минимальное количество — {constants.INGREDIENT_AMOUNT_MIN}'
        ),),
        verbose_name='Количество',
        help_text='Укажите количество ингредиента',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = (
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique_recipe_ingredient',
            ),
        )

    def __str__(self):
        return f'Рецепт {self.recipe} содержит ингредиент {self.ingredient}'


class RecipeTags(models.Model):
    """
    Промежуточная модель для связи рецептов с тегами.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='tag_list',
        verbose_name='Рецепт',
        help_text='Рецепт, связанный с тегом',
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='tag_recipe',
        verbose_name='Тег',
        help_text='Тег, связанный с рецептом',
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецептов'

    def __str__(self):
        return f'Рецепт "{self.recipe}" имеет тег "{self.tag}"'


class Favorite(models.Model):
    """
    Модель для хранения информации о рецептах в избранном.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Пользователь',
        help_text='Пользователь, добавивший рецепт в избранное',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Рецепт',
        help_text='Рецепт, добавленный в избранное',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'

        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite_recipe'
            ),
        )

    def __str__(self):
        return f'Рецепт "{self.recipe}" в избранном у пользователя {self.user}'


class ShoppingList(models.Model):
    """
    Модель для хранения списка покупок.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Пользователь',
        help_text='Пользователь, добавивший рецепт в список покупок',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Рецепт',
        help_text='Рецепт, добавленный в список покупок',
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"

        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_list_recipe'
            ),
        )

    def __str__(self):
        return (
            f'Пользователь {self.user} добавил {self.recipe} в список покупок'
        )
