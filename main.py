"""
Script/bot to search for issues in the Wikipedia project
For details, please see https://ru.wikipedia.org/wiki/Участник:KlientosBot
"""

import sys
import datetime
# for projects shuffling
import random

from jinja2 import Environment, FileSystemLoader

from wp_functions_aux import get_wp_pages_by_template, get_wp_pages_content
from wp_functions_aux import get_wp_internal_links, get_wp_authenticated_session, set_wp_page_text
from wp_functions_aux import get_disambigs, get_wp_pages_by_category_recurse
from wp_functions_aux import parse_check_template, normalize_link
from wp_functions_check import *
# import update_list

from wp_auth_data import *
from config import get_redis_client, get_tender_config

# TODO check Template:Чистить| (problem)
# TODO check if no {{references}} but has <ref> or {{sfn}}
# TODO MAYBE check Template:уточнить (problem)

class Check():
    """
    The check result that contains check names and description, affected pages,
    options for listing on the resulting page and counting in stats
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, name="", title="", descr="", pages=[], total=0, nowiki=False,
      supress_listing=False, supress_stat=False):
        self.name = name
        self.title = title
        self.descr = descr
        self.percent = 100*len(pages)/total # or 0
        self.counter = len(pages)
        self.pages = pages
        self.nowiki = nowiki
        self.supress_listing = supress_listing
        self.supress_stat = supress_stat
    def __repr__(self):
        return f'{self.name} ({self.counter} pages found)'

moment_start = datetime.datetime.now()
session = get_wp_authenticated_session(wp_login, wp_passw)

# Script config
script_config = get_tender_config()

# Redis fun
red_con = get_redis_client()

###############################
###### ITERATE FROM HERE ######
###############################

# NS 104 - project discussions
result_pages = get_wp_pages_by_template("User:KlientosBot/project-tender", 104)
random.shuffle(result_pages)
print("Pages by template randomized =", result_pages)

# iterate over found projects
for post_results_page in result_pages:
    print("")
    print("Working on", post_results_page)
    checks = []
    exclude_pages = []
    # prologue = ""
    epilogue = ""
    # FIXME this limit doesn't work (see SPb category)
    pages_limit = 50000
    summary = "плановое обновление данных"
    checks_enabled = {
        "CiteDecorations": True,
        "PoorDates": True,
        "Communes": False,
        "Experimental": False,
        "Disambigs": False,
        "UglyRedirects": False
    }

    # result disambigs
    disambigs = []
    # result ugly redirects
    long_redirects = []
    # maybe we'll need this info (not yet)
    cannot_check = []

    # Checking that result page is not too fresh
    result_content = get_wp_pages_content([post_results_page],red_con)
    mc1 = re.findall(r"{{User:Klientos(?:Bot)?/project-tender[ \n]*\|[^}]*}}",
        result_content[0][0]['content'])
    template_options = ""
    if mc1:
        check_template = parse_check_template(mc1[0], post_results_page)
        print(check_template)
        # check_template["timestamp_date"]
        # check_template["overdated_threshold"]
        if not check_template["old_enough"]:
            print("Not old enough, skipping")
            continue
        # making options for a new template
        check_template_new = check_template
        check_template_new['timestamp'] = datetime.datetime.now()
        for key, value in check_template_new.items():
            template_options = template_options + f"|{key}={value} "
    else:
        print("No bot template found! Exiting.")
        sys.exit(46)

    ### Working on template options
    # enable_checks
    if 'enable_checks' in check_template.keys():
        enabled_checks = check_template['enable_checks'].replace(' ','').split(',')
        for ec in enabled_checks:
            checks_enabled[ec] = True
    # disable_checks
    if 'disable_checks' in check_template.keys():
        disable_checks = check_template['disable_checks'].replace(' ','').split(',')
        for dc in disable_checks:
            checks_enabled[dc] = False
    # search criteria
    viet_pages = []
    for crit in check_template['criteria'].replace(', ',',').split(','):
        criteria = crit.strip()
        print("Working on criteria", criteria)
        if re.search(r"^Шаблон:", criteria):
            print("Search by template", criteria)
            viet_pages = viet_pages + get_wp_pages_by_template(criteria, 1)
        elif re.search(r"^Категория:Статьи проекта", criteria):
            print("Search by project category", criteria)
            viet_pages = viet_pages + get_wp_pages_by_category_recurse([ criteria ], 1)
        elif re.search(r"^Категория:", criteria):
            print("Search by category", criteria)
            viet_pages = viet_pages + get_wp_pages_by_category_recurse([ criteria ], 0)
        else:
            print("Unknown search criteria!")
            continue
    # Loading exceptions list
    if 'except_pages' in check_template.keys():
        if not check_template['except_pages'] == '':
            excludes_content = get_wp_pages_content([check_template['except_pages']],red_con)
            exclude_pages = re.findall(r"\[\[([^\|\]\:]*)[\|\]]", excludes_content[0][0]['content'])
    else:
        exclude_pages = []
    print("exclude_pages", exclude_pages)
    # set empty prologue and epilogue if not defined
    if 'prologue' not in check_template.keys():
        check_template['prologue'] = ""
    if 'epilogue' not in check_template.keys():
        check_template['epilogue'] = ""

    area = re.findall(r"\:([^\/\:]*)\/", post_results_page)[0]
    area = re.findall(r"\:(.*)", post_results_page)[0].replace("/","_")
    output_file = f"C:/Users/Dm/Desktop/wp/badlinks-{area}.py.txt"

    print("Updating page ", post_results_page)

    print("Total pages found:", len(viet_pages))
    viet_pages = list(set(viet_pages) - set(exclude_pages))
    print("After omitting some pages:", len(viet_pages))

    # Some custom hacks
    # if post_results_page == "Проект:Вьетнам/Недостатки статей":
        # checks_enabled["Disambigs"] = False
        # checks_enabled["UglyRedirects"] = False

    #viet_pages = get_pages_by_template("Шаблон:Статья проекта Карелия",1)
    checks.append(Check(
        name="Total",
        title="Всего",
        pages=viet_pages,
        total=len(viet_pages),
        supress_listing=True)
    )

    ### Patrolling ####

    viet_pages_content, viet_pages_not_patrolled, viet_pages_old_patrolled = \
        get_wp_pages_content(viet_pages=viet_pages,r=red_con,limit=pages_limit)

    #print("Total pages retrieved:", len(viet_pages_content), "of", len(viet_pages))
    #print("Not patrolled:", len(viet_pages_old_patrolled), "and", len(viet_pages_not_patrolled))
    print("Engaging check NotPatrolled and beyond")
    checks.append(Check(
        name="NotPatrolled",
        title="Не отпатрулированные статьи",
        pages=viet_pages_old_patrolled + viet_pages_not_patrolled,
        total=len(viet_pages),
        supress_listing=True)
    )
    #print("part done")

    # print(stats)

    ### Checks ###

    checks.append(Check(
        name="NakedLinks",
        title="Голые ссылки",
        descr="Нужно оформить ссылку в [[Ш:cite web]] или, хотя бы, в <code><nowiki>" + \
            "[http://example.com Title]</nowiki></code>.",
        pages=check_wp_naked_links(viet_pages_content),
        total=len(viet_pages),
        nowiki=True)
    )

    print("Engaging check NoLinksInLinks and beyond")
    checks.append(Check(
        name="NoLinksInLinks",
        title="Статьи без ссылок в разделе «Ссылки»",
        descr="Если в «Ссылках» есть источники без http-сылок, то их, возможно, стоит " + \
            "переместить в раздел «Литература».",
        pages=check_wp_no_links_in_links(viet_pages_content,r=red_con),
        total=len(viet_pages))
    )

    # print("Engaging check NoRefs")
    checks.append(Check(
        name="NoRefs",
        title="Нет примечаний в разделе «Примечания»",
        descr="Не считает примечания, подтянутые из ВД. В любом случае, было бы неплохо " + \
            "добавить сноски в тело статьи.",
        pages=check_wp_no_refs(viet_pages_content),
        total=len(viet_pages))
    )

    #print(check_result)
    checks.append(Check(
        name="DirectInterwikis",
        title="Статьи с прямыми интервики-ссылками",
        descr="Нужно заменить на шаблон iw или добавить прямую ссылку на статью в РуВП, если " + \
            "она уже есть.",
        pages=check_wp_pages_direct_interwikis(viet_pages_content),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="WPLinks",
        title="Ссылки на ВП как внешние",
        descr="<nowiki>[http://ссылки]</nowiki> нужно поменять на <nowiki>[[ссылки]]</nowiki>.",
        pages=check_wp_wp_links(viet_pages_content),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="WMLinks",
        title="Ссылки на проекты Викимедиа как внешние",
        descr="Вместо прямых ссылок на сестринские проекты используйте внутренние ссылки " +
            "вида <code><nowiki>[[q:en:Star Wars]]</nowiki></code> (см. " +
            "[[Википедия:Интервики#Коды проектов Фонда]]).",
        pages=check_wp_wkimedia_links(viet_pages_content),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="BotTitles",
        title="Заголовок добавлен ботом",
        descr="Нужно проверить, что заголовок правильный, и убрать html-комментарий ''<nowiki>" + \
            "<!-- Заголовок добавлен ботом --> или <!-- Bot generated title --></nowiki>''.",
        pages=check_wp_pages_bot_titles(viet_pages_content),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="BotArchives",
        title="Архив добавлен ботом",
        descr="Нужно проверить архив, и убрать html-комментарий ''<nowiki><!-- Bot retrieved " + \
            "archive --></nowiki>''.",
        pages=check_wp_pages_bot_archives(viet_pages_content),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="NoCats",
        title="Не указаны категории",
        descr="Иногда категории назначаются шаблонами, тогда указывать категории напрямую не " +
            "нужно. В таком случае категоризирующий шаблон следует учитывать при составлении " +
            "этого списка.",
        pages=check_wp_no_cats(viet_pages_content,r=red_con),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="DirectGoogleBooks",
        title="Прямые ссылки на Google books",
        descr="Их желательно поменять на [[Шаблон:книга]].",
        pages=check_wp_pages_direct_googlebooks(viet_pages_content),
        total=len(viet_pages))
    )

    if checks_enabled["CiteDecorations"] :
        checks.append(Check(
            name="DirectWebarchive",
            title="Прямые ссылки на web.archive.org",
            descr="Желательно заменить их на [[Ш:cite web]] с параметрами archiveurl и " +
                "archivedate.",
            pages=check_wp_pages_direct_webarchive(viet_pages_content),
            total=len(viet_pages))
        )

    checks.append(Check(
        name="SNPREP",
        title="[[ВП:СН-ПРЕП|СН-ПРЕП]]",
        descr="Страницы, в тексте которых есть <code><nowiki>.<ref</nowiki></code> или " +
            "<code><nowiki>.{{sfn</nowiki></code>, либо их вариации с пробелами, как <code>" +
            "<nowiki>. <ref</nowiki></code>, а также те же сочетания с запятой." +
            "Сноска должна стоять перед точкой или запятой, кроме случаев, "+
            "когда точка является частью сокращения.",
        pages=check_wp_snprep(viet_pages_content),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="SemicolonSections",
        title=";Недоразделы",
        descr="Использована кострукция <code><nowiki>;Что-то</nowiki></code>. Скорее всего, её " +
            "следует заменить, например, на <code><nowiki>=== Что-то ===</nowiki></code>.",
        pages=check_wp_semicolon_sections(viet_pages_content),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="TooFewWikilinks",
        title="Мало внутренних ссылок",
        descr="Добавьте больше.",
        pages=check_wp_too_few_wikilinks(viet_pages_content),
        total=len(viet_pages))
    )

    if checks_enabled["PoorDates"]:
        checks.append(Check(
            name="PoorDates",
            title="Неформатные даты в cite web",
            descr="Используйте формат <code>YYYY-MM-DD</code> ([[ВП:ТД]]).",
            pages=check_wp_poor_dates(viet_pages_content),
            total=len(viet_pages),
            nowiki=True)
        )

    checks.append(Check(
        name="BadSquareKm",
        title="Страницы с кв км или кв. км",
        descr="Желательно поменять на км².",
        pages=check_wp_pages_square_km(viet_pages_content),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="BadSquareKmSup",
        title="Страницы с <nowiki>км<sup>2</sup></nowiki>",
        descr="Желательно поменять на км².",
        pages=check_wp_pages_square_km_sup(viet_pages_content),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="BadSquareMSup",
        title="Страницы с <nowiki>м<sup>2</sup></nowiki>",
        descr="Желательно поменять на м².",
        pages=check_wp_pages_square_m_sup(viet_pages_content),
        total=len(viet_pages))
    )

    print("Engaging check LinksInText")
    checks.append(Check(
        name="LinksInText",
        title="Ссылки в тексте",
        descr="Не следует вставлять внешние ссылки прямо в текст. Обычно они размещаются в " + \
            "сносках, разделе \"Ссылки\" и других подобающих местах.",
        pages=check_wp_links_in_text(viet_pages_content),
        total=len(viet_pages),
        nowiki=True)
    )

    # Template checks (can be looped later)

    if checks_enabled["CiteDecorations"]:
        template = "Citation"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="Используйте шаблоны {{tl|Книга}}, {{tl|Статья}} или {{tl|Cite web}} вместо " +
                "этого шаблона, чтобы ссылки отображались в принятом для русских публикаций " +
                "формате. N. B.: не забудьте добавить фамилию автора в ref, если " +
                "источник используется в сносках {{tl|sfn}}!",
            pages=check_wp_template_regexp(viet_pages_content, template),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        template = "Cite press release"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="Используйте шаблоны {{tl|Книга}}, {{tl|Статья}} или {{tl|Cite web}} вместо " +
                "этого шаблона, чтобы ссылки отображались в принятом для русских публикаций " +
                "формате.",
            pages=check_wp_template_regexp(viet_pages_content, template),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        template = "PDFlink"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="Используйте шаблоны {{tl|Книга}}, {{tl|Статья}} или {{tl|Cite web}} вместо " +
                "этого шаблона, чтобы ссылки отображались в принятом для русских публикаций " +
                "формате.",
            pages=check_wp_template_regexp(viet_pages_content, template),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        template = "Wayback"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="Служебный шаблон для бота-архиватора. Ссылку и шаблон желательно " +
                "переоформлять на {{tl|cite web}}, {{tl|Книга}} или {{tl|Статья}} с параметрами " +
                "''archiveurl'' и ''archivedate''.",
            pages=check_wp_template_regexp(viet_pages_content, template),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        template = "webarchive"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="Ссылку и шаблон желательно переоформлять на " +
                "{{tl|cite web}}, {{tl|Книга}} или {{tl|Статья}} с параметрами " +
                "''archiveurl'' и ''archivedate''.",
            pages=check_wp_template_regexp(viet_pages_content, template),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        template = "Архивировано"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="Ссылку и шаблон желательно переоформлять на " +
                "{{tl|cite web}}, {{tl|Книга}} или {{tl|Статья}} с параметрами " +
                "''archiveurl'' и ''archivedate''.",
            pages=check_wp_template_regexp(viet_pages_content, template),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        template = "Проверено"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="",
            pages=check_wp_template_regexp(viet_pages_content, template),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        template = "ISBN"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="Можно заменить на {{tl|книга}} с параметром ''isbn''.",
            pages=check_wp_template_regexp(viet_pages_content, template),
            total=len(viet_pages))
        )

    if checks_enabled["Experimental"]:
        template = "h"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="",
            pages=check_wp_template_regexp(viet_pages_content, template),
            total=len(viet_pages))
        )

    # End of templates checks

    if checks_enabled["CiteDecorations"]:
        checks.append(Check(
            name="IconTemplates",
            title="Страницы с *icon-шаблонами",
            descr="Не требуются, если ссылка оформлена в <code><nowiki>{{cite web}}</nowiki>" +
                "</code>.",
            pages=check_wp_icon_template(viet_pages_content),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        checks.append(Check(
            name="RefTemplates",
            title="Страницы с ref-шаблонами",
            descr="Не требуются, если ссылка оформлена в <code><nowiki>{{cite web}}</nowiki>" +
                "</code>.",
            pages=check_wp_ref_templates(viet_pages_content),
            total=len(viet_pages))
        )

    checks.append(Check(
        name="Isolated",
        title="Изолированные статьи",
        descr="В другие статьи Википедии нужно добавить ссылки на такую статью, а потом удалить " +
            "из неё шаблон об изолированности.",
        pages=check_wp_isolated(viet_pages_content),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="Empty",
        title="Очень короткие статьи",
        descr="Содержат шаблон<code><nowiki>{{rq|empty}}</nowiki></code> или {{tl|дописать}}.",
        pages=check_wp_pages_empty(viet_pages_content),
        total=len(viet_pages))
    )

    no_sources_pages = check_wp_no_sources(viet_pages_content)
    no_sources_titles = [p.title for p in no_sources_pages]
    # print(no_sources_titles)
    checks.append(Check(
        name="NoSources",
        title="Статьи без источников",
        descr="Статьи без разделов «Ссылки», «Литература», «Источники», примечаний или других " +
            "признаков наличия источников.",
        pages=no_sources_pages,
        total=len(viet_pages))
    )

    checks.append(Check(
        name="SourceRequest",
        title="Страницы с запросом источников",
        descr="Добавьте источники, а затем уберите шаблон запроса с исправленной страницы.",
        pages=check_wp_source_request(viet_pages_content, no_sources_titles),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="LinksUnanvailable",
        title="Недоступные ссылки",
        descr="Нужно обновить ссылку, найти страницу в [http://web.archive.org/ архиве] или " +
            "подобрать другой источник.",
        pages=check_wp_links_unavailable(viet_pages_content),
        total=len(viet_pages))
    )

    template = "Аффилированные источники"
    checks.append(Check(
        name=f"TemplateRegexp {template}",
        title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
        descr="",
        pages=check_wp_template_regexp(viet_pages_content, template),
        total=len(viet_pages))
    )

    template = "Спам-ссылки"
    checks.append(Check(
        name=f"TemplateRegexp {template}",
        title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
        descr="",
        pages=check_wp_template_regexp(viet_pages_content, template),
        total=len(viet_pages))
    )

    template = "Обновить"
    checks.append(Check(
        name=f"TemplateRegexp {template}",
        title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
        descr="",
        pages=check_wp_template_regexp(viet_pages_content, template),
        total=len(viet_pages))
    )

    template = "V"
    checks.append(Check(
        name=f"TemplateRegexp {template}",
        title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
        descr="",
        pages=check_wp_template_regexp(viet_pages_content, template),
        total=len(viet_pages))
    )

    template = "закончить перевод"
    checks.append(Check(
        name=f"TemplateRegexp {template}",
        title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
        descr="",
        pages=check_wp_template_regexp(viet_pages_content, template),
        total=len(viet_pages))
    )

    template = "плохой перевод"
    checks.append(Check(
        name=f"TemplateRegexp {template}",
        title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
        descr="",
        pages=check_wp_template_regexp(viet_pages_content, template),
        total=len(viet_pages))
    )

    template = "Нерабочие сноски"
    checks.append(Check(
        name=f"TemplateRegexp {template}",
        title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
        descr="",
        pages=check_wp_template_regexp(viet_pages_content, template),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="ArabicNumerals",
        title="Века арабскими цифрами",
        descr="Номера веков должны быть записаны рисмкими цифрами, см. [[ВП:ДАТЫ]].",
        pages=check_wp_centuries(viet_pages_content),
        total=len(viet_pages))
    )

    if checks_enabled["Experimental"]:
        checks.append(Check(
            name="BadDelimiters",
            title="Неформатные разделители в числах",
            descr="В тексте есть конструкции вида 1,234,567 или 12.345.678. Если это одно число, " +
                "то в качестве разделителя групп цифр нужно использовать пробел (см. [[ВП:Ч]]).",
            pages=check_wp_pages_delimiters(viet_pages_content),
            total=len(viet_pages))
        )

    if checks_enabled["Communes"]:
        checks.append(Check(
            name="Communes",
            title="Коммуны",
            descr="Это актуально только для ПРО:Вьетнам, в прочих случаях должно быть выключено. " +
                "В статьях о Вьетнаме ''коммуны'' (равно как ''приходы'' и, в большинстве " +
                "случаев, ''деревни'') следует заменить на ''общины''.",
            pages=check_wp_communes(viet_pages_content),
            total=len(viet_pages))
        )

    ### Overwikified dates ###
    # TODO rewrite this
    # пока на похер работает как работает

    #print(datetime.datetime.now(), "lets work on links")

    from itertools import groupby
    internal_links = get_wp_internal_links(viet_pages_content)
    date_links = []
    rx_date = r"^[0-9]* (?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)$"
    rx_year = r"^[0-9]* год$"
    for link in internal_links:
        #print(link)
        if re.search(rx_date, link.link) or re.search(rx_year, link.link):
            date_links.append(link)

    sorted_dates = sorted(date_links, key=lambda x: x.page, reverse=True)
    grouped_dates = [list(result) for key, result in groupby(
        sorted_dates, key=lambda olink: olink.page)]

    sorted_counted_dates = []
    for page in grouped_dates:
        # print(page[0].page, len(page))
        if len(page) > check_template["overdated_threshold"]:
            sorted_counted_dates.append({
                "page": page[0].page,
                "count": len(page)
            })
    #scs_dates = sorted(sorted_counted_dates, key=lambda x: x['count'], reverse=True)
    #print(scs_dates)

    final_dates = []
    I_LIMIT = 20
    i = 0
    for date_page in sorted(sorted_counted_dates, key=lambda x: x['count'], reverse=True):
        if i < I_LIMIT and not re.search(r"^Хронология ", date_page['page']) and \
          not re.search(r"^Список ", date_page['page']):
            i = i + 1
            #print(f"* [[{date_page['page']}]] ({date_page['count']})")
            final_dates.append(ProblemPage(title=date_page['page'],counter=date_page['count']))

    checks.append(Check(
        name="OverDated",
        title="Статьи с наиболее перевикифицированными датами",
        pages=final_dates,
        total=len(viet_pages),
        supress_stat=True)
    )

    ### Search for disambigs ###
    if checks_enabled["Disambigs"]:
        i = 0
        batch_size = 20
        # set by Wikipedia
        BATCH_HARD_LIMIT = 50
        BATCH_LENGTH = 1300
        batch_unknown = []

        da_total,da_cache_hits = 0,0
        for il in internal_links:
            da_total += 1
            i += 1
            il.link = normalize_link(il.link)
            if il.link == "":
                continue
            # TODO replace with page:isdisambig:
            red_cached = red_con.get(f"page:status:{il.link}")
            if il.link == "":
                pass
            elif red_cached == "4" or red_cached == "1":
                da_cache_hits += 1
            elif red_cached == "2":
                da_cache_hits += 1
                disambigs.append(il)
            # elif red_cached == 3:
                # print(f"{red_cached} is a redirect")
                # redirects.append(mb_page['title'])
            else:
                batch_unknown.append(il)
            #if len(batch_unknown) > batch_size:
            if sum(len(s.link) for s in batch_unknown) > BATCH_LENGTH or \
              len(batch_unknown) >= BATCH_HARD_LIMIT:
                print("Checker invoked", i, "/", len(internal_links),
                    "( len", sum(len(s.link) for s in batch_unknown),
                    ", items", len(batch_unknown), ")")
                dis_or_not_append = get_disambigs(batch_unknown,red_con)
                # long_redirects = long_redirects + long_redirects_append
                for ib in batch_unknown:
                    ib2 = normalize_link(ib.link)
                    if ib2 in dis_or_not_append:
                        disambigs.append(ib)
                batch_unknown = []
            print(f"{round(100*da_total/len(internal_links), 2)}% disambigs",
                f"checked ({da_total} of {len(internal_links)});", \
                f"cache hits: {round(100*da_cache_hits/da_total, 2)}% so far, "
                f"{round(100*da_cache_hits/len(internal_links), 3)}% in total")
        # It becomes ordered by tha magic
        disambig_ordered = {}
        for da in disambigs:
            if not da.page in disambig_ordered:
                disambig_ordered[da.page] = {}
            if not da.link in disambig_ordered[da.page]:
                disambig_ordered[da.page][da.link] = True
            #disambig_ordered[da.page][da.link] = disambig_ordered[da.page][da.link] + 1
        disambig_problems = []
        for i_p, key_p in enumerate(disambig_ordered):
            samples = []
            for i_l, key_l in enumerate(disambig_ordered[key_p]):
                samples.append(f'[[{key_l}]]')
            disambig_problems.append(ProblemPage(title=key_p, \
              samples=samples))
        #print("creating check for", len(disambig_problems), "problems", disambig_problems)
        checks.append(Check(
            name="BadLinks",
            title="Ссылки на неоднозначности",
            descr="Такую ссылку надо заменить ссылкой на нужную статью, а если всё-таки " +
                "необходимо оставить ссылку на дизамбиг, то завернуть её в {{tl|D-l}}.",
            pages=disambig_problems,
            total=len(viet_pages))
        )

    # End of checks

    ### Rendering ###

    environment = Environment(loader=FileSystemLoader("templates/"),
                      trim_blocks=True,
                      lstrip_blocks=True)
    template = environment.get_template("index.wp")

    content = template.render(
        prologue = check_template['prologue'],
        epilogue = check_template['epilogue'],
        viet_pages_not_patrolled = viet_pages_not_patrolled,
        viet_pages_old_patrolled = viet_pages_old_patrolled,
        checks = checks,
        template_options = template_options
    )

    ### Publishing ###

    # Local file
    # This goes before the web. If web posting fails, we'll be able to debug using this

    with open(output_file, mode="w", encoding="utf-8") as message:
        message.write(content)
        print(f"... wrote {output_file}")

    # Web
    # exit(0)
    if set_wp_page_text(session, post_results_page, content, summary):
        print("Updated.")
    else:
        print("Cannot update page.")

    ### Stats ###
    print(datetime.datetime.now()-moment_start)
