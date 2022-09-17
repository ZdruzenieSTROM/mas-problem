from django.urls import path

from . import views

app_name = 'competition'

urlpatterns = [
    path('registracia', views.SignUpView.as_view(), name='registration')
]
