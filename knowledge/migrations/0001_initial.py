import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import knowledge.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("slug", models.SlugField(max_length=90, unique=True)),
                ("description", models.CharField(blank=True, max_length=240)),
                ("position", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"ordering": ["position", "name"], "verbose_name_plural": "categories"},
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
                ("slug", models.SlugField(max_length=60, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("bio", models.CharField(blank=True, max_length=280)),
                ("website", models.URLField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Note",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("slug", models.SlugField(max_length=200, unique=True)),
                ("summary", models.CharField(max_length=300)),
                ("body", models.TextField(help_text="Markdown is supported. HTML is sanitized before display.")),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published")], db_index=True, default="draft", max_length=12)),
                ("cover_image", models.ImageField(blank=True, upload_to="covers/", validators=[knowledge.validators.validate_cover_image])),
                ("published_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="notes", to=settings.AUTH_USER_MODEL)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="notes", to="knowledge.category")),
                ("tags", models.ManyToManyField(blank=True, related_name="notes", to="knowledge.tag")),
            ],
            options={"ordering": ["-published_at", "-created_at"]},
        ),
        migrations.CreateModel(
            name="BlogPost",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("slug", models.SlugField(max_length=200, unique=True)),
                ("summary", models.CharField(max_length=300)),
                ("body", models.TextField(help_text="Markdown is supported. HTML is sanitized before display.")),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published")], db_index=True, default="draft", max_length=12)),
                ("cover_image", models.ImageField(blank=True, upload_to="covers/", validators=[knowledge.validators.validate_cover_image])),
                ("published_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="blogposts", to=settings.AUTH_USER_MODEL)),
                ("category", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="blog_posts", to="knowledge.category")),
                ("tags", models.ManyToManyField(blank=True, related_name="blogposts", to="knowledge.tag")),
            ],
            options={"ordering": ["-published_at", "-created_at"]},
        ),
        migrations.CreateModel(
            name="SavedContent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("blog_post", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="saved_by", to="knowledge.blogpost")),
                ("note", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="saved_by", to="knowledge.note")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_content", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
                "constraints": [
                    models.CheckConstraint(condition=models.Q(models.Q(("blog_post__isnull", True), ("note__isnull", False)), models.Q(("blog_post__isnull", False), ("note__isnull", True)), _connector="OR"), name="saved_content_exactly_one_target"),
                    models.UniqueConstraint(condition=models.Q(("note__isnull", False)), fields=("user", "note"), name="unique_user_saved_note"),
                    models.UniqueConstraint(condition=models.Q(("blog_post__isnull", False)), fields=("user", "blog_post"), name="unique_user_saved_post"),
                ],
            },
        ),
        migrations.CreateModel(
            name="UploadedAsset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="attachments/%Y/%m/", validators=[knowledge.validators.validate_attachment])),
                ("original_name", models.CharField(blank=True, max_length=255)),
                ("content_type", models.CharField(blank=True, max_length=120)),
                ("file_size", models.PositiveBigIntegerField(default=0)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("blog_post", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="assets", to="knowledge.blogpost")),
                ("note", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="assets", to="knowledge.note")),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="uploaded_assets", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["uploaded_at"],
                "constraints": [models.CheckConstraint(condition=models.Q(models.Q(("blog_post__isnull", True), ("note__isnull", False)), models.Q(("blog_post__isnull", False), ("note__isnull", True)), _connector="OR"), name="uploaded_asset_exactly_one_target")],
            },
        ),
        migrations.CreateModel(
            name="ContactMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("email", models.EmailField(max_length=254)),
                ("subject", models.CharField(max_length=160)),
                ("message", models.TextField(max_length=4000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("is_read", models.BooleanField(default=False)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="RateLimitBucket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=32)),
                ("key_hash", models.CharField(max_length=64)),
                ("window", models.PositiveBigIntegerField()),
                ("hits", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "constraints": [models.UniqueConstraint(fields=("action", "key_hash", "window"), name="unique_rate_limit_bucket")],
                "indexes": [models.Index(fields=["window"], name="knowledge_rate_window")],
            },
        ),
    ]
