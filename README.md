# Required Reading

Standalone Django app for Open edX LMS that provides authenticated users with required PDF documents and records per-user acknowledgements.

## Features

- Authenticated-only Required Reading page.
- Staff-only document management page.
- Multiple PDF upload with drag-and-drop, progress, upload speed, and completion status.
- Per-user acknowledgement tracking for each document.
- Introductory page text managed by staff.
- Django admin integration.
- Self-contained templates, CSS, JavaScript, migrations, and tests.

## Install

Development install:

```bash
pip install -e src/required-reading/
```

Production image install:

```bash
pip install /openedx/custom/required-reading/
```

Add to LMS installed apps:

```python
ADDL_INSTALLED_APPS = ['required_reading']
```

Include URLs in the LMS root URL configuration:

```python
path('', include('required_reading.urls'))
```

Run migrations:

```bash
./manage.py lms migrate required_reading
```

## Remove

1. Remove `required_reading` from installed apps.
2. Remove the URL include.
3. Uninstall the package.
4. Keep the database tables for audit history, or explicitly drop them only after confirming retention requirements.

## Security

- Anonymous users are redirected to login.
- Management views require staff/superuser access.
- Acknowledgement updates are always tied to `request.user`.
- Uploads accept PDF files only and enforce configurable size limits.
- CSRF protection is required for all POST operations.
