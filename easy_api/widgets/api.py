from EasyAPI.api import publicapi, privateapi
from .models import Widget
from EasyAPI.models import ModelAPI


class PublicWidgetAPI(ModelAPI):
    model = Widget
    api_fields = ('name', 'color', 'size', 'shape', 'cost')
    crud = ['r']

class PrivateWidgetAPI(ModelAPI):
    model = Widget
    api_fields = ('name', 'color')
    permissions = 'Check Logged In' # just a placeholder value etc

publicapi.register(Widget, PublicWidgetAPI)
privateapi.register(Widget, PrivateWidgetAPI)
