from rest_framework import viewsets, status, exceptions
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from rest_framework.decorators import action

from django_filters.rest_framework import DjangoFilterBackend

from EasyAPI.metadata import EasyAPIMetadata
from EasyAPI.serializers import classproperty

import django.db.models

def create_mutation_view(resource, mutation, options):
    detail = options.get('detail', False)
    read_only = options.get('read_only', False)
    
    wrapper = action(detail=detail,
            name=mutation,
            methods=options.get('rest_methods', read_only and ['GET',] or ['POST',]),
            url_path=options.get('rest_url_path', mutation),
            url_name=options.get('rest_url_name', mutation.replace('_', '-'))
    )
    def mutation_view(view_self, request, **kwargs):
        target = detail and view_self.get_object() or model
        method = getattr(target, mutation)
        return Response({
                    'result': resource.api.serialize(
                        method(**request.data, **kwargs)).data
                })
    mutation_view.__name__ = mutation
    return wrapper(mutation_view)

class EasyViewSet(viewsets.ModelViewSet):
    metadata_class = EasyAPIMetadata
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    permissions = None

    @classmethod
    def Assemble(cls, resource, **kwargs):
        model = resource.model
        filterset_class = kwargs.pop("filterset_class", resource.filterset_class)
        actions = kwargs.pop("actions", {})
        extra_views = {}

        for mutation, options in resource.mutations.items():
            extra_views[mutation] = create_mutation_view(resource, mutation, options)
        
        klass = type(
            "%sViewSet" % model._meta.object_name,
            (cls,),
            {
                "model": model,
                "resource": resource,
                "filterset_class": filterset_class,
                "actions": actions,
                **kwargs,
                **extra_views
            },
        )
        


        return klass
        

    @classmethod
    def get_view_name(self):
        return self.model._meta.app_label

    def get_serializer_class(self):
        return self.resource.serializer_class

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
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        data = self.view_update_data(self, request)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
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
            raise serializers.ValidationError(getattr(e, "message", str(e)))

    def perform_update(self, serializer):
        from django.core.exceptions import ValidationError
        from rest_framework import serializers

        try:
            return self.view_perform_update(self, serializer)
        except (ValidationError) as e:
            raise serializers.ValidationError(getattr(e, "message", str(e)))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        as_csv = request.GET.get("format") == "csv"
        all_rows = request.GET.get("all_rows") == "true"

        page = self.paginate_queryset(queryset)

        if not all_rows and page is not None:
            serializer = self.get_serializer(page, many=True)
            resp = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            resp = Response(serializer.data)

        if as_csv:
            fn = request.GET.get("filename", self.model.plural + ".csv")
            dispo = 'attachment; filename="%s"' % fn
            resp["Content-Disposition"] = dispo
            resp["Content-Type"] = "text/csv; charset=utf-8"
        resp["Count"] = queryset.count()
        return resp

    def check_permissions(self, request):
        parent_permitted = super(EasyViewSet, self).check_permissions(request)
        user = self.request.user.is_authenticated and self.request.user or None
        permission, audit = self.resource.get_action_permission(self.action, user=user)

        if permission:
            return parent_permitted
        else:
            raise exceptions.MethodNotAllowed(self.action)


    def get_queryset(self):
        user = self.request.user.is_authenticated and self.request.user or None
        qs, audit = self.resource.get_permitted_queryset(self.action, user=user)

        return qs

    def get_permissions(self):
        permission_classes = self.permissions + []

        return [permission() for permission in permission_classes]
