import datetime

from django.test import TestCase
from example.app.widgets.models import Widget, Customer, Purchase, PurchaseItem

class WidgetTests(TestCase):

    def setUp(self):
        basic_obj = Widget(name='testwidget',
                           color='Black',
                           size='Small',
                           shape='Rectangle')
        basic_obj.save()
        dummy_obj = Widget(name='dummywidget',
                           color='Green',
                           size='Medium',
                           shape='Ellipse')
        dummy_obj.save()

    def test_get_name(self):
        obj = Widget.objects.get(name='testwidget')
        self.assertEqual(obj.name, 'testwidget')
        self.assertEqual(str(obj), 'testwidget')

    def test_get_color(self):
        obj = Widget.objects.get(name='testwidget')
        self.assertEqual(obj.color, 'Black')

    def test_get_size(self):
        obj = Widget.objects.get(name='testwidget')
        self.assertEqual(obj.size, 'Small')

    def test_get_shape(self):
        obj = Widget.objects.get(name='testwidget')
        self.assertEqual(obj.shape, 'Rectangle')

    def test_all(self):
        obj = Widget.objects.get(name='testwidget')
        self.assertEqual(obj.name, 'testwidget')
        self.assertEqual(obj.color, 'Black')
        self.assertEqual(obj.size, 'Small')
        self.assertEqual(obj.shape, 'Rectangle')

    def test_create_new(self):
        obj = Widget.objects.create(name='otherwidget',
                                    color='Red',
                                    size='Large',
                                    shape='Triangle')
        obj.save()

        other = Widget.objects.get(name='otherwidget')
        self.assertEqual(other.name, 'otherwidget')
        self.assertEqual(other.color, 'Red')
        self.assertEqual(other.size, 'Large')
        self.assertEqual(other.shape, 'Triangle')

        obj2 = Widget.objects.create(color='Red',
                                     size='Large',
                                     shape='Triangle')

        self.assertEqual(obj2.name, 'Red.Large.Triangle')


class PurchaseTests(TestCase):

    def setUp(self):
        widg1 = Widget(name='testwidget',
                       color='Black',
                       size='Small',
                       shape='Rectangle')
        widg1.save()
        widg2 = Widget(name='dummywidget',
                       color='Green',
                       size='Medium',
                       shape='Ellipse')
        widg2.save()
        cust = Customer.objects.create(name='testcust',
                                       state='Florida',
                                       gender='M',
                                       age='29')
        purch1 = Purchase(customer=cust)
        purch1.save()
        purch1.add_item(widg1)
        purch1.add_item(widg2)
        purch1.save()

    def test_customer_methods(self):
        cust = Customer.objects.get(name='testcust')
        pur = Purchase.objects.first()
        self.assertEqual(cust.get_purchases().first(), pur)

        self.assertEqual(cust.name, 'testcust')
        self.assertEqual(cust.state, 'Florida')
        self.assertEqual(cust.gender, 'M')
        self.assertEqual(cust.age, 29)

    def test_items_added(self):
        purch1 = Purchase.objects.first()
        self.assertQuerysetEqual(purch1.items.all(),
                                 PurchaseItem.objects.all(),
                                 transform=lambda x: x,
                                 ordered=False)

    def test_get_customer(self):
        purch1 = Purchase.objects.first()
        self.assertIsInstance(purch1.customer, Customer)

    def test_correct_cost(self):
        purch1 = Purchase.objects.first()
        widg1 = Widget.objects.get(name='testwidget')
        widg2 = Widget.objects.get(name='dummywidget')
        pur_cost = purch1.get_cost()
        widg_cost = widg1.cost + widg2.cost
        self.assertEqual(pur_cost, widg_cost)

    def test_item_count(self):
        purch1 = Purchase.objects.first()
        self.assertEqual(purch1.items.count(), Widget.objects.all().count())

    def test_sale_date(self):
        purch1 = Purchase.objects.first()
        self.assertEqual(purch1.sale_date.date(),
                         datetime.datetime.now().date())

    def test_sale_price_profit(self):
        purch1 = Purchase.objects.first()
        pur_sale_price = purch1.sale_price

        widg1 = Widget.objects.get(name='testwidget')
        widg2 = Widget.objects.get(name='dummywidget')
        widg_cost = widg1.cost + widg2.cost

        widg_sale_price = round(widg_cost * 1.5, 2)
        self.assertEqual(pur_sale_price, widg_sale_price)

        pur_profit = purch1.profit
        widg_profit = round(widg_cost * 0.5, 2)
        self.assertEqual(pur_profit, widg_profit)
