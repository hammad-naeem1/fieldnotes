from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
import mimetypes
from pathlib import Path

from .forms import ContactForm, ProfileForm, RegistrationForm
from .models import BlogPost, Category, ContactMessage, Note, Profile, SavedContent, Tag, UploadedAsset
from .rate_limits import rate_limit

User = get_user_model()


def published(queryset):
    return queryset.filter(status="published", published_at__lte=timezone.now())


def home(request):
    notes = published(Note.objects.select_related("category", "author").prefetch_related("tags"))[:4]
    posts = published(BlogPost.objects.select_related("author").prefetch_related("tags"))[:3]
    return render(request, "knowledge/home.html", {"recent_notes": notes, "recent_posts": posts})


def notes(request):
    queryset = published(Note.objects.select_related("category", "author").prefetch_related("tags"))
    category_slug = request.GET.get("category", "").strip()
    tag_slug = request.GET.get("tag", "").strip()
    query = request.GET.get("q", "").strip()[:100]
    current_category = None
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        queryset = queryset.filter(category=current_category)
    if tag_slug:
        queryset = queryset.filter(tags__slug=tag_slug)
    if query:
        queryset = queryset.filter(Q(title__icontains=query) | Q(summary__icontains=query) | Q(body__icontains=query))
    page = Paginator(queryset.distinct(), 12).get_page(request.GET.get("page"))
    return render(request, "knowledge/notes.html", {
        "page": page,
        "categories": Category.objects.all(),
        "tags": Tag.objects.all(),
        "current_category": current_category,
        "current_tag": tag_slug,
        "query": query,
    })


def note_detail(request, slug):
    note = get_object_or_404(
        published(Note.objects.select_related("category", "author").prefetch_related("tags", "assets")),
        slug=slug,
    )
    related = published(Note.objects.filter(tags__in=note.tags.all()).exclude(pk=note.pk).distinct())[:3]
    is_saved = request.user.is_authenticated and SavedContent.objects.filter(user=request.user, note=note).exists()
    return render(request, "knowledge/note_detail.html", {"note": note, "related_notes": related, "is_saved": is_saved})


def blog(request):
    queryset = published(BlogPost.objects.select_related("author", "category").prefetch_related("tags"))
    query = request.GET.get("q", "").strip()[:100]
    tag_slug = request.GET.get("tag", "").strip()
    if query:
        queryset = queryset.filter(Q(title__icontains=query) | Q(summary__icontains=query) | Q(body__icontains=query))
    if tag_slug:
        queryset = queryset.filter(tags__slug=tag_slug)
    page = Paginator(queryset.distinct(), 10).get_page(request.GET.get("page"))
    return render(request, "knowledge/blog.html", {"page": page, "query": query, "current_tag": tag_slug, "tags": Tag.objects.all()})


def blog_detail(request, slug):
    post = get_object_or_404(
        published(BlogPost.objects.select_related("category", "author").prefetch_related("tags", "assets")),
        slug=slug,
    )
    is_saved = request.user.is_authenticated and SavedContent.objects.filter(user=request.user, blog_post=post).exists()
    related = published(BlogPost.objects.filter(tags__in=post.tags.all()).exclude(pk=post.pk).distinct())[:3]
    return render(request, "knowledge/blog_detail.html", {"post": post, "related_posts": related, "is_saved": is_saved})


def search(request):
    query = request.GET.get("q", "").strip()[:100]
    note_results = Note.objects.none()
    if query:
        note_results = published(Note.objects.select_related("category").filter(
            Q(title__icontains=query) | Q(summary__icontains=query) | Q(body__icontains=query)
        )).distinct()[:20]
        blog_results = published(BlogPost.objects.filter(
            Q(title__icontains=query) | Q(summary__icontains=query) | Q(body__icontains=query)
        )).distinct()[:20]
    else:
        blog_results = BlogPost.objects.none()
    return render(request, "knowledge/search.html", {"query": query, "note_results": note_results, "blog_results": blog_results})


def about(request):
    return render(request, "knowledge/about.html")


@rate_limit("contact", limit=5, window_seconds=3600)
def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Thanks for reaching out. Your message has been received.")
        return redirect("contact")
    return render(request, "knowledge/contact.html", {"form": form})


@rate_limit("signup", limit=5, window_seconds=3600)
def signup(request):
    if request.user.is_authenticated:
        return redirect("profile")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready.")
        return redirect("profile")
    return render(request, "registration/signup.html", {"form": form})


@rate_limit("login", limit=10, window_seconds=900)
def login_view(request):
    if request.user.is_authenticated:
        return redirect("profile")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "You are signed in.")
        destination = request.POST.get("next", "") or request.GET.get("next", "")
        if destination and url_has_allowed_host_and_scheme(destination, {request.get_host()}):
            return redirect(destination)
        return redirect("profile")
    return render(request, "registration/login.html", {"form": form})


@login_required
def profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=profile_obj, initial={
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
    })
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()
            request.user.first_name = form.cleaned_data["first_name"]
            request.user.last_name = form.cleaned_data["last_name"]
            request.user.save(update_fields=["first_name", "last_name"])
        messages.success(request, "Your profile has been updated.")
        return redirect("profile")
    return render(request, "accounts/profile.html", {"form": form})


@login_required
def saved_content(request):
    now = timezone.now()
    items = SavedContent.objects.filter(user=request.user).filter(
        Q(note__status="published", note__published_at__lte=now)
        | Q(blog_post__status="published", blog_post__published_at__lte=now)
    ).select_related(
        "note", "note__category", "blog_post", "blog_post__category"
    )
    notes_saved = [item.note for item in items if item.note]
    posts_saved = [item.blog_post for item in items if item.blog_post]
    return render(request, "accounts/saved.html", {"notes_saved": notes_saved, "posts_saved": posts_saved})


def download_asset(request, asset_id):
    asset = get_object_or_404(UploadedAsset.objects.select_related("note", "blog_post"), pk=asset_id)
    visible = (
        asset.note is not None and published(Note.objects.filter(pk=asset.note_id)).exists()
    ) or (
        asset.blog_post is not None and published(BlogPost.objects.filter(pk=asset.blog_post_id)).exists()
    )
    if not visible and not (request.user.is_staff and request.user.has_perm("knowledge.view_uploadedasset")):
        raise Http404
    name = asset.original_name or Path(asset.file.name).name
    content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
    inline = Path(name).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    response = FileResponse(asset.file.open("rb"), content_type=content_type, as_attachment=not inline, filename=name)
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
def toggle_saved(request, kind, slug):
    if request.method != "POST":
        raise Http404
    intent = request.POST.get("intent")
    if intent not in {"save", "remove"}:
        return HttpResponseBadRequest("Choose whether to save or remove this item.")
    if kind == "note":
        content = get_object_or_404(published(Note.objects.all()), slug=slug)
        lookup = {"user": request.user, "note": content}
        detail_url = "note_detail"
    elif kind == "post":
        content = get_object_or_404(published(BlogPost.objects.all()), slug=slug)
        lookup = {"user": request.user, "blog_post": content}
        detail_url = "blog_detail"
    else:
        raise Http404
    if intent == "remove":
        SavedContent.objects.filter(**lookup).delete()
        messages.info(request, "Removed from your saved content.")
    else:
        _, created = SavedContent.objects.get_or_create(**lookup)
        if created:
            messages.success(request, "Added to your saved content.")
        else:
            messages.info(request, "This item is already saved.")
    destination = request.POST.get("next", "")
    if destination and url_has_allowed_host_and_scheme(destination, {request.get_host()}):
        return redirect(destination)
    return redirect(detail_url, slug=slug)


@staff_member_required
def dashboard(request):
    context = {
        "note_count": Note.objects.count(),
        "draft_notes": Note.objects.filter(status="draft").count(),
        "post_count": BlogPost.objects.count(),
        "draft_posts": BlogPost.objects.filter(status="draft").count(),
        "member_count": User.objects.filter(is_staff=False).count(),
        "unread_messages": ContactMessage.objects.filter(is_read=False).count(),
    }
    return render(request, "admin/dashboard.html", context)


@staff_member_required
def preview_note(request, slug):
    if not request.user.has_perm("knowledge.change_note"):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    note = get_object_or_404(Note.objects.select_related("category", "author").prefetch_related("tags", "assets"), slug=slug)
    return render(request, "knowledge/note_detail.html", {"note": note, "preview_mode": True, "related_notes": [], "is_saved": False})


@staff_member_required
def preview_post(request, slug):
    if not request.user.has_perm("knowledge.change_blogpost"):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    post = get_object_or_404(BlogPost.objects.select_related("category", "author").prefetch_related("tags", "assets"), slug=slug)
    return render(request, "knowledge/blog_detail.html", {"post": post, "preview_mode": True, "related_posts": [], "is_saved": False})


def not_found(request, exception=None):
    return render(request, "errors/404.html", status=404)


def server_error(request):
    return render(request, "errors/500.html", status=500)
