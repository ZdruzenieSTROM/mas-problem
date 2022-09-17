from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.fields import BooleanField

# Create your models here.

User = get_user_model()  # Neviem ci bude stacit django USer model pr9padne si ho uprav


class Grade(models.Model):
    """Školský ročník"""
    class Meta:
        verbose_name = 'Školský ročník'
        verbose_name_plural = 'Školské ročníky'

    verbose_name = models.CharField(max_length=50)
    shortcut = models.CharField(max_length=5)


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


class Level(models.Model):
    """úroveň príkladov"""
    class Meta:
        verbose_name = 'Úroveň'
        verbose_name_plural = 'Úrovne'

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    order = models.IntegerField()
    min_solved_to_unlock = models.IntegerField()
    is_starting_level_for_grades = models.ManyToManyField(Grade, blank=True)
    previous_level = models.ForeignKey(
        'Level', on_delete=models.SET_NULL, null=True, blank=True, related_name='levels')

    def unlocked_for_team(team):
        """Vráti či tím má odomknutý level"""
        return True


class Competitor(models.Model):
    """Súťažiaci"""
    class Meta:
        verbose_name = 'Súťažiaci'
        verbose_name_plural = 'Súťažiaci'

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # Nechajme zatial ako text, časom prepojíme asi v backendom stránky
    first_name = models.CharField(max_length=64)
    second_name = models.CharField(max_length=64)
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
    paid = BooleanField()


class Problem(models.Model):
    """Úloha"""
    class Meta:
        verbose_name = 'Úloha'
        verbose_name_plural = 'Úlohy'

    level = models.ForeignKey(
        Level, on_delete=models.CASCADE, related_name='problems')
    text = models.TextField()
    solution = models.CharField(max_length=25)

    def correctly_submitted(self, competitor: Competitor):
        """Vráti či tím správne odovzdal daný príklad"""
        pass

    def get_timeout(self, competitor: Competitor):
        """Return timeout"""


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
