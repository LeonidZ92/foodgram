from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import Subscription, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "id",
        "email",
        "first_name",
        "last_name",
    )
    search_fields = ("first_name", "last_name", "email", "username")
    empty_value_display = "-пусто-"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user_username",
        "author_username",
    )
    list_display_links = (
        "user_username",
        "author_username",
    )
    search_fields = (
        "user__username",
        "user__email",
        "author__username",
        "author__email",
    )
    empty_value_display = "-пусто-"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("user", "author")

    def user_username(self, obj):
        return obj.user.username

    def author_username(self, obj):
        return obj.author.username
