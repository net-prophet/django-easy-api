__all__ = ['autodiscover']


def autodiscover():
    from django.utils.module_loading import autodiscover_modules
    autodiscover_modules('api')


default_app_config = 'EasyAPI.apps.EasyAPIConfig'
