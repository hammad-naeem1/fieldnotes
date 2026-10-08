from django.contrib import admin
from django.utils.html import format_html

from .models import BlogPost, Category, ContactMessage, Note, Profile, RateLimitBucket, SavedContent, Tag, UploadedAsset


class UploadedAssetInline(admin.TabularInline):
    model = UploadedAsset
    extra = 0
    fields = ("file", "original_name", "content_type", "file_size")
    readonly_fields = ("content_type", "file_size")
    show_change_link = True


class ContentAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "author", "published_at", "updated_at", "preview_link")
    list_filter = ("status", "published_at", "tags")
    search_fields = ("title", "summary", "body", "slug")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("tags",)
    date_hierarchy = "published_at"
    save_on_top = True

    @admin.display(description="Preview")
    def preview_link(self, obj):
        if not obj.pk:
            return "Save to preview"
        route = "preview_note" if isinstance(obj, Note) else "preview_post"
        return format_html('<a href="{}" target="_blank" rel="noopener">Open preview</a>', f"/{'manage/preview/notes' if route == 'preview_note' else 'manage/preview/blog'}/{obj.slug}/")


@admin.register(Note)
class NoteAdmin(ContentAdmin):
    list_display = ContentAdmin.list_display + ("category",)
    list_filter = ContentAdmin.list_filter + ("category",)
    autocomplete_fields = ("category", "author")
    inlines = (UploadedAssetInline,)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for deleted in formset.deleted_objects:
            deleted.delete()
        for instance in instances:
            if isinstance(instance, UploadedAsset) and not instance.uploaded_by_id:
                instance.uploaded_by = request.user
            instance.save()
        formset.save_m2m()


@admin.register(BlogPost)
class BlogPostAdmin(ContentAdmin):
    autocomplete_fields = ("category", "author")
    inlines = (UploadedAssetInline,)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for deleted in formset.deleted_objects:
            deleted.delete()
        for instance in instances:
            if isinstance(instance, UploadedAsset) and not instance.uploaded_by_id:
                instance.uploaded_by = request.user
            instance.save()
        formset.save_m2m()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "position")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("position", "name")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(UploadedAsset)
class UploadedAssetAdmin(admin.ModelAdmin):
    list_display = ("original_name", "content_type", "file_size", "note", "blog_post", "uploaded_by", "uploaded_at")
    search_fields = ("original_name", "note__title", "blog_post__title")
    readonly_fields = ("uploaded_at", "content_type", "file_size")
    autocomplete_fields = ("note", "blog_post")

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        if not obj.original_name and obj.file:
            obj.original_name = obj.file.name.rsplit("/", 1)[-1]
        if obj.file:
            obj.file_size = obj.file.size
            obj.content_type = obj.content_type or "application/octet-stream"
        super().save_model(request, obj, form, change)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "updated_at")
    search_fields = ("user__username", "user__email")


@admin.register(SavedContent)
class SavedContentAdmin(admin.ModelAdmin):
    list_display = ("user", "note", "blog_post", "created_at")
    search_fields = ("user__username", "note__title", "blog_post__title")
    readonly_fields = ("created_at",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "subject", "message", "created_at")
    list_editable = ("is_read",)

    def has_add_permission(self, request):
        return False


@admin.register(RateLimitBucket)
class RateLimitBucketAdmin(admin.ModelAdmin):
    list_display = ("action", "window", "hits")
    readonly_fields = ("action", "key_hash", "window", "hits")

    def has_add_permission(self, request):
        return False
