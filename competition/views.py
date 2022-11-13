
from datetime import datetime

from allauth.account.models import EmailAddress
from allauth.account.signals import email_confirmed
from allauth.account.utils import send_email_confirmation
from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db import IntegrityError
from django.db.models import (Avg, Count, DecimalField, F, FloatField, Max,
                              OuterRef, Q, Subquery)
from django.db.models.functions import Cast
from django.dispatch import receiver
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from django.views.generic import DetailView, FormView, ListView

from .forms import (AuthForm, ChangePasswordForm, EditCompetitorForm,
                    RegisterForm)
from .models import (Competitor, CompetitorGroup, Game, Level, Payment,
                     Problem, Submission, User)


def view_404(request, exception=None):  # pylint: disable=unused-argument
    """Presmerovanie 404 na homepage"""
    return redirect('competition:pravidla')


@receiver(email_confirmed)  # Signal sent to activate user upon confirmation
def email_confirmed_(request, email_address, **kwargs):
    user = User.objects.get(email=email_address.email)
    user.is_active = True
    user.save()
    payment = Payment.objects.create(
        amount=user.competitor.game.price, competitor=user.competitor)
    payment.send_invoice()


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
            user.is_active = False
            user.save()
            EmailAddress.objects.create(
                user=user, email=email, primary=True, verified=False)
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
            phone_number=form.cleaned_data['phone_number']
        )
        send_email_confirmation(self.request, user, True)

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
        context['payment'] = (
            self.request.user.competitor.payment
            if hasattr(self.request.user, 'competitor')
            and hasattr(self.request.user.competitor, 'payment') else False
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
                request, 'Heslo bolo zmenené.')
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
        if self.object.is_active() and not competitor.started() and competitor.paid:
            response = super().get(request, *args, **kwargs)
            return response
        return game_redirect(self.object, competitor)

    def post(self, request, *args, **kwargs):
        if not self.request.user.competitor.started():
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
        competitor = self.request.user.competitor
        group = CompetitorGroup.objects.filter(
            game=competitor.game, grades=competitor.grade).get()
        context['levels'] = Level.objects.filter(
            game=self.object,
            order__gte=group.start_level.order,
            order__lte=group.end_level.order
        ).order_by('order')
        for level in context['levels']:
            level.problems_with_submissions = []
            for problem in level.problems.all():
                problem.competitor_submissions = problem.submission_set.filter(
                    competitor=competitor).order_by('-submitted_at')
                level.problems_with_submissions.append(problem)
        context['competitor'] = competitor
        if 'level' in self.request.GET:
            context['show_level'] = Level.objects.get(
                pk=int(self.request.GET['level']))
        else:
            context['show_level'] = context['levels'][0]
        # TODO: Naming convension
        context['endDateTimeString'] = (competitor.started_at +
                                        competitor.game.max_session_duration).isoformat()
        return context

@login_required
def not_paid(request):
    return render(request,'competition/not_paid.html')

# This should probably be defined in another file
def game_redirect(game, competitor):
    if not competitor.paid:
        return redirect('competition:not-paid')
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

    def post(self, request, *args, **kwargs):
        """Odovzdanie úlohy"""
        competitor = self.request.user.competitor
        self.object = self.get_object()
        if self.object.can_submit(competitor):
            answer = self.request.POST['answer']

            Submission.objects.create(
                problem=self.object,
                competitor=competitor,
                competitor_answer=answer,
                submitted_at=now(),
                correct=self.object.check_answer(answer)
            )
        return redirect(reverse('competition:game')+f'?level={self.object.level.pk}')


class UploadGameView():
    pass

# class GameStatisticsView(DetailView):
#     """Štatistika hry"""
#     model = Game
#     template_name = 'competition/game_statistics.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['problems'] = Problem.objects.filter(
#             level__game=self.object
#         ).annotate(
#             num_correctly_submitted=Count('submissions',filter=Q(submissions__correct=True)),
#             average_time=Count('submissions',filter=Q(submissions__correct=True))/Count('submissions')

#         )
#         context['grades'] = Competitor.objects.filter(started_at__isnull=False).values('grade').annotate(
#             correct=Count('submissions',filter=Q(submissions__correct=True),output_filed=FloatField()),
#             competitors=Count('pk',output_filed=FloatField())
#         )
#         return context

class ArchiveView(ListView):
    model=Game
    template_name='competition/archive.html'
    context_object_name = 'games'
    queryset = Game.objects.filter(results_public=True).order_by('-end')

class ResultView(DetailView):
    """Náhľad súťaže"""
    model = Game
    template_name = 'competition/results.html'

    def add_places(self, results):
        current_place = 1
        previous_last_correct_submission = None
        results_list = []
        for i, result_row in enumerate(results):
            if previous_last_correct_submission != result_row.last_correct_submission:
                current_place = i+1
                previous_last_correct_submission = result_row.last_correct_submission
            result_row.place = current_place
            results_list.append(result_row)
        return results_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['games'] = Game.objects.all()
        if self.object.start < now() and not self.object.results_public:
            return context
        if self.object.pdf_results:
            context['pdf_results'] = self.object.pdf_results
            return context
        result_groups = self.object.result_groups.all()
        results = []
        for result_group in result_groups:
            result = self.object.competitor_set.filter(
                    grade__in=result_group.grades.all(), user__is_active=True
            ).annotate(
                solved_problems=Count(
                    'submission', filter=Q(submission__correct=True)),
                max_level=Subquery(
                    Submission.objects.filter(competitor=OuterRef('pk'), correct=True).order_by(
                        '-problem__level__order').values('problem__level__order')[:1]
                ),
                last_correct_submission=(Max(
                    'submission__submitted_at', filter=Q(submission__correct=True)) - F('started_at'))
            ).order_by('-max_level', '-solved_problems', 'last_correct_submission', 'grade')

            results.append(
                {
                    'name': result_group.name,
                    'results': self.add_places(result)
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
