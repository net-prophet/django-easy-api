from .models import Customer
from EasyAPI.models import ModelAPI, publicapi, privateapi, complexapi


class PublicCustomerAPI(ModelAPI):
    api_fields = ('name', 'age')


class PrivateCustomerAPI(ModelAPI):
    api_fields = ('name', 'state', 'gender', 'age')
    create = True


class ComplexCustomerAPI(ModelAPI):
    from rest_framework import permissions
    api_fields = ('name', 'state', 'gender', 'age')
    actions = {'create': permissions.IsAdminUser,
               'edit': permissions.IsAuthenticated,
               'retrieve': permissions.AllowAny,
               'list': permissions.IsAuthenticated,
               'delete': permissions.IsAdminUser,
               }


publicapi.register(Customer, PublicCustomerAPI)
privateapi.register(Customer, PrivateCustomerAPI)
complexapi.register(Customer, ComplexCustomerAPI)
