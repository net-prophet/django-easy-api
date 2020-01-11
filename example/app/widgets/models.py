from django.db import models

from .options import COLORS, SIZES, SHAPES, GENDERS, STATES
import django.utils.timezone

class Store(models.Model):
    name = models.CharField(max_length=30, blank=True)
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    @classmethod
    def DEFAULT(cls):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.count():
            User.objects.create(username='default_user')

        return cls.objects.get_or_create(name='DEFAULT',
                owner=User.objects.first())[0]

def default_store_id():
    return Store.DEFAULT().id
    
class Widget(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, default=default_store_id, related_name='widgets')
    name = models.CharField(max_length=30, blank=True)
    color = models.CharField(choices=COLORS, max_length=30)
    size = models.CharField(choices=SIZES, max_length=30)
    shape = models.CharField(choices=SHAPES, max_length=30)
    cost = models.FloatField(default=0,
                             blank=True)

    def save(self, *args, **kwargs):
        if self.name == '':
            self.name = '%s.%s.%s' % (self.color, self.size, self.shape)

        color_sum = sum([ord(x) for x in self.color])
        size_sum = sum([ord(x) for x in self.size])
        shape_sum = sum([ord(x) for x in self.shape])
        self.cost = color_sum + size_sum + shape_sum
        super(Widget, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

class Customer(models.Model):
    name = models.CharField(max_length=30, blank=True)
    state = models.CharField(max_length=30, blank=True)
    gender = models.CharField(max_length=1, blank=True)
    age = models.IntegerField(blank=True)

    def get_purchases(self):
        return Purchase.objects.all().filter(customer=self)

    def get_name(self):
        return self.name

    def get_state(self):
        return self.state

    def get_gender(self):
        return self.gender

    def get_age(self):
        return self.age

class Purchase(models.Model):
    sale_date = models.DateTimeField(default=django.utils.timezone.now)
    sale_price = models.FloatField(default=0, blank=True)
    profit = models.FloatField(default=0, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="purchases")

    def get_cost(self):
        costs = [item.widget.cost for item in self.items.all()]
        return round(sum(costs), 2)

    def add_item(self, widget):
        return self.items.create(widget=widget)


    def set_sale_price(self):
        cost_plus_profit = 1.5
        cost = self.get_cost()
        self.sale_price = round(cost*cost_plus_profit, 2)

    def set_profit(self):
        profit_margin = 0.5
        cost = self.get_cost()
        self.profit = round(cost*profit_margin, 2)

    def save(self, *args, **kwargs):
        self.set_sale_price()
        self.set_profit()
        super(Purchase, self).save(*args, **kwargs)

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    widget = models.ForeignKey('widgets.Widget', on_delete=models.CASCADE, related_name='items')
