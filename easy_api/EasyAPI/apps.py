from django.apps import AppConfig
from django.core import checks
from django.utils.module_loading import autodiscover_modules


class EasyAPIConfig(AppConfig):
    default_api = 'EasyAPI.api.DefaultAPI'
    name = 'EasyAPI'
    verbose_name = 'API'

    def ready(self):
        print('huillo', dir(self), '\n')
        print('huillo', dir(self.default_api), '\n')
        # print('modules', dir(self.module), '\n')
        # print('modules api', dir(self.module.api), '\n')
        #print('modules default', dir(self.module.DefaultAPI), '\n')
        # print('modules easy', dir(self.module.EasyAPI), '\n')
        # print('modules apps', dir(self.module.apps), '\n')
        from EasyAPI.api import EasyAPI, api
        #checks.register(EasyAPI.check_api_app(self), checks.Tags.models)
        super().ready()
        # autodiscover_modules('EasyAPI')
