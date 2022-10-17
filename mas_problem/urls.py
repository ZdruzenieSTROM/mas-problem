from allauth.account.views import confirm_email
from django.contrib import admin
from django.urls import include, path, re_path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('competition.urls', namespace='competition')),
    re_path(r'^accounts/confirm-email/(?P<key>[-:\w]+)/$', confirm_email, name='account_confirm_email'),
]
handler404 = 'competition.views.view_404'