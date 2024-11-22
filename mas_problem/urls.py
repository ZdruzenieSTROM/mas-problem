import allauth.account.views as allauth_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from competition.views import LoginFormView, SignUpView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('competition.urls', namespace='competition')),
    
    # Allauth
    re_path(r'^accounts/confirm-email/(?P<key>[-:\w]+)/$', allauth_views.confirm_email, name='account_confirm_email'),
    path("password/reset/", allauth_views.password_reset, name="account_reset_password"),
    path(
        "password/reset/done/",
        allauth_views.password_reset_done,
        name="account_reset_password_done",
    ),
    re_path(
        r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        allauth_views.password_reset_from_key,
        name="account_reset_password_from_key",
    ),
    path(
        "password/reset/key/done/",
        allauth_views.password_reset_from_key_done,
        name="account_reset_password_from_key_done",
    ),
    path('login',LoginFormView.as_view(),name='account_login'),
    path('register',SignUpView.as_view(),name='account_signup')
]
# TODO: Not serve in production
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# else:

urlpatterns.append(
            re_path(r'^media/public/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT / 'public'})
             )
urlpatterns.append(
            re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT / 'public'})
)
handler404 = 'competition.views.view_404'
handler400 = 'competition.views.view_400'