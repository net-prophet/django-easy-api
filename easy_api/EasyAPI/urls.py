from django.conf.urls import url, include
from .api import EasyAPI


print('_++++++++++++++++++', EasyAPI._registry)
urlpatterns = [
    url(r'^public/', include(EasyAPI.api)),
]
