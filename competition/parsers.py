import re


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

