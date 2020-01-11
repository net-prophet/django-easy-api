from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend

from EasyAPI.metadata import EasyAPIMetadata
from EasyAPI.EasySerializer import classproperty


class EasyViewSet(viewsets.ModelViewSet):
    metadata_class = EasyAPIMetadata
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    permissions = None

    @classmethod
    def Assemble(cls, **kwargs):
        class AssembledEasyViewSet(cls):
            fields = kwargs['fields']
            model = kwargs['model']
            resource = kwargs['resource']
            permissions = kwargs['permissions']
            description = kwargs['description']
            actions = kwargs.get('actions', {})
            filterset_class = kwargs['resource'].get_filterset_class()
        return AssembledEasyViewSet

    @classmethod
    def get_view_name(self):
        return self.model._meta.app_label

    def get_serializer_class(self):
        from EasyAPI.EasySerializer import EasySerializable
        return EasySerializable.get_base_serializer_class(self.resource)

    def get_queryset(self):
        return self.model.objects.all()

    @property
    def filters(self):
        return self.resource.get_filters()

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

    def check_permissions(self, request):
        permitted = super(EasyViewSet, self).check_permissions(request)
        return permitted

    def get_permissions(self):
        permission_classes = self.permissions + []
        

        return [permission() for permission in permission_classes]
