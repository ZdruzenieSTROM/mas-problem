from datetime import timedelta

import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, User
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.timezone import now

from competition.models import (Competitor, CompetitorGroup,
                                CompetitorGroupLevelSettings, Game, Grade,
                                Level, Problem, Submission)


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


class ProtectedCertificateTest(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        start = now()
        game = Game.objects.create(
            name='Test', start=start, end=start + timedelta(hours=1),
            registration_start=start, registration_end=start,
            max_session_duration=timedelta(hours=1), price=0)
        self.owner = User.objects.create_user('owner', password='x')
        self.game = game
        self.competitor = Competitor.objects.create(
            user=self.owner, first_name='A', last_name='B', school='S',
            game=game, legal_representative='R')
        self.competitor.certificate.save('diplom.pdf', ContentFile(b'%PDF-test'))
        self.url = self.competitor.certificate.url

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_other_user_forbidden(self):
        User.objects.create_user('other', password='x')
        self.client.login(username='other', password='x')
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_owner_can_download(self):
        self.client.login(username='owner', password='x')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'%PDF-test')

    def test_staff_with_permission_can_download(self):
        staff = User.objects.create_user('staff', password='x', is_staff=True)
        staff.user_permissions.add(
            Permission.objects.get(codename='view_competitor'))
        self.client.login(username='staff', password='x')
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_unknown_certificate_not_served(self):
        self.client.login(username='owner', password='x')
        # 404 handler projektu presmeruje na pravidlá
        response = self.client.get('/media/diplomy/neexistuje.pdf')
        self.assertRedirects(response, reverse('competition:pravidla'),
                             fetch_redirect_response=False)

    def test_my_certificate_redirects_to_protected_url(self):
        self.client.login(username='owner', password='x')
        response = self.client.get(
            reverse('competition:my-certificate', kwargs={'pk': self.game.pk}))
        self.assertRedirects(response, self.url, fetch_redirect_response=False)

    def test_my_certificate_without_certificate(self):
        self.competitor.certificate = None
        self.competitor.save()
        self.client.login(username='owner', password='x')
        response = self.client.get(
            reverse('competition:my-certificate', kwargs={'pk': self.game.pk}))
        self.assertRedirects(
            response, reverse('competition:after-game', kwargs={'pk': self.game.pk}),
            fetch_redirect_response=False)

    def test_my_certificate_without_competitor(self):
        User.objects.create_user('other', password='x')
        self.client.login(username='other', password='x')
        response = self.client.get(
            reverse('competition:my-certificate', kwargs={'pk': self.game.pk}))
        self.assertRedirects(
            response, reverse('competition:after-game', kwargs={'pk': self.game.pk}),
            fetch_redirect_response=False)


IMAGE_TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=IMAGE_TEMP_MEDIA)
class ProblemImageAccessTest(TestCase):
    """Obrázky úloh nesmú byť dostupné pred začiatkom hry (#129)"""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(IMAGE_TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.game = Game.objects.create(
            name='Test', start=now() + timedelta(days=1), end=now() + timedelta(days=2),
            registration_start=now() - timedelta(days=1), registration_end=now() + timedelta(days=1),
            max_session_duration=timedelta(hours=2), price=0)
        self.level1 = Level.objects.create(game=self.game, order=1)
        self.level2 = Level.objects.create(game=self.game, order=2, previous_level=self.level1)
        grade = Grade.objects.create(verbose_name='Prvý', shortcut='1')
        self.group = group = CompetitorGroup.objects.create(
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

    def test_level_outside_group_range(self):
        """Prvá úroveň pod začiatočnou úrovňou skupiny nie je dostupná (review PR #176)"""
        self.group.start_level = self.level2
        self.group.save()
        self._start_game()
        self.competitor.started_at = now()
        self.competitor.save()
        self.client.force_login(self.user)
        self._assert_denied(self.problem1)
        self.assertEqual(self._get(self.problem2).status_code, 200)

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
