
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db import IntegrityError
from django.db.models import Count, Max, Q
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.generic import DetailView, FormView

from competition.parsers import MasProblemCurrentParser

from .forms import (AuthForm, ChangePasswordForm, CreateCompetitionForm,
                    EditCompetitorForm, RegisterForm)
from .models import (Competitor, CompetitorGroup, Game, Level, Payment,
                     Problem, Submission, User)

# Create your views here.


class SignUpView(FormView):
    """Registračný formulár"""
    form_class = RegisterForm
    next_page = reverse_lazy("competition:login")
    success_url = reverse_lazy("competition:login")
    template_name = "competition/registration.html"

    def get_initial(self):
        initial_data = super().get_initial()
        try:
            initial_data['game'] = Game.objects.filter(
                registration_start__lte=now(), registration_end__gte=now()).get()
        except Game.DoesNotExist:
            pass
        return initial_data

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        try:
            user = User.objects.create_user(email, email, password)
        except IntegrityError:
            messages.error(
                self.request, 'Užívateľ s týmto emailom už existuje')
            return super().form_invalid(form)

        # Create competitor
        competitor = Competitor.objects.create(
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            user=user,
            grade=form.cleaned_data['grade'],
            school=form.cleaned_data['school'],
            game=form.cleaned_data['game'],
            address=form.cleaned_data['address'],
            legal_representative=form.cleaned_data['legal_representative'],
            phone_number=form.cleaned_data['phone_number'],
            current_level=CompetitorGroup.objects.filter(
                game=form.cleaned_data['game'], grades=form.cleaned_data['grade']).get().start_level,
            paid=False
        )
        payment = Payment.objects.create(
            amount=form.cleaned_data['game'].price, competitor=competitor)
        payment.create_invoice()
        payment.send_invoice()
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
        initial['legal_representative'] = competitor.legal_representative
        initial['address'] = competitor.address
        return initial

    def form_valid(self, form):
        if hasattr(self.request.user, 'competitor'):
            competitor = self.request.user.competitor
            competitor.first_name = form.cleaned_data['first_name']
            competitor.last_name = form.cleaned_data['last_name']
            competitor.grade = form.cleaned_data['grade']
            competitor.school = form.cleaned_data['school']
            competitor.phone_number = form.cleaned_data['phone_number']
            competitor.legal_representative = form.cleaned_data['legal_representative']
            competitor.address = form.cleaned_data['address']
            competitor.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['paid'] = (
            self.request.user.competitor.paid
            if hasattr(self.request.user, 'competitor') else False
        )
        return context


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
    return redirect('competition:login')


class BeforeGameView(LoginRequiredMixin, DetailView):
    """Zobrazí sa súťažiacemu pred začiatkom hry"""
    model = Game
    template_name = 'competition/before_game.html'
    context_object_name = 'game'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        competitor = self.request.user.competitor
        if now() < self.object.start:
            response = super().get(request, *args, **kwargs)
            return response
        return game_redirect(self.object, competitor)


class AfterGameView(LoginRequiredMixin, DetailView):
    """Zobrazí sa súťažiacemu po konci hry"""
    model = Game
    template_name = 'competition/after_game.html'
    context_object_name = 'game'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        competitor = self.request.user.competitor
        if self.object.end < now():
            response = super().get(request, *args, **kwargs)
            return response
        return game_redirect(self.object, competitor)


class GameReadyView(LoginRequiredMixin, DetailView):
    """Súťaž už začala ale užívateľ si ju ešte nespustil"""
    model = Game
    template_name = 'competition/game_ready.html'
    context_object_name = 'game'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        competitor = self.request.user.competitor
        if self.object.is_active() and not competitor.started():
            response = super().get(request, *args, **kwargs)
            return response
        return game_redirect(self.object, competitor)

    def post(self, request, *args, **kwargs):
        print('a')
        self.request.user.competitor.start()
        return game_redirect(self.get_object(), self.request.user.competitor)


class GameFinishedView(LoginRequiredMixin, DetailView):
    """Súťaž ešte beží ale užívateľ už dosúťažil"""
    model = Game
    template_name = 'competition/game_finished.html'
    context_object_name = 'game'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        competitor = self.request.user.competitor
        if self.object.is_active() and competitor.finished():
            response = super().get(request, *args, **kwargs)
            return response
        return game_redirect(self.object, competitor)


class GameView(LoginRequiredMixin, DetailView):
    """Náhľad súťaže"""
    model = Game
    template_name = 'competition/game.html'
    context_object_name = 'game'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        competitor = self.request.user.competitor
        if self.object.is_active() and competitor.started() and not competitor.finished():
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)
        return game_redirect(self.object, competitor)

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


# This should probably be defined in another file
def game_redirect(game, competitor):
    if now() < game.start:
        # Pred začatím hry
        return redirect('competition:before-game', pk=game.pk)
    if game.end < now():
        # Po konci hry
        return redirect('competition:after-game', pk=game.pk)
    if not competitor.started():
        # Súťažiaci ešte nezačal
        return redirect('competition:game-ready', pk=game.pk)
    if competitor.finished():
        # Súťažiaci už dosúťažil
        return redirect('competition:game-finished', pk=game.pk)
    # Hra prebieha
    return redirect('competition:game')


class ProblemView(LoginRequiredMixin, DetailView):
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
        if self.object.start < now() and self.object.end > now():
            return context
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
        return context


class CurrentResultView(ResultView):
    def dispatch(self, request, *args, **kwargs):
        return redirect(
            reverse(
                'competition:results',
                kwargs={'pk': Game.objects.order_by('-start').first().pk})
        )


@method_decorator(staff_member_required, name='dispatch')
class CreateCompetitionView(FormView):
    form_class = CreateCompetitionForm
    template_name = 'competition/create_game.html'

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        file = request.FILES.get('file')
        if form.is_valid():
            print(file)
            # MasProblemCurrentParser()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
