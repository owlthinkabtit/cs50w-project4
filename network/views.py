from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.core.paginator import Paginator
import json


from .models import User, Post


def index(request):
    qs = Post.objects.select_related("author").prefetch_related("likes").all()
    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "network/index.html", {
        "page_obj": page_obj,
        "posts": page_obj.object_list,
        "total_posts": paginator.count,
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")

@require_http_methods(["GET", "POST"])
def api_posts(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        
        content = data.get("content", "").strip()
        if not content:
            return JsonResponse({"error": "Post cannot be empty"}, status=400)
        
        post = Post.objects.create(author=request.user, content=content)
        return JsonResponse ({
            "id": post.id,
            "author": post.author.username,
            "content": post.content,
            "created_at": post.created_at.strftime("%Y-%m-%d %H:%M"),
            "likes": 0
        }, status=201)
    return JsonResponse({"message": "ok"})

def profile(request, username):
    profile_user = get_object_or_404(User, username=username)

    posts = (profile_user.posts
             .select_related("author")
             .prefetch_related("likes")
             .all())
    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    is_self = request.user.is_authenticated and request.user.id == profile_user.id
    is_following = (
        request.user.is_authenticated
        and not is_self
        and profile_user in request.user.following.all()
    )

    context = {
        "profile_user": profile_user,
        "followers_count": profile_user.followers.count(),
        "following_count": profile_user.following.count(),
        "is_self": is_self,
        "is_following": is_following,
        "page_obj": page_obj,
        "posts": page_obj.object_list,
    }
    return render(request, "network/profile.html", context)

@require_POST
@login_required
def toggle_follow(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return JsonResponse({"error": "You cannot follow yourself."}, status=400)
    
    if target in request.user.following.all():
        request.user.following.remove(target)
        state = "unfollowed"
    else: 
        request.user.following.add(target)
        state = "followed"
    return JsonResponse({
        "state": state,
        "followers": target.followers.count()
    }) 
@login_required
def following_feed(request):
    following_users = request.user.following.all()
    posts = (
        Post.objects
            .filter(author__in=following_users)
            .select_related("author")
            .prefetch_related("likes")
            .order_by("-created_at")
    )   
    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "posts": page_obj.object_list,
        "page_obj": page_obj,
        "total_posts": paginator.count,
    }

    return render(request, "network/following.html", context)

@require_POST
@login_required
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    u = request.user

    if post.likes.filter(id=u.id).exists():
        post.likes.remove(u)
        liked = False

    else:
        post.likes.add(u)
        liked = True

    return JsonResponse({"liked": liked, "likes": post.likes.count(), "id": post.id})