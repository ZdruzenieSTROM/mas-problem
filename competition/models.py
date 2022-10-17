from tabnanny import verbose

from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.fields import BooleanField
from django.template.loader import render_to_string
from django.utils.timezone import now

from competition.invoice_handler import InvoiceItem, InvoiceSession

# Create your models here.

User = get_user_model()  # Neviem ci bude stacit django USer model pr9padne si ho uprav


class Grade(models.Model):
    """Školský ročník"""
    class Meta:
        verbose_name = 'Školský ročník'
        verbose_name_plural = 'Školské ročníky'

    verbose_name = models.CharField(max_length=50)
    shortcut = models.CharField(max_length=5)

    def __str__(self):
        return self.shortcut


class Game(models.Model):
    """Hra"""
    class Meta:
        verbose_name = 'Súťaž'
        verbose_name_plural = 'Súťaže'

    name = models.CharField(max_length=128)
    start = models.DateTimeField()
    end = models.DateTimeField()
    registration_start = models.DateTimeField()
    registration_end = models.DateTimeField()
    max_session_duration = models.DurationField()
    results_public = models.BooleanField(default=False)
    price = models.DecimalField(
        verbose_name='Účastnícky poplatok', decimal_places=2, max_digits=5)

    def create_game(levels):
        game = Game.objects.create(
            name='TO DO',
            results_public=False
        )
        previous_level = None
        for i, level in enumerate(levels):
            previous_level = Level.objects.create(
                game=game,
                order=i+1,
                previous_level=previous_level
            )
            for problem, solution in zip(level['problems'], level['results']):
                Problem.objects.create(
                    level=previous_level,
                    text=problem,
                    solution=solution
                )

        return game

    def get_finish_time(self, competitor):
        """Čas kedy musí hráč hru ukončiť"""
        return min(competitor.started_at+self.max_session_duration, self.end)  # TODO: what if started_at is None

    def start_or_continue_game(self, competitor):
        if competitor.started_at is not None:
            competitor.started_at = now()

    def is_active(self):
        return self.start <= now() < self.end

    def __str__(self):
        return self.name


class Level(models.Model):
    """úroveň príkladov"""
    class Meta:
        verbose_name = 'Úroveň'
        verbose_name_plural = 'Úrovne'

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    order = models.IntegerField()
    previous_level = models.ForeignKey(
        'Level', on_delete=models.SET_NULL, null=True, blank=True, related_name='levels')

    def unlocked(self, competitor):
        """Vráti či súťažiaci má odomknutý level"""
        if self.previous_level is None:
            return self.game == competitor.game
        level_settings = CompetitorGroupLevelSettings.get_settings(
            competitor, self)
        return (
            self.previous_level.number_of_solved(
                competitor) > level_settings.num_to_unlock
            and self.game == competitor.game
        )

    def number_of_solved(self, competitor):
        """Počet vyriešených úloh"""
        return Problem.objects.filter(
            level=self,
            submission__competitor=competitor,
            submission__correct=True).count()

    def level_letter(self):
        """Converts order to letter"""
        return chr(ord('A')-1+self.order)

    def __str__(self):
        return f'{self.game} - Úroveň {self.level_letter()}.'


class Problem(models.Model):
    """Úloha"""
    class Meta:
        verbose_name = 'Úloha'
        verbose_name_plural = 'Úlohy'

    level = models.ForeignKey(
        Level, on_delete=models.CASCADE, related_name='problems')
    text = models.TextField()
    solution = models.CharField(max_length=25)

    def correctly_submitted(self, competitor):
        """Vráti či súťažiaci správne odovzdal daný príklad"""
        return Submission.objects.filter(correct=True).exist()

    def can_submit(self, competitor):
        return self.level.unlocked(competitor)

    def get_timeout(self, competitor):
        """Return timeout"""
        return

    def __str__(self):
        return self.text


class Competitor(models.Model):
    """Súťažiaci"""
    class Meta:
        verbose_name = 'Súťažiaci'
        verbose_name_plural = 'Súťažiaci'

    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, related_name='competitor')
    # Nechajme zatial ako text, časom prepojíme asi v backendom stránky
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    school = models.CharField(max_length=128)
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=17, blank=True)  # Validators should be a list
    current_level = models.ForeignKey(
        Level, on_delete=models.CASCADE, null=True)
    started_at = models.DateTimeField(null=True)
    address = models.CharField(max_length=256, blank=True)
    legal_representative = models.CharField(max_length=128)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def start(self):
        self.started_at = now()
        self.save()

    def started(self):
        return self.started_at is not None

    def finished(self):
        return self.game.is_active() and self.started() and self.game.get_finish_time(self) < now()

    def to_invoice_dict(self):
        return {
            'o_name': f'{self.first_name} {self.last_name}',
            'o_email': self.user.email,
        }


class Submission(models.Model):
    """Odvozdanie riešenia"""
    class Meta:
        verbose_name = 'Odpoveď na úlohu'
        verbose_name_plural = 'Odpovede na úlohy'

    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE)
    competitor_answer = models.CharField(max_length=25)
    submitted_at = models.DateTimeField()
    correct = models.BooleanField()


class ResultGroup(models.Model):
    """Skupina pre tvorbu výsledkov. 
    Výsledkovky budú zoskupená opodľa týchto skupín ročníkov"""
    class Meta:
        verbose_name = 'výsledkové skupiny'

    name = models.CharField(max_length=128)
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name='result_groups')
    grades = models.ManyToManyField(Grade)


class CompetitorGroup(models.Model):
    """Skupina ročníkov pre nastavenie hry"""
    class Meta:
        verbose_name = 'Skupina ročníkov pre hru'

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    grades = models.ManyToManyField(Grade)
    start_level = models.ForeignKey(
        Level, on_delete=models.CASCADE, related_name='groups_starting')
    end_level = models.ForeignKey(
        Level, on_delete=models.CASCADE, related_name='groups_ending')

    @classmethod
    def get_group_from_competitor(cls, competitor: Competitor):
        return cls.objects.get(grade=competitor.grade)


class CompetitorGroupLevelSettings(models.Model):
    """Nastavenie postupových podmienok z levelu"""
    class Meta:
        verbose_name = 'postupové podmienky'

    level = models.ForeignKey(
        Level, on_delete=models.CASCADE, related_name='setting_groups')
    competitor_group = models.ForeignKey(
        CompetitorGroup, on_delete=models.CASCADE, related_name='setting_groups')
    num_to_unlock = models.PositiveSmallIntegerField()

    @classmethod
    def get_settings(cls, competitor, level):
        return cls.objects.get(grade=competitor.grade, level=level)


class Payment(models.Model):
    """Platby"""
    class Meta:
        verbose_name = 'platba'
        verbose_name_plural = 'platby'

    amount = models.DecimalField(
        verbose_name='suma', decimal_places=2, max_digits=5)
    competitor = models.OneToOneField(Competitor, on_delete=models.CASCADE)
    invoice_code = models.CharField(max_length=100, null=True, blank=True)
    payment_reference_number = models.CharField(max_length=32, null=True, blank=True)
    paid = models.BooleanField(default=False)

    def create_invoice(self):
        """Vytvorenie faktúry"""
        invoice_session = InvoiceSession()
        game = self.competitor.game
        item = InvoiceItem(
            f'Účastnícky poplatok za {game.name}',
            'ks', game.price)
        self.invoice_code, self.payment_reference_number = invoice_session.create_invoice(
            self.competitor.to_invoice_dict(),
            {item: 1},
            game.start
        )
        self.save()

    def send_invoice(self):
        """Zaslanie informácií k platbe"""
        if self.invoice_code is None:
            self.create_invoice()
        invoice_session = InvoiceSession()
        invoice_content = invoice_session.get_invoice(self.invoice_code)
        mail = EmailMessage(
            subject=f'{self.competitor.game.name} - Informácie k platbe',
            body=render_to_string('competition/invoice_email.html', {
                                  'competitor': self.competitor, 'game': self.competitor.game}),
            from_email='noreply@strom.sk',
            to=[self.competitor.user.email],
        )
        mail.attach('faktura.pdf', invoice_content,
                    mimetype='application/pdf')
        mail.send()
