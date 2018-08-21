from EasyAPI.models import ModelAPI, publicapi, privateapi
from .models import Purchase


class PublicPurchaseAPI(ModelAPI):
    api_fields = ('items', 'sale_price')


class PrivatePurchaseAPI(ModelAPI):
    api_fields = ('items', 'sale_price', 'sale_date', 'profit', 'customer')
    create = True
    update = True


publicapi.register(Purchase, PublicPurchaseAPI)
privateapi.register(Purchase, PrivatePurchaseAPI)
