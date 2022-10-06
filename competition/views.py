
from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db.models import Count, Max, Q
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from django.views.generic import DetailView, FormView, ListView

from .forms import (AuthForm, ChangePasswordForm, CreateCompetitionForm,
                    RegisterForm)
from .models import Competitor, Game, Grade, Level, Problem, Submission, User

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
            last_name=form.cleaned_data['last_name'],
            user=user,
            grade=form.cleaned_data['grade'],
            school=form.cleaned_data['school'],
            game=form.cleaned_data['game'],
            phone_number=form.cleaned_data['phone_number'],
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
        competitor = self.request.user.competitor
        if not self.can_submit(competitor):
            raise
        answer = ''
        Submission.objects.create(
            problem=self.object,
            competitor=competitor,
            competitor_answer=answer,
            submitted_at=now(),
            correct=self.object.check_answer(answer)
        )
        if Level.objects.get(previous_level=self.object.level).unlocked(competitor):
            competitor.current_level = max(
                competitor.current_level, self.object.level+1)
        return redirect('competition:game')


class UploadGameView():
    pass


class ResultView(DetailView):
    """Náhľad súťaže"""
    model = Game
    template_name = 'competition/results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        result_groups = self.object.result_groups
        results = []
        for result_group in result_groups.all():
            result = self.object.competitor_set.filter(grade__in=result_group.grades.all()).annotate(
                solved_problems=Count(
                    'submission', filter=Q(submission__correct=True)),

                last_correct_submission=Max(
                    'submission__submitted_at', filter=Q(submission__correct=True))
            ).order_by('-current_level', 'solved_problems', 'last_correct_submission')
            results.append(
                {
                    'name': result_group.name,
                    'results': result
                }
            )
        context['results'] = result
        return context


class CurrentResultView(ResultView):
    def dispatch(self, request, *args, **kwargs):
        return redirect(
            reverse(
                'competition:results',
                kwargs={'pk': Game.objects.order_by('-start').first().pk})
        )


class CreateCompetitionView(FormView):
    form_class = CreateCompetitionForm
    template_name = ''

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('file_field')
        if form.is_valid():
            for f in files:
                pass  # Do something with each file.
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
