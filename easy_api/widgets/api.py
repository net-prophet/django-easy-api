from .models import Widget
from EasyAPI.models import ModelAPI, publicapi, privateapi, complexapi


class PublicWidgetAPI(ModelAPI):
    api_fields = ('name', 'color')


class PrivateWidgetAPI(ModelAPI):
    api_fields = ('name', 'color', 'size', 'shape', 'cost')


class ComplexWidgetAPI(ModelAPI):
    from rest_framework import permissions
    api_fields = ('name', 'color', 'size', 'shape', 'cost')
    actions = {'create': permissions.IsAdminUser,
               'edit': permissions.IsAuthenticated,
               'retrieve': permissions.AllowAny,
               'list': permissions.IsAuthenticated,
               'delete': permissions.IsAdminUser,
               }


publicapi.register(Widget, PublicWidgetAPI)
privateapi.register(Widget, PrivateWidgetAPI)
complexapi.register(Widget, ComplexWidgetAPI)
