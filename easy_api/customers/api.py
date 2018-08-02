from .models import Customer
from EasyAPI.models import ModelAPI, publicapi, privateapi


class PublicCustomerAPI(ModelAPI):
    model = Customer
    api_fields = ('name', 'age')
    crud = ['r']

class PrivateCustomerAPI(ModelAPI):
    model = Customer
    api_fields = ('name', 'state', 'gender', 'age')
    permissions = 'Check Logged In' # just a placeholder value etc

publicapi.register(Customer, PublicCustomerAPI)
privateapi.register(Customer, PrivateCustomerAPI)
