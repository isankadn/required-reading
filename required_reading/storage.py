import os
from uuid import uuid4


def required_reading_upload_path(instance, filename):
    """Return a safe, app-scoped upload path for PDF documents."""
    _, ext = os.path.splitext(filename or "")
    return "required_reading/pdfs/{uuid}{ext}".format(
        uuid=uuid4().hex,
        ext=(ext or ".pdf").lower(),
    )
