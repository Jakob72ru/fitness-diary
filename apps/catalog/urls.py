from django.urls import path
from .views import (ProductDetailView, DayDetailView, main, ProductListview, CreateProductView, UpdateProductView,
                    day_today, search_json, chart_image)
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include

urlpatterns = [
    path('', main, name='start'),
    path('main/', main, name='home'),
    path('main/<slug:slug>', main, name='main'),
    path('search/', search_json, name='search_json'),
    path('day/today/', day_today, name='day_today'),
    path('day/<slug:slug>', DayDetailView.as_view(), name='day_detail'),
    path('day/<slug:slug>/create_product', CreateProductView.as_view(), name='create_product_from_day'),
    path('products/<slug:slug>', ProductListview.as_view(), name='products'),
    path('product/<slug:slug>/update', UpdateProductView.as_view(), name='update_product'),
    path('product/<slug:slug>', ProductDetailView.as_view(), name='product_detail'),
    path('chart.png', chart_image, name='chart_image')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)