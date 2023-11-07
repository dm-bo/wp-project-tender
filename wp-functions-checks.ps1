### Single-Page Checks ###

















### Function that calls other function

# returns wikicode for a problem list
# Big nasty ad-hoc function, just to move code out of main file quickly
function CheckWikipages-Router {
    param (
        $checkPages = @(),
        $checkType = "invalid",
        $returnEmpty = $true,
        # optional
        $bypassArgument = "",
        $returnModeVersion = 1
    )
    # $pages = $vietPagesContent
    $FunctionParameters = @{}

    if ( $checkType -like "BadSquareKm" ) {
        $checkTitle = "Страницы с кв км или кв. км"
        $wikiDescription = "Желательно поменять на км².`n"
    } elseif ( $checkType -like "BotTitles" ) {
        $checkTitle = "Заголовок добавлен ботом"
        $wikiDescription = "Нужно проверить, что заголовок правильный, и убрать html-комментарий ''<nowiki><!-- Заголовок добавлен ботом --></nowiki>''`n"
    } elseif ( $checkType -like "BotArchives" ) {
        $checkTitle = "Архив добавлен ботом"
        $wikiDescription = "Нужно проверить архив, и убрать html-комментарий ''<nowiki><!-- Bot retrieved archive --></nowiki>''`n"
    } elseif ( $checkType -like "Communes" ) {
        $checkTitle = "Коммуны"
        $wikiDescription = "Это актуально только для ПРО:Вьетнам, в прочих случаях должно быть выключено.`n"
        $wikiDescription += "В ПРО:Вьетнам ''коммуны'' (равно как ''приходы'' и, в большинстве случаев, ''деревни'') следует заменить на ''общины''.`n"
    } elseif ( $checkType -like "DirectGoogleBooks" ) {
        $checkTitle = "Прямые ссылки на Google books"
        $wikiDescription = "Их желательно поменять на [[Шаблон:книга]].`n"
    } elseif ( $checkType -like "DirectInterwikis" ) {
        $checkTitle = "Статьи с прямыми интервики-ссылками"
        $wikiDescription = "Нужно заменить на шаблон iw или добавить прямую ссылку на статью в РуВП, если она уже есть.`n"
    } elseif ( $checkType -like "DirectWebarchive" ) {
        $checkTitle = "Прямые ссылки на web.archive.org"
        $wikiDescription = "Желательно заменить их на [[Ш:cite web]] с параметрами archiveurl и archivedate.`n"
    } elseif ( $checkType -like "Empty" ) {
        $checkTitle = "Очень короткие статьи"
        $wikiDescription = "Содержат шаблон<code><nowiki>{{rq|empty}}</nowiki></code>.`n"
    } elseif ( $checkType -like "IconTemplates" ) {
        $checkTitle = "Страницы с *icon-шаблонами"
        $wikiDescription = "Не требуются, если ссылка оформлена в <code><nowiki>{{cite web}}</nowiki></code>.`n"
    } elseif ( $checkType -like "Isolated" ) {
        $checkTitle = "Изолированные статьи"
        $wikiDescription = "В другие статьи Википедии нужно добавить ссылки на такую статью, а потом удалить из неё шаблон об изолированности.`n"
    } elseif ( $checkType -like "LinksUnanvailable" ) {
        $checkTitle = "Недоступные ссылки"
        $wikiDescription = "Нужно обновить ссылку, найти страницу в [http://web.archive.org/ архиве] или подобрать другой источник.`n"
    } elseif ( $checkType -like "NakedLinks" ) {
        $checkTitle = "Голые ссылки"
        $wikiDescription = "Нужно оформить ссылку в [[Ш:cite web]] или, хотя бы, в <code><nowiki>[http://example.com Title]</nowiki></code>.`n"
    } elseif ( $checkType -like "NoCats" ) {
        $checkTitle = "Не указаны категории"
        $wikiDescription = "Иногда категории назначаются шаблонами, тогда указывать категории напрямую не нужно. В таком случае "
        $wikiDescription += "категоризирующий шаблон следует учитывать при составлении этого списка.`n"
    } elseif ( $checkType -like "NoLinksInLinks" ) {
        $checkTitle = "Статьи без ссылок в разделе «Ссылки»"
        $wikiDescription = "Если в «Ссылках» есть источники без http-сылок, то их, возможно, стоит переместить в  раздел «Литература».`n"
    } elseif ( $checkType -like "NoRefs" ) {
        $checkTitle = "Нет примечаний в разделе «Примечания»"
        $wikiDescription = "Не считает примечания, подтянутые из ВД. В любом случае, было бы неплохо добавить сноски в тело статьи.`n"
    } elseif ( $checkType -like "NoSources" ) {
        $checkTitle = "Статьи без источников"
        $wikiDescription = "Статьи без разделов «Ссылки», «Литература», «Источники», примечаний или других признаков наличия источников.`n"
    } elseif ( $checkType -like "PoorDates" ) {
        $checkTitle = "Неформатные даты в cite web"
        $wikiDescription = "Используйте формат <code>YYYY-MM-DD</code> ([[ВП:ТД]]).`n"
    } elseif ( $checkType -like "RefTemplates" ) {
        $checkTitle = "Страницы с ref-шаблонами"
        $wikiDescription = "Не требуются, если ссылка оформлена в <code><nowiki>{{cite web}}</nowiki></code>.`n"
    } elseif ( $checkType -like "SemicolonSections" ) {
        $checkTitle = ";Недоразделы"
        $wikiDescription = "Использована кострукция <code><nowiki>;Что-то</nowiki></code>. Скорее всего, "
        $wikiDescription += "её следует заменить, например, на <code><nowiki>=== Что-то ===</nowiki></code>.`n"
    } elseif ( $checkType -like "SNPREP" ) {
        $checkTitle = "[[ВП:СН-ПРЕП|СН-ПРЕП]]"
        $wikiDescription += "Страницы, в тексте которых есть <code><nowiki>.<ref</nowiki></code> или " +
        "<code><nowiki>.{{sfn</nowiki></code>, либо их вариации с пробелами, как <code><nowiki>. " +
        "<ref</nowiki></code>. Сноска должна стоять перед точкой, кроме случаев, когда точка является "+
        "частью сокращения.`n"
    } elseif ( $checkType -like "SourceRequest" ) {
        $checkTitle = "Страницы с запросом источников"
        $wikiDescription += "Добавьте источники, а затем уберите шаблон запроса с исправленной страницы.`n"
    } elseif ( $checkType -like "TooFewWikilinks" ) {
        $checkTitle = "Мало внутренних ссылок"
        $wikiDescription += "Добавьте больше.`n"
    } elseif ( $checkType -like "TemplateRegexp" ) {
        $checkTitle = "Страницы с шаблоном [[Шаблон:__ARG__|]]"
        $wikiDescription = ""
    } elseif ( $checkType -like "WPLinks" ) {
        $checkTitle = "Ссылки на ВП как внешние"
        $wikiDescription = "<nowiki>[http://ссылки]</nowiki> нужно поменять на <nowiki>[[ссылки]]</nowiki>.`n"
    } else {
        throw "Unknown check: $checkType"
    }

    $FunctionParameters = @{bypassedArgument = $bypassArgument}
    $checkFunction = "CheckWikipages-$checkType-Single"
    $pagesCounter = 0
    $wikiTextBody = ""
    foreach ($page in $checkPages) {
        # $Results = &$MockFunctionName @FunctionParameters
        $wikiTextThisPage = &$checkFunction -page $page @FunctionParameters
        if ($wikiTextThisPage -notlike "") { $pagesCounter++ }
        $wikiTextBody += $wikiTextThisPage
    }

    #"Replacing __ARG__ in $checkTitle with $bypassArgument ($($bypassArgument.GetType()))" | Append-Log
    #$bypassArgument.GetEnumerator() | % {"$($_.Name) = $($_.Value)" | Append-Log}

    $checkTitleProcessed = $checkTitle -replace "__ARG__",$bypassArgument
    if ( ($pagesCounter -gt 0) -or ($returnEmpty) ){
        $wikiText = "=== $checkTitleProcessed ===`n"
        $wikiText += $wikiDescription
        $wikiText += $wikiTextBody
    } else {
        $wikiText = ""
    }

    "$pagesCounter pages: $checkType $bypassArgument" | Append-Log
    $problemStat = New-ProblemStat -name "$checkType $bypassArgument" -text $checkTitleProcessed `
         -counter $pagesCounter -total $checkPages.Count
    if ($returnModeVersion -eq 1) {
        $result = "" | select `
            @{n='wikitext';e={$wikiText}},
            @{n='problemstat';e={$problemStat}}
        return $result
    } else {
        #"Returning ver 2" | Append-Log
        return $wikiText,$problemStat
    }
}
