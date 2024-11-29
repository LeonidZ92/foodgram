from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET

from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.reverse import reverse

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomLimitPagination
from api.permissions import IsAdminAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    CustomUserSerializer,
    FavoriteRecipeSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    SubscriberDetailSerializer,
    TagSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingList,
    Tag,
)
from users.models import Subscription

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomLimitPagination

    @action(["get"], detail=False, permission_classes=(IsAuthenticated,))
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(
        ["put"],
        detail=False,
        permission_classes=(IsAdminAuthorOrReadOnly,),
        url_path="me/avatar",
    )
    def avatar(self, request, *args, **kwargs):
        serializer = AvatarSerializer(
            instance=request.user,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        user = self.request.user
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=("GET",),
        permission_classes=(IsAuthenticated,),
        url_path="subscriptions",
        url_name="subscriptions",
    )
    def subscriptions(self, request):
        user = request.user
        queryset = (
            Subscription.objects.filter(user=user)
            .select_related("author")
            .prefetch_related("author__recipes")
            .annotate(recipes_count=Count("author__recipes"))
        )
        pages = self.paginate_queryset(queryset)
        serializer = SubscriberDetailSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=("post", "delete"),
    )
    def subscribe(self, request, id):
        user = request.user

        if self.request.method == "POST":
            author = get_object_or_404(User, id=id)
            if user == author:
                return Response(
                    {"errors": "Вы не можете подписаться на себя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {"errors": "Вы уже подписаны на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription = Subscription.objects.create(
                user=user, author=author
            )
            queryset = (
                Subscription.objects.filter(id=subscription.id)
                .annotate(recipes_count=Count("author__recipes"))
                .first()
            )
            serializer = SubscriberDetailSerializer(
                queryset, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif self.request.method == "DELETE":
            if not User.objects.filter(id=id).exists():
                return Response(
                    {"errors": "Пользователь с данным ID не найден"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            deleted_count, _ = Subscription.objects.filter(
                user=user, author_id=id
            ).delete()

            if deleted_count == 0:
                return Response(
                    {"errors": "Вы не подписаны на данного пользователя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAdminAuthorOrReadOnly,)
    pagination_class = None
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ("^name",)


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminAuthorOrReadOnly,)
    pagination_class = CustomLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    queryset = Recipe.objects.select_related("author").prefetch_related(
        "tags", "ingredients"
    )

    def get_serializer_class(self):
        if self.action in ("list", "retrieve", "get-link"):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(
        detail=True,
        methods=["GET"],
        permission_classes=[AllowAny],
        url_path="get-link",
        url_name="get-link",
    )
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        rev_link = reverse("short_url", args=[recipe.pk])
        return Response(
            {"short-link": request.build_absolute_uri(rev_link)},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        permission_classes=[IsAuthenticated],
        url_path="shopping_cart",
        url_name="shopping_cart",
    )
    def shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == "POST":
            if ShoppingList.objects.filter(recipe=recipe, user=user).exists():
                return Response(
                    {
                        "detail": f'Рецепт "{recipe.name}" уже был добавлен '
                        "в список покупок."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingList.objects.create(recipe=recipe, user=user)
            serializer = FavoriteRecipeSerializer(
                recipe, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            cart_item = ShoppingList.objects.filter(recipe__id=pk, user=user)
            if cart_item.exists():
                cart_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {
                    "detail": f'Рецепт "{recipe.name}" отсутствует '
                    "в списке покупок."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    @staticmethod
    def shopping_list_to_txt(ingredients):
        return "\n".join(
            f'{ingredient["ingredient__name"]} - {ingredient["sum"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            for ingredient in ingredients
        )

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[IsAuthenticated],
        url_path="download_shopping_cart",
        url_name="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shopping_list__user=request.user
            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(sum=Sum("amount"))
        )
        shopping_list = self.shopping_list_to_txt(ingredients)
        return HttpResponse(shopping_list, content_type="text/plain")

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        permission_classes=[IsAuthenticated],
        url_path="favorite",
        url_name="favorite",
    )
    def favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == "POST":
            if Favorite.objects.filter(recipe=recipe, user=user).exists():
                return Response(
                    {
                        "detail": f'Рецепт "{recipe.name}" уже был добавлен '
                        "в избранное."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Favorite.objects.create(recipe=recipe, user=user)
            serializer = FavoriteRecipeSerializer(
                recipe, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            favorite_entry = Favorite.objects.filter(recipe=recipe, user=user)
            if favorite_entry.exists():
                favorite_entry.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"detail": f'Рецепт "{recipe.name}" не в избранном.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


@require_GET
def short_url(request, pk):
    if not Recipe.objects.filter(pk=pk).exists():
        raise Http404(f'Рецепт с id "{pk}" не существует.')

    return redirect(f"/recipes/{pk}/")
