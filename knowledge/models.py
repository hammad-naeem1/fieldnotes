from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify
from mimetypes import guess_type
from pathlib import Path

from .validators import validate_attachment, validate_cover_image


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    bio = models.CharField(max_length=280, blank=True)
    website = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.get_username()}"


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    description = models.CharField(max_length=240, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        self.slug = self.slug or slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        self.slug = self.slug or slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ContentBase(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True)
    summary = models.CharField(max_length=300)
    body = models.TextField(help_text="Markdown is supported. HTML is sanitized before display.")
    tags = models.ManyToManyField(Tag, blank=True, related_name="%(class)ss")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="%(class)ss")
    cover_image = models.ImageField(upload_to="covers/", blank=True, validators=[validate_cover_image])
    published_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-published_at", "-created_at"]

    def save(self, *args, **kwargs):
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Note(ContentBase):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="notes")


class BlogPost(ContentBase):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name="blog_posts", blank=True, null=True)


class SavedContent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_content")
    note = models.ForeignKey(Note, on_delete=models.CASCADE, blank=True, null=True, related_name="saved_by")
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, blank=True, null=True, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(Q(note__isnull=False, blog_post__isnull=True) | Q(note__isnull=True, blog_post__isnull=False)),
                name="saved_content_exactly_one_target",
            ),
            models.UniqueConstraint(fields=["user", "note"], condition=Q(note__isnull=False), name="unique_user_saved_note"),
            models.UniqueConstraint(fields=["user", "blog_post"], condition=Q(blog_post__isnull=False), name="unique_user_saved_post"),
        ]

    def __str__(self):
        return f"{self.user} saved {self.note or self.blog_post}"


class UploadedAsset(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, blank=True, null=True, related_name="assets")
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, blank=True, null=True, related_name="assets")
    file = models.FileField(upload_to="attachments/%Y/%m/", validators=[validate_attachment])
    original_name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=120, blank=True)
    file_size = models.PositiveBigIntegerField(default=0)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="uploaded_assets", blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]
        constraints = [
            models.CheckConstraint(
                condition=(Q(note__isnull=False, blog_post__isnull=True) | Q(note__isnull=True, blog_post__isnull=False)),
                name="uploaded_asset_exactly_one_target",
            ),
        ]

    def clean(self):
        if self.file:
            if not self.original_name:
                self.original_name = Path(self.file.name).name
            self.file_size = self.file.size
            self.content_type = guess_type(self.original_name)[0] or "application/octet-stream"

    def __str__(self):
        return self.original_name or self.file.name


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=160)
    message = models.TextField(max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} — {self.name}"


class RateLimitBucket(models.Model):
    action = models.CharField(max_length=32)
    key_hash = models.CharField(max_length=64)
    window = models.PositiveBigIntegerField()
    hits = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["action", "key_hash", "window"], name="unique_rate_limit_bucket"),
        ]
        indexes = [models.Index(fields=["window"], name="knowledge_rate_window")]
