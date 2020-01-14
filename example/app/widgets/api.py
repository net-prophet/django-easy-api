from .models import Widget, Purchase, Customer, Store, User
from example.app.api import publicapi, privateapi, complexapi

# Stores: Read All, Write Owner
#  | Widgets: Read All, Write Store Owner
#    | Purchases: Read Store Owner
#  | Customers: Read Store Owner
#    | Purchases: Read Store Owner

publicapi.register(Widget, fields=['name', 'color', 'store'])
privateapi.register(Widget, fields=['name', 'color', 'size', 'shape', 'cost', 'store'], dump_info=True)
complexapi.register(Widget, list_display=['name', 'color', 'size', 'shape', 'cost', 'age'])

publicapi.register(Purchase, fields=['items', 'sale_price'])
privateapi.register(Purchase, fields=['items', 'sale_price', 'sale_date', 'profit', 'customer'], inlines=['items'])
complexapi.register(Purchase, inlines=['items'])

publicapi.register(Customer, fields=['name', 'age'])
privateapi.register(Customer, fields=['name', 'state', 'gender', 'age'])
complexapi.register(Customer)

publicapi.register(Store, fields=['name'], inlines=['widgets'])
privateapi.register(Store, inlines=['widgets'], dump_info=True)
complexapi.register(Store, inlines=['widgets'])

privateapi.register(User)
complexapi.register(User)