import re
from io import BytesIO

from competition.models import Level, Problem


class CompetitionParser:
    def __init__(self, file):
        self.file : BytesIO = file

    def load_file(self):
        lines = self.file.readlines()
        text = ''.join(l.decode("utf-8")  for l in lines)
        return text

    def parse(self):
        return self.load_file()


class MasProblemUntil2021Parse(CompetitionParser):

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
        return levels

    def create_problems(self,game):
        levels = self.parse()
        previous_level =None
        for i,level in enumerate(levels):
            new_level = Level.objects.create(
                game=game,
                order=i+1,
                previous_level=previous_level
            )
            previous_level = new_level
            for j,(problem,result) in enumerate(zip(level['problems'],level['results'])):
                Problem.objects.create(
                    level=new_level,
                    text = problem,
                    order = j+1,
                    solution=result
                )


