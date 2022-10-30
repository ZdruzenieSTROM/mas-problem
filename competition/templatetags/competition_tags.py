from django import template
from django.utils.timezone import now

from competition.models import Level

register = template.Library()


@register.simple_tag
def number_of_solved(level, competitor):
    return level.number_of_solved(competitor)

@register.simple_tag
def can_submit(problem, competitor):
    return problem.can_submit(competitor)

@register.simple_tag
def level_unlocked(level,competitor):
    return level.unlocked(competitor)

@register.simple_tag
def get_timeout(problem,competitor):
    return now() + problem.get_timeout(competitor)

@register.filter
def to_letter(level_number):
    return Level.number_to_letter(level_number)
