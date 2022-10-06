from django import template
from django.utils.timezone import now

register = template.Library()


@register.simple_tag
def number_of_solved(level, competitor):
    return level.number_of_solved(competitor)