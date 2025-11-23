from django.db import models
from django.contrib.auth.models import User
from apps.catalog.models import Day
from datetime import date, timedelta
from services.utils import unique_slugify
from  django.shortcuts import reverse
from dateutil.relativedelta import relativedelta
from django.utils import timezone


class Profile(models.Model):
    GENDER_MALE = 'мужской'
    GENDER_FEMALE = 'женский'

    GENDER_CHOICES = [
        (GENDER_MALE, 'мужской'),
        (GENDER_FEMALE, 'женский'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    slug = models.SlugField(verbose_name='URL', max_length=255, blank=True)
    name = models.CharField(verbose_name='Имя', default='')
    surname = models.CharField(verbose_name='Фамилия', default='')
    avatar = models.ImageField(default='default_profile.webp', upload_to='profile_images/')
    gender = models.CharField(verbose_name='Пол', default='мужчина', choices=GENDER_CHOICES)
    height = models.IntegerField(verbose_name='Рост', default=175)
    weight = models.IntegerField(verbose_name='Вес', default=75)
    aim_weight = models.IntegerField(verbose_name='Цель', default=0)
    birthday = models.DateField(verbose_name='Дата рождения', default=date(1991, 12, 21))
    proteins = models.IntegerField(verbose_name='Белки', default=0)
    fats = models.IntegerField(verbose_name='Жиры', default=0)
    carbohydrates = models.IntegerField(verbose_name='Углеводы', default=0)
    calories = models.IntegerField(verbose_name="Калорийность", default=0)
    max_streak = models.IntegerField(verbose_name='максимальный стрик', default=0)

    @property
    def age(self):
        # Рассчитываем возраст на основе дня рождения
        if not self.birthday:
            return 0

        today = timezone.now().date()
        return relativedelta(today, self.birthday).years

    def __str__(self):
        return self.user.username

    def get_standard(self):
        self.proteins = self.aim_weight * 1.75
        self.fats = self.aim_weight
        self.carbohydrates = self.aim_weight * 2.3
        self.calories = self.proteins * 4 + self.fats * 9 + self.carbohydrates * 4

    def get_absolute_url(self):
        # Получаем прямую ссылку на продукт
        return reverse('profile')


    def save(self, *args, **kwargs):

        if not self.aim_weight or self.aim_weight == 0:
            self.aim_weight = self.height - 100
        if not self.proteins:
            self.proteins = self.aim_weight * 1.6
        if not self.fats:
            self.fats = self.aim_weight
        if not self.carbohydrates:
            self.carbohydrates = self.aim_weight * 2.4
        if not self.calories:
            self.calories = self.aim_weight * 1.6 * 4 + self.aim_weight * 9 + self.aim_weight * 2.4 * 4
        if not self.age:
            today = date.today()
            years = today.year - self.birthday.year
            if (today.month, today.day) < (self.birthday.month, self.birthday.day):
                years -= 1
            self.age = years
        if not self.slug:  # Only set the slug if it's not already set
            self.slug = unique_slugify(self, self.user, self.slug)


        super().save(*args, **kwargs)
