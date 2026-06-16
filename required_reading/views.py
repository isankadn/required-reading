from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .forms import (
    RequiredReadingDocumentForm,
    RequiredReadingSettingsForm,
    RequiredReadingUploadForm,
    document_title_from_file,
)
from .models import (
    RequiredReadingAcknowledgement,
    RequiredReadingDocument,
    RequiredReadingSettings,
)
from .permissions import staff_required


@login_required
def document_list(request):
    settings_obj = RequiredReadingSettings.get_solo()
    documents = list(RequiredReadingDocument.objects.filter(is_active=True))
    acknowledgements = {
        acknowledgement.document_id: acknowledgement
        for acknowledgement in RequiredReadingAcknowledgement.objects.filter(
            user=request.user,
            document__in=documents,
        )
    }
    acknowledged_count = sum(
        1 for document in documents if acknowledgements.get(document.id) and acknowledgements[document.id].acknowledged
    )
    document_rows = [
        {
            "document": document,
            "acknowledgement": acknowledgements.get(document.id),
            "is_acknowledged": bool(acknowledgements.get(document.id) and acknowledgements[document.id].acknowledged),
        }
        for document in documents
    ]
    return render(
        request,
        "required_reading/document_list.html",
        {
            "settings_obj": settings_obj,
            "document_rows": document_rows,
            "document_count": len(documents),
            "acknowledged_count": acknowledged_count,
            "pending_count": max(len(documents) - acknowledged_count, 0),
        },
    )


@login_required
@require_POST
def save_acknowledgements(request):
    documents = list(RequiredReadingDocument.objects.filter(is_active=True))
    selected_ids = set()
    for value in request.POST.getlist("acknowledged_documents"):
        try:
            selected_ids.add(int(value))
        except (TypeError, ValueError):
            continue

    with transaction.atomic():
        for document in documents:
            acknowledgement, created = RequiredReadingAcknowledgement.objects.get_or_create(
                user=request.user,
                document=document,
            )
            acknowledgement.acknowledged = document.id in selected_ids
            acknowledgement.save()

    messages.success(request, _("Your required reading confirmations have been saved."))
    return redirect("required_reading:document_list")


@staff_required
def manage_documents(request):
    settings_obj = RequiredReadingSettings.get_solo()
    settings_form = RequiredReadingSettingsForm(instance=settings_obj)
    document_forms = [
        (document, RequiredReadingDocumentForm(instance=document))
        for document in RequiredReadingDocument.objects.all()
    ]
    return render(
        request,
        "required_reading/manage_documents.html",
        {
            "settings_form": settings_form,
            "document_forms": document_forms,
            "documents": RequiredReadingDocument.objects.all(),
        },
    )


@staff_required
@require_POST
def update_intro_text(request):
    settings_obj = RequiredReadingSettings.get_solo()
    form = RequiredReadingSettingsForm(request.POST, instance=settings_obj)
    if form.is_valid():
        form.save()
        messages.success(request, _("Introductory text updated."))
    else:
        messages.error(request, _("Please correct the introductory text."))
    return redirect("required_reading:manage_documents")


@staff_required
@require_POST
def upload_documents(request):
    form = RequiredReadingUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        messages.error(request, _("Upload failed. Only valid PDF files are allowed."))
        return redirect("required_reading:manage_documents")

    created = []
    for uploaded_file in form.cleaned_data["files"]:
        document = RequiredReadingDocument.objects.create(
            title=document_title_from_file(uploaded_file),
            pdf_file=uploaded_file,
            uploaded_by=request.user,
        )
        created.append({"id": document.id, "title": document.title, "url": document.pdf_file.url})

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "documents": created})

    messages.success(request, _("PDF document upload complete."))
    return redirect("required_reading:manage_documents")


@staff_required
@require_POST
def edit_document(request, pk):
    document = get_object_or_404(RequiredReadingDocument, pk=pk)
    form = RequiredReadingDocumentForm(request.POST, request.FILES or None, instance=document)
    if form.is_valid():
        form.save()
        messages.success(request, _("Document updated."))
    else:
        messages.error(request, _("Document update failed. Please check the title and PDF file."))
    return redirect("required_reading:manage_documents")


@staff_required
@require_POST
def delete_document(request, pk):
    document = get_object_or_404(RequiredReadingDocument, pk=pk)
    document.delete()
    messages.success(request, _("Document deleted."))
    return redirect("required_reading:manage_documents")


def permission_denied_view(request, exception=None):
    raise PermissionDenied
