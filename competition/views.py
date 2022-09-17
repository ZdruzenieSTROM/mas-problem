
from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db.models import Count, Max, Q
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic import DetailView, FormView, ListView

from .forms import AuthForm, ChangePasswordForm, RegisterForm
from .models import Competitor, Game, Grade, Problem, User

# Create your views here.


class SignUpView(FormView):
    """Registračný formulár"""
    form_class = RegisterForm
    next_page = reverse_lazy("competition:login")
    success_url = reverse_lazy("competition:game")
    template_name = "competition/registration.html"

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = User.objects.create_user(email, email, password)

        # Create competitor
        Competitor.objects.create(
            first_name=form.cleaned_data['first_name'],
            second_name=form.cleaned_data['second_name'],
            user=user,
            grade=form.cleaned_data['grade'],
            school=form.cleaned_data['school'],
            game=form.cleaned_data['game'],
            phno_number=form.cleaned_data['phone_number'],
            is_online=form.cleaned_data['is_online'],
            current_level=1,
            paid=False
        )
        return super().form_valid(form)


class LoginFormView(LoginView):
    """Prihlasovací formulár"""
    authentication_form = AuthForm
    next_page = reverse_lazy('competition:game')
    template_name = 'competition/login.html'


@login_required
def change_password(request):
    """Zmena hesla"""
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(
                request, 'Heslo bolo zmenené!')
            return redirect('competition:change-password')
        messages.error(request, 'Chyba pri zmene hesla')
    else:
        form = ChangePasswordForm(request.user)
    return render(request, 'competition/change_password.html', {
        'form': form
    })


@login_required
def logout_view(request):
    """Odhlásenie"""
    logout(request)
    return redirect('competition:game')


class GameView(DetailView):
    """Náhľad súťaže"""
    model = Game
    template_name = 'competition/game.html'


class ProblemView(DetailView):
    model = Problem

    def post(self):
        """Odovzdanie úlohy"""
        competitor =
        if self.can_submit(competitor):


class ResultView(DetailView):
    """Náhľad súťaže"""
    model = Game
    template_name = 'competition/results.html'
