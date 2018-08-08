from django.contrib import admin
from django.conf.urls import url
from EasyAPI.models import publicapi, privateapi, debugapi, adminapi




urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^adminapi/', adminapi.urls),
    url(r'^publicapi/', publicapi.urls),
    url(r'^privateapi/', privateapi.urls),
    url(r'^debugapi/', debugapi.urls)
]


