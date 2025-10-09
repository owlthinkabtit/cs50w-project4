from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Post

# Register your models here.
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "created_at")
    autocomplete_fields = ("author", "likes")

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    filter_horizontal = ("following",)
