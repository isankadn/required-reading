from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

try:
    from edx_django_utils.plugins import PluginURLs
    from openedx.core.djangoapps.plugins.constants import ProjectType
except ImportError:  # Allows standalone Django test/use outside Open edX.
    PluginURLs = None
    ProjectType = None


class RequiredReadingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "required_reading"
    verbose_name = _("Required Reading")

    if PluginURLs and ProjectType:
        plugin_app = {
            PluginURLs.CONFIG: {
                ProjectType.LMS: {
                    PluginURLs.NAMESPACE: "required_reading",
                    PluginURLs.REGEX: r"^",
                    PluginURLs.RELATIVE_PATH: "urls",
                }
            }
        }
