from django.urls import path

from . import views

app_name = 'competition'

urlpatterns = [
    path('registracia', views.SignUpView.as_view(), name='registration'),
    path('prihlasenie', views.LoginFormView.as_view(), name='login'),
    path('odhlasenie', views.logout_view, name='logout'),
    path('sutaz', views.GameView.as_view(), name='game'),
    path('vysledky', views.ResultView.as_view(), name='results'),
    path('zmena-hesla', views.change_password, name='change-password')
]
