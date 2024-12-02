from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingList,
    Tag,
)
from rest_framework import serializers
from users.models import Subscription

from foodgram import constants

from .utils import get_serializer_method_field_value

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """Сериализатор для работы с информацией о пользователях."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(represent_in_base64=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        return request.user.follower.filter(author=obj).exists()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователей."""

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
        )


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ("avatar",)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeReadSerializer(serializers.ModelSerializer):

    tags = TagSerializer(many=True)
    author = CustomUserSerializer()
    ingredients = RecipeIngredientSerializer(
        source="ingredient_list", many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, recipe):
        return get_serializer_method_field_value(
            self.context, Favorite, recipe, "user_id", "recipe"
        )

    def get_is_in_shopping_cart(self, recipe):
        return get_serializer_method_field_value(
            self.context, ShoppingList, recipe, "user_id", "recipe"
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        label="Tags",
    )
    ingredients = RecipeIngredientWriteSerializer(
        many=True,
        label="Ingredients",
    )
    image = Base64ImageField(allow_null=True, label="images")

    class Meta:
        model = Recipe
        fields = (
            "tags",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError("Добавьте тег")

        if len(value) != len(set(value)):
            raise serializers.ValidationError("Теги должны быть уникальными")

        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Добавьте ингредиент")

        ingredient_ids = [ingredient["id"] for ingredient in value]
        existing_ingredient_count = Ingredient.objects.filter(
            id__in=ingredient_ids
        ).count()
        if existing_ingredient_count != len(ingredient_ids):
            raise serializers.ValidationError(
                "Один или несколько ингредиентов не существуют"
            )

        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                "Вы должны добавить изображение для рецепта"
            )
        return value

    def to_representation(self, instance):
        serializer = RecipeReadSerializer(
            instance, context={"request": self.context.get("request")}
        )
        return serializer.data

    def create_tags(self, tags, recipe):
        recipe.tags.set(tags)

    def create_ingredients(self, ingredients, recipe):
        for ingredient_data in ingredients:
            ingredient_id = ingredient_data["id"]
            ingredient = Ingredient.objects.get(pk=ingredient_id)
            amount = ingredient_data["amount"]
            RecipeIngredient.objects.create(
                ingredient=ingredient, recipe=recipe, amount=amount
            )

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        user = self.context.get("request").user
        recipe = Recipe.objects.create(**validated_data, author=user)
        self.create_tags(tags, recipe)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.get("tags")
        if tags is None:
            raise serializers.ValidationError({"tags": "Добавьте тег"})
        ingredients = validated_data.get("ingredients")
        if ingredients is None:
            raise serializers.ValidationError(
                {"ingredients": "Добавьте ингридиент"}
            )
        instance.tags.set(tags)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.create_ingredients(validated_data.pop("ingredients"), instance)
        return super().update(instance, validated_data)


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class SubscriberDetailSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source="author.email")
    id = serializers.ReadOnlyField(source="author.id")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)
    avatar = Base64ImageField(source="author.avatar")

    class Meta:
        model = Subscription
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def create(self, validated_data):
        user = validated_data.pop('user')
        author = validated_data.pop('author')
        return Subscription.objects.create(user=user, author=author)

    def get_is_subscribed(self, obj):
        user = self.context.get("request").user
        return Subscription.objects.filter(
            author=obj.author, user=user
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit", constants.PAGE_SIZE)
        limit = (
            int(limit)
            if isinstance(limit, str) and limit.isdigit()
            else constants.PAGE_SIZE
        )

        return ShortRecipeSerializer(
            Recipe.objects.filter(author=obj.author)[:limit],
            many=True,
            context={"request": request},
        ).data


class FavoriteRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ("id", "user", "recipe")
