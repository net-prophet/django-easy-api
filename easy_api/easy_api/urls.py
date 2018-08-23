from django.contrib import admin
from django.conf.urls import url
from EasyAPI.models import publicapi, privateapi, complexapi


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^publicapi/', publicapi.urls),
    url(r'^privateapi/', privateapi.urls),
    url(r'^complexapi/', complexapi.urls),
]
