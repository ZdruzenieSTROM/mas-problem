from django.contrib import admin
from django_admin_listfilter_dropdown.filters import (AllValuesFieldListFilter,
                                                      DropdownFilter,
                                                      RelatedDropdownFilter)
from allauth.account.models import EmailAddress

from competition import models
from .views import email_confirmed_


# Register your models here.
@admin.register(models.Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('verbose_name', 'shortcut')


@admin.register(models.Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'start', 'end', 'registration_start',
                    'registration_end', 'results_public')
    list_filter = ('results_public',)


@admin.register(models.Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('order', 'game', 'previous_level')
    list_filter = ('game',)


@admin.register(models.Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('level', 'get_game', 'text')
    list_filter = ('level',
                   ('level__game', RelatedDropdownFilter))

    @admin.display(ordering='level__game', description='Súťaž')
    def get_game(self, obj):
        return obj.level.game


@admin.register(models.Competitor)
class CompetitorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'grade',
                    'school', 'started_at', 'user_is_active')
    list_filter = ('grade', 'game', 'user__is_active')
    search_fields = ('first_name', 'last_name')

    actions = ['activate_users']

    def user_is_active(self, obj):
        return obj.user.is_active

    @admin.action(description="Aktivovať označených súťažiacich")
    def activate_users(self, request, queryset):
        for competitor in queryset:
            email = EmailAddress.objects.get(email=competitor.user.email)
            email_confirmed_(request, email)  # Probably not ideal to call this directly but we want to go through the payment logic


@admin.register(models.Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('problem', 'competitor', 'competitor_answer', 'correct')
    list_filter = ('correct',
                   ('problem', RelatedDropdownFilter),
                   ('competitor', RelatedDropdownFilter),
                   ('problem__level', RelatedDropdownFilter),
                   ('problem__level__game', RelatedDropdownFilter))


@admin.register(models.ResultGroup)
class ResultGroupAdmin(admin.ModelAdmin):
    list_display = ('game',)


@admin.register(models.CompetitorGroup)
class CompetitorGroupAdmin(admin.ModelAdmin):
    list_display = ('game', 'start_level', 'end_level')


@admin.register(models.CompetitorGroupLevelSettings)
class CompetitorGroupLevelSettings(admin.ModelAdmin):
    list_display = ('level', 'competitor_group', 'num_to_unlock')


@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('competitor', 'payment_reference_number', 'paid')
    list_editable = ('paid',)
    list_filter = ('paid',)
    search_fields = ('payment_reference_number',
                     'competitor__first_name', 'competitor__last_name')


@admin.register(models.UTMinfo)
class UTMinfoAdmin(admin.ModelAdmin):
    list_display = ('source', 'medium', 'campaign', 'content', 'timestamp')
    list_filter = (
        ('source', AllValuesFieldListFilter),
        ('medium', DropdownFilter),
        ('campaign', DropdownFilter),
        ('content', DropdownFilter),
    )
