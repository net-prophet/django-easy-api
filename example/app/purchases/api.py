from .models import Purchase
from EasyAPI.api import ModelResource
from example.app.api import publicapi, privateapi


class PublicPurchaseAPI(ModelResource):
    api_fields = ('items', 'sale_price')
    class Meta:
        model = Purchase


class PrivatePurchaseAPI(ModelResource):
    api_fields = ('items', 'sale_price', 'sale_date', 'profit', 'customer')
    class Meta:
        model = Purchase


publicapi.register(Purchase, PublicPurchaseAPI)
privateapi.register(Purchase, PrivatePurchaseAPI)
