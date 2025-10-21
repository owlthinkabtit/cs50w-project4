
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("u/<str:username>/", views.profile, name="profile"),
    path("api/follow/<str:username>", views.toggle_follow, name="toggle_follow"),
    path("following/", views.following_feed, name="following"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("api/posts", views.api_posts, name="api_posts"),
]
