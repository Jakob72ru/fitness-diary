from django.contrib import admin
from .models import Product, Day, DayProduct

class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'id')

class DayAdmin(admin.ModelAdmin):
    list_display = ('date', 'id')

class DayProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'day_id', 'product_id', 'weight', 'calories')

admin.site.register(Product, ProductAdmin)
admin.site.register(Day, DayAdmin)
admin.site.register(DayProduct, DayProductAdmin)

