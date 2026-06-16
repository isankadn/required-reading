# Generated manually for the standalone required_reading app.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import required_reading.storage


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RequiredReadingSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("intro_text", models.TextField(blank=True, default="Please review the required documents below and confirm once you have read each one.", help_text="Introductory text displayed at the top of the Required Reading page.")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Required reading settings",
                "verbose_name_plural": "Required reading settings",
            },
        ),
        migrations.CreateModel(
            name="RequiredReadingDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("pdf_file", models.FileField(upload_to=required_reading.storage.required_reading_upload_path)),
                ("is_active", models.BooleanField(default=True)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="required_reading_uploads", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["display_order", "title", "id"],
                "permissions": [("manage_required_reading", "Can manage required reading documents")],
            },
        ),
        migrations.CreateModel(
            name="RequiredReadingAcknowledgement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("acknowledged", models.BooleanField(default=False)),
                ("acknowledged_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="acknowledgements", to="required_reading.requiredreadingdocument")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="required_reading_acknowledgements", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["document__display_order", "document__title"],
                "unique_together": {("user", "document")},
            },
        ),
    ]
