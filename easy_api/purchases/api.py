from EasyAPI.api import publicapi, privateapi
from .models import Purchase
from EasyAPI.models import ModelAPI


class PublicPurchaseAPI(ModelAPI):
    model = Purchase
    api_fields = ('items', 'sale_price')
    crud = ['r']

class PrivatePurchaseAPI(ModelAPI):
    model = Purchase
    api_fields = ('items', 'sale_price', 'sale_date', 'profit', 'customer')
    permissions = 'Check Logged In' # just a placeholder value etc

publicapi.register(Purchase, PublicPurchaseAPI)
privateapi.register(Purchase, PrivatePurchaseAPI)
