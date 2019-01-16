from django.contrib import admin
from django.conf.urls import url
from .api import publicapi, privateapi, complexapi
from graphene_django.views import GraphQLView


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^publicapi/', publicapi.urls),
    url(r'^privateapi/', privateapi.urls),
    url(r'^complexapi/', complexapi.urls),
]
