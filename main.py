import datetime

from jinja2 import Environment, FileSystemLoader

from wp_functions_aux import get_wp_pages_by_template, get_wp_pages_content, get_wp_page_sections
from wp_functions_aux import get_wp_internal_links
from wp_functions_check import *

area = "Vietnam"

checks = []

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

UPDATES = [
    {'date': datetime.datetime(2023, 10, 17, 22, 22),
     'text': "Новая проверка: Архив добавлен ботом"}
]

AREAS = [ "Vietnam", "Karelia", "Vologda", "cybersport", "Tatarstan", "Holocaust", "Belarus",
    "Israel", "SverdlovskObl" ]
AREAS = [ "Holocaust" ]

###############################
###### ITERATE FROM HERE ######
###############################

area = AREAS[0]

exclude_pages = []
# output_file = f"C:\Users\Dm\Desktop\wp\badlinks-{area}.py.txt"
output_file = f"C:/Users/Dm/Desktop/wp/badlinks-{area}.py.txt"
prologue = ""
post_results = False
post_results_page = ""
summary = "плановое обновление данных"
checks_enabled = {
    "CiteDecorations": True,
    "Communes": False,
    "Experimental": False
}

# FIXME тупо перенесено почти 1:1

if area == "Vologda":
    viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Вологда", 1)
    post_results_page = "Проект:Вологда/Недостатки статей"
elif area == "Vietnam":
    viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Вьетнам", 1)
    checks_enabled["Communes"] = True
    checks_enabled["Experimental"] = True
    post_results_page = "Участник:Klientos/Ссылки проекта Вьетнам"
elif area == "Holocaust":
    viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Холокост", 1)
    checks_enabled["CiteDecorations"] = False
    prologue = "Исправленные проблемы просьба убирать из списка!"
    post_results_page = "Проект:Холокост/Недостатки статей"
elif area == "Belarus":
    # TODO исключения
    exclude_pages = [ "Белоруссия/Шапка" ]
    viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Белоруссия", 1)
    checks_enabled["CiteDecorations"] = False
    post_results_page = "Проект:Белоруссия/Недостатки статей"
elif area == "Israel":
    viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Израиль", 1)
    checks_enabled["CiteDecorations"] = False
    post_results_page = "Проект:Израиль/Недостатки статей"
elif area == "SverdlovskObl":
    viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Свердловская область", 1)
    post_results_page = "Проект:Свердловская область/Недостатки статей"

    # } elseif ($area -like "Tatarstan") {
        # $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Татарстан" | where {$_ -notin $excludePages } | sort
        # $postResults = $true
        # $postResultsPage = "Проект:Татарстан/Недостатки статей"
    # } elseif ($area -like "cybersport") {
        # $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Киберспорт" | where {$_ -notin $excludePages } | sort
        # $postResults = $true
        # $postResultsPage = "Проект:Киберспорт/Недостатки статей"
    # } elseif ($area -like "Karelia") {
        # $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Карелия" | where {$_ -notin $excludePages } | sort
        # $postResults = $true
        # $postResultsPage = "Проект:Карелия/Недостатки статей"
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
    get_wp_pages_content(viet_pages=viet_pages)
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
    if i < I_LIMIT:
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

#print(checks)

### Rendering ###

environment = Environment(loader=FileSystemLoader("templates/"),
                  trim_blocks=True,
                  lstrip_blocks=True)
template = environment.get_template("index.wp")

content = template.render(
    prologue = prologue,
    viet_pages_not_patrolled = viet_pages_not_patrolled,
    viet_pages_old_patrolled = viet_pages_old_patrolled,
    checks = checks,
    timestamp = datetime.datetime.now()
)
with open(output_file, mode="w", encoding="utf-8") as message:
    message.write(content)
    print(f"... wrote {output_file}")
