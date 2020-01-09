from .models import Customer
from EasyAPI import ModelResource
from example.app.api import publicapi, privateapi, complexapi


class PublicCustomerAPI(ModelResource):
    api_fields = ('name', 'age')
    class Meta:
        model = Customer

class PrivateCustomerAPI(ModelResource):
    api_fields = ('name', 'state', 'gender', 'age')
    class Meta:
        model = Customer

class ComplexCustomerAPI(ModelResource):
    api_fields = ('name', 'state', 'gender', 'age')
    class Meta:
        model = Customer


publicapi.register(Customer, PublicCustomerAPI)
privateapi.register(Customer, PrivateCustomerAPI)
complexapi.register(Customer, ComplexCustomerAPI)
