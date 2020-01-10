from django.contrib import admin
from .models import Purchase, PurchaseItem


class WidgetInLine(admin.TabularInline):
    model = PurchaseItem


class PurchaseAdmin(admin.ModelAdmin):
    model = Purchase
    list_display = ('sale_date', 'sale_price', 'profit')
    list_filter = ('sale_date', 'sale_price', 'profit')
    inlines = [WidgetInLine]


#admin.site.register(Purchase, PurchaseAdmin)
