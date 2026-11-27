from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import now

from competition.models import Competitor, Game, Level, Problem, Submission


class AverageCorrectSubmissionTest(TestCase):
    def setUp(self):
        start = now()
        self.game = Game.objects.create(
            name='Test', start=start, end=start + timedelta(hours=1),
            registration_start=start, registration_end=start,
            max_session_duration=timedelta(hours=1), price=0)
        level = Level.objects.create(game=self.game, order=1)
        self.problem = Problem.objects.create(level=level, text='1+1', solution='2')

    def _competitor(self):
        return Competitor.objects.create(
            first_name='A', last_name='B', school='S', game=self.game,
            legal_representative='R', started_at=now())

    def _submit(self, competitor, correct):
        Submission.objects.create(
            problem=self.problem, competitor=competitor,
            competitor_answer='2' if correct else '3',
            submitted_at=now(), correct=correct)

    def test_no_submissions(self):
        self.assertIsNone(self.problem.average_correct_submission())

    def test_only_incorrect_submissions(self):
        self._submit(self._competitor(), correct=False)
        self.assertIsNone(self.problem.average_correct_submission())

    def test_average_attempts_of_solvers(self):
        first = self._competitor()
        self._submit(first, correct=True)
        second = self._competitor()
        self._submit(second, correct=False)
        self._submit(second, correct=False)
        self._submit(second, correct=True)
        # Nevyriešil, nezapočítava sa
        self._submit(self._competitor(), correct=False)
        self.assertEqual(self.problem.average_correct_submission(), 2)
