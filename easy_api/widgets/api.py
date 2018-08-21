from .models import Widget
from EasyAPI.models import ModelAPI, publicapi, privateapi


class PublicWidgetAPI(ModelAPI):
    api_fields = ('name', 'color')


class PrivateWidgetAPI(ModelAPI):
    api_fields = ('name', 'color', 'size', 'shape', 'cost')


publicapi.register(Widget, PublicWidgetAPI)
privateapi.register(Widget, PrivateWidgetAPI)
