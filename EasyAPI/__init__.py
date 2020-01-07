from .api import EasyAPI, ModelAPI, check_dependencies, AlreadyRegistered, all_apis
__all__ = ['autodiscover', 'EasyAPI', 'ModelAPI', 'check_dependencies', 'AlreadyRegistered', 'all_apis']


def autodiscover():
    from django.utils.module_loading import autodiscover_modules
    autodiscover_modules('api')


default_app_config = 'EasyAPI.app_config.EasyAPIConfig'
