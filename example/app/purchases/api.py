from .models import Purchase
from EasyAPI import ModelAPI
from example.app.api import publicapi, privateapi


class PublicPurchaseAPI(ModelAPI):
    api_fields = ('items', 'sale_price')


class PrivatePurchaseAPI(ModelAPI):
    api_fields = ('items', 'sale_price', 'sale_date', 'profit', 'customer')
    create = True
    update = True


publicapi.register(Purchase, PublicPurchaseAPI)
privateapi.register(Purchase, PrivatePurchaseAPI)
