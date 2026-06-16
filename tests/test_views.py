import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from required_reading.models import RequiredReadingAcknowledgement, RequiredReadingDocument

pytestmark = pytest.mark.django_db


def make_pdf(name="document.pdf"):
    return SimpleUploadedFile(name, b"%PDF-1.4\n%test pdf", content_type="application/pdf")


def create_user(username="learner", **kwargs):
    return get_user_model().objects.create_user(username=username, password="test", **kwargs)


def test_anonymous_user_redirected_from_document_list(client):
    response = client.get(reverse("required_reading:document_list"))
    assert response.status_code == 302
    assert "/login" in response["Location"]


def test_authenticated_user_can_view_document_list(client):
    user = create_user()
    client.force_login(user)
    response = client.get(reverse("required_reading:document_list"))
    assert response.status_code == 200


def test_regular_user_cannot_access_management(client):
    user = create_user()
    client.force_login(user)
    response = client.get(reverse("required_reading:manage_documents"))
    assert response.status_code == 403


def test_staff_user_can_access_management(client):
    user = create_user(username="staff", is_staff=True)
    client.force_login(user)
    response = client.get(reverse("required_reading:manage_documents"))
    assert response.status_code == 200


def test_user_can_save_own_acknowledgement(client):
    user = create_user()
    document = RequiredReadingDocument.objects.create(title="Policy", pdf_file=make_pdf())
    client.force_login(user)
    response = client.post(
        reverse("required_reading:save_acknowledgements"),
        {"acknowledged_documents": [str(document.id)]},
    )
    assert response.status_code == 302
    acknowledgement = RequiredReadingAcknowledgement.objects.get(user=user, document=document)
    assert acknowledgement.acknowledged is True
    assert acknowledgement.acknowledged_at is not None


def test_staff_can_upload_pdf(client):
    user = create_user(username="staff", is_staff=True)
    client.force_login(user)
    response = client.post(
        reverse("required_reading:upload_documents"),
        {"files": [make_pdf("policy.pdf")]},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    assert RequiredReadingDocument.objects.filter(title="Policy").exists()


def test_staff_upload_rejects_non_pdf(client):
    user = create_user(username="staff", is_staff=True)
    client.force_login(user)
    response = client.post(
        reverse("required_reading:upload_documents"),
        {"files": [SimpleUploadedFile("bad.txt", b"no", content_type="text/plain")]},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 400
    assert RequiredReadingDocument.objects.count() == 0
