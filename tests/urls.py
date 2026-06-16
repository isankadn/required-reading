from django.urls import include, path
from django.http import HttpResponse


def login_view(request):
    return HttpResponse("login")


urlpatterns = [
    path("", include("required_reading.urls")),
    path("login", login_view, name="login"),
]
