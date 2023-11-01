import re
from io import BytesIO
from random import choice
from string import ascii_lowercase
from unidecode import unidecode

from competition.models import Competitor, Grade, Level, Problem, User


class UTF8Parser:
    def __init__(self, file):
        self.file: BytesIO = file

    def load_file(self):
        lines = self.file.readlines()
        text = ''.join(l.decode("utf-8") for l in lines)
        return text

    def parse(self):
        return self.load_file()


class MasProblemUntil2021Parse(UTF8Parser):

    def parse(self):
        text = super().parse()
        problems = re.findall(r'(\\. .*)', text)
        levels = {}

        for problem in problems:
            if problem.split(' ')[0][1] in levels:
                levels[problem[1]].append(problem[2:].strip())
            else:
                levels[problem[1]] = [problem[2:].strip()]

        levels = [{'problems': problem} for _, problem in levels.items()]

        results = text.split(r'\centerline{\large \bf VÝSLEDKY}')[1]
        results = results.split(r'\bf ÚROVEŇ')

        for i, result in enumerate(results[1:]):
            levels[i]['results'] = [result.strip()
                                    for result in re.findall(r'\s*\\item(.*)', result)]

        return levels


class MasProblemCurrentParser(UTF8Parser):
    def parse(self):
        text = super().parse()
        level_text = text.split(sep=r'\uroven')
        # levels = re.findall(r'\\uroven\{(.)\}', text)
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
        return levels

    def create_problems(self, game):
        levels = self.parse()
        previous_level = None
        for i, level in enumerate(levels):
            new_level = Level.objects.create(
                game=game,
                order=i+1,
                previous_level=previous_level
            )
            previous_level = new_level
            for j, (problem, result) in enumerate(zip(level['problems'], level['results'])):
                Problem.objects.create(
                    level=new_level,
                    text=problem,
                    order=j+1,
                    solution=result
                )

# TODO: Should be defined in another file
def generate_password():
    return ''.join(choice(ascii_lowercase) for _ in range(8))


class CompetitorsParser(UTF8Parser):
    def parse(self):
        text = super().parse()
        competitors = []
        for user_line in text.split('\n'):
            if not user_line:
                continue
            firstname, lastname, school, grade, legal_representative = user_line.split(';')
            competitors.append(
                {
                    'firstname': firstname,
                    'lastname': lastname,
                    'school': school,
                    'grade': Grade.grade_from_number(int(grade)),
                    'legal_representative': legal_representative
                }
            )
        return competitors

    def create_users(self, game):
        competitors = self.parse()
        result = []
        for competitor in competitors:
            email = ''
            username = f"{unidecode(competitor['firstname'] + competitor['lastname']).replace(' ', '').lower()}"
            password = generate_password()

            user = User.objects.create_user(username, email, password)
            Competitor.objects.create(
                user=user,
                game=game,
                first_name=competitor['firstname'],
                last_name=competitor['lastname'],
                school=competitor['school'],
                grade=competitor['grade'],
                legal_representative=competitor['legal_representative']
            )

            result.append({'username': username, 'password': password, 'user': user})

        return result