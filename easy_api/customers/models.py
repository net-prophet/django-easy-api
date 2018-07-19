from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=30, blank=True)
    state = models.CharField(max_length=30, blank=True)
    gender = models.CharField(max_length=1, blank=True)
    age = models.IntegerField(blank=True)

    def get_purchases(self):
        from purchases.models import Purchase
        return Purchase.objects.all().filter(customer=self)

    def get_name(self):
        return self.name

    def get_state(self):
        return self.state

    def get_gender(self):
        return self.gender

    def get_age(self):
        return self.age
