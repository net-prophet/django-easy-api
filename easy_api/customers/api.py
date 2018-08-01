from EasyAPI.api import publicapi, privateapi
from .models import Customer
from EasyAPI.models import ModelAPI


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
