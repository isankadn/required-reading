from django.urls import path

from . import views

app_name = "required_reading"

urlpatterns = [
    path("required-reading/", views.document_list, name="document_list"),
    path("required-reading/save/", views.save_acknowledgements, name="save_acknowledgements"),
    path("required-reading/document/<int:pk>/open/", views.open_document, name="open_document"),
    path("required-reading/manage/", views.manage_documents, name="manage_documents"),
    path("required-reading/manage/analytics/", views.analytics, name="analytics"),
    path("required-reading/manage/analytics/export.csv", views.analytics_export_csv, name="analytics_export_csv"),
    path("required-reading/manage/analytics/<int:pk>/", views.analytics_document, name="analytics_document"),
    path(
        "required-reading/manage/analytics/<int:pk>/export.csv",
        views.analytics_document_export_csv,
        name="analytics_document_export_csv",
    ),
    path("required-reading/manage/upload/", views.upload_documents, name="upload_documents"),
    path("required-reading/manage/intro/", views.update_intro_text, name="update_intro_text"),
    path("required-reading/manage/<int:pk>/edit/", views.edit_document, name="edit_document"),
    path("required-reading/manage/<int:pk>/delete/", views.delete_document, name="delete_document"),
]
