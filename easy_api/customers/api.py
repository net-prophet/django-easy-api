from .models import Customer
from EasyAPI.models import ModelAPI, publicapi, privateapi


class PublicCustomerAPI(ModelAPI):
    api_fields = ('name', 'age')


class PrivateCustomerAPI(ModelAPI):
    api_fields = ('name', 'state', 'gender', 'age')
    create = True


publicapi.register(Customer, PublicCustomerAPI)
privateapi.register(Customer, PrivateCustomerAPI)
