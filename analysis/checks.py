from .definitions import CheckDefinition
from .functions import (
    check_wp_return_all,
    check_patrolling,
    check_wp_naked_links,
    check_wp_no_links_in_links,
    check_wp_no_refs,
    check_wp_pages_direct_interwikis,
    check_wp_wp_links,
    check_wp_wkimedia_links,
    check_wp_pages_bot_titles,
    check_wp_pages_bot_archives,
    check_wp_no_cats,
    check_wp_pages_direct_googlebooks,
    check_wp_pages_direct_webarchive,
    check_wp_snprep,
    check_wp_semicolon_sections,
    check_wp_too_few_wikilinks,
    check_wp_poor_dates,
    check_wp_pages_square_km,
    check_wp_pages_square_km_sup,
    check_wp_pages_square_m_sup,
    check_wp_links_in_text,
    check_wp_template_regexp,
    check_wp_icon_template,
    check_wp_ref_templates,
    check_wp_isolated,
    check_wp_pages_empty,
    check_wp_no_sources,
    check_wp_source_request,
    check_wp_links_unavailable,
    check_wp_centuries2,
    check_wp_pages_delimiters,
    check_wp_communes,
    check_wp_images,
    check_wp_overdated,
    check_links_to_disambigs_fast
)

CHECKS = [

    CheckDefinition(
        name="Total",
        title="Всего",
        descr="",
        func=check_wp_return_all,
        supress_listing=True
    ),

    CheckDefinition(
        name="NotPatrolled",
        title="Не отпатрулированные статьи",
        descr="",
        func=check_patrolling,
    ),

    CheckDefinition(
        name="NakedLinks",
        title="Голые ссылки",
        descr="Нужно оформить ссылку в [[Ш:cite web]] или, хотя бы, в <code><nowiki>" + \
            "[http://example.com Title]</nowiki></code>.",
        func=check_wp_naked_links,
        nowiki=True,
    ),

    CheckDefinition(
        name="NoLinksInLinks",
        title="Статьи без ссылок в разделе «Ссылки»",
        descr="Если в «Ссылках» есть источники без http-сылок, то их, возможно, стоит " + \
            "переместить в раздел «Литература».",
        func=check_wp_no_links_in_links,
        runtime_kwargs={"r": "red_con"},
    ),

    CheckDefinition(
        name="NoRefs",
        title="Нет примечаний в разделе «Примечания»",
        descr="Не считает примечания, подтянутые из ВД. В любом случае, было бы неплохо " + \
            "добавить сноски в тело статьи.",
        func=check_wp_no_refs, # 1 arg
        #is_enabled_by_default=False,
    ),

    CheckDefinition(
        name="DirectInterwikis",
        title="Статьи с прямыми интервики-ссылками",
        descr="Нужно заменить на шаблон iw или добавить прямую ссылку на статью в РуВП, если " + \
            "она уже есть.",
        func=check_wp_pages_direct_interwikis, # 1 arg
        #kwargs={"r": red_con},
    ),
    #

    CheckDefinition(
        name="WPLinks",
        title="Ссылки на ВП как внешние",
        descr="<nowiki>[http://ссылки]</nowiki> нужно поменять на <nowiki>[[ссылки]]</nowiki>.",
        func=check_wp_wp_links
    ),

    CheckDefinition(
        name="WMLinks",
        title="Ссылки на проекты Викимедиа как внешние",
        descr="Вместо прямых ссылок на сестринские проекты используйте внутренние ссылки " +
            "вида <code><nowiki>[[q:en:Star Wars]]</nowiki></code> (см. " +
            "[[Википедия:Интервики#Коды проектов Фонда]]).",
        func=check_wp_wkimedia_links
    ),
    
    CheckDefinition(
        name="BotTitles",
        title="Заголовок добавлен ботом",
        descr="Нужно проверить, что заголовок правильный, и убрать html-комментарий ''<nowiki>" + \
            "<!-- Заголовок добавлен ботом --> или <!-- Bot generated title --></nowiki>''.",
        func=check_wp_pages_bot_titles
    ),

    CheckDefinition(
        name="BotArchives",
        title="Архив добавлен ботом",
        descr="Нужно проверить архив, и убрать html-комментарий ''<nowiki><!-- Bot retrieved " + \
            "archive --></nowiki>''.",
        func=check_wp_pages_bot_archives
    ),

    CheckDefinition(
        name="NoCats",
        title="Не указаны категории",
        descr="Иногда категории назначаются шаблонами, тогда указывать категории напрямую не " +
            "нужно. В таком случае категоризирующий шаблон следует учитывать при составлении " +
            "этого списка.",
        func=check_wp_no_cats,
        runtime_kwargs={"r": "red_con"},
    ),

    CheckDefinition(
        name="DirectGoogleBooks",
        title="Прямые ссылки на Google books",
        descr="Их желательно поменять на [[Шаблон:книга]].",
        func=check_wp_pages_direct_googlebooks,
    ),

    CheckDefinition(
        name="DirectWebarchive",
        title="Прямые ссылки на web.archive.org",
        descr="Желательно заменить их на [[Ш:cite web]] с параметрами archiveurl и " +
            "archivedate.",
        func=check_wp_pages_direct_webarchive,
    ),

    CheckDefinition(
        name="SNPREP",
        title="[[ВП:СН-ПРЕП|СН-ПРЕП]]",
        descr="Страницы, в тексте которых есть <code><nowiki>.<ref</nowiki></code> или " +
            "<code><nowiki>.{{sfn</nowiki></code>, либо их вариации с пробелами, как <code>" +
            "<nowiki>. <ref</nowiki></code>, а также те же сочетания с запятой. " +
            "Сноска должна стоять перед точкой или запятой, кроме случаев, "+
            "когда точка является частью сокращения.",
        func=check_wp_snprep,
    ),

    CheckDefinition(
        name="SemicolonSections",
        title=";Недоразделы",
        descr="Использована кострукция <code><nowiki>;Что-то</nowiki></code>. Скорее всего, её " +
            "следует заменить, например, на <code><nowiki>=== Что-то ===</nowiki></code>.",
        func=check_wp_semicolon_sections,
    ),

    CheckDefinition(
        name="TooFewWikilinks",
        title="Мало внутренних ссылок",
        descr="Добавьте больше.",
        func=check_wp_too_few_wikilinks,
    ),

    CheckDefinition(
        name="PoorDates",
        title="Неформатные даты в cite web",
        descr="Используйте формат <code>YYYY-MM-DD</code> ([[ВП:ТД]]).",
        func=check_wp_poor_dates,
        nowiki=True,
    ),

    CheckDefinition(
        name="BadSquareKm",
        title="Страницы с кв км или кв. км",
        descr="Желательно поменять на км².",
        func=check_wp_pages_square_km,
    ),

    CheckDefinition(
        name="BadSquareKmSup",
        title="Страницы с <nowiki>км<sup>2</sup></nowiki>",
        descr="Желательно поменять на км².",
        func=check_wp_pages_square_km_sup,
    ),

    CheckDefinition(
        name="BadSquareMSup",
        title="Страницы с <nowiki>м<sup>2</sup></nowiki>",
        descr="Желательно поменять на м².",
        func=check_wp_pages_square_m_sup,
    ),

    CheckDefinition(
        name="LinksInText",
        title="Ссылки в тексте",
        descr="Не следует вставлять внешние ссылки прямо в текст. Обычно они размещаются в " + \
            "сносках, разделе «Ссылки» и других подобающих местах.",
        func=check_wp_links_in_text,
        nowiki=True,
    ),
    
    # Template checks

    CheckDefinition(
        name="TemplateRegexp Citation",
        title="Страницы с шаблоном [[Шаблон:Citation|]]",
        descr="Используйте шаблоны {{tl|Книга}}, {{tl|Статья}} или {{tl|Cite web}} вместо " +
            "этого шаблона, чтобы ссылки отображались в принятом для русских публикаций " +
            "формате. N. B.: не забудьте добавить фамилию автора в ref, если " +
            "источник используется в сносках {{tl|sfn}}!",
        func=check_wp_template_regexp,
        kwargs={"template": "Citation"},
    ),

    CheckDefinition(
        name="TemplateRegexp Cite press release",
        title="Страницы с шаблоном [[Шаблон:Cite press release|]]",
        descr="Используйте шаблоны {{tl|Книга}}, {{tl|Статья}} или {{tl|Cite web}} вместо " +
            "этого шаблона, чтобы ссылки отображались в принятом для русских публикаций " +
            "формате.",
        func=check_wp_template_regexp,
        kwargs={"template": "Cite press release"},
    ),

    CheckDefinition(
        name="TemplateRegexp Wayback",
        title="Страницы с шаблоном [[Шаблон:Wayback|]]",
        descr="Служебный шаблон для бота-архиватора. Ссылку и шаблон желательно " +
            "переоформлять на {{tl|cite web}}, {{tl|Книга}} или {{tl|Статья}} с параметрами " +
            "''archiveurl'' и ''archivedate''.",
        func=check_wp_template_regexp,
        kwargs={"template": "Wayback"},
    ),

    CheckDefinition(
        name=f"TemplateRegexp webarchive",
        title=f"Страницы с шаблоном [[Шаблон:webarchive|]]",
        descr="Ссылку и шаблон желательно переоформлять на " +
            "{{tl|cite web}}, {{tl|Книга}} или {{tl|Статья}} с параметрами " +
            "''archiveurl'' и ''archivedate''.",
        func=check_wp_template_regexp,
        kwargs={"template": "webarchive"},
    ),

    CheckDefinition(
        name=f"TemplateRegexp Архивировано",
        title=f"Страницы с шаблоном [[Шаблон:Архивировано|]]",
        descr="Ссылку и шаблон желательно переоформлять на " +
            "{{tl|cite web}}, {{tl|Книга}} или {{tl|Статья}} с параметрами " +
            "''archiveurl'' и ''archivedate''.",
        func=check_wp_template_regexp,
        kwargs={"template": "Архивировано"},
    ),

    CheckDefinition(
        name=f"TemplateRegexp Проверено",
        title=f"Страницы с шаблоном [[Шаблон:Проверено|]]",
        descr="",
        func=check_wp_template_regexp,
        kwargs={"template": "Проверено"},
    ),

    CheckDefinition(
        name=f"TemplateRegexp ISBN",
        title=f"Страницы с шаблоном [[Шаблон:ISBN|]]",
        descr="Можно заменить на {{tl|книга}} с параметром ''isbn''.",
        func=check_wp_template_regexp,
        kwargs={"template": "ISBN"},
    ),

    CheckDefinition(
        name=f"TemplateRegexp h",
        title=f"Страницы с шаблоном [[Шаблон:h|]]",
        descr="",
        func=check_wp_template_regexp,
        is_enabled_by_default=False,
        kwargs={"template": "h"},
    ),

    # End of templates checks

    CheckDefinition(
        name="IconTemplates",
        title="Страницы с *icon-шаблонами",
        descr="Не требуются, если ссылка оформлена в <code><nowiki>{{cite web}}</nowiki>" +
            "</code>.",
        func=check_wp_icon_template,
    ),

    CheckDefinition(
        name="RefTemplates",
        title="Страницы с ref-шаблонами",
        descr="Не требуются, если ссылка оформлена в <code><nowiki>{{cite web}}</nowiki>" +
            "</code>.",
        func=check_wp_ref_templates,
    ),

    CheckDefinition(
        name="Isolated",
        title="Изолированные статьи",
        descr="В другие статьи Википедии нужно добавить ссылки на такую статью, а потом удалить " +
            "из неё шаблон об изолированности.",
        func=check_wp_isolated,
    ),

    CheckDefinition(
        name="Empty",
        title="Очень короткие статьи",
        descr="Содержат шаблон<code><nowiki>{{rq|empty}}</nowiki></code> или {{tl|дописать}}.",
        func=check_wp_pages_empty,
    ),

    CheckDefinition(
        name="NoSources",
        title="Статьи без источников",
        descr="Статьи без разделов «Ссылки», «Литература», «Источники», примечаний или других " +
            "признаков наличия источников.",
        func=check_wp_no_sources,
    ),

    CheckDefinition(
        name="SourceRequest",
        title="Страницы с запросом источников",
        descr="Добавьте источники, а затем уберите шаблон запроса с исправленной страницы.",
        func=check_wp_source_request,
    ),

    CheckDefinition(
        name="LinksUnanvailable",
        title="Недоступные ссылки",
        descr="Нужно обновить ссылку, найти страницу в [http://web.archive.org/ архиве] или " +
            "подобрать другой источник.",
        func=check_wp_links_unavailable,
    ),

    CheckDefinition(
        name=f"TemplateRegexp Аффилированные источники",
        title=f"Страницы с шаблоном [[Шаблон:Аффилированные источники|]]",
        descr="",
        func=check_wp_template_regexp,
        kwargs={"template": "Аффилированные источники"},
    ),

    CheckDefinition(
        name=f"TemplateRegexp Спам-ссылки",
        title=f"Страницы с шаблоном [[Шаблон:Спам-ссылки|]]",
        descr="",
        func=check_wp_template_regexp,
        kwargs={"template": "Спам-ссылки"},
    ),

    CheckDefinition(
        name=f"TemplateRegexp Обновить",
        title=f"Страницы с шаблоном [[Шаблон:Обновить|]]",
        descr="",
        func=check_wp_template_regexp,
        kwargs={"template": "Обновить"},
    ),

    CheckDefinition(
        name=f"TemplateRegexp V",
        title=f"Страницы с шаблоном [[Шаблон:V|]]",
        descr="",
        func=check_wp_template_regexp,
        kwargs={"template": "V"},
    ),

    CheckDefinition(
        name=f"TemplateRegexp закончить перевод",
        title=f"Страницы с шаблоном [[Шаблон:закончить перевод|]]",
        descr="",
        func=check_wp_template_regexp,
        kwargs={"template": "закончить перевод"},
    ),

    CheckDefinition(
        name=f"TemplateRegexp плохой перевод",
        title=f"Страницы с шаблоном [[Шаблон:плохой перевод|]]",
        descr="",
        func=check_wp_template_regexp,
        kwargs={"template": "плохой перевод"},
    ),

    CheckDefinition(
        name=f"TemplateRegexp Нерабочие сноски",
        title=f"Страницы с шаблоном [[Шаблон:Нерабочие сноски|]]",
        descr="",
        func=check_wp_template_regexp,
        kwargs={"template": "Нерабочие сноски"},
    ),
    
    CheckDefinition(
        name="ArabicNumerals",
        title="Века арабскими цифрами",
        descr="Номера веков должны быть записаны рисмкими цифрами, см. [[ВП:ДАТЫ]].",
        func=check_wp_centuries2,
    ),

    CheckDefinition(
        name="BadDelimiters",
        title="Неформатные разделители в числах",
        descr="В тексте есть конструкции вида 1,234,567 или 12.345.678. Если это одно число, " +
            "то в качестве разделителя групп цифр нужно использовать пробел (см. [[ВП:Ч]]).",
        func=check_wp_pages_delimiters,
        is_enabled_by_default=False,
    ),

    CheckDefinition(
        name="Communes",
        title="Коммуны",
        descr="Это актуально только для ПРО:Вьетнам, в прочих случаях должно быть выключено. " +
            "В статьях о Вьетнаме ''коммуны'' (а также, в большинстве " +
            "случаев, ''приходы'' и ''деревни'') следует заменить на ''общины''.",
        func=check_wp_communes,
        is_enabled_by_default=False,
    ),

    CheckDefinition(
        name="Images",
        title="Нужно добавить изображение",
        descr="В статье стоит запрос изображения, или статья иным образом включена в одну из" +
            "категорий \"Категория:Википедия:Статьи без изображений*\". ",
        func=check_wp_images,
        is_enabled_by_default=False,
    ),

    CheckDefinition(
        name="OverDated",
        title="Статьи с наиболее перевикифицированными датами",
        descr="",
        func=check_wp_overdated,
        supress_stat=True,
        runtime_kwargs={"running_config": "running_config"},
    ),

    CheckDefinition(
        name="BadLinks",
        title="Ссылки на неоднозначности",
        descr="Такую ссылку надо заменить ссылкой на нужную статью, а если всё-таки " +
            "необходимо оставить ссылку на дизамбиг, то завернуть её в {{tl|D-l}}.",
        func=check_links_to_disambigs_fast,
        is_enabled_by_default=False,
        runtime_kwargs={"r": "red_con", "script_config": "script_config"},
    ),
    # check_links_to_disambigs_fast(pages_content,r,script_config)

]