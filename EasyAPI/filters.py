import django_filters
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.db.models.fields import reverse_related


def map_filter_fields(resource, fields):
    filter_fields = {}
    filters = {}
    for name in fields:
        if (
            name not in resource.model_fields
            or name in resource.relations
            or name in resource.reverse_relations
        ):
            continue
        f = resource.model_fields[name]
        if isinstance(f, GenericForeignKey):
            continue
        if isinstance(f, (models.CharField, models.TextField)):
            filter_fields[name] = ["exact", "icontains", "istartswith", "iendswith"]
            contains = name + "_icontains"
            filters[contains] = django_filters.CharFilter(
                field_name=name, lookup_expr=contains
            )

        if isinstance(f, (models.FloatField, models.IntegerField, models.DecimalField)):
            filter_fields[name] = ["exact", "gt", "lt", "gte", "lte"]
            lt = name + "_less_than"
            filters[lt] = django_filters.NumberFilter(field_name=name, lookup_expr=lt)
            gt = name + "_greater_than"
            filters[gt] = django_filters.NumberFilter(field_name=name, lookup_expr=gt)

        if isinstance(f, (models.DateField, models.DateTimeField)):
            filter_fields[name] = ["exact", "gt", "lt", "gte", "lte", "range"]
            lt = name + "_less_than"
            filters[lt] = django_filters.DateTimeFilter(field_name=name, lookup_expr=lt)

            gt = f.name + "_greater_than"
            filters[gt] = django_filters.DateTimeFilter(field_name=name, lookup_expr=gt)

            rng = name + "_range"
            filters[rng] = django_filters.DateRangeFilter(field_name=name)

    return filter_fields, filters


class EasyFilters(object):
    @classmethod
    def Assemble(cls, resource):
        the_fields = [f for f in resource.fields if f in resource.model_fields_simple]

        class GenericBaseFilters(django_filters.FilterSet):
            filter_fields = {}
            local_filter_fields = {}
            sub_filter_fields = {}
            local_filters = {}
            sub_filters = {}

            def __init__(self, *args, **kwargs):
                super(GenericBaseFilters, self).__init__(*args, **kwargs)
                _fields, _filters = map_filter_fields(resource, the_fields)
                self.resource = resource
                self.local_filter_fields = _fields
                self.filter_fields = dict(**_fields)
                self.local_filters = _filters
                self.filters.update(_filters)

            class Meta:
                model = resource.model
                fields = the_fields

            def add_subfilters(self):
                return
                for relation in self.resource.reverse_relations:
                    if relation not in self.resource.fields:
                        continue
                    model = self.resource.get_inline_model(relation)
                    registered = self.resource.api._registry.get(model, None)
                    if not registered:
                        continue
                    subfilterset = registered.filterset
                    for name, _filter in subfilterset.local_filters.items():
                        self.sub_filters["%s__%s" % (relation, name)] = _filter
                    for name, fields in subfilterset.local_filter_fields.items():
                        self.sub_filter_fields["%s__%s" % (relation, name)] = fields

                for relation in self.resource.relations:
                    if relation not in self.resource.fields:
                        continue
                    fk = self.resource.model_fields[relation]
                    registered = self.resource.api._registry.get(fk.related_model, None)
                    if not registered:
                        continue
                    subfilterset = registered.filterset
                    for name, _filter in subfilterset.local_filters.items():
                        self.sub_filters["%s__%s" % (relation, name)] = _filter
                    for name, fields in subfilterset.local_filter_fields.items():
                        self.sub_filter_fields["%s__%s" % (relation, name)] = fields

                self.filter_fields.update(self.sub_filter_fields)
                self.filters.update(self.sub_filters)

        return GenericBaseFilters
