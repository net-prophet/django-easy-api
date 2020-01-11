import django_filters
from django.db import models

def map_filter_fields(resource, fields):
    filter_fields = {}
    filters = {}
    for name in fields:
        f = resource.model_fields[name]
        if isinstance(f, (models.CharField, models.TextField)):
            filter_fields[name] = ['exact', 'icontains', 'istartswith', 'iendswith']
            contains = name + '_contains'
            filters[contains] = django_filters.CharFilter(
                    field_name=name,
                    lookup_expr=contains
            )

        if isinstance(f,
                        (models.FloatField,
                        models.IntegerField,
                        models.DecimalField
                        )
                        ):
            filter_fields[name] = ['exact', 'gt', 'lt', 'gte', 'lte']
            lt = name + '_less_than'
            filters[lt] = django_filters.NumberFilter(
                    field_name=name,
                    lookup_expr=lt
            )
            gt = name + '_greater_than'
            filters[gt] = django_filters.NumberFilter(
                    field_name=name,
                    lookup_expr=gt
                )

        if isinstance(f, (models.DateField, models.DateTimeField)):
            filter_fields[name] = ['exact', 'gt', 'lt', 'gte', 'lte', 'range']
            lt = name + '_less_than'
            filters[lt] = django_filters.DateTimeFilter(
                    field_name=name,
                    lookup_expr=lt
                )

            gt = f.name + '_greater_than'
            filters[gt] = django_filters.DateTimeFilter(
                    field_name=name,
                    lookup_expr=gt
                )

            rng = name + '_range'
            filters[rng] = django_filters.DateRangeFilter(field_name=name)

    for relation in resource.inlines:
        model = resource.get_inline_model(relation)
        registered = resource.api._registry.get(model, None)
        if not registered: continue
        label = relation
        subfilterset = registered.get_filterset()
        for name, field in subfilterset.filters.items():
            filters["%s__%s"%(label, name)] = field
    
    for relation in resource.get_foreign_key_fields():
        fk = resource.model_fields[relation]
        registered = resource.api._registry.get(fk.related_model, None)
        if not registered: continue
        subfilterset = registered.get_filterset()
        for name, field in subfilterset.filters.items():
            filters["%s__%s"%(relation, name)] = field
    return filter_fields, filters


class EasyFilters(object):
    @classmethod
    def Assemble(cls, resource):
        the_fields = list(resource.model_fields.keys())
        class GenericBaseFilters(django_filters.FilterSet):
            filter_fields = {}
            local_filter_fields = {}
            def __init__(self, *args, **kwargs):
                super(GenericBaseFilters, self).__init__(*args, **kwargs)
                _fields, _filters = map_filter_fields(resource, the_fields)
                self.local_filter_fields = self.filter_fields = _fields
                self.filters.update(_filters)

            class Meta:
                model = resource.model
                fields = the_fields

        return GenericBaseFilters
