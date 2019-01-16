from .models import Customer
from EasyAPI.models import ModelAPI
from easy_api.api import publicapi, privateapi, complexapi


class PublicCustomerAPI(ModelAPI):
    api_fields = ('name', 'age')


class PrivateCustomerAPI(ModelAPI):
    api_fields = ('name', 'state', 'gender', 'age')
    create = True


class ComplexCustomerAPI(ModelAPI):
    from rest_framework import permissions
    api_fields = ('name', 'state', 'gender', 'age')

    # ONLY basic permissions can be used that only look at request.user
    # because DRF complex permissions depend on a valid
    # View object to resolve (e.g. per object ID)
    # and we don't always have a View object (e.g. graphql)

    actions = {
        'create': permissions.IsAdminUser,
        'edit': permissions.IsAuthenticated,
        'retrieve': permissions.AllowAny,
        'list': permissions.IsAuthenticated,
        'delete': permissions.IsAdminUser,
    }


    # This is the preferred more complex way for imposing row-level restrictions
    @classmethod
    def get_queryset_for_user(self, viewset_class, user):

        if user.is_authenticated:
            return viewset_class.model.objects.all()

        return viewset_class.model.objects.filter(age__lte=30)


publicapi.register(Customer, PublicCustomerAPI)
privateapi.register(Customer, PrivateCustomerAPI)
complexapi.register(Customer, ComplexCustomerAPI)
