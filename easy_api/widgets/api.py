from EasyAPI.models import ModelAPI, publicapi, privateapi
from .models import Widget


class PublicWidgetAPI(ModelAPI):
    model = Widget
    api_fields = ('name', 'color')
    crud = ['r']


class PrivateWidgetAPI(ModelAPI):
    model = Widget
    api_fields = ('name', 'color', 'size', 'shape', 'cost')


publicapi.register(Widget, PublicWidgetAPI)
privateapi.register(Widget, PrivateWidgetAPI)
