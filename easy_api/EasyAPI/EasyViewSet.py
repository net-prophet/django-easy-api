from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend
from graphql import GraphQLError


from EasyAPI.metadata import EasyAPIMetadata
from EasyAPI.EasySerializer import classproperty


class EasyViewSet(viewsets.ModelViewSet):
    metadata_class = EasyAPIMetadata
    filter_backends = (DjangoFilterBackend, OrderingFilter)

    @classmethod
    def factory(cls, **kwargs):
        class EasyViewSetInstance(EasyViewSet):
            pass

        for attr, value in kwargs.items():
            setattr(EasyViewSetInstance, attr, value)

        return EasyViewSetInstance

    @classmethod
    def get_view_name(self):
        return self.model._meta.app_label

    @classmethod
    def get_serializer_class(cls):
        from EasyAPI.EasySerializer import EasySerializable
        return EasySerializable.get_base_serializer_class(cls.model,
                                                          cls.fields)

    @classmethod
    def get_graphql_query(cls):
        import types
        from graphene import relay, ObjectType
        from graphene_django.types import DjangoObjectType
        from graphene_django.filter import DjangoFilterConnectionField
        from graphene_django.rest_framework.mutation import SerializerMutation

        model_name = cls.model._meta.model_name
        plural = cls.model._meta.verbose_name_plural

        class EasyGraphQLNodeMeta:
            model = cls.model
            name = model_name
            interfaces = (relay.Node, )
            only_fields = cls.fields

        class EasyGraphQLUpsertMutationMeta:
            serializer_class = cls.get_serializer_class()


        def get_node(node_cls, info, id):
            qs = cls.get_queryset_for_user(info.context.user)
            if not cls.actions['retrieve']().has_permission(info.context, info):
                qs = qs.none()

            try:
                return qs.get(id=id)
            except cls.model.DoesNotExist:
                return None

        def upsert_get_serializer_kwargs(mutation_cls, root, info, **input):
            qs = cls.get_queryset_for_user(info.context.user)

            if 'pk' in input:
                action = 'edit'
            else:
                action = 'create'

            # Do permissions checking on edit and create
            if not cls.actions[action]().has_permission(info.context, info):
                raise GraphQLError("You don't have permission to %s this %s"
                                   %(action, model_name))

            if action == 'edit':
                instance = qs.filter(id=input['pk']).first()
                del input['pk']
                if instance:
                    return {'instance': instance, 'data': input, 'partial': True}

                else:
                    raise http.Http404


            return {'data': input, 'partial': True}


        node = type('%s_graphql_node'%model_name,
                    (DjangoObjectType, ), {
                        'Meta': EasyGraphQLNodeMeta,
                        'get_node': classmethod(get_node)
                    })

        upsert = type('%s_graphql_upsert'%model_name,
                      (SerializerMutation, ), {
                          'Meta': EasyGraphQLUpsertMutationMeta,
                          'get_serializer_kwargs': classmethod(upsert_get_serializer_kwargs)
                      })

        class EasyGraphQLQuery(ObjectType):
            def resolve_all(self, info):
                qs = cls.get_queryset_for_user(info.context.user)
                if not cls.actions['list']().has_permission(info.context, info):
                    qs = qs.none()
                return qs

        class EasyGraphQLMutation(ObjectType):
            pass


        setattr(EasyGraphQLQuery, model_name,
                relay.Node.Field(node))

        setattr(EasyGraphQLQuery, 'all_%s'%plural,
                DjangoFilterConnectionField(node,
                        filterset_class=cls.get_filter_class()))

        setattr(EasyGraphQLQuery, 'resolve_all_%s'%plural,
                EasyGraphQLQuery.resolve_all)

        setattr(EasyGraphQLMutation, 'upsert_%s'%model_name,
                upsert.Field())

        return EasyGraphQLQuery, EasyGraphQLMutation


    @classmethod
    def get_queryset_for_user(cls, user):
        if hasattr(cls.model_api, 'get_queryset_for_user'):
            return cls.model_api().get_queryset_for_user(cls, user)
        return cls.model.objects.all()

    @classmethod
    def get_queryset_for_class(cls):
        if cls.model_api and hasattr(cls.model_api, 'get_queryset'):
            return cls.model_api().get_queryset(cls)
        return cls.model.objects.all()

    def get_queryset(self):
        return self.get_queryset_for_class()

    @classproperty
    def filters(cls):
        return cls.get_filter_class().get_filters()

    @property
    def filterset_class(cls):
        return cls.get_filter_class()

    @classmethod
    def get_filter_class(cls):
        from EasyAPI.EasyFilters import EasyFilters
        return EasyFilters.get_filter_class(cls.model, [f for f in cls.fields if
                                                        f != 'pk'])

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

    def get_permissions(self):
        permission_classes = []

        try:
            permission_classes = [self.actions[self.action]]
        except KeyError as e:
            print(e)

        return [permission() for permission in permission_classes]
