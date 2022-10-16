from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('competition.urls', namespace='competition')),
    path('accounts/', include('allauth.urls')),
]
