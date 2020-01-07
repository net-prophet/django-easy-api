import pytz
import random
import factory
import datetime as dt
import factory.fuzzy as fuz
from example.app.widgets.models import Widget
from example.app.customers.models import Customer
from example.app.purchases.models import Purchase
from example.app.customers.options import GENDERS, STATES


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    name = factory.Sequence(lambda n: 'John Doe %s' % n)
    state = fuz.FuzzyChoice(STATES)
    gender = fuz.FuzzyChoice(GENDERS)
    age = fuz.FuzzyInteger(18, 78)


class PurchaseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Purchase

    sale_date = fuz.FuzzyDateTime(dt.datetime(2010, 1, 1, tzinfo=pytz.UTC))
    customer = factory.SubFactory(CustomerFactory)

    @factory.post_generation
    def items(self, create, purchased, **kwargs):
        amt_purchased = random.randint(1, 10)
        purchased = Widget.objects.all().order_by('?')[:amt_purchased]

        if create and purchased:
            for item in purchased:
                self.items.add(item)
