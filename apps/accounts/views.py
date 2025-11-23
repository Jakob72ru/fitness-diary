from http.client import responses

from django.urls import reverse_lazy
from django.shortcuts import render, redirect, reverse
from django.views.generic import CreateView, UpdateView
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm
from .forms import UpdateProfileForm
from django.contrib.auth.views import LoginView
from django.core.files.storage import default_storage
from datetime import date
from .forms import BootstrapStyledAuthenticationForm, CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import login
from apps.catalog.models import Day
from .models import Profile
from datetime import datetime, timedelta
from collections import defaultdict
import os


class SignUpView(SuccessMessageMixin, CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    extra_context = {'selected_day': date.today()}
    success_message = 'Вы успешно зарегистрировались! Заполните информацию профиля для корректного расчета показателей'

    def form_valid(self, form):
        # Сохраняем пользователя
        response = super().form_valid(form)

        # Автоматически логиним пользователя
        login(self.request, self.object, backend='django.contrib.auth.backends.ModelBackend')

        return response

    def get_success_url(self):
        return reverse('edit_profile', kwargs={'slug': self.object.profile.slug})


class SignInView(LoginView):
    success_url = reverse_lazy('profile')
    template_name = 'accounts/login.html'
    extra_context = {'selected_day': date.today()}
    form_class = BootstrapStyledAuthenticationForm

@login_required
def profile(request):
    today = date.today()
    selected_day = request.session.get('selected_day_title', today)

    queryset = Day.objects.filter(date__gte=date.fromordinal(today.toordinal() - 365),
                                   date__lte=today, user_id=request.user.id)
    profile = request.user.profile
    days = []

    if queryset.count() < 365:
        for i in range(365, -1, -1):
            if not Day.objects.filter(date=date.fromordinal(today.toordinal()-i), user_id=request.user.id):
                Day.objects.create(date=date.fromordinal(today.toordinal()-i), user_id=request.user.id)

    print(selected_day)
    standard = Day.objects.get(date=selected_day, user=request.user.id).standard
    if standard.get('user_weight'):
        del standard['user_weight']
    for day in queryset:
        res = int(sum(getattr(day, attr)/standard[attr]*100 for attr in standard) / 4)
        if res in range(90, 111):
            color = 'mediumseagreen'
        elif res in range(80, 121):
            color = 'greenyellow'
        elif res in range(70, 131):
            color = 'yellow'
        elif res in range(60, 141):
            color = 'orange'
        else:
            color = 'red'
        days.append({'object': day, 'date': day.date, 'color': ('#f0f3f7', color)[bool(day.calories)]})


    nonempty = Day.objects.filter(calories__gt=0, user_weight__gt=0, user_id=request.user.id, date__lte=today).count()
    streak = 0
    for day in reversed(queryset):
        if day.calories > 0:
            streak += 1
        else:
            break
    max_streak = profile.max_streak
    if streak > max_streak:
        profile.max_streak = streak
        max_streak = profile.max_streak
        profile.save()


    # Получаем даты за последний год
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=364)  # 53 недели * 7 дней - 1 день

    # Собираем данные по месяцам
    current_date = start_date
    month_columns = defaultdict(list)

    for i in range(371):  # 53 недели * 7 дней
        column = i // 7  # номер столбца (0-52)
        month_columns[current_date.month].append(column)
        current_date += timedelta(days=1)

    # Формируем данные для шаблона
    months_data = []
    month_names = {
        1: 'янв', 2: 'фев', 3: 'мар', 4: 'апр', 5: 'май', 6: 'июн',
        7: 'июл', 8: 'авг', 9: 'сен', 10: 'окт', 11: 'ноя', 12: 'дек'
    }

    for month_num, columns in month_columns.items():
        if columns:
            months_data.append({
                'name': month_names[month_num],
                'start_column': min(columns) + 1,  # +1 потому что grid-column начинается с 1

            })

    if request.method == 'POST':
        if request.POST.get('action') == 'save_edit':
            profile.proteins = request.POST.get('proteins')
            profile.fats = request.POST.get('fats')
            profile.carbohydrates = request.POST.get('carbohydrates')
            profile.calories = request.POST.get('calories')
            profile.aim_weight = request.POST.get('aim_weight')
            profile.save()
            Day.objects.get(date=today, user_id=request.user.id).save()
            return redirect('profile')


    return render(request, 'accounts/profile.html', {'selected_day': selected_day,
                                                     'days': days,
                                                     'nonempty': nonempty,
                                                     'streak': streak,
                                                     'max_streak': max_streak,
                                                     'months_data': months_data,
                                                     'profile': profile,
                                                     'page_title': f'{request.user.username} - Fitness Diary'
                                                     })


@require_POST
def update_avatar(request):
    if request.FILES.get('avatar'):
        try:
            profile = request.user.profile

            # Удаляем старый файл если он существует
            if profile.avatar:
                if default_storage.exists(profile.avatar.name):
                    default_storage.delete(profile.avatar.name)

            # Получаем файл
            avatar_file = request.FILES['avatar']

            # Генерируем новое имя файла
            username = request.user.username
            file_extension = os.path.splitext(avatar_file.name)[1]
            new_filename = f"avatars/{username}{file_extension}"

            # Сохраняем файл с новым именем
            profile.avatar.save(new_filename, avatar_file, save=True)

        except Exception as e:
            messages.error(request, f'Ошибка при загрузке: {str(e)}')

    return redirect('profile')


class UpdateProfileView(UpdateView):
    model = Profile
    template_name = 'accounts/edit_profile.html'
    form_class = UpdateProfileForm
    context_object_name = 'profile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        context['selected_day'] = date.fromisoformat(self.request.session.get('selected_day', str(date.today())))
        context['page_title'] = 'Редактирование профиля - Fitness Diary'
        return context

