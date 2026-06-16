import pytest
from django.contrib.auth import get_user_model

from required_reading.permissions import is_required_reading_manager

pytestmark = pytest.mark.django_db


def test_staff_user_is_manager():
    user = get_user_model().objects.create_user(username="staff", is_staff=True)
    assert is_required_reading_manager(user) is True


def test_superuser_is_manager():
    user = get_user_model().objects.create_superuser(username="admin", email="admin@example.com", password="test")
    assert is_required_reading_manager(user) is True


def test_regular_user_is_not_manager():
    user = get_user_model().objects.create_user(username="learner")
    assert is_required_reading_manager(user) is False
