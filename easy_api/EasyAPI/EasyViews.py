import json
import inflect
from django.db import models
from rest_framework import status
from collections import OrderedDict
from django.http import HttpResponse
from django.shortcuts import redirect
from rest_framework.response import Response
from .EasySerializer import EasySerializable, classproperty

p = inflect.engine()


class EasyUIMixin(EasySerializable):
    @classmethod
    def get_serializer_class(cls):
        from rest_framework import serializers

        class EasyUISerializer(EasySerializable.get_serializer_class()):
            dataviews = serializers.SerializerMethodField(read_only=True)

            def get_dataviews(self, obj):
                request = self.context.get('request', None)
                views = self.context.get(
                    'views',
                    getattr(request, 'GET', {}).get('views')
                )
                if not views:
                    return {}

                rendered_views = {}
                config = obj.get_dataviews_config()
                for v in views.split(','):
                    rendered_views[v] = {}
                    if v in config:
                        rendered_views[v] = obj.get_dataview(v, request)
                if 'views' in views:
                    rendered_views['views'] = config
                if 'actions' in views:
                    rendered_views['actions'] = obj.get_actions_config()
                return rendered_views

            class Meta:
                model = cls

        return EasyUISerializer

    @classmethod
    def ui_info(cls):
        return {
            "label": cls.label,
            "title": cls.title,
            "plural": cls.plural,
            "icon": getattr(cls, '__fa_icon__', 'edit'),
            "api_path":
            callable(cls.api_path) and cls.api_path() or cls.api_path,
            "ui_path": cls.ui_path,
            "full_label": cls.full_label,
            'list_style': getattr(cls, '__list_style__', None),
            "relations": cls.relations,
        }

    @classproperty
    def ui_path(cls):
        from django.core.urlresolvers import reverse
        return reverse('ui-%s-list' % cls.label)

    @classproperty
    def api_path(cls):
        from django.core.urlresolvers import reverse
        return reverse('%s-list' % cls.label)

    @classproperty
    def title(cls):
        return cls.verbose_name.capitalize()

    @classproperty
    def plural(cls):
        return getattr(cls, '__plural__', p.plural(cls.title))

    @classmethod
    def crud_permissions(cls, request):
        if request.user.is_authenticated:
            return ['create', 'edit', 'details', 'list', 'delete']

    # Views related stuff
    @classmethod
    def get_model_views(cls):
        from rest_framework.decorators import list_route, detail_route
        from rest_framework import viewsets, filters

        class ModelViews(viewsets.ModelViewSet):
            model = cls
            permission_classes = cls.get_permissions_classes()
            serializer_class = cls.get_serializer_class()
            queryset = cls.get_default_views_queryset()
            filter_backends = (filters.DjangoFilterBackend,
                               filters.OrderingFilter)
            filter_class = cls.get_filter_class()
            ordering_fields = [] and cls.get_ordering_fields()

            def get_queryset(self):
                req = self.request
                qs = cls.get_views_queryset(self)
                for f, info in cls.filters.items():
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
                    if field in cls.get_ordering_fields():
                        field_obj = cls._meta.get_field(field)
                        order_param = field
                        if isinstance(field_obj, models.CharField):
                            order_param = Lower(field)
                        qs = qs.order_by(order_param)
                        if ordering.startswith('-'):
                            qs = qs.reverse()
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
                    raise serializers.ValidationError(getattr(e, 'message',
                                                              str(e)))

            def perform_update(self, serializer):
                from django.core.exceptions import ValidationError
                from rest_framework import serializers
                try:
                    return self.model.view_perform_update(self, serializer)
                except (ValidationError) as e:
                    raise serializers.ValidationError(getattr(e, 'message',
                                                              str(e)))

            @detail_route()
            def edit_form(self, request, *args, **kwargs):
                obj = self.get_object()
                return obj.get_bound_form(request).render_response(
                    request,
                    style='react'
                )

            @list_route()
            def create_form(self, request, *args, **kwargs):
                return cls.get_form(request).render_response(
                    request,
                    style='react'
                )

            @detail_route()
            def run_action(self, request, *args, **kwargs):
                obj = self.get_queryset().g404(**kwargs)
                result = obj.run_action(request.GET.get('action', ''),
                                        request.GET.get('value', ''),
                                        request)
                if not isinstance(result, dict):
                    result = {'success': bool(result), 'result': result}
                if result.get('updated', False) and 'object' not in result:
                    result['object'] = obj.serialize().data
                    if not result.get('class', ''):
                        succ = result['success'] and 'success' or 'warning'
                        result['class'] = succ
                return Response(result)
                if result.get('redirect', ''):
                    return redirect(result['redirect'])
                return redirect(obj)

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

            @list_route()
            def metrics(self, request, *args, **kwargs):
                def get_split(s):
                    return [t.strip() for t in
                            request.GET.get(s, '').split(',')
                            if t.strip()]

                pks = get_split('pks')
                totals = get_split('totals')
                charts = get_split('charts')
                period = request.GET.get('period', None) or 'year'
                if not pks or (not totals and not charts):
                    return Response({'success': False, 'result': {}})

                queryset = self.filter_queryset(
                    self.get_queryset()
                ).f(pk__in=pks)
                pks = [result[0] for result in queryset.values_list('pk')]

                totals = totals and self.model.multi_totals(
                    self.model.report_model,
                    pks,
                    totals,
                    period
                )
                charts = charts and self.model.multi_charts(
                    self.model.report_model,
                    pks,
                    charts,
                    period
                )

                return HttpResponse(json.dumps({
                    'success': True,
                    'pks': pks,
                    'totals': totals,
                    'period': period,
                    'charts': charts,
                }))

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

        ModelViews.__name__ = cls.__name__
        return ModelViews

    def view_details_link(self):
        try:
            return self.ui_path + "/" + self.id
        except:  # noqa: E722
            return None

    @classmethod
    def view_create_data(cls, view, request):
        return view.model.view_save_data(view, request)

    @classmethod
    def view_update_data(cls, view, request):
        return view.model.view_save_data(view, request)

    @classmethod
    def view_save_data(cls, view, request):
        return {k: v for k, v in request.data.items()}

    @classmethod
    def view_perform_save(cls, view, serializer):
        return serializer.save()

    @classmethod
    def view_perform_create(cls, view, serializer):
        return view.model.view_perform_save(view, serializer)

    @classmethod
    def view_perform_update(cls, view, serializer):
        return view.model.view_perform_save(view, serializer)

    @classmethod
    def get_default_views_queryset(cls):
        return cls.objects.a()

    # Rest Permissions
    @classmethod
    def get_permissions_classes(cls):
        from rest_framework import permissions
        return [permissions.IsAuthenticated]

    # Basic Filtering
    @classmethod
    def get_filter_class(cls):
        from easy.filters import EasyFilter

        class EasyAutoFilter(EasyFilter):

            class Meta:
                model = cls
                fields = cls.get_filter_fields()
        return EasyAutoFilter

    @classmethod
    def get_filter_fields(cls):
        filters = {}
        for f in cls._meta.get_fields():
            if isinstance(f, (models.CharField, models.TextField)):
                filters[f.name] = ['icontains', 'exact']
            if isinstance(f, (models.ForeignKey)):
                filters[f.name] = ['exact']
        return filters

    @classmethod
    def get_ordering_fields(cls):
        return (cls.__get_inheritable_property__('ordering_fields', list()) or
                cls.get_filter_fields().keys())

    # UI-side filters
    @classproperty
    def filters(cls):
        return cls.__get_inheritable_property__('filters', OrderedDict())

    @classmethod
    def register_filter(cls, name, conf, override=False):
        if name in cls.filters and not override:
            name = '%s_%s' % (cls.class_name().lower(), name)
        if callable(conf):
            conf = {'options': conf}
        if 'name' not in conf:
            conf['name'] = name
        if 'style' not in conf:
            conf['style'] = 'dropdown'
        if 'title' not in conf:
            conf['title'] = name.capitalize()
        cls.__filters__[name] = conf
        return cls

    # UI - Datagrid Columns
    @classmethod
    def datagrid_column_defaults(cls):
        return cls.__get_inheritable_property__(
            '__datagrid_column_defaults__',
            []
        )

    @classproperty
    def datagrid_column_config(cls):
        return cls.__get_inheritable_property__(
            'datagrid_columns',
            OrderedDict()
        )

    @classmethod
    def field_groups(cls):
        return cls.__get_inheritable_property__(
            '__field_groups__',
            OrderedDict()
        )

    @classmethod
    def field_group_info(cls, request=None, view=None):
        import copy
        groups = copy.deepcopy(cls.field_groups())

        undefined = {}
        for f in cls.get_serializer_fields():
            if f not in groups:
                undefined[f] = True

        for group_name, group in groups.items():
            # Support shorthand where all we do is define list
            if isinstance(group, list):
                group = {'fields': group}
            if 'title' not in group:
                group['title'] = group_name.replace('_', ' ').capitalize()

        return groups

    @classmethod
    def table_header_info(cls):
        return

    @classmethod
    def datagrid_columns(cls, request, view):
        ordering_fields = cls.get_ordering_fields()
        columns = cls.datagrid_column_config
        # groups = cls.field_group_info(request, view)
        header_info = cls.table_header_info()
        if callable(columns):
            columns = columns(request, view)

        for f in cls.get_serializer_fields():
            if f not in columns:
                columns[f] = True
        request_cols = {}

        for key, col in columns.items():
            if callable(col):
                col = col(request, view)
            if isinstance(col, bool):
                if not col:
                    columns.pop(key, None)
                    return cls
                col = {}
            if 'key' not in col:
                col['key'] = key
            try:
                field = cls._meta.get_field(col['key'])
            except:  # noqa: E722
                field = None
            if 'name' not in col:
                if 'title' in col:
                    col['name'] = col['title']
                else:
                    col['name'] = getattr(field, 'verbose_name',
                                          key).replace('_', ' ').capitalize()
            if field:
                col['field'] = key
                if key in ordering_fields:
                    col['sort'] = key

            if 'type' not in col:
                if(isinstance(field, models.DateTimeField)):
                    col['type'] = 'datetime'

            if header_info:
                if key in header_info:
                    col['name'] = header_info[key]['title']
                    col['tooltip'] = header_info[key]['tooltip']

            # For someday later: add a reverse lookup of which group
            # field is in.
            # I'm not sure the function for this in new abstract style
            # if not 'group' in col:
            # for g_name, group in groups.items():
            # if key in group.get('fields',[]): col['group'] = g_name
            request_cols[key] = col
        return request_cols

    @classmethod
    def register_datagrid_column(cls, field, cfg=True):
        columns = cls.datagrid_column_config
        if isinstance(cfg, bool):
            if not cfg:
                columns.pop(field, None)
                return cls
        columns[field] = cfg
        return cls

    # Parent/Child relationships
    @classproperty
    def relations(cls):
        return cls.__get_inheritable_property__('relations')

    @classproperty
    def ui_parent(cls):
        return cls.relations.get('ui_parent', {})

    # Actions and Info Views
    @classproperty
    def actions(cls):
        return cls.__get_inheritable_property__('actions')

    @classproperty
    def dataviews(cls):
        return cls.__get_inheritable_property__('dataviews')

    def get_running_actions(self, action=None):
        from easy.jobs.models import Job
        qs = Job.a().for_object(self).running()
        if action:
            qs = qs.f(method='run_%s' % action)
        return qs

    def get_running_action(self, action):
        running = self.get_running_actions(action).first()
        return running and running.serialized() or False

    def get_actions_config(self):
        def action_config(a, c):
            cfg = {'title': c['title'],
                   'style': c.get('style', 'button'),
                   'class': c.get('class', 'info'),
                   'enabled': 'enabled' in c and c['enabled'](self) or True,
                   }
            if 'config' in c:
                cfg['config'] = c['config'](self) or {}
            if c.get('icon'):
                cfg['icon'] = c['icon']
            if c.get('async'):
                cfg['async'] = c['async']
            if c.get('async'):
                cfg['running'] = self.get_running_action(a)
            return cfg
        return {a: action_config(a, c) for a, c in self.actions.items()}

    def get_dataviews_config(self):
        views = {}
        for v, c in self.dataviews.items():
            views[v] = {'title': c['title']}
            if 'config' in c:
                if callable(c['config']):
                    views[v]['config'] = c['config'](self)
                else:
                    views[v]['config'] = c['config']
        return views

    def run_action(self, action, value=None, request=None):
        from easy.notifications.models import Notification
        from easy.jobs.models import Job
        result = None
        cfg = self.get_actions_config()
        if action not in cfg:
            return None
        info = cfg[action]
        for n in ['run_%s', ]:
            if callable(getattr(self, n % action, None)):
                if info.get('async', False):
                    from easy.jobs.tasks import run_job
                    task, result = run_job(self, n % action, value=value)
                else:
                    result = getattr(self, n % action)(value, request)
                break

        title = '%s on %s %s' % (info['title'], self.verbose_name, self.title)
        v_msg = value and ': %s' % value or ''

        if isinstance(result, Job):
            n_msg = 'Started job %s%s' % (title, v_msg)
            Notification.deliver(self.user, n_msg.title(), 'running')
            return {'running': result.serialized()}

        if not result or isinstance(result, bool):
            result = {'success': bool(result)}

        success = result['success']
        n_error = (not success and '[FAILED] ') or ''
        n_msg = '%s%s%s' % (n_error, title, v_msg)
        n_icon = ''
        if not success:
            n_icon = 'exclamation'
        else:
            if info['style'] == 'dropdown' and 'config' in info:
                n_icon = info['config']['options'][value].get('icon', '')
            n_icon = n_icon or info.get('icon', '') or 'check'

        if(action == 'archive' or action == 'unarchive'):
            return result

        if not (self.verbose_name == 'notification'):
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = None
            if isinstance(getattr(self, 'user'), User):
                user = self.user
            if isinstance(self, User):
                user = self.leader or self
            if user:
                Notification.deliver(user, n_msg.title(), n_icon)
        return result

    def get_dataview(self, view, request=None):
        result = None
        if view not in self.get_dataviews_config():
            return None
        for n in ['dataview_%s', ]:
            if callable(getattr(self, n % view, None)):
                result = getattr(self, n % view)(request)
                break
        if isinstance(result, bool):
            return {'success': result}
        return result

    def get_dataviews(self, views, request=None):
        return {v: self.get_dataview(v, request) for v in views}

    def dataview_actions(self, request):
        return self.get_actions_config()

    @classmethod
    def register_action(cls, name, conf):
        if name in cls.actions:
            name = '%s_%s' % (cls.class_name().lower(), name)
        if callable(conf):
            conf = {'options': conf}
        if 'name' not in conf:
            conf['name'] = name
        if 'title' not in conf:
            conf['title'] = name.capitalize()
        cls.__actions__[name] = conf
        return cls

    @classmethod
    def register_dataview(cls, name, conf=None):
        conf = conf or {}
        if name in cls.dataviews:
            name = '%s_%s' % (cls.class_name().lower(), name)
        if callable(conf):
            conf = {'func': conf}
        if 'name' not in conf:
            conf['name'] = name
        if 'title' not in conf:
            conf['title'] = name.capitalize()
        cls.__dataviews__[name] = conf
        return cls

    # Child/Parent registrations

    @classmethod
    def register_child(cls, child_name):
        rel = cls._meta.get_field(child_name)
        return rel.related_model.register_parent(rel.remote_field.name)

    @classmethod
    def register_parent(
        cls,
        field_name,
        field=None,
        parent_class=None,
        filter_name=None
    ):
        if not parent_class:
            field = field or cls._meta.get_field(field_name)
            parent_class = field.related_model

        filter_name = filter_name or field.related_query_name()

        cls.relations['parent'] = {
            'field': field_name,
            'model': parent_class.full_label,
            'children_attr': filter_name,
        }

        if 'children' not in parent_class.relations:
            parent_class.relations['children'] = OrderedDict()
        parent_class.relations['children'][filter_name] = {
            'related_query_attr': filter_name,
            'model': cls.full_label,
            'parent_attr': field_name,
        }

        return cls.relations['parent']

    # Reporting Iotas and Restrictions

    @classproperty
    def iotas(cls):
        return cls.__get_inheritable_property__('iotas')

    @classmethod
    def register_iota(cls, iota, pk_binding=None):
        table = iota.__tablename__
        if not pk_binding:
            if not hasattr(iota, '%s_id' % cls.label):
                raise Exception(
                    'Unable to register iota %s on model %s'
                    '(pk_binding not present)' % (iota, cls)
                )
        cls.iotas[table] = pk_binding
