import re

from wp_functions_aux import get_wp_page_sections, get_date_format
from wp_functions_aux import get_wp_pages_content, get_norefs_nolinks_content, get_justtext_content
from wp_functions_aux import get_wp_content_cached
from wp_functions_aux import get_wp_internal_links_flat

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

def check_wp_pages_square_km_sup(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"км\<sup\>2\<\/sup\>", page['content'])
        if mc:
            next_problem = ProblemPage(title=page['title'])
            result.append(next_problem)
    return result

def check_wp_pages_square_m_sup(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"[  ]м\<sup\>2\<\/sup\>", page['content'])
        if mc:
            next_problem = ProblemPage(title=page['title'])
            result.append(next_problem)
    return result

def check_wp_pages_square_km_sup(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"км\<sup\>2\<\/sup\>", page['content'])
        if mc:
            next_problem = ProblemPage(title=page['title'])
            result.append(next_problem)
    return result
def check_wp_pages_bot_titles(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"<!-- Заголовок добавлен ботом -->", page['content'])
        mc += re.findall(r"<!-- Bot generated title -->", page['content'])
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

def check_wp_centuries(viet_pages_content):
    result = []
    for page in viet_pages_content:
        # allowed in notes and source titles
        norefs_content = get_norefs_nolinks_content(page['content'])
        # "веков" ?..
        mc = re.findall(r"[0-9][  ](век|веком|веку|века|веке|веков|векам|веками|веках)[^а-я]", norefs_content)
        if mc:
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
        mc += re.findall(r"{{дописать[\|}]", page['content'])
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
                nc.append(m.replace('http://','').replace('https://',''))
            # was
            #  samples=re.findall(rx, page['content'])))
            result.append(ProblemPage(title=page['title'],counter=len(mc),
              samples=nc))
    return result

def check_wp_naked_links(viet_pages_content):
    result = []
    print("we are inside naked links")
    for page in viet_pages_content:
        mc = re.findall(r"\[http[^ ]*\]", page['content'])
        mc += re.findall(r"[^=][^/\?\=\[\|\:]{1}http[s]{0,1}://[^\) \|\<\n]+", page['content'])
        if mc:
            # TODO rework hack
            nc = []
            for m in mc:
                nc.append(m.replace('http://','').replace('https://',''))
            result.append(ProblemPage(title=page['title'],samples=nc))
    return result

def check_wp_links_in_text(viet_pages_content):
    result = []
    print("we are inside check_wp_links_in_text")
    i = 0
    for page in viet_pages_content:
        i = i + 1
        print(str(i) + " / " + str(len(viet_pages_content)) + " " + page['title'])
        just_text = get_justtext_content(page['content'])
        mc = re.findall(r"http[s]*\:\/\/[^ ]*", just_text)
        if mc:
            result.append(ProblemPage(title=page['title'],samples=mc))
    return result

def check_wp_no_cats(viet_pages_content,r):
    result = []
    exclude_templates_raw = get_wp_content_cached(['Участник:KlientosBot/project-tender/Категоризирующие шаблоны'],r)
    # searches for [[:Шаблон: or [[Шаблон: on the page
    exclude_templates = re.findall(r"\[\[[\:]*Шаблон\:([^\|\]\:]*)[\|\]]", exclude_templates_raw[0]['content'])
    # print("Found templates:")
    # print(exclude_templates)
    # print(len(exclude_templates))
    # print()
    for page in viet_pages_content:
        has_cats = False
        for t in exclude_templates:
            t_pattern = re.compile(r"{{{{[ \n]*{0}[ \n]*[\|}}]*".format(t), re.IGNORECASE)
            # print('checking template', t_pattern)
            if re.search(t_pattern, page['content']):
                has_cats = True
                # print(page['title'], "okay by template", t)
        if not re.search(r"\[\[Категория\:", page['content']) and not has_cats:
            result.append(ProblemPage(title=page['title']))
    return result

def check_wp_no_links_in_links(viet_pages_content,r):
    result = []
    exclude_templates_raw = get_wp_content_cached(['Участник:KlientosBot/project-tender/Шаблоны-ссылки'],r)
    exclude_templates = re.findall(r"\[\[Шаблон\:([^\|\]\:]*)[\|\]]", exclude_templates_raw[0]['content'])
    for page in viet_pages_content:
        # nothing to do if there is no "Ссылки" section
        if not re.search(r"==[ ]*Ссылки[ ]*==", page['content']):
            continue
        # page has links
        if re.search(r"http[s]{0,1}://", page['content']):
            continue
        has_links = False
        for t in exclude_templates:
            t_pattern = re.compile(r"{{{{[ \n]*{0}[ \n]*[\|}}]*".format(t), re.IGNORECASE)
            if re.search(t_pattern, page['content']):
                has_links = True
                # print(page['title'], "okay by template", t)
        if not has_links:
            result.append(ProblemPage(title=page['title']))
    return result

def check_wp_no_refs(viet_pages_content):
    result = []
    for page in viet_pages_content:
        if re.search(r"==[ ]*Примечания[ ]*==", page['content']) and \
          not re.search(r"<ref", page['content'], re.IGNORECASE) and \
          not re.search(r"{{source-ref", page['content'], re.IGNORECASE) and \
          not re.search(r"{{sfn", page['content'], re.IGNORECASE) and \
          not re.search(r"{{[ \n]*Население[ \n]*\|", page['content'], re.IGNORECASE):
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

# TODO also need check colons etc.
def check_wp_snprep(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r".{6}[\.\,][ ]*(?:<ref[ >]|{{sfn\|)", page['content'])
        samples = []
        for m in mc:
            if re.search(r"[  ]г.(<|{)", m) or \
              re.search(r"[  ]с.(<|{)", m) or \
              re.search(r"[  ](гг|лл|др|пр|вв|руб|экз|чел|л\. с|н\. э|т\.[  ]д|т\.[  ]п)\.(<|{)", m) or \
              re.search(r"[  ](тыс|млн|долл|проч)\.(<|{)", m) or \
              re.search(r"[  ]([а-яА-Я]{1}\.[  ]{0,1}[а-яА-Я]{1})\.(<|{)", m) or \
              re.search(r"[  ](ж\.д|Inc|M\.E\.P)\.(<|{)", m):
                pass
            else:
                samples.append(m)
        if len(samples):
            result.append(ProblemPage(title=page['title'],counter=len(samples)))
    return result

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

def check_wp_wkimedia_links(viet_pages_content):
    result = []
    for page in viet_pages_content:
        mc = re.findall(r"\[http[s]*://[a-z]+.wiktionary.org", page['content'])
        mc += re.findall(r"\[http[s]*://[a-z]+.wikiquote.org", page['content'])
        mc += re.findall(r"\[http[s]*://[a-z]+.wikibooks.org", page['content'])
        mc += re.findall(r"\[http[s]*://[a-z]+.wikisource.org", page['content'])
        mc += re.findall(r"\[http[s]*://[a-z]+.wikinews.org", page['content'])
        mc += re.findall(r"\[http[s]*://[a-z]+.wikiversity.org", page['content'])
        mc += re.findall(r"\[http[s]*://[a-z\.]*commons.wikimedia.org", page['content'])
        mc += re.findall(r"\[http[s]*://[a-z]+.wikivoyage.org", page['content'])
        mc += re.findall(r"\[http[s]*://[a-z]+.wikidata.org", page['content'])
        mc += re.findall(r"\[http[s]*://[a-z\.]*species.wikimedia.org", page['content'])
        mc += re.findall(r"\[http[s]*://[a-z\.]*meta.wikimedia.org", page['content'])
        mc += re.findall(r"\[http[s]*://[a-z]+.mediawiki.org", page['content'])
        if mc:
            result.append(ProblemPage(title=page['title'],samples=mc))
        # per Lvova (12)
        # wiktionary, wikiquote, wikibooks, wikisource, wikinews, wikiversity, commons.wikimedia.org,
        #         wikivoyage, wikidata, species.wikimedia.org, meta.wikimedia.org, mediawiki.org
    return result

def check_wp_images(viet_pages_content):
    result = []
    for page in viet_pages_content:
        for cat in page["categories"]:
            # if page["title"] == "ST25":
            if re.search(r"Википедия:Статьи без изображений", cat):
                #result += page['title']
                result.append(ProblemPage(title=page['title']))
    # result_sorted = sorted(set(items))
    result_unique = {item.title: item for item in result}.values()
    # потом сортируем по name
    result_sorted = sorted(result_unique, key=lambda x: x.title)
    return result_sorted

def check_links_to_disambigs(pages_content,r):
    # Step 1. Dump all links targets to cache
    # Step 2. Get content for all link targets (non -redirects)
    # Sep 3. For all redirects, get a redirect target and check it
    result = []
    i = 0
    for page in pages_content:
        i = i + 1
        print(f"Checking disambigs on {page['title']} ( {i} / {len(pages_content)} )")
        page_disambigs = []
        internal_links = get_wp_internal_links_flat([page])
        internal_links_targets_content = get_wp_content_cached(internal_links,r,verbose=False)
        
        redirect_pairs = {}
        redirects = []
        for i_l in internal_links_targets_content:
            #print(f"Disamb working on {i_l["title"]}")
            if 'redirects_to' in i_l:
                if i_l['redirects_to']:
                    print("R".ljust(12) + f"{i_l['title']} -> {i_l['redirects_to']}")
                    redirect_pairs[i_l['title']] = i_l['redirects_to']
                    #redirest_pairs.append(a)
                    #exit(555)
                    #continue
            if 'categories' in i_l:
                if "Категория:Страницы значений по алфавиту" in i_l['categories']:
                    print("DIS IS A DISAMBIG!")
                    page_disambigs.append(f"[[{i_l['title']}]]")
        if page['title'] == "Командование по оказанию военной помощи Вьетнаму" and False:
            print("now move over redirect_pairs")
            print(redirect_pairs)
            exit(88)
        for i_p, key_p in redirect_pairs.items():
            #print(f"workink on i_p, key_p: {i_p}, {key_p}")
            redirect_target_content = get_wp_content_cached([key_p],r,verbose=False)[0]
            #print(redirect_target_content)
            if "Категория:Страницы значений по алфавиту" in redirect_target_content['categories']:
                print("DIS IS A REDIRECTR To DISAMBIG!!!")
                page_disambigs.append(f"[[{i_p}]]")
        page_disambigs_sorted = sorted(set(page_disambigs))
        if len(page_disambigs) > 0:   
            result.append(ProblemPage(title=page['title'],samples=page_disambigs_sorted))
            print(f"{page['title']} added with disambigs {page_disambigs_sorted}")
    return result

### Single-Page Checks ###
