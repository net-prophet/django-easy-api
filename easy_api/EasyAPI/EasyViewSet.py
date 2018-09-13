import django_filters
from django.db import models

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend

from EasyAPI.metadata import EasyAPIMetadata
from EasyAPI.EasySerializer import EasySerializable, classproperty


class EasyViewSet(viewsets.ModelViewSet):
    metadata_class = EasyAPIMetadata
    filter_backends = (DjangoFilterBackend, OrderingFilter)

    @classmethod
    def kwargs(cls, **kwargs):
        class Kwargs(cls):
            fields = kwargs['fields']
            model = kwargs['model']
            actions = kwargs['actions']
            description = kwargs['description']
        return Kwargs

    @classmethod
    def get_view_name(self):
        return self.model._meta.app_label

    def get_serializer_class(self):
        e = EasySerializable.get_base_serializer_class()
        e.Meta.fields = self.fields
        e.Meta.model = self.model
        return e

    def get_queryset(self):
        return self.model.objects.all()

    @classproperty
    def filters(cls):
        return cls.get_filter_class().get_filters()

    @property
    def filterset_class(cls):
        return cls.get_filter_class()

    @classmethod
    def get_filter_class(cls):
        class GenericFilter(django_filters.FilterSet):

            def num_filter(self, name, lookup):
                return django_filters.NumberFilter(
                    field_name=name,
                    lookup_expr=lookup
                )

            def char_filter(self, name, lookup):
                return django_filters.CharFilter(
                    field_name=name,
                    lookup_expr=lookup
                )

            def date_filter(self, name, lookup):
                return django_filters.DateFilter(
                    name=name,
                    lookup_expr=lookup
                )

            def __init__(self, *args, **kwargs):
                super(GenericFilter, self).__init__(*args, **kwargs)
                for f in cls.model._meta.get_fields():
                    if f.name not in cls.fields:
                        continue
                    if isinstance(f, (models.CharField, models.TextField)):
                        contains = f.name + '_contains'
                        self.filters[contains] = self.char_filter(f.name,
                                                                  'icontains'
                                                                  )

                    if isinstance(f,
                                  (models.FloatField,
                                   models.IntegerField,
                                   models.DecimalField
                                   )
                                  ):
                        lt = f.name + '_less_than'
                        self.filters[lt] = self.num_filter(f.name, 'lt')
                        gt = f.name + '_greater_than'
                        self.filters[gt] = self.num_filter(f.name, 'gt')

            class Meta:
                model = cls.model
                fields = list(cls.fields)

        return GenericFilter

    @classmethod
    def view_save_data(cls, view, request):
        return {k: v for k, v in request.data.items()}

    @classmethod
    def view_perform_save(cls, view, serializer):
        return serializer.save()

    @classmethod
    def view_create_data(cls, view, request):
        return cls.view_save_data(view, request)

    @classmethod
    def view_perform_create(cls, view, serializer):
        return cls.view_perform_save(view, serializer)

    @classmethod
    def view_update_data(cls, view, request):
        return cls.view_save_data(view, request)

    @classmethod
    def view_perform_update(cls, view, serializer):
        return cls.view_perform_save(view, serializer)

    def create(self, request, *args, **kwargs):
        data = self.view_create_data(self, request)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        data = self.view_update_data(self, request)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied
            # to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    # from rest_framework.permissions import IsAdminUser
    @action(methods=['delete'], detail=False)
    def delete(self, request, *args, **kwargs):
        qs = self.model.objects.filter(**request.query_params.dict())
        if qs.count() > 1:
            msg = 'Bulk delete is not implemented for this API.'
            return Response(data=msg, status=status.HTTP_403_FORBIDDEN)
        if qs.count() < 1:
            return Response(status=status.HTTP_404_NOT_FOUND)
        obj = qs.get()
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        from django.core.exceptions import ValidationError
        from rest_framework import serializers
        try:
            return self.view_perform_create(self, serializer)
        except (ValidationError) as e:
            raise serializers.ValidationError(getattr(e,
                                                      'message',
                                                      str(e))
                                              )

    def perform_update(self, serializer):
        from django.core.exceptions import ValidationError
        from rest_framework import serializers
        try:
            return self.view_perform_update(self, serializer)
        except (ValidationError) as e:
            raise serializers.ValidationError(getattr(e,
                                                      'message',
                                                      str(e))
                                              )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        as_csv = request.GET.get('format') == 'csv'
        all_rows = request.GET.get('all_rows') == 'true'

        page = self.paginate_queryset(queryset)

        if not all_rows and page is not None:
            serializer = self.get_serializer(page, many=True)
            resp = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            resp = Response(serializer.data)

        if(as_csv):
            fn = request.GET.get('filename', self.model.plural+'.csv')
            dispo = 'attachment; filename="%s"' % fn
            resp['Content-Disposition'] = dispo
            resp['Content-Type'] = 'text/csv; charset=utf-8'
        resp['Count'] = queryset.count()
        return resp

    def get_permissions(self):
        permission_classes = []

        try:
            permission_classes = [self.actions[self.action]]
        except KeyError as e:
            print(e)

        return [permission() for permission in permission_classes]
