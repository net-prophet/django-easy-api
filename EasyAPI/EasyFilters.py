import django_filters
from django.db import models


class EasyFilters(object):

    @classmethod
    def get_filter_class(cls, the_model, the_fields):
        class GenericBaseFilters(django_filters.FilterSet):
            filter_fields = {}
            def __init__(self, *args, **kwargs):
                super(GenericBaseFilters, self).__init__(*args, **kwargs)
                for f in the_model._meta.get_fields():
                    if f.name not in the_fields:
                        continue
                    if isinstance(f, (models.CharField, models.TextField)):
                        self.filter_fields[f.name] = ['exact', 'icontains', 'istartswith', 'iendswith']
                        contains = f.name + '_contains'
                        self.filters[contains] = self.char_filter(
                            f.name,
                            'icontains'
                        )
                        setattr(self, contains, self.filters[contains])

                    if isinstance(f,
                                  (models.FloatField,
                                   models.IntegerField,
                                   models.DecimalField
                                   )
                                  ):
                        self.filter_fields[f.name] = ['exact', 'gt', 'lt', 'gte', 'lte']
                        lt = f.name + '_less_than'
                        self.filters[lt] = self.num_filter(f.name, 'lt')
                        gt = f.name + '_greater_than'
                        self.filters[gt] = self.num_filter(f.name, 'gt')

                    if isinstance(f, (models.DateField, models.DateTimeField)):
                        self.filter_fields[f.name] = ['exact', 'gt', 'lt', 'gte', 'lte', 'range']
                        lt = f.name + '_less_than'
                        self.filters[lt] = self.date_filter(f.name, 'lt')

                        gt = f.name + '_greater_than'
                        self.filters[gt] = self.date_filter(f.name, 'gt')

                        r = f.name + '_range'
                        self.filters[r] = self.date_range(f.name)

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
                return django_filters.DateTimeFilter(
                    field_name=name,
                    lookup_expr=lookup
                )

            def date_range(self, name):
                return django_filters.DateRangeFilter(field_name=name)

            class Meta:
                model = the_model
                fields = the_fields

        return GenericBaseFilters
