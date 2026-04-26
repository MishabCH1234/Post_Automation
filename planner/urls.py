from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from .views import dashboard, profile, upload_plan


urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('dashboard/', dashboard, name='dashboard'),
    path('upload/', upload_plan, name='upload_plan'),
    path('profile/', profile, name='profile'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
