import datetime
from dateutil.parser import parse

from jinja2 import Environment, FileSystemLoader

from wp_functions_aux import get_wp_pages_by_template, get_wp_pages_content, get_wp_page_sections
from wp_functions_aux import get_wp_internal_links, get_wp_authenticated_session, set_wp_page_text
from wp_functions_aux import get_disambigs
from wp_functions_check import *

from wp_auth_data import *

class Check():
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

# class AreaConfig():
    # def __init__(self, name="", title="", descr=""):
        # self.name = name
        # self.title = title

moment_start = datetime.datetime.now()
dis_or_not = {}
session = get_wp_authenticated_session(wp_login, wp_passw)

UPDATES = [
    {'date': datetime.datetime(2023, 10, 17, 22, 22),
     'text': "Новая проверка: Архив добавлен ботом"},
    {'date': datetime.datetime(2023, 11, 4, 0, 29),
     'text': "Скрипт переведён на python. Возможны некоторые изменения в формате выдачи, " + \
        "сортировке и результатах проверок."},
    {'date': datetime.datetime(2023, 11, 6, 23, 12),
     'text': "Добавлена проверка неформатных дат в accessdate/access-date"},
    {'date': datetime.datetime(2023, 11, 14, 23, 20),
     'text': "Добавлена проверка неформатных дат в datepublished (алиас для date)"},
    {'date': datetime.datetime(2023, 11, 14, 23, 40),
     'text': "Теперь можно добавлять произвольный текст в конец страницы (например, категории)"},
    {'date': datetime.datetime(2023, 11, 15, 18, 00),
     'text': "Добавлен поиск ссылок на страницы неоднозначностей."}
]

AREAS = [  ]
# ready: 
# "Holocaust", , "Israel", "Christianity" , "Bible", "India"
# already 
# "Vietnam", "Karelia", "Cybersport", "Belarus", "Vologda", "SverdlovskObl", "Tatarstan"
AREAS = [ "Mythology" ]

###############################
###### ITERATE FROM HERE ######
###############################

#area = AREAS[0]
for area in AREAS:
    checks = []
    exclude_pages = []
    # output_file = f"C:\Users\Dm\Desktop\wp\badlinks-{area}.py.txt"
    output_file = f"C:/Users/Dm/Desktop/wp/badlinks-{area}.py.txt"
    prologue = ""
    epilogue = ""
    post_results = False
    post_results_page = ""
    pages_limit = 5000
    summary = "плановое обновление данных"
    checks_enabled = {
        "CiteDecorations": True,
        "Communes": False,
        "Experimental": False,
        "Disambigs": False
    }
    time_cooldown = 5

    # result disambigs
    disambigs = []
    # result ugly redirects
    long_redirects = []
    # maybe we'll need this info (not yet)
    cannot_check = []

    # FIXME тупо перенесено почти 1:1

    if area == "Vologda":
        # post_results = True
        viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Вологда", 1)
        post_results_page = "Проект:Вологда/Недостатки статей"
        checks_enabled["Disambigs"] = True
    elif area == "Vietnam":
        post_results = True
        time_cooldown = 0
        #pages_limit = 20
        viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Вьетнам", 1)
        checks_enabled["Communes"] = True
        checks_enabled["Experimental"] = True
        checks_enabled["Disambigs"] = True
        post_results_page = "Участник:Klientos/Ссылки проекта Вьетнам"
    elif area == "Holocaust":
        post_results = True
        viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Холокост", 1)
        checks_enabled["CiteDecorations"] = False
        prologue = "Исправленные проблемы просьба убирать из списка!"
        post_results_page = "Проект:Холокост/Недостатки статей"
    elif area == "Belarus":
        exclude_pages = [ "Белоруссия/Шапка" ]
        viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Белоруссия", 1)
        checks_enabled["CiteDecorations"] = False
        post_results_page = "Проект:Белоруссия/Недостатки статей"
    elif area == "Israel":
        post_results = True
        viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Израиль", 1)
        checks_enabled["CiteDecorations"] = False
        post_results_page = "Проект:Израиль/Недостатки статей"
    elif area == "SverdlovskObl":
        # TODO категория проекта
        viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Свердловская область", 1)
        post_results_page = "Проект:Свердловская область/Недостатки статей"
        epilogue = "[[Категория:Проект:Свердловская область]]"
    elif area == "Tatarstan":
        viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Татарстан", 1)
        post_results_page = "Проект:Татарстан/Недостатки статей"
    elif area == "Karelia":
        viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Карелия", 1)
        post_results_page = "Проект:Карелия/Недостатки статей"
    elif area == "Cybersport":
        viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Киберспорт", 1)
        post_results_page = "Проект:Киберспорт/Недостатки статей"
    elif area == "Bible":
        post_results = True
        viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Библия", 1)
        post_results_page = "Проект:Библия/Недостатки статей"
        checks_enabled["Disambigs"] = True
    elif area == "Christianity":
        viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Христианство", 1)
        post_results_page = "Проект:Христианство/Недостатки статей"
    elif area == "India":
        post_results = True
        viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Индия", 1)
        post_results_page = "Проект:Индия/Недостатки статей"
    elif area == "Mythology":
        post_results = True
        viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Мифология", 1)
        post_results_page = "Проект:Мифология/Недостатки статей"

        # } elseif ($area -like "Astronomy") {
            # $vietPagesSO = Get-PagesByCategory -Category "Статьи проекта Астрономия высшей важности" | ? { $_ -like "Обсуждение:*"}
            # $vietPagesSO += Get-PagesByCategory -Category "Статьи проекта Астрономия высокой важности" | ? { $_ -like "Обсуждение:*"}
            # $vietPagesSO | % { $vietPages += $_ -replace "Обсуждение:" }
        # } elseif ($area -like "Bollywood") {
            # #$vietPages = Get-PagesByCategory -Category "Кинематограф Индии"
            # $cats = @("Кинематограф Индии")
            # #throw "not implemented yet"
            # $vietPages = $pags
            # $vietPages = @()
        # } else {
            # "INFO: Please set variable `$area first!"
            # throw "no valid area selected"
        # }

    # Checking that result page is not too fresh
    # Searching for actual updates
    
    print("")
    print("==========")
    print("Working on", area)

    print("Total pages found:", len(viet_pages))
    viet_pages = list(set(viet_pages) - set(exclude_pages))
    print("After omitting some pages:", len(viet_pages))

    time_threshold = datetime.datetime.now() - datetime.timedelta(days=time_cooldown)
    result_content = get_wp_pages_content([post_results_page])
    mc = re.findall(r"{{User:Klientos(?:Bot)?/project-tender[ \n]*\|timestamp=([^}\|]*)", result_content[0][0]['content'])
    #print
    if mc:
        print(mc[0])
        dt_obj = parse(mc[0])
        print("From current page:", dt_obj)
        if dt_obj > time_threshold:
            print("Not old enough, skipping")
            continue
        actual_updates = []
        for UPDATE in UPDATES:
            if UPDATE['date'] > dt_obj:
                actual_updates.append(UPDATE['text'])
        if actual_updates:
                summary = summary + ", обновление скрипта"
        has_bot_template = True
    else:
        has_bot_template = False
        actual_updates = []

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
        get_wp_pages_content(viet_pages=viet_pages,limit=pages_limit)
    #print("Total pages retrieved:", len(viet_pages_content), "of", len(viet_pages))
    #print("Not patrolled:", len(viet_pages_old_patrolled), "and", len(viet_pages_not_patrolled))
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

    checks.append(Check(
        name="NoLinksInLinks",
        title="Статьи без ссылок в разделе «Ссылки»",
        descr="Если в «Ссылках» есть источники без http-сылок, то их, возможно, стоит переместить " + \
            "в раздел «Литература».",
        pages=check_wp_no_links_in_links(viet_pages_content),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="NoRefs",
        title="Нет примечаний в разделе «Примечания»",
        descr="Не считает примечания, подтянутые из ВД. В любом случае, было бы неплохо добавить " + \
            "сноски в тело статьи.",
        pages=check_wp_no_refs(viet_pages_content),
        total=len(viet_pages))
    )

    #print(check_result)
    checks.append(Check(
        name="DirectInterwikis",
        title="Статьи с прямыми интервики-ссылками",
        descr="Нужно заменить на шаблон iw или добавить прямую ссылку на статью в РуВП, если она " + \
            "уже есть.",
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
        name="BotTitles",
        title="Заголовок добавлен ботом",
        descr="Нужно проверить, что заголовок правильный, и убрать html-комментарий ''<nowiki>" + \
            "<!-- Заголовок добавлен ботом --></nowiki>''.",
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
        descr="Иногда категории назначаются шаблонами, тогда указывать категории напрямую не нужно. " +
            "В таком случае категоризирующий шаблон следует учитывать при составлении этого списка.",
        pages=check_wp_no_cats(viet_pages_content),
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
            descr="Желательно заменить их на [[Ш:cite web]] с параметрами archiveurl и archivedate.",
            pages=check_wp_pages_direct_webarchive(viet_pages_content),
            total=len(viet_pages))
        )

    checks.append(Check(
        name="SNPREP",
        title="[[ВП:СН-ПРЕП|СН-ПРЕП]]",
        descr="Страницы, в тексте которых есть <code><nowiki>.<ref</nowiki></code> или " + \
            "<code><nowiki>.{{sfn</nowiki></code>, либо их вариации с пробелами, как <code>" + \
            "<nowiki>. <ref</nowiki></code>. Сноска должна стоять перед точкой, кроме случаев, "+ \
            "когда точка является частью сокращения.",
        pages=check_wp_SNPREP(viet_pages_content),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="SemicolonSections",
        title=";Недоразделы",
        descr="Использована кострукция <code><nowiki>;Что-то</nowiki></code>. Скорее всего, её " + \
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

    checks.append(Check(
        name="PoorDates",
        title="Неформатные даты в cite web",
        descr="Используйте формат <code>YYYY-MM-DD</code> ([[ВП:ТД]]).",
        pages=check_wp_poor_dates(viet_pages_content),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="BadSquareKm",
        title="Страницы с кв км или кв. км",
        descr="Желательно поменять на км².",
        pages=check_wp_pages_square_km(viet_pages_content),
        total=len(viet_pages))
    )

    # Template checks (can be looped later)

    if checks_enabled["CiteDecorations"]:
        template = "Citation"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="Используйте шаблоны {{tl|Книга}}, {{tl|Статья}} или {{tl|Cite web}} вместо этого " + \
                "шаблона, чтобы ссылки отображались в принятом для русских публикаций формате.",
            pages=check_wp_template_regexp(viet_pages_content, template),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        template = "Cite press release"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="Используйте шаблоны {{tl|Книга}}, {{tl|Статья}} или {{tl|Cite web}} вместо этого " + \
                "шаблона, чтобы ссылки отображались в принятом для русских публикаций формате.",
            pages=check_wp_template_regexp(viet_pages_content, template),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        template = "PDFlink"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="Используйте шаблоны {{tl|Книга}}, {{tl|Статья}} или {{tl|Cite web}} вместо этого " + \
                "шаблона, чтобы ссылки отображались в принятом для русских публикаций формате.",
            pages=check_wp_template_regexp(viet_pages_content, template),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        template = "Wayback"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="Служебный шаблон для бота-архиватора. Ссылку и шаблон желательно переоформлять на " + \
                "{{tl|cite web}}, {{tl|Книга}} или {{tl|Статья}} с параметрами " + \
                "''archiveurl'' и ''archivedate''.",
            pages=check_wp_template_regexp(viet_pages_content, template),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        template = "webarchive"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="Ссылку и шаблон желательно переоформлять на " + \
                "{{tl|cite web}}, {{tl|Книга}} или {{tl|Статья}} с параметрами " + \
                "''archiveurl'' и ''archivedate''.",
            pages=check_wp_template_regexp(viet_pages_content, template),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        template = "Архивировано"
        checks.append(Check(
            name=f"TemplateRegexp {template}",
            title=f"Страницы с шаблоном [[Шаблон:{template}|]]",
            descr="Ссылку и шаблон желательно переоформлять на " + \
                "{{tl|cite web}}, {{tl|Книга}} или {{tl|Статья}} с параметрами " + \
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
            descr="Не требуются, если ссылка оформлена в <code><nowiki>{{cite web}}</nowiki></code>.",
            pages=check_wp_icon_template(viet_pages_content),
            total=len(viet_pages))
        )

    if checks_enabled["CiteDecorations"]:
        checks.append(Check(
            name="RefTemplates",
            title="Страницы с ref-шаблонами",
            descr="Не требуются, если ссылка оформлена в <code><nowiki>{{cite web}}</nowiki></code>.",
            pages=check_wp_ref_templates(viet_pages_content),
            total=len(viet_pages))
        )

    checks.append(Check(
        name="Isolated",
        title="Изолированные статьи",
        descr="В другие статьи Википедии нужно добавить ссылки на такую статью, а потом удалить " + \
            "из неё шаблон об изолированности.",
        pages=check_wp_isolated(viet_pages_content),
        total=len(viet_pages))
    )

    checks.append(Check(
        name="Empty",
        title="Очень короткие статьи",
        descr="Содержат шаблон<code><nowiki>{{rq|empty}}</nowiki></code>.",
        pages=check_wp_pages_empty(viet_pages_content),
        total=len(viet_pages))
    )

    no_sources_pages = check_wp_no_sources(viet_pages_content)
    no_sources_titles = [p.title for p in no_sources_pages]
    # print(no_sources_titles)
    checks.append(Check(
        name="NoSources",
        title="Статьи без источников",
        descr="Статьи без разделов «Ссылки», «Литература», «Источники», примечаний или других признаков наличия источников.",
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
        descr="Нужно обновить ссылку, найти страницу в [http://web.archive.org/ архиве] или подобрать другой источник.",
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

    if checks_enabled["Communes"]:
        checks.append(Check(
            name="Communes",
            title="Коммуны",
            descr="Это актуально только для ПРО:Вьетнам, в прочих случаях должно быть выключено. " + \
                "В статьях о Вьетнаме ''коммуны'' (равно как ''приходы'' и, в большинстве случаев," + \
                " ''деревни'') следует заменить на ''общины''.",
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
    #sorted_dates = sorted(date_links, key=link)
    # print(sorted_dates)
    # grouped_dates = [list(g[1]) for g in groupby(sorted_dates, page)]
    grouped_dates = [list(result) for key, result in groupby(
        sorted_dates, key=lambda olink: olink.page)]
    # print(grouped_dates)
    # print("===")
    # print(datetime.datetime.now(), "work on links done")

    sorted_counted_dates = []
    for page in grouped_dates:
        # print(page[0].page, len(page))
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
    # TODO rewrite this
    if checks_enabled["Disambigs"]:
        i = 0
        batch_size = 20
        # set by Wikipedia
        batch_hard_limit = 50
        batch_length = 1300
        batch_unknown = []
        for il in internal_links:
            i = i + 1
            il.link = il.link.replace(" "," ").replace("  "," ").replace("_"," ").strip()
            il.link = re.sub("#.*$","", il.link)
            if il.link == "":
                # in case of [[#smth]]
                pass
            elif not il.link in dis_or_not:
                batch_unknown.append(il)
            elif dis_or_not[il.link]:
                disambigs.append(il)
            #if len(batch_unknown) > batch_size:
            if sum(len(s.link) for s in batch_unknown) > batch_length or \
              len(batch_unknown) >= batch_hard_limit:
                print("Checker invoked", i, "/", len(internal_links), "( len", sum(len(s.link) for s in batch_unknown), ", items", len(batch_unknown), ")")
                # Splitted in two to make as long request as possible (this is a first one)
                dis_or_not_append,long_redirects_append = get_disambigs(batch_unknown)
                dis_or_not.update(dis_or_not_append)
                long_redirects = long_redirects + long_redirects_append
                # # Splitted in two to make as long request as possible (this is a second)
                # dis_or_not_append,long_redirects_append = get_disambigs(batch_unknown)
                # dis_or_not.update(dis_or_not_append)
                long_redirects = long_redirects + long_redirects_append
                for ib in batch_unknown:
                    ib2 = ib.link[0].upper() + ib.link[1:]
                    ib2 = ib2.replace(" "," ").replace("  "," ").replace("_"," ").strip()
                    ib2 = re.sub("#.*$","", ib2)
                    if not ib2 in dis_or_not:
                        cannot_check.append(ib)
                    elif dis_or_not[ib2]:
                        disambigs.append(ib)
                batch_unknown = []
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
            descr="Такую ссылку надо заменить ссылкой на нужную статью, а если всё-таки необходимо оставить ссылку на дизамбиг, то завернуть её в {{tl|D-l}}.",
            pages=disambig_problems,
            total=len(viet_pages))
        )
        # side-product
        long_redirects_set = set(long_redirects)
        long_redirects = list(long_redirects_set)
        # TODO construct Problems (now only the page list)
        # checks.append(Check(
            # name="UncheckableLinks",
            # title="Непроверяемые внутренние ссылки",
            # descr="Внутренние ссылки, для которых не получилось определить, редирерект это или нет. " + \
              # "Возможно, с ними что-то не так; надо проверить.",
            # pages=cannot_check,
            # total=len(internal_links))
        # )
        # print("Long redirects are", long_redirects)
        long_redirecting_pages = []
        for il in internal_links:
            if il.link in long_redirects:
                long_redirecting_pages.append(il)
        # print("Long redirects pages are", long_redirecting_pages)
        # TODO rewrire as function (for 3 calls)
        long_redirects_ordered = {}
        for lr in long_redirecting_pages:
            if not lr.page in long_redirects_ordered:
                long_redirects_ordered[lr.page] = {}
            if not lr.link in long_redirects_ordered[lr.page]:
                long_redirects_ordered[lr.page][lr.link] = True
        # print("Long redirects ordered are", long_redirects_ordered)
        long_redirects_problems = []
        for i_p, key_p in enumerate(long_redirects_ordered):
            samples = []
            for i_l, key_l in enumerate(long_redirects_ordered[key_p]):
                samples.append(f'[[{key_l}]]')
            long_redirects_problems.append(ProblemPage(title=key_p, \
              samples=samples))
        # print("Long redirects problems are", long_redirects_problems)
        checks.append(Check(
            name="UglyRedirects",
            title="Громоздкие редиректы",
            descr="Длинные, некрасивые, избыточные редиректы. Такой редирект можно заменить " + \
              "прямой ссылкой на саму статью.<!-- Побочный продукт от поиска дизамбигов -->",
            pages=long_redirects_problems,
            total=len(viet_pages))
        )

    # End of checks

    ### Rendering ###

    environment = Environment(loader=FileSystemLoader("templates/"),
                      trim_blocks=True,
                      lstrip_blocks=True)
    template = environment.get_template("index.wp")

    content = template.render(
        prologue = prologue,
        epilogue = epilogue,
        viet_pages_not_patrolled = viet_pages_not_patrolled,
        viet_pages_old_patrolled = viet_pages_old_patrolled,
        checks = checks,
        updates = actual_updates,
        timestamp = datetime.datetime.now()
    )

    ### Publishing ###

    # Web

    if not post_results:
        print("Posting skipped (disabled).")
    elif not has_bot_template:
        print("Posting skipped (no template on the page).")
    elif set_wp_page_text(session, post_results_page, content, summary):
        print("Updated.")
    else:
        print("Cannot update page.")

    # Local file

    with open(output_file, mode="w", encoding="utf-8") as message:
        message.write(content)
        print(f"... wrote {output_file}")
    
    
    ### Stats ###
    print("Checked", len(dis_or_not), "of", len(internal_links))
    print(datetime.datetime.now()-moment_start)
