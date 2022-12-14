from allauth.account.forms import ResetPasswordForm, ResetPasswordKeyForm
from allauth.account.utils import filter_users_by_email
from allauth.account.adapter import get_adapter
from allauth.account import app_settings
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.forms import ValidationError
from django.utils.safestring import mark_safe
from django.utils.timezone import now

from competition.models import Game, Grade


class RegisterForm(forms.Form):
    """Kos team registration form"""

    class GradeModelChoiceField(forms.ModelChoiceField):
        def label_from_instance(self, obj):
            return obj.verbose_name
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='Krstné meno*')
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='Priezvisko*')
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-control main-input'}),
        label='Email*')
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control main-input'}),
        label='Heslo*')
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control main-input'}),
        label='Zopakuj heslo*',)
    phone_number = forms.RegexField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='Telefónne číslo (nepovinné)',
        regex=r'^\+?1?\d{9,15}$', required=False)

    grade = GradeModelChoiceField(
        widget=forms.Select(attrs={'class': 'main-input'}),
        queryset=Grade.objects.all(),
        label='Kategória*',
        to_field_name='verbose_name'
    )
    school = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='Škola*'
    )
    legal_representative = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='Meno a priezvisko zákonného zástupcu*'
    )
    address = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='Adresa (údaj je nepovinný a bude použitý iba v prípade zaslania ocenenia)',
        required=False
    )
    gdpr = forms.CharField(
        widget=forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
        label="",
        help_text=mark_safe(
            '*Beriem na vedomie, že osobné údaje môjho dieťaťa budú spracovávané podľa: <a href="https://seminar.strom.sk/gdpr/" target="_blank" class="main-link">https://seminar.strom.sk/gdpr/</a>'),
    )
    game = forms.ModelChoiceField(
        queryset=Game.objects.all(), widget=forms.HiddenInput())

    def clean_password2(self):
        """Heslo a zopakované heslo sa rovnajú"""
        password1 = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if not password2:
            raise forms.ValidationError("Je potrebné potvrdiť heslo")
        if password1 != password2:
            raise forms.ValidationError("Heslá sa musia zhodovať")
        return password2

    def clean_game(self):
        game = self.cleaned_data['game']
        if game.registration_start > now() or game.registration_end < now():
            raise ValidationError('Registrácia na túto súťaž nie je aktívna')
        return game


class ChangePasswordForm(PasswordChangeForm):
    """Lokalizovaný formulár pre zmenu hesla"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = 'Staré heslo'
        self.fields['old_password'].widget = forms.PasswordInput(
            attrs={'autofocus': True, 'class': 'main-input'})
        self.fields['new_password1'].label = 'Nové heslo'
        self.fields['new_password1'].widget = forms.PasswordInput(
            attrs={'class': 'main-input'})
        self.fields['new_password2'].label = 'Nové heslo (znova)'
        self.fields['new_password2'].widget = forms.PasswordInput(
            attrs={'class': 'main-input'})

        self.error_messages = {
            "password_incorrect": "Zadané heslo bolo nesprávne",
            "password_mismatch": "Heslá sa musia zhodovať"
        }


class CustomResetPasswordForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = 'Email'
        self.fields['email'].widget.attrs['placeholder'] = 'Email'

    def clean_email(self):
        email = self.cleaned_data["email"]
        email = get_adapter().clean_email(email)
        self.users = filter_users_by_email(email, is_active=True)
        if not self.users and not app_settings.PREVENT_ENUMERATION:
            raise forms.ValidationError(
                ("Na tento email nie je registrovaný žiaden účet alebo tento email ešte nebol potvrdený.")
            )
        return self.cleaned_data["email"]


class CustomResetPasswordFromKey(ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Nové heslo'
        self.fields['password2'].label = 'Nové heslo (znova)'
        self.fields['password1'].widget.attrs['placeholder'] = 'Nové heslo'
        self.fields['password2'].widget.attrs['placeholder'] = 'Nové heslo (znova)'


class AuthForm(AuthenticationForm):
    """Lokalizovaný prihlasovací formulár"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'
        self.fields['username'].widget = forms.TextInput(
            attrs={'autofocus': True, 'class': 'main-input'})
        self.fields['password'].label = 'Heslo'
        self.fields['password'].widget = forms.PasswordInput(
            attrs={'autocomplete': 'current-password', 'class': 'main-input'})

        self.error_messages['invalid_login'] = 'Zadaný login alebo heslo bolo nesprávne.'


class EditCompetitorForm(forms.Form):
    """Form na úpravu údajov súťažiaceho"""
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='Krstné meno')
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='Priezvisko')
    phone_number = forms.RegexField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='Telefónne číslo (nepovinné)',
        regex=r'^\+?1?\d{9,15}$', required=False)

    grade = forms.ModelChoiceField(
        widget=forms.Select(attrs={'class': 'main-input'}),
        queryset=Grade.objects.all(),
        label='Kategória'
    )
    school = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='Škola'
    )
    legal_representative = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='Zákonný zástupca:'
    )
    address = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='Adresa (údaj je nepovinný a bude použitý iba v prípade zaslania ocenenia)',
        required=False
    )
