import re

from wp_functions_aux import get_wp_page_sections, get_date_format

class ProblemPage():
    def __init__(self, title="", counter=None, samples=[], note=""):
        self.title = title
        self.note = note
        self.counter = counter
        self.samples = samples
    def __repr__(self):
        return f"[[{self.title}]] ({self.counter} hits, {self.samples} samples)"

def check_wp_pages_square_km(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"кв[.]? км", page['content'])
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

def check_wp_communes(viet_pages_content):
    result = []
    for page in viet_pages_content:
        if page['title'] == "Пиньо де Беэн, Пьер":
            continue
        samples = []
        mc = re.findall(r"[^\n ]{0,8}коммун[^\n ]{0,5}", page['content'])
        for m in mc:
            if not re.search(r"коммуни", m) and \
              not re.search(r"коммунал", m) and \
              not re.search(r"общин[а-я]{0,2}-коммун", m):
                samples.append(m)
        if samples:
            result.append(ProblemPage(title=page['title'],counter=len(samples)))
    return result

def check_wp_pages_delimiters(viet_pages_content):
    result = []
    for page in viet_pages_content:
        samples = []
        # [ \n]
        mc = re.findall(r".{4}[^№][\| \n][0-9]{1,3}\.[0-9]{3}\.[0-9]{3}[^0-9]", page['content'])
        if mc:
            for m in mc:
                if not re.findall(r"номер", m):
                    m1 = re.findall(r"[0-9]{1,3}\.[0-9]{3}\.[0-9]{3}", m)
                    samples.append(m1[0])
        if samples:
            result.append(ProblemPage(title=page['title'],counter=len(samples),samples=samples))
    return result

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

def check_wp_links_unavailable(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"{{[Нн]едоступная ссылка", page['content'])
        if mc:
            rx = r"(http[s]?://[^ \|]*)(?:(?!http[s]?://).)*{{Недоступная ссылка"
            # TODO rework hack
            nc = []
            for m in re.findall(rx, page['content']):
                if re.search(r"http://[\.a-z]*lib.ru/", m):
                    nc.append(m.replace('http://',''))
                    # nc.append("(ссылка скрыта)")
                elif re.search(r"https://[\.a-z]*lib.ru/", m):
                    nc.append(m.replace('https://',''))
                    # nc.append("(ссылка скрыта)")
                else:
                    nc.append(m)
            # was
            #  samples=re.findall(rx, page['content'])))
            result.append(ProblemPage(title=page['title'],counter=len(mc),
              samples=nc))
    return result

def check_wp_naked_links(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"\[http[^ ]*\]", page['content'])
        mc += re.findall(r"[^=][^/\?\=\[\|]{1}http[s]{0,1}://[^\) \|\<\n]+", page['content'])
        if mc:
            # TODO rework hack
            nc = []
            for m in mc:
                if re.search(r"http://[\.a-z]*lib.ru/", m):
                    nc.append(m.replace('http://',''))
                    # nc.append("(ссылка скрыта)")
                elif re.search(r"https://[\.a-z]*lib.ru/", m):
                    nc.append(m.replace('https://',''))
                    # nc.append("(ссылка скрыта)")
                else:
                    nc.append(m)
            result.append(ProblemPage(title=page['title'],samples=nc))
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
          not re.search(r"{{композитор\|", page['content'], re.IGNORECASE) and \
          not re.search(r"{{список однофамильцев}}", page['content']) and \
          not re.search(r"{{Мосты Вологды}}", page['content']) and \
          not re.search(r"{{Улица Екатеринбурга[ \n]*\|", page['content']) and \
          not re.search(r"{{Карта[ \n]*\|", page['content']) and \
          not re.search(r"{{Остров[ \n]*\|", page['content']) and \
          not re.search(r"{{Культурное наследие народов РФ\|", page['content']) and \
          not re.search(r"{{Вьетнам на Олимпийских игра}}", page['content']):
            result.append(ProblemPage(title=page['title']))
    return result

def check_wp_no_links_in_links(viet_pages_content):
    result = []
    for page in viet_pages_content:
        if re.search(r"==[ ]*Ссылки[ ]*==", page['content']) and \
          not re.search(r"http[s]{0,1}://", page['content']) and \
          not re.search(r"{{ВС}}", page['content'], re.IGNORECASE) and \
          not re.search(r"{{WAD\|", page['content']) and \
          not re.search(r"{{ВТ-ЭСБЕ\|", page['content']) and \
          not re.search(r"{{IMDb name\|", page['content'], re.IGNORECASE) and \
          not re.search(r"{{IMDb title\|", page['content']) and \
          not re.search(r"{{Шахматные ссылки[ \n]*\|", page['content']) and \
          not re.search(r"{{ЭЕЭ[ \n]*\|", page['content']) and \
          not re.search(r"{{Ethnologue[ \n]*\|", page['content']) and \
          not re.search(r"{{MacTutor Biography[ \n]*\|", page['content']) and \
          not re.search(r"{{Сотрудник РАН[ \n]*\|", page['content']) and \
          not re.search(r"{{Math-Net.ru[ \n]*\|", page['content']) and \
          not re.search(r"{{oopt.aari.ru[ \n]*\|", page['content']) and \
          not re.search(r"{{Warheroes[ \n]*\|", page['content'], re.IGNORECASE) and \
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
            # print(page['title'], "— bad notes, len", len(page['content']))
            # print(bool(re.search(r"==[ ]*Примечания[ ]*==", page['content'])))
            # print(bool(not re.search(r"<ref", page['content'])))
            # # if re.search(r"<ref", data):
                # # print("(this is true)")
            # print(bool(not re.search(r"{{sfn", page['content'])))
    return result

def check_wp_no_sources(viet_pages_content):
    result = []
    for page in viet_pages_content:
        if not re.search(r"<ref[ >]", page['content']) and \
          not re.search(r"{{sfn\|", page['content']) and \
          not re.search(r"==[ ]*Ссылки[ ]*==", page['content']) and \
          not re.search(r"==[ ]*Литература[ ]*==", page['content']) and \
          not re.search(r"==[ ]*Источники[ ]*==", page['content']) and \
          not re.search(r"{{IMDb name\|", page['content']):
            result.append(ProblemPage(title=page['title']))
    return result

def check_wp_poor_dates(viet_pages_content):
    result = []
    for page in viet_pages_content:
        bad_dates = []
        mc = re.findall(r"{{[cC]ite web[^{}]+(?:{{[^}]+}})*[^{}]+}}", page['content'])
        for m in mc:
            cite_dates = re.findall("\|[ ]*archive[-]?date[ ]*=[ ]*([^\|\n}]*)", m)
            cite_dates += re.findall("\|[ ]*date[ ]*=[ ]*([^\|\n}]*)", m)
            cite_dates += re.findall("\|[ ]*datepublished[ ]*=[ ]*([^\|\n}]*)", m)
            # TODO to activate in feature release
            cite_dates += re.findall("\|[ ]*access[-]?date[ ]*=[ ]*([^\|\n}]*)", m)
            for cite_date in cite_dates:
                if not get_date_format(cite_date.strip()):
                    bad_dates.append(cite_date.strip())
        if bad_dates:
            result.append(ProblemPage(title=page['title'], note=f"({'; '.join(bad_dates)})"))
    return result

def check_wp_ref_templates(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"{{ref-[a-zA-Z]{2}[\|} ]", page['content'])
        if mc:
            result.append(ProblemPage(title=page['title'],counter=len(mc)))
    return result

def check_wp_semicolon_sections(viet_pages_content):
    result = []
    for page in viet_pages_content:
        has_semi = False
        sections = get_wp_page_sections(page['content'])
        for section in sections:
            if re.search(r"\n;", section['content']) and \
              not re.search(r"Литература|Примечания|Источники", section['name']):
                has_semi = True
        if has_semi:
            result.append(ProblemPage(title=page['title']))
    return result

# TODO also need check commas, colons etc.
def check_wp_snprep(viet_pages_content):
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

# TODO simplify
def check_wp_source_request(viet_pages_content, excludings):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"{{rq\|[^\}]{0,20}sources[\|}]", page['content'], re.IGNORECASE)
        mc += re.findall(r"{{Нет источников\|", page['content'], re.IGNORECASE)
        mc += re.findall(r"{{Нет ссылок\|", page['content'], re.IGNORECASE)
        if mc and not page['title'] in excludings:
            result.append(ProblemPage(title=page['title']))
    return result

def check_wp_template_regexp(viet_pages_content, template):
    result = []
    for page in viet_pages_content:
        my_regex = r"{{" + template + r"[ \n]*\||{{" + template + r"[ \n]*}}"
        mc = re.findall(my_regex, page['content'], re.IGNORECASE)
        if mc:
            result.append(ProblemPage(title=page['title'],counter=len(mc)))
    return result

def check_wp_too_few_wikilinks(viet_pages_content):
    result = []
    TOO_LOW = 0.9
    TOO_HIGH = 20
    for page in viet_pages_content:
        if len(page['content'].encode('utf-8')) > 20480:
            mc = re.findall(r"\[\[[^\]:]*\]\]", page['content'])
            linksPerKB = 1024 * len(mc) / len(page['content'].encode('utf-8'))
            # linksPerKB_str = "{linksPerKB:0.2f}"
            if linksPerKB > TOO_HIGH:
                result.append(ProblemPage(title=page['title'], note=f"{linksPerKB:0.2f}, " + \
                    f"({len(mc)}/{len(page['content'].encode('utf-8'))}) — а здесь наоборот, " + \
                    "слишком много"))
            if linksPerKB < TOO_LOW:
                result.append(ProblemPage(title=page['title'],
                    note=f"({linksPerKB:0.2f}, {len(mc)}/{len(page['content'].encode('utf-8'))})"))
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
