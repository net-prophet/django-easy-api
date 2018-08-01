from django.contrib import admin
from django.conf.urls import url
from EasyAPI.api import publicapi, privateapi, debugapi


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^publicapi/', publicapi.urls),
    url(r'^privateapi/', privateapi.urls),
    url(r'^debugapi/', debugapi.urls)
]
