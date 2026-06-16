import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from required_reading.cache import clear_required_reading_cache, get_cached
from required_reading.models import RequiredReadingAcknowledgement, RequiredReadingDocument, RequiredReadingDocumentAccess

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clear_cache_between_tests():
    clear_required_reading_cache()
    yield
    clear_required_reading_cache()


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


def test_document_list_search_filters_pdf_titles(client):
    user = create_user()
    RequiredReadingDocument.objects.create(title="Safety Policy", pdf_file=make_pdf("safety.pdf"))
    RequiredReadingDocument.objects.create(title="Care Handbook", pdf_file=make_pdf("care.pdf"))
    client.force_login(user)
    response = client.get(reverse("required_reading:document_list"), {"q": "Safety"})
    assert response.status_code == 200
    assert b"Safety Policy" in response.content
    assert b"Care Handbook" not in response.content


def test_document_list_paginates_pdf_documents(client):
    user = create_user()
    for index in range(55):
        RequiredReadingDocument.objects.create(title="Policy {:02d}".format(index), pdf_file=make_pdf("policy-{}.pdf".format(index)))
    client.force_login(user)
    response = client.get(reverse("required_reading:document_list"))
    assert response.status_code == 200
    assert b"Policy 00" in response.content
    assert b"Policy 49" in response.content
    assert b"Policy 50" not in response.content
    assert b"Page 1 of 2" in response.content


def test_document_list_uses_project_cache_for_active_document_ids(client):
    user = create_user()
    document = RequiredReadingDocument.objects.create(title="Cached Policy", pdf_file=make_pdf("cached.pdf"))
    client.force_login(user)
    response = client.get(reverse("required_reading:document_list"))
    assert response.status_code == 200
    assert get_cached("active_document_ids") == [document.id]


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


def test_staff_user_sees_document_management_menu_on_document_page(client):
    user = create_user(username="staff", is_staff=True)
    client.force_login(user)
    response = client.get(reverse("required_reading:document_list"))
    assert response.status_code == 200
    assert b"Document management" in response.content
    assert b"rr-management-menu" in response.content


def test_regular_user_does_not_see_document_management_menu(client):
    user = create_user()
    client.force_login(user)
    response = client.get(reverse("required_reading:document_list"))
    assert response.status_code == 200
    assert b"Document management" not in response.content


def test_regular_user_cannot_access_analytics(client):
    user = create_user()
    client.force_login(user)
    response = client.get(reverse("required_reading:analytics"))
    assert response.status_code == 403


def test_staff_user_can_access_analytics(client):
    user = create_user(username="staff", is_staff=True)
    client.force_login(user)
    response = client.get(reverse("required_reading:analytics"))
    assert response.status_code == 200
    assert b"Required reading analytics" in response.content


def test_analytics_search_filters_users_and_documents(client):
    staff = create_user(username="staff", is_staff=True)
    create_user(username="alpha_user", email="alpha@example.com")
    create_user(username="beta_user", email="beta@example.com")
    RequiredReadingDocument.objects.create(title="Alpha PDF", pdf_file=make_pdf("alpha.pdf"))
    RequiredReadingDocument.objects.create(title="Beta PDF", pdf_file=make_pdf("beta.pdf"))
    client.force_login(staff)
    response = client.get(reverse("required_reading:analytics"), {"document_q": "Alpha", "user_q": "alpha"})
    assert response.status_code == 200
    assert b"Alpha PDF" in response.content
    assert b"Beta PDF" not in response.content
    assert b"alpha_user" in response.content
    assert b"beta_user" not in response.content


def test_analytics_paginates_users(client):
    staff = create_user(username="staff", is_staff=True)
    RequiredReadingDocument.objects.create(title="Policy", pdf_file=make_pdf("policy.pdf"))
    for index in range(55):
        create_user(username="learner_{:02d}".format(index), email="learner_{:02d}@example.com".format(index))
    client.force_login(staff)
    response = client.get(reverse("required_reading:analytics"))
    assert response.status_code == 200
    assert b"learner_00" in response.content
    assert b"learner_48" in response.content
    assert b"learner_49" in response.content
    assert b"learner_50" not in response.content
    assert b"User page 1 of 2" in response.content


def test_open_document_tracks_access_and_redirects_to_pdf(client):
    user = create_user()
    document = RequiredReadingDocument.objects.create(title="Policy", pdf_file=make_pdf())
    client.force_login(user)
    response = client.get(reverse("required_reading:open_document", args=[document.id]))
    assert response.status_code == 302
    assert response["Location"].endswith(document.pdf_file.url)
    access = RequiredReadingDocumentAccess.objects.get(user=user, document=document)
    assert access.access_count == 1

    client.get(reverse("required_reading:open_document", args=[document.id]))
    access.refresh_from_db()
    assert access.access_count == 2


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
