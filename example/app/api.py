from EasyAPI import EasyAPI
from rest_framework import permissions

publicapi = EasyAPI('PublicAPI',
                    permissions.AllowAny,
                    'This is a public API'
                    )
privateapi = EasyAPI('PrivateAPI',
                     permissions.IsAuthenticated,
                     'API for logged in users'
                     )

complexapi = EasyAPI('AdminAPI',
                     permissions.IsAdminUser,
                     'API for testing a admin permissions structure',
                     admin=True
                     )
