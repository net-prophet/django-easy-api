from .models import Purchase, PurchaseItem
from EasyAPI.resource import ModelResource
from example.app.api import publicapi, privateapi, complexapi

publicapi.register(Purchase, fields=['items', 'sale_price'])
privateapi.register(Purchase, fields=['items', 'sale_price', 'sale_date', 'profit', 'customer'], inlines=['items'])
complexapi.register(Purchase, inlines=['items'])

