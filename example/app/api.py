from EasyAPI import EasyAPI
from rest_framework import permissions

publicapi = EasyAPI('Public API',
                    permissions.AllowAny,
                    'This is a public API'
                    )
privateapi = EasyAPI('Private API',
                     permissions.IsAuthenticated,
                     'API for logged in users'
                     )

complexapi = EasyAPI('Admin API',
                     permissions.IsAdminUser,
                     'API for testing a admin permissions structure'
                     )
