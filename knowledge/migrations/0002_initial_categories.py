from django.db import migrations


DEFAULT_CATEGORIES = [
    ("Python", "python", 1),
    ("SQL & Databases", "sql-databases", 2),
    ("Object-Oriented Programming", "object-oriented-programming", 3),
    ("Data Structures & Algorithms", "data-structures-algorithms", 4),
    ("Mathematics", "mathematics", 5),
    ("Data Science", "data-science", 6),
    ("Machine Learning & AI", "machine-learning-ai", 7),
    ("Projects & Exercises", "projects-exercises", 8),
]


def seed_categories(apps, schema_editor):
    Category = apps.get_model("knowledge", "Category")
    for name, slug, position in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "position": position},
        )


class Migration(migrations.Migration):
    dependencies = [("knowledge", "0001_initial")]
    operations = [migrations.RunPython(seed_categories, migrations.RunPython.noop)]
