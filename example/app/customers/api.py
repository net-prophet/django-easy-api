from .models import Customer
from EasyAPI import ModelResource
from example.app.api import publicapi, privateapi, complexapi

publicapi.register(Customer, fields=['name', 'age'])
privateapi.register(Customer, fields=['name', 'state', 'gender', 'age'])
complexapi.register(Customer)
