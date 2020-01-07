from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend

from EasyAPI.metadata import EasyAPIMetadata
from EasyAPI.EasySerializer import classproperty

