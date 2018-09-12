from EasyAPI.models import EasyAPI
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
