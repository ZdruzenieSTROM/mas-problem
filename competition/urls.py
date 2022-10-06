
from django.contrib.flatpages.views import flatpage
from django.urls import path

from . import views

app_name = 'competition'

urlpatterns = [
    path('registracia', views.SignUpView.as_view(), name='registration'),
    path('prihlasenie', views.LoginFormView.as_view(), name='login'),
    path('odhlasenie', views.logout_view, name='logout'),
    path('sutaz', views.GameView.as_view(), name='game'),
    path('vysledky/<int:pk>', views.ResultView.as_view(), name='results'),
    path('aktualne-vysledky', views.CurrentResultView.as_view(),
         name='current-results'),
    path('zmena-hesla', views.change_password, name='change-password'),
    path('profil', views.EditProfileView.as_view(), name='profile'),
    path('', flatpage, {'url': '/pravidla/'}, name='pravidla'),
    path('vytvor-rocnik', views.CreateCompetitionView.as_view(), name='create-game')
]
