from django import forms
from django.utils.text import get_valid_filename
from django.utils.translation import gettext_lazy as _

from .models import RequiredReadingDocument, RequiredReadingSettings, validate_pdf_file


class RequiredReadingSettingsForm(forms.ModelForm):
    class Meta:
        model = RequiredReadingSettings
        fields = ["intro_text"]
        widgets = {
            "intro_text": forms.Textarea(attrs={"rows": 5, "class": "rr-textarea"}),
        }


class RequiredReadingDocumentForm(forms.ModelForm):
    class Meta:
        model = RequiredReadingDocument
        fields = ["title", "pdf_file", "is_active", "display_order"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "rr-input"}),
            "display_order": forms.NumberInput(attrs={"class": "rr-input", "min": 0}),
        }


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if isinstance(data, (list, tuple)):
            return [super(MultipleFileField, self).clean(item, initial) for item in data]
        return super().clean(data, initial)


class RequiredReadingUploadForm(forms.Form):
    files = MultipleFileField(widget=MultipleFileInput(attrs={"multiple": True}))

    def clean_files(self):
        files = self.files.getlist("files")
        if not files:
            raise forms.ValidationError(_("Select at least one PDF file."))
        for uploaded_file in files:
            validate_pdf_file(uploaded_file)
        return files


def document_title_from_file(uploaded_file):
    name = get_valid_filename(getattr(uploaded_file, "name", "document.pdf"))
    if name.lower().endswith(".pdf"):
        name = name[:-4]
    return name.replace("_", " ").replace("-", " ").strip().title() or _("Required Reading Document")
