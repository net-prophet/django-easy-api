import django.utils.timezone
import graphene
from django.db import models
import django_filters

from EasyAPI.decorators import APIProperty, APIAction, AddPermissionContext

from .options import COLORS, GENDERS, SHAPES, SIZES, STATES

from django.contrib.auth.models import AbstractUser


@AddPermissionContext(
    "*", {"*": lambda user, qs: user and qs.filter(pk=user.id)}
)
class User(AbstractUser):
    pass


@AddPermissionContext("*", {"read": True})
@AddPermissionContext(
    "store_owner", {"*": lambda user, qs: user and qs.filter(owner=user)}
)
class Store(models.Model):
    name = models.CharField(max_length=30, blank=True)
    owner = models.ForeignKey(
        "widgets.User", on_delete=models.CASCADE, related_name="stores"
    )
    setattr(owner, '_APIDefault', lambda resource, request: request.user)

    @classmethod
    def DEFAULT(cls):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        if not User.objects.count():
            User.objects.create(username="default_user")

        return cls.objects.get_or_create(name="DEFAULT", owner=User.objects.first())[0]

def default_store_id():
    return Store.DEFAULT().id

@AddPermissionContext("*", {"read": True})
@AddPermissionContext("store_owner", {"*": "store"})
class Widget(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        #default=default_store_id,
        related_name="widgets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=30, blank=True)
    color = models.CharField(choices=COLORS, max_length=30)
    size = models.CharField(choices=SIZES, max_length=30)
    shape = models.CharField(choices=SHAPES, max_length=30)
    cost = models.FloatField(default=0, blank=True)

    # Properties are non-query calculations
    @APIProperty(graphene.Int)
    def age(self):
        return (django.utils.timezone.now() - self.created_at).total_seconds()

    @APIProperty(graphene.String)
    def stub(self):
        return "%s-%s" % (self.store.name, self.name)

    # Mutations can be on an object or a queryset --
    # + pass exactly one of either detail=True or many=True
    @APIAction(detail=True)
    @classmethod
    def archive(cls, instance, **data):
        instance.archived_at = django.utils.timezone.now()
        instance.save()
        return instance

    @APIAction(many=True, read_only=True)
    @classmethod
    def top_three(cls, qs, **data):
        return qs.annotate(sold=models.Sum('items__purchase__sale_price')).order_by('sold')[:3]

    unarchived = django_filters.BooleanFilter(field_name='archived_at', lookup_expr='isnull')
    archived = django_filters.BooleanFilter(field_name='archived_at', lookup_expr='isnull', exclude=True)

    def save(self, *args, **kwargs):
        if self.name == "":
            self.name = "%s.%s.%s" % (self.color, self.size, self.shape)

        color_sum = sum([ord(x) for x in self.color])
        size_sum = sum([ord(x) for x in self.size])
        shape_sum = sum([ord(x) for x in self.shape])
        self.cost = color_sum + size_sum + shape_sum
        super(Widget, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


@AddPermissionContext(
    "store_owner", "store",
)
class Customer(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="customers",
        default=default_store_id,
    )
    name = models.CharField(max_length=30, blank=True)
    state = models.CharField(max_length=30, blank=True)
    gender = models.CharField(max_length=1, blank=True)
    age = models.IntegerField(blank=True)


@AddPermissionContext(
    "store_owner", {"read": "customer"},
)
class Purchase(models.Model):
    sale_date = models.DateTimeField(default=django.utils.timezone.now)
    sale_price = models.FloatField(default=0, blank=True)
    profit = models.FloatField(default=0, blank=True)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="purchases"
    )

    def get_cost(self):
        costs = [item.widget.cost for item in self.items.all()]
        return round(sum(costs), 2)

    def add_item(self, widget):
        return self.items.create(widget=widget)

    def set_sale_price(self):
        cost_plus_profit = 1.5
        cost = self.get_cost()
        self.sale_price = round(cost * cost_plus_profit, 2)

    def set_profit(self):
        profit_margin = 0.5
        cost = self.get_cost()
        self.profit = round(cost * profit_margin, 2)

    def save(self, *args, **kwargs):
        self.set_sale_price()
        self.set_profit()
        super(Purchase, self).save(*args, **kwargs)


@AddPermissionContext(
    "store_owner", {"read": "purchase"},
)
class PurchaseItem(models.Model):
    purchase = models.ForeignKey(
        Purchase, on_delete=models.CASCADE, related_name="items"
    )
    widget = models.ForeignKey(
        "widgets.Widget", on_delete=models.CASCADE, related_name="items"
    )
