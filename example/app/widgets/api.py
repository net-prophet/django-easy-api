from .models import Widget
from EasyAPI.resource import ModelResource
from example.app.api import publicapi, privateapi, complexapi

# Stores: Read All, Write Owner
#  | Widgets: Read All, Write Store Owner
#    | Purchases: Read Store Owner
#  | Customers: Read Store Owner
#    | Purchases: Read Store Owner

publicapi.register(Widget, fields=['name', 'color'])
privateapi.register(Widget, fields=['name', 'color', 'size', 'shape', 'cost'])
complexapi.register(Widget)
