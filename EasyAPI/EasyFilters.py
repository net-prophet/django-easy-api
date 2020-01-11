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

    subfilters, subfilter_fields = {}, {}

    for relation in resource.reverse_relations:
        model = resource.get_inline_model(relation)
        registered = resource.api._registry.get(model, None)
        if not registered: continue
        subfilterset = registered.filterset
        for name, _filter in subfilterset.local_filters.items():
            subfilters["%s__%s"%(relation, name)] = _filter
        for name, fields in subfilterset.local_filter_fields.items():
            subfilter_fields["%s__%s"%(relation, name)] = fields
            
    
    for relation in resource.relations:
        fk = resource.model_fields[relation]
        registered = resource.api._registry.get(fk.related_model, None)
        if not registered: continue
        subfilterset = registered.filterset
        for name, _filter in subfilterset.local_filters.items():
            subfilters["%s__%s"%(relation, name)] = _filter
        for name, fields in subfilterset.local_filter_fields.items():
            subfilter_fields["%s__%s"%(relation, name)] = fields
    return filter_fields, filters, subfilter_fields, subfilters


class EasyFilters(object):
    @classmethod
    def Assemble(cls, resource):
        the_fields = list(resource.model_fields.keys())
        class GenericBaseFilters(django_filters.FilterSet):
            filter_fields = {}
            local_filter_fields = {}
            sub_filter_fields = {}
            local_filters = {}
            sub_filters = {}
            def __init__(self, *args, **kwargs):
                super(GenericBaseFilters, self).__init__(*args, **kwargs)
                _fields, _filters, _subfields, _subfilters = map_filter_fields(resource, the_fields)
                self.local_filter_fields = _fields
                self.sub_filter_fields = _subfields
                self.filter_fields = dict(**_fields, **_subfields)
                self.local_filters = _filters
                self.sub_filters = _subfilters
                self.filters.update(_filters)

            class Meta:
                model = resource.model
                fields = the_fields

        return GenericBaseFilters
