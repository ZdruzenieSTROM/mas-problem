from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.utils.timezone import now

from competition.models import Game, Grade


class RegisterForm(forms.Form):
    """Kos team registration form"""
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='Krstné meno')
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='Priezvisko')
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-control main-input'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control main-input'}),
        label='Heslo')
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control main-input'}),
        label='Zopakuj heslo',)
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
    game = forms.HiddenInput()

    def clean_password2(self):
        """Heslo a zopakované heslo sa rovnajú"""
        password1 = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if not password2:
            raise forms.ValidationError("Musíte potvrdiť svoje heslo")
        if password1 != password2:
            raise forms.ValidationError("Heslá sa musia zhodovať")
        return password2


class ChangePasswordForm(PasswordChangeForm):
    """Lokalizovaný formulár pre zmenu hesla"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = 'Staré heslo'
        self.fields['old_password'].widget = forms.PasswordInput(
            attrs={'autofocus': True, 'class': 'main-input'})
        self.fields['new_password1'].label = 'Zadajte nové heslo'
        self.fields['new_password1'].widget = forms.PasswordInput(
            attrs={'autofocus': True, 'class': 'main-input'})
        self.fields['new_password2'].label = 'Zadajte znova nové heslo'
        self.fields['new_password2'].widget = forms.PasswordInput(
            attrs={'autofocus': True, 'class': 'main-input'})

        self.error_messages['password_incorrect'] = 'Staré heslo bolo zadané nesprávne. Zadajte heslo znovu.'
        self.error_messages['password_mismatch'] = 'Heslá sa musia zhodovať'


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
    """Form na úpravu tímových údajov"""
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


class UploadFileForm(forms.Form):
    name = forms.CharField(max_length=50, label='Názov ročníka')
    file = forms.FileField(
        attrs={'class': 'form-control main-input'},
        label='Zdroják brožúrky'
    )
    start = forms.DateTimeField()
    end = forms.DateTimeField()
    registration_start = forms.DateTimeField()
    registration_end = forms.DateTimeField()
    max_session_duration = forms.DurationField()
