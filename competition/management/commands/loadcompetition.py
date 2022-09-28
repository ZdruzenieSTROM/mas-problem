import re

from django.core.management.base import BaseCommand


class CompetitionParser:
    def __init__(self, file_name):
        self.file_name = file_name

    def load_file(self):
        with open(self.file_name, newline='', encoding='utf-8') as file:
            lines = file.readlines()
            text = ''.join(lines)
            return text

    def parse(self):
        return self.load_file()


class MasProblemUntil2021Parse(CompetitionParser):

    def parse():
        pass


class MasProblemCurrentParser(CompetitionParser):
    def parse(self):
        text = super().parse()
        level_text = text.split(sep=r'\uroven')
        #levels = re.findall(r'\\uroven\{(.)\}', text)
        levels = []
        for level in level_text:
            problems = re.findall(
                r'\\begin\{zadanie\}(.*?)\\end\{zadanie\}', level, re.S)
            problems = [problem.strip() for problem in problems]
            results = re.findall(
                r'\\begin\{vysledok\}(.*?)\\end\{vysledok\}', level, re.S)
            results = [result.strip() for result in results]
            levels.append(
                {
                    'problems': problems,
                    'results': results
                }
            )


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
