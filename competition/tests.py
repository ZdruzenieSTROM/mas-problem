import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.timezone import now

from .models import (Competitor, CompetitorGroup, CompetitorGroupLevelSettings,
                     Game, Grade, Level, Problem)

TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ProblemImageAccessTest(TestCase):
    """Obrázky úloh nesmú byť dostupné pred začiatkom hry (#129)"""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.game = Game.objects.create(
            name='Test', start=now() + timedelta(days=1), end=now() + timedelta(days=2),
            registration_start=now() - timedelta(days=1), registration_end=now() + timedelta(days=1),
            max_session_duration=timedelta(hours=2), price=0)
        self.level1 = Level.objects.create(game=self.game, order=1)
        self.level2 = Level.objects.create(game=self.game, order=2, previous_level=self.level1)
        grade = Grade.objects.create(verbose_name='Prvý', shortcut='1')
        group = CompetitorGroup.objects.create(
            game=self.game, start_level=self.level1, end_level=self.level2)
        group.grades.add(grade)
        for level in (self.level1, self.level2):
            CompetitorGroupLevelSettings.objects.create(
                level=level, competitor_group=group, num_to_unlock=1)

        self.problem1 = self._problem(self.level1)
        self.problem2 = self._problem(self.level2)

        User = get_user_model()
        self.user = User.objects.create_user('competitor', password='x')
        self.competitor = Competitor.objects.create(
            user=self.user, game=self.game, grade=grade)
        self.staff = User.objects.create_user('staff', password='x', is_staff=True)

    def _problem(self, level):
        problem = Problem.objects.create(level=level, text='Zadanie', solution='1')
        problem.image.save('obrazok.png', ContentFile(b'png'))
        return problem

    def _get(self, problem):
        return self.client.get(reverse('competition:problem-image', args=[problem.pk]))

    def _assert_denied(self, problem):
        # handler404 presmeruje na úvodnú stránku
        self.assertIn(self._get(problem).status_code, (302, 404))

    def _start_game(self):
        self.game.start = now() - timedelta(hours=1)
        self.game.save()

    def test_image_not_stored_in_public_dir(self):
        self.assertTrue(self.problem1.image.name.startswith('problems/'))

    def test_anonymous_before_game(self):
        self._assert_denied(self.problem1)

    def test_competitor_before_game(self):
        self.client.force_login(self.user)
        self._assert_denied(self.problem1)

    def test_competitor_not_started(self):
        self._start_game()
        self.client.force_login(self.user)
        self._assert_denied(self.problem1)

    def test_competitor_during_game(self):
        self._start_game()
        self.competitor.started_at = now()
        self.competitor.save()
        self.client.force_login(self.user)
        response = self._get(self.problem1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'png')
        # Zamknutý level
        self._assert_denied(self.problem2)

    def test_staff_before_game(self):
        self.client.force_login(self.staff)
        self.assertEqual(self._get(self.problem2).status_code, 200)

    def test_anyone_after_game(self):
        self.game.start = now() - timedelta(days=2)
        self.game.end = now() - timedelta(days=1)
        self.game.save()
        self.assertEqual(self._get(self.problem2).status_code, 200)

    def test_public_media_url_does_not_serve_image(self):
        response = self.client.get('/' + 'media/' + self.problem1.image.name)
        self.assertNotEqual(response.status_code, 200)
