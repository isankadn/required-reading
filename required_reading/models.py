import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .storage import required_reading_upload_path


DEFAULT_MAX_UPLOAD_SIZE = 25 * 1024 * 1024


def get_max_upload_size():
    return getattr(settings, "REQUIRED_READING_MAX_UPLOAD_SIZE", DEFAULT_MAX_UPLOAD_SIZE)


def validate_pdf_file(uploaded_file):
    name = getattr(uploaded_file, "name", "") or ""
    ext = os.path.splitext(name)[1].lower()
    if ext != ".pdf":
        raise ValidationError(_("Only PDF files are allowed."))

    content_type = getattr(uploaded_file, "content_type", "")
    if content_type and content_type not in {"application/pdf", "application/x-pdf"}:
        raise ValidationError(_("Uploaded file must be a PDF document."))

    size = getattr(uploaded_file, "size", 0) or 0
    max_size = get_max_upload_size()
    if size > max_size:
        raise ValidationError(_("PDF file is larger than the allowed size."))

    try:
        current_position = uploaded_file.tell()
    except (AttributeError, OSError):
        current_position = None

    try:
        uploaded_file.seek(0)
        header = uploaded_file.read(5)
        if header != b"%PDF-":
            raise ValidationError(_("Uploaded file does not appear to be a valid PDF."))
    finally:
        if current_position is not None:
            uploaded_file.seek(current_position)


class RequiredReadingSettings(models.Model):
    intro_text = models.TextField(
        blank=True,
        default="Please review the required documents below and confirm once you have read each one.",
        help_text=_("Introductory text displayed at the top of the Required Reading page."),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Required reading settings")
        verbose_name_plural = _("Required reading settings")

    def __str__(self):
        return _("Required reading settings")

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class RequiredReadingDocument(models.Model):
    title = models.CharField(max_length=255)
    pdf_file = models.FileField(
        upload_to=required_reading_upload_path,
        validators=[validate_pdf_file],
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="required_reading_uploads",
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "title", "id"]
        permissions = [
            ("manage_required_reading", _("Can manage required reading documents")),
        ]

    def __str__(self):
        return self.title

    @property
    def filename(self):
        return os.path.basename(self.pdf_file.name or "")


class RequiredReadingAcknowledgement(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="required_reading_acknowledgements",
    )
    document = models.ForeignKey(
        RequiredReadingDocument,
        on_delete=models.CASCADE,
        related_name="acknowledgements",
    )
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("user", "document"),)
        ordering = ["document__display_order", "document__title"]

    def __str__(self):
        status = _("acknowledged") if self.acknowledged else _("not acknowledged")
        return "{} - {} ({})".format(self.user, self.document, status)

    def save(self, *args, **kwargs):
        if self.acknowledged and self.acknowledged_at is None:
            self.acknowledged_at = timezone.now()
        if not self.acknowledged:
            self.acknowledged_at = None
        super().save(*args, **kwargs)


class RequiredReadingDocumentAccess(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="required_reading_document_accesses",
    )
    document = models.ForeignKey(
        RequiredReadingDocument,
        on_delete=models.CASCADE,
        related_name="accesses",
    )
    first_accessed_at = models.DateTimeField(auto_now_add=True)
    last_accessed_at = models.DateTimeField(auto_now=True)
    access_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (("user", "document"),)
        ordering = ["document__display_order", "document__title", "user__username"]
        verbose_name = _("Required reading document access")
        verbose_name_plural = _("Required reading document accesses")

    def __str__(self):
        return "{} - {} ({} opens)".format(self.user, self.document, self.access_count)

    def record_open(self):
        self.access_count = (self.access_count or 0) + 1
        self.save(update_fields=["access_count", "last_accessed_at"])
