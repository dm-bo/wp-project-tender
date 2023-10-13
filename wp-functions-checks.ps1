# returns wikicode
function CheckWikipages-SourceRequest-Single {
    param (
        $page = @(),
        $pagesNoSourcesAtAll = @()
    )
    # HACK!
    $pagesNoSourcesAtAll = $global:pagesNoSourcesAtAll
     
    if ((($page.content -match "{{rq\|[^\}]{0,20}sources[\|}]") -or
             ($page.content -match "{{Нет источников\|") -or
             ($page.content -match "{{Нет ссылок\|")) -and
            ($page.Title -notin $pagesNoSourcesAtAll))
    {
        return "* [[$($page.title)]]`n"
    } else {
        return ""
    }
}

### Single-Page Checks ###

# returns wikicode for a problem list
function CheckWikipages-BadSquareKm-Single {
    param (
        $page = ""
    )
    if (($page.content -match "кв. км") -or
         ($page.content -match "кв км"))
    {
        return "* [[$($page.title)]]`n"
    } else {
        return ""
    }
}

# returns wikicode for a problem list
function CheckWikipages-BotTitles-Single {
    param (
        $page = ""
    )
    if ($page.Content -match "<!-- Заголовок добавлен ботом -->")
    {
        return "* [[$($page.title)]]`n"
    } else {
        return ""
    }
}

# returns wikicode for a problem list
function CheckWikipages-Communes-Single {
    param (
        $page = ""
    )
    if ($page.title -in @("Пиньо де Беэн, Пьер")){
        return ""
    }
    $mc = [regex]::matches($page.content, "[^\n ]{0,8}коммун[^\n ]{0,5}")
    if ($mc.groups.count -gt 0){
        $commicount = 0
        foreach ($m in $mc) {
            if (($m.Value -notlike "*коммуни*") -and
                ($m.Value -notlike "*коммунал*") -and
                ($m.Value -notlike "*общин*-коммун*"))
            {
                #$m.Value
                $commicount++
            }
        }
        if ($commicount -gt 0){
            return "* [[$($page.Title)]] ($($commicount))`n"
        } else {
            return ""
        }
    }
}

# returns wikicode for a problem list
function CheckWikipages-DirectGoogleBooks-Single {
    param (
        $page = ""
    )
    if ($page.Content -match "\[http[s]*\:\/\/books\.google\.")
    {
        return "* [[$($page.title)]]`n"
    } else {
        return ""
    }
}

# returns wikicode for a problem list
function CheckWikipages-DirectInterwikis-Single {
    param (
        $page = ""
    )
    if ($page.Content -match "\[\[\:[a-z]{2,3}\:[^\:]*\]\]")
    {
        return "* [[$($page.title)]]`n"
    } else {
        return ""
    }
}

# returns wikicode for a problem list
function CheckWikipages-DirectWebarchive-Single {
    param (
        $page = ""
    )
    $mc = [regex]::matches($page.content, "\[http[s]*://web.archive.org[^ \]\n]*")
    if ($mc.groups.count -gt 0){
        $result = "* [[$($page.Title)]] ($($mc.groups.count))`n"
        $mc.groups.value -replace "[http[s]*://web.archive.org/web/[0-9]*/","" | % {$result += "** $_`n"}
        return $result
    } else {
        return ""
    }
}

# returns wikicode for a problem list
function CheckWikipages-Empty-Single {
    param (
        $page = ""
    )
    if ($page.content -match "{{rq\|[^\}]{0,30}empty[\|}]")
    {
        return "* [[$($page.title)]]`n"
    } else {
        return ""
    }
}

# returns wikicode for a problem list
function CheckWikipages-IconTemplates-Single {
    param (
        $page = ""
    )
    $mc = [regex]::matches($page.content, "{{[a-zA-Z]{2} icon}}")
    if ($mc.groups.count -gt 0){
        return "* [[$($page.title)]] ($($mc.groups.count))`n"
    } else {
        return ""
    }
}

# returns wikicode for a problem list
function CheckWikipages-Isolated-Single {
    param (
        $page = ""
    )
    $mc = [regex]::matches($page.content, "{{изолированная статья\||{{изолированная статья}}")
    if ($mc.groups.count -gt 0){
        return "* [[$($page.title)]]`n"
    } else {
        return ""
    }
}

# returns wikicode for a problem list
function CheckWikipages-LinksUnanvailable-Single {
    param (
        $page = ""
    )
    $wikiText = ""
    $mc = [regex]::matches($page.content, "http[s]*://[^:]*{{Недоступная ссылка\|[^\}]{0,200}}}|{{Недоступная ссылка}}")
    if ($mc.groups.count -gt 0){
        $wikiText = "* [[$($page.title)]] ($($mc.groups.count))`n"
        #"== [[$($page.title)]] == " | Append-Log
        foreach ($m in $mc.Value) {
            if ($m -match "^[^ \n\|\]{]*"){
                #$Matches.Values
                if (($Matches.Values -like "{{Недоступная") -or ($Matches.Values -like "")){
                    $wikiText += "** (unknown)`n"
                } else {
                    $wikiText += "** $($Matches.Values)`n"
                }
            } else {
                throw "bad match"
            }
        }
        #if ($page.title -like "Drabadzi-drabada") {throw "wait"}
    }

    return $wikiText
}

# returns wikicode for a problem list
function CheckWikipages-NakedLinks-Single {
    param (
        $page = ""
    )
    $seminaked = @()
    $mc = [regex]::matches($page.content, "\[http[^ ]*\]")
    if ($mc.groups.count -gt 0){
        foreach ($m in $mc) {
            $seminaked += $m
        }
    }
    $naked = @()
    $mc = [regex]::matches($page.content, "[^=][^/\?\=\[\|]{1}http[s]{0,1}://[^\) \|\<\n]+")
    if ($mc.groups.count -gt 0){
        foreach ($m in $mc) {
            $naked += $m.Value
        }
    }
    if ( ($seminaked.Count -gt 0) -or ($naked.Count -gt 0) ){
        $result = "* [[$($page.Title)]]:`n"
        $seminaked | % { $result += "** <nowiki>$_</nowiki>`n" }
        $naked | % { $result += "** <nowiki>$_</nowiki>`n" }
        return $result
    } else {
        return ""
    }
}

# returns wikicode for a problem list
function CheckWikipages-NoCats-Single {
    param (
        $page = ""
    )
    if (($page.Content -notmatch "\[\[Категория\:") -and
        ($page.Content -notmatch "{{кинорежиссёр\|") -and
        ($page.Content -notmatch "{{сценарист\|") -and
        ($page.Content -notmatch "{{певица\|") -and
        ($page.Content -notmatch "{{актриса\|") -and
        ($page.Content -notmatch "{{историк\|") -and
        ($page.Content -notmatch "{{археолог\|") -and
        ($page.Content -notmatch "{{список однофамильцев}}") -and
        ($page.Content -notmatch "{{Мосты Вологды}}") -and
        ($page.Content -notmatch "{{Улица Екатеринбурга[ \n]*\|") -and
        ($page.Content -notmatch "{{Карта[ \n]*\|") -and
        ($page.Content -notmatch "{{Культурное наследие народов РФ\|") -and
        ($page.Content -notmatch "{{Вьетнам на Олимпийских игра}}")
    ) {
        return "* [[$($page.Title)]]`n"
    } else {
        return ""
    }
}

# returns wikicode for a problem list
function CheckWikipages-NoLinksInLinks-Single {
    param (
        $page = ""
    )
    if (($page.Content -notmatch "http[s]{0,1}://") -and ($page.Content -match "==[ ]*Ссылки[ ]*==") -and
        ($page.Content -notmatch "{{ВС}}") -and ($page.Content -notmatch "{{Ethnologue\|") -and
        ($page.Content -notmatch "{{WAD\|") -and
        ($page.Content -notmatch "{{ВТ-ЭСБЕ\|") -and
        ($page.Content -notmatch "{{IMDb name\|") -and
        ($page.Content -notmatch "{{IMDb title\|") -and
        ($page.Content -notmatch "{{Шахматные ссылки[ \n]*\|") -and
        ($page.Content -notmatch "{{ЭЕЭ[ \n]*\|") -and
        ($page.Content -notmatch "{{MacTutor Biography[ \n]*\|") -and
        ($page.Content -notmatch "{{Сотрудник РАН[ \n]*\|") -and
        ($page.Content -notmatch "{{Math-Net.ru[ \n]*\|") -and
        ($page.Content -notmatch "{{oopt.aari.ru[ \n]*\|") -and
        ($page.Content -notmatch "{{Warheroes[ \n]*\|") -and
        ($page.Content -notmatch "{{SportsReference[ \n]*\|") -and
        ($page.Content -notmatch "{{DNB-Portal[ \n]*\|") -and
        ($page.Content -notmatch "{{DDB[ \n]*\|"))
    {
        return "* [[$($page.Title)]]`n"
    } else {
        return ""
    }
}

# returns wikicode for a problem list
function CheckWikipages-NoRefs-Single {
    param (
        $page = ""
    )
    if (($page.Content -notmatch "<ref") -and 
        ($page.Content -notmatch "{{sfn") -and 
        ($page.Content -match "==[ ]*Примечания[ ]*=="))
    {
        return "* [[$($page.Title)]]`n"
    } else {
        return ""
    }
}

# returns wikicode for a problem list
# FIXME bad code: operates with global variable
function CheckWikipages-NoSources-Single {
    param (
        $page = "",
        $bypassedArgument = "@()"
    )
    $wikiText = ""
    if (($page.Content -match "<ref") -or
        ($page.Content -match "{{sfn\|") -or
        ($page.Content -match "==[ ]*Ссылки[ ]*==") -or
        ($page.Content -match "==[ ]*Литература[ ]*==") -or
        ($page.Content -match "==[ ]*Источники[ ]*==") -or
        ($page.Content -match "\{\{IMDb name\|")
        )
    {
        return ""
    } else {
        $global:pagesNoSourcesAtAll += $page.Title
        return "* [[$($page.Title)]]`n"
    }

    
}

# returns wikicode for a problem list
function CheckWikipages-PoorDates-Single {
    param (
        $page = ""
    )
    $mc = [regex]::matches($page.content, "{{[cC]ite web[^{}]+({{[^}]+}})*[^{}]+}}")
    if ($mc.groups.count -gt 0){
        $badDates = @()
        foreach ($m in $mc){
            $nc = [regex]::matches(($m.Value), "\|[ ]*archive[-]*date[ ]*=[ ]*[^\|\n}]*")
            if ($nc.groups.count -eq 1){
                $archivedate = ($nc.Value -split "=")[1]
            } else {
                $archivedate = $null
            }
            $nc2 = [regex]::matches(($m.Value), "\|[ ]*date[ ]*=[ ]*[^\|\n}]*")
            if ($nc.groups.count -eq 1){
                $date = ($nc2.Value -split "=")[1]
            }
            if ( -not (Get-WPDateFormat -date $archivedate)) {
                $badDates += "$archivedate"
            }
            if ( -not (Get-WPDateFormat -date $date)) {
                $badDates += "$date"
            }
        }
        if ($badDates.Count -gt 0) {
            return "* [[$($page.title)]] ($($badDates -join "; "))`n"
        }
    }
    return ""
}

# returns wikicode for a problem list
function CheckWikipages-RefTemplates-Single {
    param (
        $page = ""
    )
    $mc = [regex]::matches($page.content, "{{ref-[a-zA-Z]+\|[^\}]{0,200}}}|{{ref-[a-zA-Z]+}}")
    if ($mc.groups.count -gt 0){
        return "* [[$($page.title)]] ($($mc.groups.count))`n"
    } else {
        return ""
    }
}

# returns wikicode for a problem list
function CheckWikipages-SemicolonSections-Single {
    param (
        $page = ""
    )
    # $page = $vietPagesContent | where {$_.title -like "Олонец" }
    $pageSections = Get-WPPageSections -content $page.content
    $hasSemi = $false
    foreach ($section in ($pageSections | where {$_.name -notmatch "Литература|Примечания|Источники"})){
        if ($section.content -match "\n;") {
            $hasSemi = $true
        }
    }
    if ($hasSemi){
        return "* [[$($page.Title)]]`n"
    } else {
        return ""
    }
}

# returns wikicode for a problem list
function CheckWikipages-SNPREP-Single {
    param (
        $page = ""
    )
    $mc = [regex]::matches($page.content, ".{6}\.[ ]*(<ref[ >]|{{sfn\|)")
    if ($mc.groups.count -gt 0){
        #$fullAnnounce += 
        $badPreps = @()
        foreach ($m in $mc){
            if (($m.Value -match "[  ]г.(<|{)") -or 
                ($m.Value -match "[  ](гг|лл|др|руб|экз|чел|л\. с|н\. э|т\.[  ]д|т\.[  ]п)\.(<|{)") -or 
                ($m.Value -match "[  ](тыс|млн|долл)\.(<|{)") -or 
                ($m.Value -match "[  ]([а-яА-Я]{1}\.[  ]{0,1}[а-яА-Я]{1})\.(<|{)") -or 
                ($m.Value -match "[  ](ж\.д|Inc|M\.E\.P)\.(<|{)"))
            {
                #"    Skipping: $($m.Value)"
            } else {
                $badPreps += $m.Value
            }
        }
        if ($badPreps.Count -gt 0){
            # $fullAnnounce += "* $($page.title) ($($badPreps -join ", "))`n"
            return "* [[$($page.title)]]`n"
        }
    }
    return ""
}

# returns wikicode for a problem list
function CheckWikipages-TemplateRegexp-Single {
    param (
        $page = "",
        $bypassedArgument = "TemplateExample"
    )
    #$checkTemplate = "Ref-en"
    $RX = "{{$bypassedArgument[ \n]*\||{{$bypassedArgument[ \n]*}}"
    $RX = [regex]::new($RX,([regex]$RX).Options -bor [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    $mc = $RX.matches($page.content)
    #$mc = [regex]::matches($page.content, "{{$checkTemplate\||{{$checkTemplate}}")
    if ($mc.groups.count -gt 0){
        return "* [[$($page.title)]] ($($mc.groups.count))`n"
    } else {
        return ""
    }
}

# returns wikicode for a problem list
function CheckWikipages-TooFewWikilinks-Single {
    param (
        $page = ""
    )
    $toolow = 0.9
    $toohigh = 20
    $enc = [System.Text.Encoding]::UTF8
    $enccont = $enc.GetBytes($page.Content)
    $pageSize = $enccont.Count
    if ($pageSize -gt 20480) {
        $mc = [regex]::matches($page.content, "\[\[[^\]:]*\]\]")
        $linksPerKB = [math]::Round($mc.groups.count / ($pageSize / 1024), 2)
        if ($linksPerKB -gt $toohigh){
            return "* [[$($page.title)]] ($linksPerKB, $($mc.groups.count)/$pageSize) — а здесь наоборот, слишком много`n"
        } elseif ($linksPerKB -gt $toolow) {
            return ""
        } else {
            return "* [[$($page.title)]] ($linksPerKB, $($mc.groups.count)/$pageSize)`n"
        }
        # Write-Host -ForegroundColor $color "* $linksPerKB — [[$($page.title)]] ($($mc.groups.count)/$pageSize)"
    } else {
        return ""
    }
}


# returns wikicode for a problem list
function CheckWikipages-WPLinks-Single {
    param (
        $page = ""
    )
    $mc = [regex]::matches($page.content, "\[http[s]*://[a-z]+.wikipedia.org")
    if ($mc.groups.count -gt 0){
        return "* [[$($page.title)]] ($($mc.groups.count))`n"
    } else {
        return ""
    }
}

### Function that calls other function

# returns wikicode for a problem list
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
        $wikiDescription += "Страницы, в тексте которых есть <code><nowiki>.<ref</nowiki></code> "
        $wikiDescription += "или <code><nowiki>.{{sfn</nowiki></code>. Сноска должна стоять перед точкой, "
        $wikiDescription += "кроме случаев, когда точка является частью сокращения.`n"
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
