import datetime

from jinja2 import Environment, FileSystemLoader

from wp_functions_aux import get_wp_pages_by_template, get_wp_pages_content
from wp_functions_check import *

area = "Vietnam"

checks = []

class Check():
    def __init__(self, name="", title="", descr="", pages=[], total=0, nowiki=False):
        self.name = name
        self.title = title
        self.descr = descr
        self.percent = 100*len(pages)/total # or 0
        self.counter = len(pages)
        self.pages = pages
        self.nowiki = nowiki
    def __repr__(self):
        return f'{self.name} ({self.counter} pages found)'

#viet_pages = get_pages_by_template("Шаблон:Статья проекта Карелия",1)
viet_pages = get_wp_pages_by_template("Шаблон:Статья проекта Вьетнам",1)
stat = {
    "name": "Total",
    "text": "Всего",
    "counter": len(viet_pages),
    "percent": 100
}
# stats.append(stat)

### Patrolling ####

viet_pages_content, viet_pages_not_patrolled, viet_pages_old_patrolled = \
    get_wp_pages_content(viet_pages=viet_pages)
print("Total pages retrieved:", len(viet_pages_content), "of", len(viet_pages))
stat = {
    "name": "NotPatrolled",
    "text": "Не отпатрулированные статьи",
    "counter": len(viet_pages_not_patrolled)+len(viet_pages_old_patrolled),
    "percent": 100*(len(viet_pages_not_patrolled)+len(viet_pages_old_patrolled))/len(viet_pages)
}
# stats.append(stat)


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
    name="NoRefs",
    title="Нет примечаний в разделе «Примечания»",
    descr="Не считает примечания, подтянутые из ВД. В любом случае, было бы неплохо добавить " + \
        "сноски в тело статьи.",
    pages=check_wp_no_refs(viet_pages_content),
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
    name="BadSquareKm",
    title="Страницы с кв км или кв. км",
    descr="Желательно поменять на км².",
    pages=check_wp_pages_square_km(viet_pages_content),
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
    name="Empty",
    title="Очень короткие статьи",
    descr="Содержат шаблон<code><nowiki>{{rq|empty}}</nowiki></code>.",
    pages=check_wp_pages_empty(viet_pages_content),
    total=len(viet_pages))
)

checks.append(Check(
    name="IconTemplates",
    title="Страницы с *icon-шаблонами",
    descr="Не требуются, если ссылка оформлена в <code><nowiki>{{cite web}}</nowiki></code>.",
    pages=check_wp_icon_template(viet_pages_content),
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
    name="NoLinksInLinks",
    title="Статьи без ссылок в разделе «Ссылки»",
    descr="Если в «Ссылках» есть источники без http-сылок, то их, возможно, стоит переместить " + \
        "в раздел «Литература».",
    pages=check_wp_no_links_in_links(viet_pages_content),
    total=len(viet_pages))
)

checks.append(Check(
    name="SourceRequest",
    title="Страницы с запросом источников",
    descr="Добавьте источники, а затем уберите шаблон запроса с исправленной страницы.",
    pages=check_wp_source_request(viet_pages_content),
    total=len(viet_pages))
)


print(checks)

### Rendering ###

environment = Environment(loader=FileSystemLoader("templates/"),
                  trim_blocks=True,
                  lstrip_blocks=True)
template = environment.get_template("index.wp")

FILENAME = r'C:\Users\Dm\Desktop\wp\badlinks-{}.py.txt'.format(area)
content = template.render(
    viet_pages_not_patrolled = viet_pages_not_patrolled,
    viet_pages_old_patrolled = viet_pages_old_patrolled,
    checks = checks,
    timestamp = datetime.datetime.now()
)
with open(FILENAME, mode="w", encoding="utf-8") as message:
    message.write(content)
    print(f"... wrote {FILENAME}")
