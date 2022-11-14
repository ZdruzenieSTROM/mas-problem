
from django.contrib.flatpages.views import flatpage
from django.urls import path

from . import views

app_name = 'competition'

urlpatterns = [
    path('registracia', views.SignUpView.as_view(), name='registration'),
    path('prihlasenie', views.LoginFormView.as_view(), name='login'),
    path('odhlasenie', views.logout_view, name='logout'),
    path('pred-hrou/<int:pk>', views.BeforeGameView.as_view(), name='before-game'),
    path('zacat-hru/<int:pk>', views.GameReadyView.as_view(), name='game-ready'),
    path('koniec-hry/<int:pk>',
         views.GameFinishedView.as_view(), name='game-finished'),
    path('po-hre/<int:pk>', views.AfterGameView.as_view(), name='after-game'),
    path('neuhradene',views.not_paid,name='not-paid'),
    path('archiv',views.ArchiveView.as_view(),name='archive'),
#     path('statistiky/<int:pk>',views.GameStatisticsView.as_view(),name='statistics'),
    path('sutaz', views.GameView.as_view(), name='game'),
    path('vysledky/<int:pk>', views.ResultView.as_view(), name='results'),
    path('aktualne-vysledky', views.CurrentResultView.as_view(),
         name='current-results'),
    path('zmena-hesla', views.change_password, name='change-password'),
    path('profil', views.EditProfileView.as_view(), name='profile'),
    path('problem/<int:pk>',views.ProblemView.as_view(),name='problem'),
    path('', flatpage, {'url': '/pravidla/'}, name='pravidla'),
    path('diplomy/<int:pk>',views.CertificateAdministrationView.as_view(),name='certificates'),
    path('moj-diplom',view=views.CompetitorCertificateView.as_view(),name='my-certificate')
]
