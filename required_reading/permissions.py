from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def is_required_reading_manager(user):
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


def staff_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("/login?next={}".format(request.get_full_path()))
        if not is_required_reading_manager(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped
