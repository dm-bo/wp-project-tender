import re

class ProblemPage(object):
    def __init__(self, title="", counter=None, samples=[]):
        self.title = title
        self.counter = counter
        self.samples = samples
    def __repr__(self):
        return '[[{}]] ({})>'.format(self.title, len(self.samples))

def check_wp_pages_square_km(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"кв. км", page['content'])
        mc += re.findall(r"кв км", page['content'])
        if mc:
            next_problem = ProblemPage(title=page['title'])
            result.append(next_problem)
    return result

def check_wp_pages_bot_titles(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"<!-- Заголовок добавлен ботом -->", page['content'])
        if mc:
            next_problem = ProblemPage(title=page['title'],counter=len(mc))
            result.append(next_problem)
    return result

def check_wp_pages_bot_archives(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"<!-- Bot retrieved archive -->", page['content'])
        if mc:
            #next_problem = ProblemPage(title=page['title'],counter=len(mc))
            #result.append(next_problem)
            result.append(ProblemPage(title=page['title'],counter=len(mc)))
    return result

# TODO Communes

def check_wp_pages_direct_googlebooks(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"\[http[s]*\:\/\/books\.google\.", page['content'])
        if mc:
            result.append(ProblemPage(title=page['title'],counter=len(mc)))
    return result

def check_wp_pages_direct_interwikis(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"\[\[\:[a-z]{2,3}\:[^\:]*\]\]", page['content'])
        if mc:
            result.append(ProblemPage(title=page['title'],counter=len(mc)))
    return result

def check_wp_pages_direct_webarchive(viet_pages_content):
    result = []
    for page in viet_pages_content:
        samples = []
        mc = re.findall(r"\[http[s]*://web.archive.org[^ \]\n]*", page['content'])
        if mc:
            for m in mc:
                samples.append(re.sub(r'\[http[s]*://web.archive.org/web/[0-9]*/', "", m))
            result.append(ProblemPage(title=page['title'],counter=len(samples),samples=samples))
    return result

def check_wp_pages_empty(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"{{rq\|[^\}]{0,30}empty[\|}]", page['content'])
        if mc:
            result.append(ProblemPage(title=page['title'],counter=len(mc)))
    return result

def check_wp_icon_template(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"{{[a-zA-Z]{2} icon}}", page['content'])
        if mc:
            result.append(ProblemPage(title=page['title'],counter=len(mc)))
    return result

def check_wp_isolated(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"{{изолированная статья\||{{изолированная статья}}", page['content'])
        if mc:
            result.append(ProblemPage(title=page['title']))
    return result

# TODO LinksUnanvailable

def check_wp_naked_links(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"\[http[^ ]*\]", page['content'])
        mc += re.findall(r"[^=][^/\?\=\[\|]{1}http[s]{0,1}://[^\) \|\<\n]+", page['content'])
        if mc:
            result.append(ProblemPage(title=page['title'],counter=len(mc),samples=mc))
    return result

def check_wp_no_cats(viet_pages_content):
    result = []
    for page in viet_pages_content:
        if not re.search(r"\[\[Категория\:", page['content']) and \
          not re.search(r"{{кинорежиссёр\|", page['content']) and \
          not re.search(r"{{сценарист\|", page['content']) and \
          not re.search(r"{{[Пп]евица\|", page['content']) and \
          not re.search(r"{{[Аа]ктриса\|", page['content']) and \
          not re.search(r"{{историк\|", page['content']) and \
          not re.search(r"{{археолог\|", page['content']) and \
          not re.search(r"{{список однофамильцев}}", page['content']) and \
          not re.search(r"{{Мосты Вологды}}", page['content']) and \
          not re.search(r"{{Улица Екатеринбурга[ \n]*\|", page['content']) and \
          not re.search(r"{{Карта[ \n]*\|", page['content']) and \
          not re.search(r"{{Культурное наследие народов РФ\|", page['content']) and \
          not re.search(r"{{Вьетнам на Олимпийских игра}}", page['content']):
            result.append(ProblemPage(title=page['title']))
    return result

def check_wp_no_links_in_links(viet_pages_content):
    result = []
    for page in viet_pages_content:
        if re.search(r"==[ ]*Ссылки[ ]*==", page['content']) and \
          not re.search(r"http[s]{0,1}://", page['content']) and \
          not re.search(r"{{ВС}}", page['content']) and \
          not re.search(r"{{WAD\|", page['content']) and \
          not re.search(r"{{ВТ-ЭСБЕ\|", page['content']) and \
          not re.search(r"{{IMDb name\|", page['content']) and \
          not re.search(r"{{IMDb title\|", page['content']) and \
          not re.search(r"{{Шахматные ссылки[ \n]*\|", page['content']) and \
          not re.search(r"{{ЭЕЭ[ \n]*\|", page['content']) and \
          not re.search(r"{{MacTutor Biography[ \n]*\|", page['content']) and \
          not re.search(r"{{Сотрудник РАН[ \n]*\|", page['content']) and \
          not re.search(r"{{Math-Net.ru[ \n]*\|", page['content']) and \
          not re.search(r"{{oopt.aari.ru[ \n]*\|", page['content']) and \
          not re.search(r"{{Warheroes[ \n]*\|", page['content']) and \
          not re.search(r"{{SportsReference[ \n]*\|", page['content']) and \
          not re.search(r"{{DNB-Portal[ \n]*\|", page['content']) and \
          not re.search(r"{{DDB[ \n]*\|", page['content']):
            result.append(ProblemPage(title=page['title']))
    return result

def check_wp_no_refs(viet_pages_content):
    result = []
    for page in viet_pages_content:
        if re.search(r"==[ ]*Примечания[ ]*==", page['content']) and \
          not re.search(r"<ref", page['content']) and \
          not re.search(r"{{sfn", page['content']):
            result.append(ProblemPage(title=page['title']))
    return result

# TODO many

# TODO also need check commas, colons etc.
def check_wp_SNPREP(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r".{6}\.[ ]*(?:<ref[ >]|{{sfn\|)", page['content'])
        samples = []
        for m in mc:
            if re.search(r"[  ]г.(<|{)", m) or \
              re.search(r"[  ](гг|лл|др|руб|экз|чел|л\. с|н\. э|т\.[  ]д|т\.[  ]п)\.(<|{)", m) or \
              re.search(r"[  ](тыс|млн|долл)\.(<|{)", m) or \
              re.search(r"[  ]([а-яА-Я]{1}\.[  ]{0,1}[а-яА-Я]{1})\.(<|{)", m) or \
              re.search(r"[  ](ж\.д|Inc|M\.E\.P)\.(<|{)", m):
                pass
            else:
                samples.append(m)
        if len(samples):
            result.append(ProblemPage(title=page['title'],counter=len(samples)))
    return result

def check_wp_source_request(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"{{rq\|[^\}]{0,20}sources[\|}]", page['content'])
        mc += re.findall(r"{{Нет источников\|", page['content'])
        mc += re.findall(r"{{Нет ссылок\|", page['content'])
        if mc:
            result.append(ProblemPage(title=page['title']))
    return result



###

def check_wp_wp_links(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"\[http[s]*://[a-z]+.wikipedia.org", page['content'])
        if mc:
            result.append(ProblemPage(title=page['title'],counter=len(mc)))
    return result


### Single-Page Checks ###