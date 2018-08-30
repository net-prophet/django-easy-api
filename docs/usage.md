---
id: usage
title: Usage
---

Example Django Model located at bottom of page.



## Instantiating an API

Create a new file named `api.py` in your projects root directory. Much like how
Django checks for any `admin.py` files on startup EasyAPI will also go through
each app folder and look for `api.py` files. You instantiate the EasyAPIs in the
root folder and register models to them in the app folders themselves.

```python
# <project root>.api.py 
from EasyAPI.models import EasyAPI
from rest_Framework import permissions

publicapi = EasyAPI('Public API',
                    permissions.AllowAny,
                    'This is a public API'
                    )

privateapi = EasyAPI('Private API',
                     permissions.IsAuthenticated,
                     )
```

## Registering the URLs

Once the API is instantiated you just need to import it and set the url as you
would for any other django view. This url will be the url of the API root. In
this example we register them in the project root `urls.py` file.

```python
# <project root>.urls.py 
from django.conf.urls import url
from <project root>.api import publicapi, privateapi

urlpatterns = [
    url(r'^publicapi/', publicapi.urls),
    url(r'^privateapi/', privateapi.urls),
]
```

## Registering a Model

So we have instantiated two EasyAPIs and now let's register some models to them.


Register the scope on `models.py`:
```python
from widgets.models import Widget
from EasyAPI.models import ModelAPI
from rest_framework import permissions
from <project root>.api import publicapi, privateapi


class PublicWidgetAPI(ModelAPI):
    api_fields = ('name', 'color')

class PrivateWidgetAPI(ModelAPI):
    api_fields = ('name', 'color', 'size', 'shape', 'cost')
    description = 'Authenticated users only.'
    permissions = {'delete': permissions.IsAdminUser}

publicapi.register(Widget, PublicWidgetAPI)
privateapi.register(Widget, PrivateWidgetAPI)
```

So the Public API now has widgets as a model but only the name and color fields
are accessable. We didn't pass it any permissions so they defaulted to the API
level permission `AllowAny`. 

For the Private API the API level permission is IsAuthenticated, so any
authenticated user has access to all of the widgets and all of the fields. We
did override the delete permission to be `IsAdminUser`. Authenticated users will
not be able to delete anything.
