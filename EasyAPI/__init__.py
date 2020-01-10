from .api import EasyAPI, check_dependencies, AlreadyRegistered, all_apis
from .resource import ModelResource

__all__ = ['autodiscover']


def autodiscover():
    from django.utils.module_loading import autodiscover_modules
    autodiscover_modules('api')

default_app_config = 'EasyAPI.app_config.EasyAPIConfig'