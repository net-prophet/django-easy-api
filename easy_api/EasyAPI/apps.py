from django.apps import AppConfig
from django.core import checks
from EasyAPI.api import EasyAPI


class EasyAPIConfig(AppConfig):
    default_api = 'EasyAPI.api'
    name = 'EasyAPI'
    verbose_name = 'API'

    def ready(self):
        checks.register(EasyAPI.check_api_app, checks.Tags.models)
        checks.register(EasyAPI.check_dependencies, checks.Tags.models)
        self.module.autodiscover()
        super().ready()
