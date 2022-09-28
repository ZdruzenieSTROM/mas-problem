import re

from competition.parsers import (MasProblemCurrentParser,
                                 MasProblemUntil2021Parse)
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Load competition from Latex source code'
    parsers = {
        '2020': MasProblemUntil2021Parse,
        'current': MasProblemCurrentParser
    }

    def add_arguments(self, parser):
        parser.add_argument('file', type=str)
        parser.add_argument('parser', type=str)

    def handle(self, *args, **options):
        parser = self.parsers[options['parser']](options['file'])
        parser.parse()
