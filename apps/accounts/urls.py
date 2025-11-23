from django.contrib.auth.views import LogoutView
from django.urls import path
from .views import SignUpView, SignInView, profile, UpdateProfileView, update_avatar

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', SignInView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', profile, name='profile'),
    path('update-avatar/', update_avatar, name='update_avatar'),
    path('edit_profile/<slug:slug>/', UpdateProfileView.as_view(), name='edit_profile'),
]
