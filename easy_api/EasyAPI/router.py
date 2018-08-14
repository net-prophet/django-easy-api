from django.db import models
from collections import OrderedDict

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from rest_framework.routers import DefaultRouter, APIRootView
from rest_framework.decorators import list_route, detail_route

from django_filters.rest_framework import DjangoFilterBackend

from EasyAPI.EasySerializer import EasySerializable, classproperty
from EasyAPI.metadata import EasyAPIMetadata


class EasyViewSet(viewsets.ModelViewSet):
    metadata_class = EasyAPIMetadata
    # permission_classes = cls.get_permissions_classes()
    # serializer_class = cls.get_serializer_class()
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    # filter_class = cls.get_filter_class(target_model)

    @classmethod
    def get_ordering_fields(cls):
        return (cls.__get_inheritable_property__(
                    'ordering_fields',
                    list()
                    )
                )

    @classmethod
    def __get_inheritable_property__(cls, name, default=None):
        import inspect
        attr = '__%s__' % name
        parents = [b for b in inspect.getmro(cls)
                   if cls != b and hasattr(b, attr)]
        combined = default or {}
        if parents:
            for base in parents:
                value = getattr(base, attr)
                e = '%s used to be a %s, but you tried updating it with a %s'
                if not value:
                    continue
                elif isinstance(value, list):
                    if not combined:
                        combined = value
                    elif not isinstance(combined, list):
                        raise Exception(e % (attr,
                                             type(combined),
                                             type(value))
                                        )
                    else:
                        combined += value
                elif isinstance(combined, dict) and isinstance(value, dict):
                    combined.update(value)
                else:
                    raise Exception(e % (attr,
                                         type(combined),
                                         type(value))
                                    )
        if isinstance(combined, dict):
            combined.update(getattr(cls, attr, {}))
        setattr(cls, attr, combined)
        return combined

    @classproperty
    def filters(cls):
        return cls.__get_inheritable_property__('filters', OrderedDict())

    @property
    def permission_classes(cls):
        return cls.get_serializer_class()

    @classmethod
    def get_view_name(self):
        return self.model._meta.app_label

    @classmethod
    def kwargs(cls, **kwargs):
        class Kwargs(cls):
            fields = kwargs['fields']
            model = kwargs['model']
            description = kwargs['description']
            model_perm = kwargs['model_perm']
            permission_classes = kwargs['api_perm']
        return Kwargs

    @property
    def fields(cls):
        return cls.fields

    @classmethod
    def crud_permissions(cls, request):
        crud = []
        if request.user.is_authenticated:
            crud = ['create', 'edit', 'details', 'list', 'delete']
        return crud

    def get_serializer_class(self):
        e = EasySerializable.get_base_serializer_class()
        e.Meta.fields = self.fields
        e.Meta.model = self.model
        return e

    @classmethod
    def get_filter_fields(cls):
        filters = {}
        for f in cls.model._meta.get_fields():
            if f.name not in cls.fields:
                continue
            if isinstance(f, (models.CharField, models.TextField)):
                filters[f.name] = ['icontains', 'exact']
                if isinstance(f, (models.ForeignKey)):
                    filters[f.name] = ['exact']
                    return filters
        print('filters? ', filters)
        return filters

    def get_queryset(self):
        req = self.request
        qs = self.model.objects.all()
        for f, info in self.filters.items():
            if f not in req.GET:
                continue
            ordered = info['options'](req)
            options = {str(k): opts for k, opts in ordered}
            value = str(req.GET[f])
            if value in options:
                qs = options[value]['func'](qs)
        ordering = self.request.query_params.get('ordering', None)
        if ordering is not None:
            from django.db.models.functions import Lower
            field = ordering
            if ordering.startswith('-'):
                field = ordering[1:]
            if field in self.get_ordering_fields():
                field_obj = self.model._meta.get_field(field)
                order_param = field
                if isinstance(field_obj, models.CharField):
                    order_param = Lower(field)
                qs = qs.order_by(order_param)
                if ordering.startswith('-'):
                    qs = qs.reverse()
        print('\n\nnow returning: ', qs)
        return qs

    def create(self, request, *args, **kwargs):
        data = self.model.view_create_data(self, request)
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
        data = self.model.view_update_data(self, request)
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
            return self.model.view_perform_create(self, serializer)
        except (ValidationError) as e:
            raise serializers.ValidationError(getattr(e,
                                                      'message',
                                                      str(e))
                                              )

    def perform_update(self, serializer):
        from django.core.exceptions import ValidationError
        from rest_framework import serializers
        try:
            return self.model.view_perform_update(self, serializer)
        except (ValidationError) as e:
            raise serializers.ValidationError(getattr(e,
                                                      'message',
                                                      str(e))
                                              )

    @detail_route()
    def edit_form(self, request, *args, **kwargs):
        obj = self.get_object()
        return obj.get_bound_form(request).render_response(
            request,
            style='react'
        )

    @list_route()
    def create_form(self, request, *args, **kwargs):
        return self.get_form(request).render_response(
            request,
            style='react'
        )

    @detail_route()
    def dataview(self, request, *args, **kwargs):
        obj = self.get_queryset().g404(**kwargs)
        if 'views' in request.GET:
            views = request.GET['views'].split(',')
        if 'view' in request.GET:
            views = [request.GET['view'], ]

        result = obj.get_dataviews(views, request)

        if not isinstance(result, dict):
            result = {'success': bool(result), 'result': result}
        return Response(result)

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
        return resp


def easy_router(self):
    router = DefaultRouter()
    description = 'model_tem'

    class EasyAPIRootView(APIRootView):
        metadata_class = EasyAPIMetadata

        @classmethod
        def get_view_name(self):
            return self.name

        @classmethod
        def kwargs(cls, **kwargs):
            class Kwargs(cls):
                name = kwargs['name']
            return Kwargs

    router.APIRootView = EasyAPIRootView.kwargs(name=self.name)
    router.APIRootView.__doc__ = self.description
    for model, model_api in self._registry.items():
        name = model._meta.model_name
        label = model._meta.app_label
        crud_perm = model_api.crud_permissions,
        router.register(r'%s' % label,
                        EasyViewSet.kwargs(model=model,
                                           fields=model_api.api_fields,
                                           model_perm=crud_perm,
                                           description=description,
                                           api_perm=self.permissions,
                                           ),
                        '%s %s' % (name, label)
                        )

    urlpatterns = router.urls
    return urlpatterns
