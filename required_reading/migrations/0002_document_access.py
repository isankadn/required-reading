# Generated manually for required_reading analytics.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("required_reading", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RequiredReadingDocumentAccess",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("first_accessed_at", models.DateTimeField(auto_now_add=True)),
                ("last_accessed_at", models.DateTimeField(auto_now=True)),
                ("access_count", models.PositiveIntegerField(default=0)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="accesses", to="required_reading.requiredreadingdocument")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="required_reading_document_accesses", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Required reading document access",
                "verbose_name_plural": "Required reading document accesses",
                "ordering": ["document__display_order", "document__title", "user__username"],
                "unique_together": {("user", "document")},
            },
        ),
    ]
