from django.db import models
from django.shortcuts import reverse
from services.utils import unique_slugify
from pytils.translit import slugify
import decimal
from django.contrib.auth.models import User

class Product(models.Model):
    # Модель продуктов

    title = models.CharField(verbose_name="Название", max_length=255)
    slug = models.SlugField(verbose_name='URL', max_length=255, blank=True)
    create = models.DateTimeField(auto_now_add=True, verbose_name='Время добавления')
    update = models.DateTimeField(auto_now=True, verbose_name='Время обновления')
    proteins = models.DecimalField(verbose_name='Белки', max_digits=10, decimal_places=1)
    fats = models.DecimalField(verbose_name='Жиры', max_digits=10, decimal_places=1)
    carbohydrates = models.DecimalField(verbose_name='Углеводы', max_digits=10, decimal_places=1)
    weight = models.IntegerField(verbose_name='Вес порции')
    calories = models.DecimalField(verbose_name="Калорийность", max_digits=10, decimal_places=1)
    thumbnail = models.ImageField(verbose_name='Изображение',
                                  default='default.png',
                                  upload_to='images/thumbnails/',
                                  )


    class Meta:
        db_table = 'Products'
        ordering = ['title']
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # при сохранении генерируем слаг и проверяем на уникальность
        self.slug = unique_slugify(self, self.title, self.slug)

        if not self.thumbnail or self.thumbnail.name == 'default.png':
            # Убедитесь, что путь начинается с 'images/thumbnails/'
            self.thumbnail.name = 'images/thumbnails/default.png'
            # сохраняем файл изображения с новым именем
        else:
            if self.slug:
                # получаем расширение загруженного изображения
                extension = self.thumbnail.name.split('.')[-1]
                # формируем новое имя файла аналогичное слагу
                self.thumbnail.name = f'{self.slug}.{extension}'
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # Получаем прямую ссылку на продукт
        return reverse('product_detail', kwargs={'slug': self.slug})


class Day(models.Model):
    # модель дня
    date = models.DateField(verbose_name='Дата')
    slug = models.SlugField(verbose_name='URL', max_length=255, blank=True, unique=False)
    create = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    update = models.DateTimeField(auto_now=True, verbose_name='Время обновления')
    proteins = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    fats = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    carbohydrates = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    user_weight = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    calories = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='day', null=True, blank=True)
    standard = models.JSONField(verbose_name='Целевые показатели', default=dict)

    class Meta:
        db_table = 'Day'
        ordering = ['date']
        verbose_name = 'День'
        verbose_name_plural = 'Дни'


    def __str__(self):
        return str(self.date)

    def add_product(self, product, weight):
        self.proteins += product.proteins * decimal.Decimal(int(weight)/100)
        self.fats += product.fats * decimal.Decimal(int(weight)/100)
        self.carbohydrates += product.carbohydrates * decimal.Decimal(int(weight)/100)
        self.calories += product.calories * decimal.Decimal(int(weight)/100)
        self.save()

    def remove_product(self, product, weight):
        self.proteins -= product.proteins * decimal.Decimal(int(weight) / 100)
        self.fats -= product.fats * decimal.Decimal(int(weight) / 100)
        self.carbohydrates -= product.carbohydrates * decimal.Decimal(int(weight) / 100)
        self.calories -= product.calories * decimal.Decimal(int(weight) / 100)
        self.save()

    def reset_day(self):
        self.proteins = 0
        self.fats = 0
        self.carbohydrates = 0
        self.calories = 0
        self.save()

    def add_user_weight(self, weight):
        self.user_weight = decimal.Decimal(weight)
        self.save()

    def save(self, *args, **kwargs):
        if not self.slug:  # Only set the slug if it's not already set
            self.slug = slugify(self.date)

        self.standard = {'proteins': self.user.profile.proteins,
                         'fats': self.user.profile.fats,
                         'carbohydrates': self.user.profile.carbohydrates,
                         'calories': self.user.profile.calories,
                         'user_weight': self.user.profile.aim_weight}

        super().save(*args, **kwargs)


    def get_absolute_url(self):
        # Получаем прямую ссылку на день
        return reverse('day_detail', kwargs={'slug': self.slug})


class DayProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='day_products', null=True, blank=True)
    day = models.ForeignKey(Day, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    weight = models.IntegerField(default=0)
    calories = models.IntegerField(default=0)

    class Meta:
        db_table = 'DayProduct'
        verbose_name = 'Продукты дня'
        verbose_name_plural = 'Продукты дня'

    def __str__(self):
        return f'{self.product.title} on {self.day.date}: {self.weight} g ({self.calories} cal)'

