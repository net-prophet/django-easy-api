import django
from django.db import models
from django.db.models import Sum
from example.app.widgets.models import Widget
from example.app.customers.models import Customer

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
