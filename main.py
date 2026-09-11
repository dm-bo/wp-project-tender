"""
Script/bot to search for issues in the Wikipedia project
For details, please see https://ru.wikipedia.org/wiki/Участник:KlientosBot
"""

import sys
import datetime
# for projects shuffling
import random
import re

from jinja2 import Environment, FileSystemLoader

from wp_functions_aux import get_wp_pages_by_template, get_wp_pages_by_category_recurse
from wp_functions_aux import get_wp_authenticated_session, set_wp_page_text
from wp_functions_aux import get_wp_content_cached
from wp_functions_aux import parse_check_template, build_running_config
#
from wp_functions_check import check_links_to_disambigs_fast
from wp_functions_check import check_patrolling
from wp_functions_check import check_wp_overdated

from get_all_redirects_2 import ensure_redirects_cache

# for fun
from wp_functions_aux import get_wp_pages_by_category

from wp_functions_check import check_wp_naked_links, \
    check_wp_no_links_in_links, \
    check_wp_no_refs, \
    check_wp_pages_direct_interwikis, \
    check_wp_wp_links, \
    check_wp_wkimedia_links, \
    check_wp_pages_bot_titles, \
    check_wp_pages_bot_archives, \
    check_wp_no_cats, \
    check_wp_pages_direct_googlebooks, \
    check_wp_pages_direct_webarchive, \
    check_wp_snprep, \
    check_wp_semicolon_sections, \
    check_wp_too_few_wikilinks, \
    check_wp_poor_dates, \
    check_wp_pages_square_km, \
    check_wp_pages_square_km_sup, \
    check_wp_pages_square_m_sup, \
    check_wp_links_in_text, \
    check_wp_template_regexp, \
    check_wp_icon_template, \
    check_wp_ref_templates, \
    check_wp_isolated, \
    check_wp_pages_empty, \
    check_wp_no_sources, \
    check_wp_source_request, \
    check_wp_links_unavailable, \
    check_wp_centuries2, \
    check_wp_pages_delimiters, \
    check_wp_communes, \
    check_wp_images


# from wp_functions_check import *

from wp_auth_data import get_auth_data
from config import get_redis_client, get_tender_config

# TODO ! check if session is interactive -> confirm cache reload

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
auth_data = get_auth_data()
session = get_wp_authenticated_session(auth_data["wp_login"], auth_data["wp_passw"])

# Script config
script_config = get_tender_config()

# Redis fun
red_con = get_redis_client()

###############################
###### ITERATE FROM HERE ######
###############################

# NS 104 - project discussions
result_pages = get_wp_pages_by_template("User:KlientosBot/project-tender", 104)
# print("Pages by template =", result_pages)
random.shuffle(result_pages)
print("Pages by template randomized =", result_pages)

result_pages_static = None
#result_pages_static = ["Проект:Холокост/Недостатки статей", "Проект:Мифология/Недостатки статей"]
#result_pages_static = ['Проект:Вьетнам/Недостатки статей']
#result_pages_static = ['Проект:Россия/Недостатки статей/Вологодская область']
if result_pages_static:
    print()
    print("NOTICE: запускаем со статичным набором страниц.")
    print()
    print("Было:",result_pages)
    result_pages = result_pages_static
    print("Стало:",result_pages)

# DISAMBIGS CACHING
REDIRECTS_KEY = "wiki:ru:redirects"
REDIRECTS_TTL = 3 * 24 * 3600
RELOAD_THRESHOLD = 3 * 3600
ttl = red_con.ttl(script_config["REDIS_DISAMB_SET"])
if ttl >= script_config["REDIS_SET_RELOAD_THRESHOLD"]:
    print(f"Disambig cache is still warm ({round(ttl/3600, 1)} hours)")
else:
    disambs = get_wp_pages_by_category("Категория:Страницы значений по алфавиту", namespace=0)
    red_con.delete(script_config["REDIS_DISAMB_SET"])
    red_con.sadd(script_config["REDIS_DISAMB_SET"], *disambs)
    red_con.expire(script_config["REDIS_DISAMB_SET"], REDIRECTS_TTL)
    print("Got some disambigs:", len(disambs))

# REDIRECTS CACHING
ensure_redirects_cache(red_con)

# iterate over found projects
for post_results_page in result_pages:
    print("")
    print("Working on", post_results_page)
    checks = []
    exclude_pages = []
    # prologue = ""
    epilogue = ""
    summary = "плановое обновление данных"
    checks_enabled = {
        "CiteDecorations": True,
        "PoorDates": True,
        "Communes": False,
        "Images": False,
        "Experimental": False,
        "Disambigs": False,
        "UglyRedirects": False
    }

    # TODO rework messy config parser
    # Checking that result page is not too fresh
    result_content = get_wp_content_cached([post_results_page],red_con)
    mc1 = re.findall(r"{{User:Klientos(?:Bot)?/project-tender[ \n]*\|[^}]*}}",
        result_content[0]['content'])
    template_options = ""
    if mc1:
        check_template = parse_check_template(mc1[0])
        print(check_template)
        # TODO replace all following "check_template" with running_config
        running_config = build_running_config(post_results_page, check_template, script_config)

        if running_config["timestamp_date"] + datetime.timedelta(days=running_config["time_cooldown"]) \
          > datetime.datetime.now():
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
            excludes_content = get_wp_content_cached([check_template['except_pages']],red_con)
            exclude_pages = re.findall(r"\[\[([^\|\]\:]*)[\|\]]", excludes_content[0]['content'])
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
    OUTPUT_FILE = f"C:/Users/Dm/Desktop/wp/badlinks-{area}.py.txt"

    print("Updating page ", post_results_page)

    print("Total pages found:", len(viet_pages))
    viet_pages = list(set(viet_pages) - set(exclude_pages))
    print("After omitting some pages:", len(viet_pages))

    # Some custom hacks
    # if post_results_page == "Проект:Вьетнам/Недостатки статей":
        # checks_enabled["Disambigs"] = False
        # checks_enabled["UglyRedirects"] = False

    checks.append(Check(
        name="Total",
        title="Всего",
        pages=viet_pages,
        total=len(viet_pages),
        supress_listing=True)
    )

    ### Patrolling ####

    pages_content2 = get_wp_content_cached(viet_pages,red_con)
    checks.append(Check(
        name="NotPatrolled",
        title="Не отпатрулированные статьи",
        pages=check_patrolling(pages_content2),
        total=len(viet_pages))
    )

    ### Checks ###

    checks.append(Check(
        name="NakedLinks",
        title="Голые ссылки",
        descr="Нужно оформить ссылку в [[Ш:cite web]] или, хотя бы, в <code><nowiki>" + \
            "[http://example.com Title]</nowiki></code>.",
        pages=check_wp_naked_links(pages_content2),
        total=len(viet_pages),
        nowiki=True)
    )

    print("Engaging check NoLinksInLinks and beyond")
    checks.append(Check(
        name="NoLinksInLinks",
        title="Статьи без ссылок в разделе «Ссылки»",
        descr="Если в «Ссылках» есть источники без http-сылок, то их, возможно, стоит " + \
            "переместить в раздел «Литература».",
        pages=check_wp_no_links_in_links(pages_content2,r=red_con),
        total=len(viet_pages))
    )

    # print("Engaging check NoRefs")
    checks.append(Check(
        name="NoRefs",
        title="Нет примечаний в разделе «Примечания»",
        descr="Не считает примечания, подтянутые из ВД. В любом случае, было бы неплохо " + \
            "добавить сноски в тело статьи.",
        pages=check_wp_no_refs(pages_content2),
        total=len(viet_pages))
    )

    #print(check_result)
    checks.append(Check(
        name="DirectInterwikis",
        title="Статьи с прямыми интервики-ссылками",
        descr="Нужно заменить на шаблон iw или добавить прямую ссылку на статью в РуВП, если " + \
            "она уже есть.",
        pages=check_wp_pages_direct_interwikis(pages_content2),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="WPLinks",
        title="Ссылки на ВП как внешние",
        descr="<nowiki>[http://ссылки]</nowiki> нужно поменять на <nowiki>[[ссылки]]</nowiki>.",
        pages=check_wp_wp_links(pages_content2),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="WMLinks",
        title="Ссылки на проекты Викимедиа как внешние",
        descr="Вместо прямых ссылок на сестринские проекты используйте внутренние ссылки " +
            "вида <code><nowiki>[[q:en:Star Wars]]</nowiki></code> (см. " +
            "[[Википедия:Интервики#Коды проектов Фонда]]).",
        pages=check_wp_wkimedia_links(pages_content2),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="BotTitles",
        title="Заголовок добавлен ботом",
        descr="Нужно проверить, что заголовок правильный, и убрать html-комментарий ''<nowiki>" + \
            "<!-- Заголовок добавлен ботом --> или <!-- Bot generated title --></nowiki>''.",
        pages=check_wp_pages_bot_titles(pages_content2),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="BotArchives",
        title="Архив добавлен ботом",
        descr="Нужно проверить архив, и убрать html-комментарий ''<nowiki><!-- Bot retrieved " + \
            "archive --></nowiki>''.",
        pages=check_wp_pages_bot_archives(pages_content2),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="NoCats",
        title="Не указаны категории",
        descr="Иногда категории назначаются шаблонами, тогда указывать категории напрямую не " +
            "нужно. В таком случае категоризирующий шаблон следует учитывать при составлении " +
            "этого списка.",
        pages=check_wp_no_cats(pages_content2,r=red_con),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="DirectGoogleBooks",
        title="Прямые ссылки на Google books",
        descr="Их желательно поменять на [[Шаблон:книга]].",
        pages=check_wp_pages_direct_googlebooks(pages_content2),
        total=len(viet_pages))
    )

    if checks_enabled["CiteDecorations"] :
        checks.append(Check(
            name="DirectWebarchive",
            title="Прямые ссылки на web.archive.org",
            descr="Желательно заменить их на [[Ш:cite web]] с параметрами archiveurl и " +
                "archivedate.",
            pages=check_wp_pages_direct_webarchive(pages_content2),
            total=len(viet_pages))
        )

    checks.append(Check(
        name="SNPREP",
        title="[[ВП:СН-ПРЕП|СН-ПРЕП]]",
        descr="Страницы, в тексте которых есть <code><nowiki>.<ref</nowiki></code> или " +
            "<code><nowiki>.{{sfn</nowiki></code>, либо их вариации с пробелами, как <code>" +
            "<nowiki>. <ref</nowiki></code>, а также те же сочетания с запятой. " +
            "Сноска должна стоять перед точкой или запятой, кроме случаев, "+
            "когда точка является частью сокращения.",
        pages=check_wp_snprep(pages_content2),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="SemicolonSections",
        title=";Недоразделы",
        descr="Использована кострукция <code><nowiki>;Что-то</nowiki></code>. Скорее всего, её " +
            "следует заменить, например, на <code><nowiki>=== Что-то ===</nowiki></code>.",
        pages=check_wp_semicolon_sections(pages_content2),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="TooFewWikilinks",
        title="Мало внутренних ссылок",
        descr="Добавьте больше.",
        pages=check_wp_too_few_wikilinks(pages_content2),
        total=len(viet_pages))
    )

    if checks_enabled["PoorDates"]:
        checks.append(Check(
            name="PoorDates",
            title="Неформатные даты в cite web",
            descr="Используйте формат <code>YYYY-MM-DD</code> ([[ВП:ТД]]).",
            pages=check_wp_poor_dates(pages_content2),
            total=len(viet_pages),
            nowiki=True)
        )

    checks.append(Check(
        name="BadSquareKm",
        title="Страницы с кв км или кв. км",
        descr="Желательно поменять на км².",
        pages=check_wp_pages_square_km(pages_content2),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="BadSquareKmSup",
        title="Страницы с <nowiki>км<sup>2</sup></nowiki>",
        descr="Желательно поменять на км².",
        pages=check_wp_pages_square_km_sup(pages_content2),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="BadSquareMSup",
        title="Страницы с <nowiki>м<sup>2</sup></nowiki>",
        descr="Желательно поменять на м².",
        pages=check_wp_pages_square_m_sup(pages_content2),
        total=len(viet_pages))
    )

    print("Engaging check LinksInText")
    checks.append(Check(
        name="LinksInText",
        title="Ссылки в тексте",
        descr="Не следует вставлять внешние ссылки прямо в текст. Обычно они размещаются в " + \
            "сносках, разделе «Ссылки» и других подобающих местах.",
        pages=check_wp_links_in_text(pages_content2),
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
            pages=check_wp_template_regexp(pages_content2, template),
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
            pages=check_wp_template_regexp(pages_content2, template),
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
            pages=check_wp_template_regexp(pages_content2, template),
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
            pages=check_wp_template_regexp(pages_content2, template),
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
            pages=check_wp_template_regexp(pages_content2, template),
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
            pages=check_wp_template_regexp(pages_content2, template),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        template = "Проверено"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="",
            pages=check_wp_template_regexp(pages_content2, template),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        template = "ISBN"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="Можно заменить на {{tl|книга}} с параметром ''isbn''.",
            pages=check_wp_template_regexp(pages_content2, template),
            total=len(viet_pages))
        )

    if checks_enabled["Experimental"]:
        template = "h"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="",
            pages=check_wp_template_regexp(pages_content2, template),
            total=len(viet_pages))
        )

    # End of templates checks

    if checks_enabled["CiteDecorations"]:
        checks.append(Check(
            name="IconTemplates",
            title="Страницы с *icon-шаблонами",
            descr="Не требуются, если ссылка оформлена в <code><nowiki>{{cite web}}</nowiki>" +
                "</code>.",
            pages=check_wp_icon_template(pages_content2),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        checks.append(Check(
            name="RefTemplates",
            title="Страницы с ref-шаблонами",
            descr="Не требуются, если ссылка оформлена в <code><nowiki>{{cite web}}</nowiki>" +
                "</code>.",
            pages=check_wp_ref_templates(pages_content2),
            total=len(viet_pages))
        )

    checks.append(Check(
        name="Isolated",
        title="Изолированные статьи",
        descr="В другие статьи Википедии нужно добавить ссылки на такую статью, а потом удалить " +
            "из неё шаблон об изолированности.",
        pages=check_wp_isolated(pages_content2),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="Empty",
        title="Очень короткие статьи",
        descr="Содержат шаблон<code><nowiki>{{rq|empty}}</nowiki></code> или {{tl|дописать}}.",
        pages=check_wp_pages_empty(pages_content2),
        total=len(viet_pages))
    )

    # TODO этачо
    no_sources_pages = check_wp_no_sources(pages_content2)
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
        pages=check_wp_source_request(pages_content2, no_sources_titles),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="LinksUnanvailable",
        title="Недоступные ссылки",
        descr="Нужно обновить ссылку, найти страницу в [http://web.archive.org/ архиве] или " +
            "подобрать другой источник.",
        pages=check_wp_links_unavailable(pages_content2),
        total=len(viet_pages))
    )

    template = "Аффилированные источники"
    checks.append(Check(
        name=f"TemplateRegexp {template}",
        title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
        descr="",
        pages=check_wp_template_regexp(pages_content2, template),
        total=len(viet_pages))
    )

    template = "Спам-ссылки"
    checks.append(Check(
        name=f"TemplateRegexp {template}",
        title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
        descr="",
        pages=check_wp_template_regexp(pages_content2, template),
        total=len(viet_pages))
    )

    template = "Обновить"
    checks.append(Check(
        name=f"TemplateRegexp {template}",
        title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
        descr="",
        pages=check_wp_template_regexp(pages_content2, template),
        total=len(viet_pages))
    )

    template = "V"
    checks.append(Check(
        name=f"TemplateRegexp {template}",
        title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
        descr="",
        pages=check_wp_template_regexp(pages_content2, template),
        total=len(viet_pages))
    )

    template = "закончить перевод"
    checks.append(Check(
        name=f"TemplateRegexp {template}",
        title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
        descr="",
        pages=check_wp_template_regexp(pages_content2, template),
        total=len(viet_pages))
    )

    template = "плохой перевод"
    checks.append(Check(
        name=f"TemplateRegexp {template}",
        title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
        descr="",
        pages=check_wp_template_regexp(pages_content2, template),
        total=len(viet_pages))
    )

    template = "Нерабочие сноски"
    checks.append(Check(
        name=f"TemplateRegexp {template}",
        title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
        descr="",
        pages=check_wp_template_regexp(pages_content2, template),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="ArabicNumerals",
        title="Века арабскими цифрами",
        descr="Номера веков должны быть записаны рисмкими цифрами, см. [[ВП:ДАТЫ]].",
        pages=check_wp_centuries2(pages_content2),
        total=len(viet_pages))
    )

    if checks_enabled["Experimental"]:
        checks.append(Check(
            name="BadDelimiters",
            title="Неформатные разделители в числах",
            descr="В тексте есть конструкции вида 1,234,567 или 12.345.678. Если это одно число, " +
                "то в качестве разделителя групп цифр нужно использовать пробел (см. [[ВП:Ч]]).",
            pages=check_wp_pages_delimiters(pages_content2),
            total=len(viet_pages))
        )

    if checks_enabled["Communes"]:
        checks.append(Check(
            name="Communes",
            title="Коммуны",
            descr="Это актуально только для ПРО:Вьетнам, в прочих случаях должно быть выключено. " +
                "В статьях о Вьетнаме ''коммуны'' (равно как ''приходы'' и, в большинстве " +
                "случаев, ''деревни'') следует заменить на ''общины''.",
            pages=check_wp_communes(pages_content2),
            total=len(viet_pages))
        )

    if checks_enabled["Images"]:
        checks.append(Check(
            name="Images",
            title="Нужно добавить изображение",
            descr="В статье стоит запрос изображения, или статья иным образом включена в одну из" +
                "категорий \"Категория:Википедия:Статьи без изображений*\". ",
            pages=check_wp_images(pages_content2),
            total=len(viet_pages))
        )

    ### Overwikified dates ###
    checks.append(Check(
        name="OverDated",
        title="Статьи с наиболее перевикифицированными датами",
        pages=check_wp_overdated(pages_content2,check_template["overdated_threshold"]),
        total=len(viet_pages),
        supress_stat=True)
    )
    #exit(0)

    ### Search for disambigs ###
    if checks_enabled["Disambigs"]:
        checks.append(Check(
            name="BadLinks",
            title="Ссылки на неоднозначности",
            descr="Такую ссылку надо заменить ссылкой на нужную статью, а если всё-таки " +
                "необходимо оставить ссылку на дизамбиг, то завернуть её в {{tl|D-l}}.",
            pages=check_links_to_disambigs_fast(pages_content2,red_con,script_config),
            total=len(viet_pages))
        )

    ### Rendering ###

    environment = Environment(loader=FileSystemLoader("templates/"),
                      trim_blocks=True,
                      lstrip_blocks=True)
    template = environment.get_template("index.wp")

    content = template.render(
        prologue = check_template['prologue'],
        epilogue = check_template['epilogue'],
        checks = checks,
        template_options = template_options
    )

    ### Publishing ###

    # Local file
    # This goes before the web. If web posting fails, we'll be able to debug using this

    with open(OUTPUT_FILE, mode="w", encoding="utf-8") as message:
        message.write(content)
        print(f"... wrote {OUTPUT_FILE}")

    # Web
    # sys.exit(7)
    if set_wp_page_text(session, post_results_page, content, summary):
        print("Updated.")
    else:
        print("Cannot update page.")

    ### Stats ###
    print(datetime.datetime.now()-moment_start)
