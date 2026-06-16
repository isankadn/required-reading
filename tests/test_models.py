import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from required_reading.models import (
    RequiredReadingAcknowledgement,
    RequiredReadingDocument,
    RequiredReadingSettings,
    validate_pdf_file,
)

pytestmark = pytest.mark.django_db


def make_pdf(name="document.pdf"):
    return SimpleUploadedFile(name, b"%PDF-1.4\n%test pdf", content_type="application/pdf")


def test_settings_is_singleton():
    first = RequiredReadingSettings.get_solo()
    second = RequiredReadingSettings.get_solo()
    assert first.pk == 1
    assert second.pk == 1
    assert RequiredReadingSettings.objects.count() == 1


def test_pdf_validator_accepts_real_pdf_header():
    validate_pdf_file(make_pdf())


def test_pdf_validator_rejects_non_pdf_extension():
    with pytest.raises(ValidationError):
        validate_pdf_file(SimpleUploadedFile("bad.txt", b"%PDF-1.4", content_type="text/plain"))


def test_pdf_validator_rejects_invalid_header():
    with pytest.raises(ValidationError):
        validate_pdf_file(SimpleUploadedFile("bad.pdf", b"not a pdf", content_type="application/pdf"))


def test_acknowledgement_unique_per_user_and_document():
    user = get_user_model().objects.create_user(username="learner", password="test")
    document = RequiredReadingDocument.objects.create(title="Policy", pdf_file=make_pdf())
    RequiredReadingAcknowledgement.objects.create(user=user, document=document, acknowledged=True)
    assert RequiredReadingAcknowledgement.objects.count() == 1
