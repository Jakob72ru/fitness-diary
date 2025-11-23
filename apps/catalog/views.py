from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models.functions import TruncMonth, Round
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Day, DayProduct
from apps.accounts.models import Profile
from django.views.generic import DetailView, ListView, CreateView, UpdateView
from django.views.generic.base import View
from  django.utils import timezone
from .forms import ProductWeightForm, UserWeightForm, CreateProductForm, UpdateProductForm, SearchForm
from datetime import date, timedelta
from calendar import monthcalendar, month_name
from locale import setlocale, LC_ALL
from django.db.models import Count, Avg, QuerySet, F
from django.contrib.auth.models import User
from django.views.decorators.http import require_GET
from django.http import JsonResponse, HttpResponse
import calendar
import re
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io


class ProductDetailView(DetailView):
    template_name = 'catalog/product_detail.html'
    model = Product
    context_object_name = 'product'


    def get_object(self, queryset=None):
        slug = self.kwargs.get('slug')
        product = get_object_or_404(Product, slug=slug)  # Получаем объект по slug
        return product

    def get_day_object(self):
        return get_object_or_404(Day, id=self.request.session.get('day_id'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.object.title
        context['day'] = self.get_day_object()
        query = DayProduct.objects.filter(day__date__gte=date.fromordinal(date.today().toordinal() - 30),
                                          day__date__lte=date.today(), user_id=self.request.user.id).values(
            'product_id').annotate(count=Count('product_id')).order_by('-count')[:25]
        products = [Product.objects.get(id=dict['product_id']) for dict in query]
        context['products'] = products
        context['selected_day'] = self.get_day_object().date
        context['page_title'] = f'{self.get_object()} - Fitness Diary'
        self.request.session['selected_day'] = context['selected_day'].isoformat()
        self.request.session['page_title'] = self.get_object().title
        forms = {}
        for product in products:
            # Заполняем начальное значение для каждой формы значением веса из модели
            forms[product.id] = ProductWeightForm(initial={'weight': product.weight})
        forms['user_weight'] = UserWeightForm()
        context['forms'] = forms
        context['day_products'] = DayProduct.objects.filter(day_id=self.request.session.get('day_id'))
        context['day_title'] = self.request.session.get('day_title')

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ProductWeightForm(request.POST)

        # Обработка кнопки добавления продукта
        if request.POST.get('action') == 'add_product':
            if form.is_valid():
                weight = form.cleaned_data['weight']
                product_id = request.POST.get('product_id')
                product = get_object_or_404(Product, id=product_id)
                day = self.get_day_object()
                day.add_product(product, weight)
                DayProduct.objects.create(day=day, product=product, weight=weight,
                                          user_id=request.user.id,
                                          calories=product.calories * int(weight)/100,
                                          )

        # Обработка кнопки обновления продукта
        if request.POST.get('action') == 'update_product':
            return redirect(self.object.get_absolute_url() + '/update')

        # Обработка кнопки удаления продукта из дня
        if request.POST.get('action') == 'delete_product':
            day_product = get_object_or_404(DayProduct, id=request.POST.get('day_product_id'))
            day = self.get_day_object()
            day.remove_product(day_product.product, day_product.weight)
            DayProduct.objects.filter(id=day_product.id).delete()

        # Обработка кнопки создания продукта
        if request.POST.get('action') == 'create_product':
            selected_day = self.get_context_data()['selected_day']
            return redirect(f'/day/{selected_day}/create_product')

        # Обработка кнопки удаления продукта
        if request.POST.get('action') == 'delete_current_product':
            product = self.get_object()
            request.session['deleted_product_id'] = product.id
            context = self.get_context_data()
            selected_day = context.get('selected_day')
            return redirect(f'/day/{selected_day}')


        return redirect(self.object.get_absolute_url())


class CreateProductView(CreateView):
    model = Product
    template_name = 'catalog/create_product.html'
    form_class = CreateProductForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        context['selected_day'] = self.kwargs.get('slug')
        context['page_title'] = 'Создание продукта - Fitness Diary'
        return context


class UpdateProductView(UpdateView):
    model = Product
    template_name = 'catalog/update_product.html'
    form_class = UpdateProductForm
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        context['selected_day'] = date.fromisoformat(self.request.session.get('selected_day'))

        context['page_title'] = self.request.session.get('page_title') + ': обновление продукта - Fitness Diary'
        return context


class ProductListview(ListView):
    template_name = 'catalog/products.html'
    model = Product
    context_object_name = 'products'
    queryset = Product.objects.all().order_by('title')
    paginate_by = 28


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        day_path = request.path.lstrip('products/')
        selected_day = (date.today(), day_path)[bool(day_path)]
        context['selected_day'] = date(*(int(i) for i in selected_day.lstrip('day/').split('-')))
        context['page_title'] = f'Все продукты - Fitness Diary'
        return context


class DayDetailView(View):
    template_name = 'catalog/day_detail.html'

    def get_object(self, request, queryset=None):
        slug = self.kwargs.get('slug')
        day = get_object_or_404(Day, slug=slug, user_id=request.user.id)  # Получаем объект по slug
        return day

    def get(self, request, *args, **kwargs):
        day = self.get_object(request)
        today = date.today()
        current_user_id = request.user.id
        user_weight = day.user_weight
        days = {}
        request.session['day_id'] = self.get_object(request).id

        query = DayProduct.objects.filter(day__date__gte=date.fromordinal(date.today().toordinal() - 30),
                                           day__date__lte=date.today(), user_id=request.user.id).values(
            'product_id').annotate(count=Count('product_id')).order_by('-count')[:25]
        products = [Product.objects.get(id=dict['product_id']) for dict in query]

        # сохранение стандарта дня


        # удаление продукта если была нажата кнопка
        if request.session.get('deleted_product_id', False):
            deleted_product = Product.objects.get(id=request.session['deleted_product_id'])
            query = DayProduct.objects.filter(day_id=day.id, product_id=deleted_product.id,
                                            user_id=current_user_id)
            weight = sum(item.weight for item in query)
            day.remove_product(deleted_product, weight)
            deleted_product.delete()
            request.session['deleted_product_id'] = False

        postfixes = {1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля', 5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
                   9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'}
        day_title = f'{day.date.day} {postfixes[day.date.month]}'
        request.session['day_title'] = day_title
        day_products = DayProduct.objects.filter(day_id=day.id)
        selected_day_url = request.path
        selected_day = date(*(int(i) for i in selected_day_url.lstrip('day/').split('-')))

        forms = {}
        for product in products:
            # Заполняем начальное значение для каждой формы значением веса из модели
            forms[product.id] = ProductWeightForm(initial={'weight': product.weight})
        forms['user_weight'] = UserWeightForm()



        # формируем календарь
        month_cal = monthcalendar(today.year, today.month)
        for week in month_cal:
            for weekday in week:
                if weekday != 0:
                    day_date = date(today.year, today.month, weekday)
                    if Day.objects.filter(date=day_date, user_id=current_user_id).exists():
                        days[weekday] = Day.objects.get(date=day_date, user_id=current_user_id)
                    else:
                        days[weekday] = Day.objects.create(date=day_date, user_id=current_user_id)

        return render(request, self.template_name, {'forms': forms,
                                                    'products': products,
                                                    'days': days,
                                                    'page_title': f"{day.date.strftime("%d.%m.%y")} - Fitness Diary",
                                                    'day': day,
                                                    'day_title': day_title,
                                                    'selected_day': selected_day,
                                                    'selected_day_slug': selected_day_url,
                                                    'month_cal': month_cal,
                                                    'day_products': day_products,
                                                    'user_weight': user_weight,
                                                    })


    def post(self, request, *args, **kwargs):
        self.object = self.get_object(request)
        form = ProductWeightForm(request.POST)


        # Обработка добавления продукта
        if request.POST.get('action') == 'add_product':
            product = get_object_or_404(Product, id=request.POST.get('product_id'))
            if form.is_valid():
                weight = form.cleaned_data['weight']
                self.object.add_product(product, weight)
                DayProduct.objects.create(day=self.object, product=product, weight=weight,
                                          user_id=request.user.id,
                                          calories=product.calories * int(weight)/100)

        if request.POST.get('action') == 'reset_day':
            self.object.reset_day()
            DayProduct.objects.filter(day_id=self.object.id).delete()
            self.object.user_weight = 0
            self.object.save()

        if request.POST.get('action') == 'delete_product':
            day_product = get_object_or_404(DayProduct, id=request.POST.get('day_product_id'))
            self.object.remove_product(day_product.product, day_product.weight)
            DayProduct.objects.filter(id=day_product.id).delete()

        if request.POST.get('action') == 'input_weight':
            form = UserWeightForm(request.POST)
            if form.is_valid():
                user_weight = form.cleaned_data['user_weight']
                self.object.add_user_weight(user_weight)
                profile = Profile.objects.get(id=request.user.id)
                profile.weight = user_weight
                profile.save()


        if request.POST.get('action') == 'create_product':
            return redirect(self.object.get_absolute_url() + '/create_product')

        return redirect(self.object.get_absolute_url())


def summary(request, month:str, year:str, period='selected_month') -> dict:
    current_user_id = request.user.id
    today = date.today()
    standard = Day.objects.get(date=today, user=request.user.id).standard
    checkpoint = {attr: 100 for attr in standard}
    items, items_not_null, items_avg = {}, {}, {}

    match period:
        case 'last_30_days':
            queryset = ((Day.objects.filter(date__gte=date.fromordinal(today.toordinal() - 30),
                                           date__lte=today, user_id=current_user_id, calories__gt=0))
                        .annotate(tick=F('date'))
                        .values('tick', 'proteins', 'fats', 'carbohydrates', 'calories', 'user_weight')
                        .order_by('tick'))

            period_range = [today - timedelta(days=i) for i in range(29, -1, -1)]

        case 'last_365_days':
            queryset = (Day.objects.filter(date__gte=date.fromordinal(today.toordinal() - 365),
                                          date__lte=today, user_id=current_user_id, calories__gt=0)
                        .annotate(tick=TruncMonth('date'))
                        .values('tick')
                        .annotate(proteins=Round(Avg('proteins'), 1),
                                  fats=Round(Avg('fats'), 1),
                                  carbohydrates=Round(Avg('carbohydrates'), 1),
                                  calories=Round(Avg('calories'), 1),
                                  user_weight=Round(Avg('user_weight'), 1)
                                  )
                        .order_by('tick')
                        )

            period_range = [date((today.year, today.year - 1)[today.month < month], month, 1) for month in
                            list(range(today.month + 1, 13)) + list(range(1, today.month + 1))]

        case _:
            if month == today.month and year == today.year:
                date_limit = today
            else:
                date_limit = date(year, month, calendar.monthrange(year, month)[1])

            queryset = (Day.objects.filter(date__month=str(month), date__lte=str(date_limit),
                                            date__year=str(year), user_id=current_user_id,  calories__gt=0)
                            .annotate(tick=F('date'))
                            .values('tick', 'proteins', 'fats', 'carbohydrates', 'calories', 'user_weight')
                            .order_by('tick'))

            period_range = [date(date_limit.year, date_limit.month, day) for day in range(1, date_limit.day)]

    # Формируется словарь ненулевых значений в % отношении к стандартным
    for item in queryset:
        items_not_null[item['tick']] = {attr: round(item[attr] / standard[attr] * 100) for attr in standard}

    # формируется словарь всех значений с заменой нулевых на предыдущие ненулевые или стандартные
    for tick in period_range:
        items[tick] = items_not_null.get(tick, checkpoint)
        checkpoint = items[tick]

    # формируется словарь средних значений по периоду
    for item in queryset:
        for attr in standard:
            items_avg[attr] = items_avg.get(attr, 0) + item[attr]
    items_avg = {attr: round(items_avg[attr] / len(items_not_null), 1) for attr in items_avg}

    return items, items_not_null, items_avg


@login_required
def main(request, slug=date.today()):
    today = date.today()
    if not Day.objects.filter(date=today, user=request.user.id):
        Day.objects.create(date=today, user=request.user.id)
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    selected_day_slug = re.match(r'.*/(\d{4}-\d\d-\d\d).*', request.path)
    if selected_day_slug:
        selected_day = date(*(int(i) for i in selected_day_slug.group(1).split('-')))
    else:
        selected_day = date.today()
    period = request.POST.get('period')
    setlocale(LC_ALL, 'ru_RU.UTF-8')
    days = {}
    current_user_id = request.user.id
    month_cal = monthcalendar(year, month)
    month_title = month_name[month]
    next_month = month_name[(month+1, 1)[month==12]]
    previous_month = month_name[(month-1, 12)[month==1]]
    results = summary(request, month, year, period)[2]
    active_period = period

    for week in month_cal:
        for day in week:
            if day != 0:
                day_date = date(year, month, day)
                if Day.objects.filter(date=day_date, user_id=current_user_id).exists():
                    days[day] = Day.objects.get(date=day_date, user_id=current_user_id)
                else:
                    days[day] = Day.objects.create(date=day_date, user_id=current_user_id)

    return render(request, 'catalog/main_page.html', {'month_title': month_title,
                                                     'month': month,
                                                     'next_month': next_month,
                                                     'previous_month': previous_month,
                                                     'year': year,
                                                     'days': days,
                                                     'selected_day': selected_day,
                                                     'selected_day_slug': selected_day_slug,
                                                     'month_cal': month_cal,
                                                     'today': today,
                                                     'results': results,
                                                     'period': period,
                                                     'active_period': active_period,
                                                     'page_title': 'Fitness Diary',
                                                     })

def chart_image(request):
    period = request.GET.get('period')
    month = int(request.GET.get('month', date.today().month))
    year = int(request.GET.get('year', date.today().year))
    items, items_not_null, items_avg = summary(request, month, year, period)
    x = list(range(1, len(items)+1))
    a = [item['proteins'] for item in items.values()]
    b = [item['fats'] for item in items.values()]
    c = [item['carbohydrates'] for item in items.values()]
    d = [item['calories'] for item in items.values()]
    plt.figure(figsize=(11.5, 6))
    plt.plot(x, a, color='#1E90FF', marker='o', markersize=3)
    plt.plot(x, b, color='gold', marker='o', markersize=3)
    plt.plot(x, c, color='#3CB371', marker='o', markersize=3)
    plt.plot(x, d, color='#DC143C', marker='o', markersize=3)
    plt.grid()
    plt.xlim(1, len(items))
    plt.title('Соответствие БЖУ целям по дням периода (%)', fontsize=20)
    y_bottom = min(number for item in items.values() for number in item.values())
    y_top = max(number for item in items.values() for number in item.values())
    y_range = range(int(y_bottom - y_bottom%10), int(y_top + 10 - y_top%10)+1, 10)
    plt.ylim(min(y_range), max(y_range))
    attr = ('day', 'month')[period == 'last_365_days']
    plt.xticks(x, labels=[getattr(item, attr) for item in items.keys()])
    plt.yticks(y_range, labels=(f'{tick}%' for tick in y_range))
    plt.axhspan(90, 110, facecolor='green', alpha=0.10)
    plt.legend(labels=('Белки', 'Жиры', 'Углеводы', 'Калории'), fontsize=12, shadow=True)

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')


def product_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            results = Product.objects.filter(title__search=query)

    return render(request, 'catalog/search.html',
                  {'form': form, 'query': query, 'results': results})

def day_today(request):
    today = timezone.now().date().isoformat()
    return  redirect('day_detail', slug=today)


@require_GET
def search_json(request):
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        qs = Product.objects.filter(title__icontains=q)[:5]
        results = [
            {'title': a.title,
             'slug': a.slug,
             'url': request.build_absolute_uri(f'/product/{a.slug}')
             }
            for a in qs
        ]
    return JsonResponse({'results': results})