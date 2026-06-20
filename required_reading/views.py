import csv
import io

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .cache import get_cached, set_cached
from .forms import (
    RequiredReadingDocumentForm,
    RequiredReadingSettingsForm,
    RequiredReadingUploadForm,
    document_title_from_file,
)
from .models import (
    RequiredReadingAcknowledgement,
    RequiredReadingDocument,
    RequiredReadingDocumentAccess,
    RequiredReadingSettings,
)
from .permissions import is_required_reading_manager, staff_required

DOCUMENTS_PER_PAGE = 50
ANALYTICS_USERS_PER_PAGE = 50


def get_settings_cached():
    settings_obj = get_cached("settings")
    if settings_obj is None:
        settings_obj = RequiredReadingSettings.get_solo()
        set_cached("settings", settings_obj)
    return settings_obj


def get_active_document_ids_cached():
    document_ids = get_cached("active_document_ids")
    if document_ids is None:
        document_ids = list(
            RequiredReadingDocument.objects.filter(is_active=True)
            .order_by("display_order", "title", "id")
            .values_list("id", flat=True)
        )
        set_cached("active_document_ids", document_ids)
    return document_ids


def paginate_queryset(request, queryset, per_page, page_param="page"):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get(page_param))


def get_analytics_documents_queryset(document_search=""):
    queryset = RequiredReadingDocument.objects.all().annotate(
        opened_count=Count("accesses__user", filter=Q(accesses__access_count__gt=0), distinct=True),
        confirmed_count=Count(
            "acknowledgements__user",
            filter=Q(acknowledgements__acknowledged=True),
            distinct=True,
        ),
    ).order_by("display_order", "title", "id")
    if document_search:
        queryset = queryset.filter(title__icontains=document_search)
    return queryset


def get_analytics_users_queryset(user_search=""):
    User = get_user_model()
    users_queryset = User.objects.filter(is_active=True).order_by("username", "email")
    if user_search:
        users_queryset = users_queryset.filter(Q(username__icontains=user_search) | Q(email__icontains=user_search))
    return users_queryset


def build_analytics_user_rows(document, users):
    acknowledgements = {
        item.user_id: item
        for item in RequiredReadingAcknowledgement.objects.filter(document=document, user__in=users)
    }
    accesses = {
        item.user_id: item
        for item in RequiredReadingDocumentAccess.objects.filter(document=document, user__in=users)
    }
    user_rows = []
    for user in users:
        acknowledgement = acknowledgements.get(user.id)
        access = accesses.get(user.id)
        user_rows.append(
            {
                "user": user,
                "acknowledgement": acknowledgement,
                "access": access,
                "is_confirmed": bool(acknowledgement and acknowledgement.acknowledged),
                "has_opened": bool(access and access.access_count),
            }
        )
    return user_rows


def format_analytics_datetime(value):
    if not value:
        return ""
    return timezone.localtime(value).strftime("%b %d, %Y %H:%M")


def csv_response(filename_prefix, header, rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    timestamp = timezone.localtime(timezone.now()).strftime("%Y%m%d-%H%M%S")
    filename = "{}-{}.csv".format(filename_prefix, timestamp)
    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)
    return response


@login_required
def document_list(request):
    settings_obj = get_settings_cached()
    search_query = request.GET.get("q", "").strip()
    documents_queryset = RequiredReadingDocument.objects.filter(
        id__in=get_active_document_ids_cached(),
        is_active=True,
    ).order_by("display_order", "title", "id")
    if search_query:
        documents_queryset = documents_queryset.filter(title__icontains=search_query)

    document_page = paginate_queryset(request, documents_queryset, DOCUMENTS_PER_PAGE)
    documents = list(document_page.object_list)
    total_document_count = RequiredReadingDocument.objects.filter(id__in=get_active_document_ids_cached(), is_active=True).count()
    acknowledgements = {
        acknowledgement.document_id: acknowledgement
        for acknowledgement in RequiredReadingAcknowledgement.objects.filter(
            user=request.user,
            document__in=documents,
        )
    }
    acknowledged_count = RequiredReadingAcknowledgement.objects.filter(
        user=request.user,
        document_id__in=get_active_document_ids_cached(),
        acknowledged=True,
    ).count()
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
            "document_count": total_document_count,
            "filtered_document_count": document_page.paginator.count,
            "document_page": document_page,
            "search_query": search_query,
            "acknowledged_count": acknowledged_count,
            "pending_count": max(total_document_count - acknowledged_count, 0),
            "can_manage_required_reading": is_required_reading_manager(request.user),
            "required_reading_active_page": "documents",
        },
    )


@login_required
@require_POST
def save_acknowledgements(request):
    documents = list(RequiredReadingDocument.objects.filter(id__in=get_active_document_ids_cached(), is_active=True))
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


@login_required
def open_document(request, pk):
    document = get_object_or_404(RequiredReadingDocument, pk=pk, is_active=True)
    access, created = RequiredReadingDocumentAccess.objects.get_or_create(
        user=request.user,
        document=document,
    )
    access.record_open()
    return redirect(document.pdf_file.url)


@staff_required
def analytics(request):
    User = get_user_model()
    document_search = request.GET.get("document_q", "").strip()
    total_user_count = User.objects.filter(is_active=True).count()

    documents_queryset = get_analytics_documents_queryset(document_search)

    document_page = paginate_queryset(request, documents_queryset, DOCUMENTS_PER_PAGE)
    analytics_rows = [
        {
            "document": document,
            "opened_count": document.opened_count,
            "confirmed_count": document.confirmed_count,
            "pending_count": max(total_user_count - document.confirmed_count, 0),
        }
        for document in document_page.object_list
    ]

    return render(
        request,
        "required_reading/analytics.html",
        {
            "analytics_rows": analytics_rows,
            "user_count": total_user_count,
            "document_count": RequiredReadingDocument.objects.count(),
            "filtered_document_count": document_page.paginator.count,
            "document_page": document_page,
            "document_search": document_search,
            "can_manage_required_reading": True,
            "required_reading_active_page": "analytics",
        },
    )


@staff_required
def analytics_document(request, pk):
    User = get_user_model()
    document = get_object_or_404(RequiredReadingDocument, pk=pk)
    user_search = request.GET.get("user_q", "").strip()
    users_queryset = get_analytics_users_queryset(user_search)

    user_page = paginate_queryset(request, users_queryset, ANALYTICS_USERS_PER_PAGE, page_param="user_page")
    users = list(user_page.object_list)
    total_user_count = User.objects.filter(is_active=True).count()
    confirmed_count = RequiredReadingAcknowledgement.objects.filter(document=document, acknowledged=True).count()
    opened_count = RequiredReadingDocumentAccess.objects.filter(document=document, access_count__gt=0).count()
    user_rows = build_analytics_user_rows(document, users)

    return render(
        request,
        "required_reading/analytics_detail.html",
        {
            "document": document,
            "user_rows": user_rows,
            "user_count": total_user_count,
            "filtered_user_count": user_page.paginator.count,
            "user_page": user_page,
            "user_search": user_search,
            "opened_count": opened_count,
            "confirmed_count": confirmed_count,
            "pending_count": max(total_user_count - confirmed_count, 0),
            "can_manage_required_reading": True,
            "required_reading_active_page": "analytics",
        },
    )


@staff_required
def analytics_export_csv(request):
    User = get_user_model()
    document_search = request.GET.get("document_q", "").strip()
    total_user_count = User.objects.filter(is_active=True).count()
    documents = get_analytics_documents_queryset(document_search)
    rows = [
        [
            document.title,
            document.opened_count,
            document.confirmed_count,
            max(total_user_count - document.confirmed_count, 0),
        ]
        for document in documents
    ]
    header = [_("PDF name"), _("Opened"), _("Confirmed"), _("Pending")]
    return csv_response("required-reading-analytics", header, rows)


@staff_required
def analytics_document_export_csv(request, pk):
    document = get_object_or_404(RequiredReadingDocument, pk=pk)
    user_search = request.GET.get("user_q", "").strip()
    users = list(get_analytics_users_queryset(user_search))
    user_rows = build_analytics_user_rows(document, users)
    rows = []
    for user_row in user_rows:
        access = user_row["access"]
        acknowledgement = user_row["acknowledgement"]
        rows.append(
            [
                user_row["user"].username,
                user_row["user"].email or "",
                _("Yes") if user_row["has_opened"] else _("No"),
                access.access_count if access else 0,
                format_analytics_datetime(access.last_accessed_at if access else None),
                _("Yes") if user_row["is_confirmed"] else _("No"),
                format_analytics_datetime(
                    acknowledgement.acknowledged_at if acknowledgement and acknowledgement.acknowledged else None
                ),
            ]
        )
    header = [
        _("User"),
        _("Email"),
        _("Opened PDF"),
        _("Open count"),
        _("Last opened"),
        _("Confirmed"),
        _("Confirmed at"),
    ]
    title_slug = slugify(document.title) or "document"
    filename_prefix = "required-reading-analytics-{}".format(title_slug)
    return csv_response(filename_prefix, header, rows)


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
            "can_manage_required_reading": True,
            "required_reading_active_page": "manage",
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
