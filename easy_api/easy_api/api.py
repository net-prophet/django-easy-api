from django.contrib.auth.models import User
from EasyAPI.models import EasyAPI, ModelAPI
from rest_framework import permissions

publicapi = EasyAPI('Public API',
                    permissions.AllowAny,
                    'This is a public API'
                    )
privateapi = EasyAPI('Private API',
                     permissions.IsAuthenticated,
                     )

complexapi = EasyAPI('Complex API',
                     permissions.AllowAny,
                     'API for testing a complicated permissions structure'
                     )


class PrivateUserAPI(ModelAPI):
    api_fields = ('username', 'email', 'first_name', 'last_name',
                  'is_superuser', 'last_login', 'date_joined')


privateapi.register(User, PrivateUserAPI)
