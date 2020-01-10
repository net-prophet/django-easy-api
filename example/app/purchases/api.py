from .models import Purchase
from EasyAPI.resource import ModelResource
from example.app.api import publicapi, privateapi


class PublicPurchaseAPI(ModelResource):
    api_fields = ('items', 'sale_price')


class PrivatePurchaseAPI(ModelResource):
    api_fields = ('items', 'sale_price', 'sale_date', 'profit', 'customer')

publicapi.register(Purchase, fields=['items', 'sale_price'])
privateapi.register(Purchase, fields=['items', 'sale_price', 'sale_date', 'profit', 'customer'])
