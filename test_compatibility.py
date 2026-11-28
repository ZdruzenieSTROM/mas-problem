"""Regressions for the Django/allauth dependency upgrade."""
import re
from datetime import timedelta
from urllib.parse import urlsplit

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now


class AccountCompatibilityTests(TestCase):
    def test_registration_confirmation_activates_user(self):
        self.prepare_registration()
        response = self.client.post(reverse('competition' + ':registration'), self.registration)
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(email='upgrade@example.com')
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        url = re.search(r'https?://[^\s<>]+/accounts/confirm-email/[^\s<>]+', mail.outbox[0].body).group()
        response = self.client.get(urlsplit(url).path)
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(EmailAddress.objects.get(user=user).verified)

    def test_custom_password_reset_completes(self):
        user = get_user_model().objects.create_user('reset@example.com', 'reset@example.com', 'old-password')
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
        response = self.client.post(reverse('account_reset_password'), {'email': user.email})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        url = re.search(r'https?://[^\s<>]+/password/reset/[^\s<>]+', mail.outbox[0].body).group()
        response = self.client.get(urlsplit(url).path, follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(response.request['PATH_INFO'], {'password1': 'new-strong-password-2026', 'password2': 'new-strong-password-2026'})
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.check_password('new-strong-password-2026'))

    def prepare_registration(self):
        from competition.models import Game, Grade
        start = now()
        game = Game.objects.create(name='Upgrade', start=start, end=start + timedelta(hours=1), registration_start=start - timedelta(hours=1), registration_end=start + timedelta(hours=1), max_session_duration=timedelta(hours=1), price=0)
        grade = Grade.objects.create(verbose_name='Grade', shortcut='G')
        self.registration = dict(first_name='Test', last_name='User', email='upgrade@example.com', password='password', password2='password', grade=grade.verbose_name, school='School', legal_representative='Parent', gdpr='on', game=game.pk)


class CertificateCompatibilityTests(TestCase):
    def test_uploaded_certificate_pages_are_saved(self):
        from io import BytesIO
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from django.core.files.uploadedfile import SimpleUploadedFile
        from pypdf import PdfReader, PdfWriter
        from competition.models import Competitor, Game

        start = now()
        game = Game.objects.create(name='Certificates', start=start, end=start + timedelta(hours=1), registration_start=start, registration_end=start, max_session_duration=timedelta(hours=1), price=0)
        game_id = game.pk
        competitor = Competitor.objects.create(first_name='Test', last_name='User', school='School', legal_representative='Parent', game_id=game_id)
        staff = get_user_model().objects.create_user('staff', is_staff=True)
        self.client.force_login(staff)
        pdf = PdfWriter()
        pdf.add_blank_page(width=200, height=300)
        stream = BytesIO()
        pdf.write(stream)
        with TemporaryDirectory() as folder, self.settings(CERTIFICATES_ROOT=Path(folder), MEDIA_ROOT=folder):
            response = self.client.post(reverse('competition:game-admin', kwargs={'pk': game_id}), {'competitor_ids': [competitor.pk], 'filename': SimpleUploadedFile('certificates.pdf', stream.getvalue(), content_type='application/pdf')})
            self.assertEqual(response.status_code, 302)
            competitor.refresh_from_db()
            with competitor.certificate.open('rb') as saved:
                self.assertEqual(len(PdfReader(saved).pages), 1)
