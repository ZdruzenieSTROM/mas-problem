
from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db import IntegrityError
from django.db.models import Count, Max, Q
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from django.views.generic import DetailView, FormView, ListView, UpdateView

from .forms import (AuthForm, ChangePasswordForm, EditCompetitorForm,
                    RegisterForm)
from .models import (Competitor, CompetitorGroup, Game, Grade, Level, Problem,
                     Submission, User)

# Create your views here.


class SignUpView(FormView):
    """Registračný formulár"""
    form_class = RegisterForm
    next_page = reverse_lazy("competition:login")
    success_url = reverse_lazy("competition:login")
    template_name = "competition/registration.html"

    def get_initial(self):
        initial_data = super().get_initial()
        initial_data['game'] = Game.objects.filter(
            registration_start__lte=now(), registration_end__gte=now()).get()
        return initial_data

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        user = User.objects.create_user(email, email, password)
        # TODO: Get school from hidden input
        game = Game.objects.filter(
            registration_start__lte=now(), registration_end__gte=now()).get()

        # Create competitor
        Competitor.objects.create(
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            user=user,
            grade=form.cleaned_data['grade'],
            school=form.cleaned_data['school'],
            game=game,
            phone_number=form.cleaned_data['phone_number'],
            current_level=CompetitorGroup.objects.filter(
                game=game, grades=form.cleaned_data['grade']).get().start_level,
            paid=False
        )
        return super().form_valid(form)


class LoginFormView(LoginView):
    """Prihlasovací formulár"""
    authentication_form = AuthForm
    next_page = reverse_lazy('competition:game')
    template_name = 'competition/login.html'


class EditProfileView(LoginRequiredMixin, FormView):
    form_class = EditCompetitorForm
    model = Competitor
    template_name = 'competition/change_profile.html'
    success_url = reverse_lazy('competition:profile')

    def get_initial(self):

        initial = super().get_initial()
        if not hasattr(self.request.user, 'competitor'):
            return initial
        competitor = self.request.user.competitor
        initial['first_name'] = competitor.first_name
        initial['last_name'] = competitor.last_name
        initial['grade'] = competitor.grade
        initial['school'] = competitor.school
        initial['phone_number'] = competitor.phone_number
        return initial

    def form_valid(self, form):
        if hasattr(self.request.user, 'competitor'):
            competitor = self.request.user.competitor
            competitor.first_name = form.cleaned_data['first_name']
            competitor.last_name = form.cleaned_data['last_name']
            competitor.grade = form.cleaned_data['grade']
            competitor.school = form.cleaned_data['school']
            competitor.phone_number = form.cleaned_data['phone_number']
            competitor.save()
        return super().form_valid(form)


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
    return redirect('competition:home')


class GameView(DetailView, LoginRequiredMixin):
    """Náhľad súťaže"""
    model = Game
    template_name = 'competition/game.html'
    login_url = reverse_lazy('competition:login')
    context_object_name = 'game'

    def get_object(self):
        return self.request.user.competitor.game

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = CompetitorGroup.objects.filter(
            game=self.request.user.competitor.game, grades=self.request.user.competitor.grade).get()
        context['levels'] = Level.objects.filter(
            game=self.object,
            order__gte=group.start_level.order,
            order__lte=group.end_level.order
        ).order_by('order')
        context['competitor'] = self.request.user.competitor
        return context


class ProblemView(DetailView, LoginRequiredMixin):
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

        result_groups = self.object.result_groups.all()
        results = []
        for result_group in result_groups:
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
        context['results'] = results
        print(result)
        return context


class CurrentResultView(ResultView):
    def dispatch(self, request, *args, **kwargs):
        return redirect(
            reverse(
                'competition:results',
                kwargs={'pk': Game.objects.order_by('-start').first().pk})
        )
