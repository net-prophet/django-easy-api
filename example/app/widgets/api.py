from .models import Widget, Purchase, Customer
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

publicapi.register(Purchase, fields=['items', 'sale_price'])
privateapi.register(Purchase, fields=['items', 'sale_price', 'sale_date', 'profit', 'customer'], inlines=['items'])
complexapi.register(Purchase, inlines=['items'])

publicapi.register(Customer, fields=['name', 'age'])
privateapi.register(Customer, fields=['name', 'state', 'gender', 'age'])
complexapi.register(Customer)
