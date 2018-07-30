from EasyAPI.api import api, EasyAPI
from .models import Widget


class WidgetAPI(EasyAPI):
    model = Widget

print('IKOJROIFWEJIOJF', dir(api))
api.register(WidgetAPI, Widget)
