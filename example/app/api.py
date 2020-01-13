from EasyAPI.api import EasyAPI
from rest_framework import permissions

publicapi = EasyAPI('PublicAPI',
                    permissions.AllowAny,
                    'This is a public API',
                    rest=True,
                    graphql=True,
                    )
privateapi = EasyAPI('PrivateAPI',
                     permissions.IsAuthenticated,
                     'API for logged in users',
                     permission_context='store_owner'
                     )

complexapi = EasyAPI('AdminAPI',
                     permissions.IsAdminUser,
                     'API for testing a admin permissions structure',
                     permission_context=lambda model: True,
                     admin=True
                     )
