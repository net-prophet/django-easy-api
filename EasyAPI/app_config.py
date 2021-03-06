from django.apps import AppConfig
from django.core import checks


class EasyAPIConfig(AppConfig):
    default_api = "EasyAPI.models"
    name = "EasyAPI"
    verbose_name = "API"

    def ready(self):
        from EasyAPI.api import EasyAPI, check_dependencies

        checks.register(check_dependencies, checks.Tags.models)
        self.module.autodiscover()
        super().ready()
