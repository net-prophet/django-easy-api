from EasyAPI.models import ModelAPI, publicapi, privateapi
from .models import Widget


class PublicWidgetAPI(ModelAPI):
    api_fields = ('name', 'color')
    read_only = True


class PrivateWidgetAPI(ModelAPI):
    api_fields = ('name', 'color', 'size', 'shape', 'cost')


publicapi.register(Widget, PublicWidgetAPI)
privateapi.register(Widget, PrivateWidgetAPI)
