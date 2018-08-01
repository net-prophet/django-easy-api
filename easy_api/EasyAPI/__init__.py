__all__ = ['autodiscover']

from django.utils.module_loading import autodiscover_modules
from EasyAPI.api import EasyAPI
def autodiscover():
    autodiscover_modules('EasyAPI', register_to=EasyAPI)

default_app_config = 'EasyAPI.apps.EasyAPIConfig'
