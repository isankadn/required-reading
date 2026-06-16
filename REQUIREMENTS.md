# Required Reading Page Requirements

## Overview

Develop a Required Reading page inside the LMS. The page is available only to authenticated users after login. It provides important PDF documents and records each user's confirmation that they have read each document.

The organisation name supplied in the original requirement is only contextual and is intentionally not used in the application name, code, templates, URLs, or database model names.

## User Experience

Authenticated users see:

- Introductory text managed by staff.
- A list of downloadable PDF documents.
- A confirmation checkbox beside each document.
- A save action that persists confirmation state across future visits.
- A clear completion summary showing acknowledged and pending documents.

Users can:

- Download/open each PDF document.
- Tick or untick the confirmation checkbox for each document.
- Save their current confirmation status.

## Administration

Authorised administrators/staff can:

- Upload new PDF documents.
- Upload multiple documents at once.
- Use drag-and-drop upload.
- See upload progress, speed, and completion/failure status.
- Edit document titles.
- Delete existing documents.
- Update the introductory text shown on the Required Reading page.

Newly uploaded active documents automatically appear in the user-facing list.

## Tracking and Record Keeping

The system records each user's acknowledgement against each document.

This enables reporting on:

- Which users have confirmed reading a document.
- Which documents are not yet acknowledged by a specific user.
- When each acknowledgement was last saved.

Acknowledgement records remain associated with the individual Django/Open edX user account.

## Access and Permissions

Mandatory requirements:

- Required Reading page: authenticated users only.
- Management/upload/edit/delete functions: staff or superuser only.
- Anonymous users must not access documents through app views.
- Non-staff users must not access upload, edit, delete, or settings endpoints.
- Users can only save acknowledgement records for their own account.

## Upload Requirements

- PDF files only.
- Multiple upload support.
- Drag-and-drop support.
- Upload progress indicator.
- Upload speed indicator.
- Per-file completion/error status.
- Server-side PDF validation; UI validation alone is not sufficient.

## Implementation Notes

- Django app package: `required_reading`.
- Default URL: `/required-reading/`.
- Staff management URL: `/required-reading/manage/`.
- Templates extend Open edX `main_django.html` for LMS integration.
- Static files are packaged with the app.
- Uploaded files are stored through Django's configured media storage.
- The app is independently installable and removable.
