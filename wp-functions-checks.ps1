
# returns wikicode for a problem list
function CheckWikipages-Empty {
    param (
        $pages = @()
    )
    $wikiText = "=== Очень короткие статьи ===`n"
    $emptyPagesCounter = 0
    foreach ($page in $pages){
        if ($page.content -match "{{rq\|[^\}]{0,30}empty[\|}]")
        {
            $wikiText += "* [[$($page.title)]]`n"
            $emptyPagesCounter++
        }
    }
    "$emptyPagesCounter pages are too short" | Append-Log
    $problemStat = New-ProblemStat -name "Empty" -text 'Очень коротко' `
         -counter $emptyPagesCounter -total $pages.Count
    $result = "" | select `
        @{n='wikitext';e={$wikiText}},
        @{n='problemstat';e={$problemStat}}
    return $result
}

# returns wikicode
function CheckWikipages-SourceRequest {
    param (
        $pages = @(),
        $pagesNoSourcesAtAll = @()
    )
    $wikiText = "=== Страницы с запросом источников ===`n"
    $pagesCounter = 0
    foreach ($page in $pages){
        if ((($page.content -match "{{rq\|[^\}]{0,20}sources[\|}]") -or
             ($page.content -match "{{Нет источников\|") -or
             ($page.content -match "{{Нет ссылок\|")) -and
            ($page.Title -notin $pagesNoSourcesAtAll))
        {
            $wikiText += "* [[$($page.title)]]`n"
            $pagesCounter++
        }
    }
    "$pagesCounter pages have source request" | Append-Log
    $problemStat = New-ProblemStat -name "SourceRequest" -text 'Запрос источника' `
         -counter $pagesCounter -total $pages.Count
    $result = "" | select `
        @{n='wikitext';e={$wikiText}},
        @{n='problemstat';e={$problemStat}}
    return $result
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
function CheckWikipages-Communes-Single {
    param (
        $page = ""
    )
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

# NO WORK YET
function CheckWikipages-NoSources-Single {
    param (
        $page = ""
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
        #$pagesNoSourcesAtAll += $page.Title
        return "* [[$($page.Title)]]`n"
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
        $checkTemplate = "TemplateExample"
    )
    #$checkTemplate = "Ref-en"
    $RX = "{{$checkTemplate[ \n]*\||{{$checkTemplate[ \n]*}}"
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

<#
# returns wikicode for a problem list
function CheckWikipages-LinksUnanvailable {
    param (
        $pages = @()
    )
    # $pages = $vietPagesContent
    $wikiText = "=== Недоступные ссылки ===`n"
    $wikiText += "Нужно обновить ссылку, найти страницу в [http://web.archive.org/ архиве] или подобрать другой источник.`n"
    $pagesCounter = 0

    foreach ($page in $pages){
        $mc = [regex]::matches($page.content, "http[s]*://[^:]*{{Недоступная ссылка\|[^\}]{0,200}}}|{{Недоступная ссылка}}")
        if ($mc.groups.count -gt 0){
            $wikiText += "* [[$($page.title)]] ($($mc.groups.count))`n"
            $pagesCounter++
            #""
            #"== [[$($page.title)]] == "
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
    }

    "$pagesCounter have unavailable URLs" | Append-Log
    $problemStat = New-ProblemStat -name "LinksUnanvailable" -text 'Недоступные ссылки' `
         -counter $pagesCounter -total $pages.Count
    $result = "" | select `
        @{n='wikitext';e={$wikiText}},
        @{n='problemstat';e={$problemStat}}
    return $result
}
#>

### Function that calls other function

# returns wikicode for a problem list
function CheckWikipages-Router {
    param (
        $checkPages = @(),
        $checkType = "invalid",
        $returnEmpty = $true,
        # optional
        $bypassArgument = ""
    )
    # $pages = $vietPagesContent
    $FunctionParameters = @{}

    if ( $checkType -like "BadSquareKm" ) {
        $checkTitle = "Страницы с кв км или кв. км"
        $wikiDescription = "Желательно поменять на км².`n"
    } elseif ( $checkType -like "Communes" ) {
        $checkTitle = "Коммуны"
        $wikiDescription = "Это актуально только для ПРО:Вьетнам, в прочих случаях должно быть выключено.`n"
        $wikiDescription += "В ПРО:Вьетнам ''коммуны'' (равно как ''приходы'' и, в большинстве случаев, ''деревни'') следует заменить на ''общины''.`n"
    } elseif ( $checkType -like "DirectInterwikis" ) {
        $checkTitle = "Статьи с прямыми интервики-ссылками"
        $wikiDescription = "Нужно заменить на шаблон iw или добавить прямую ссылку на статью в РуВП, если она уже есть.`n"
    } elseif ( $checkType -like "Empty" ) {
        $checkTitle = "Очень короткие статьи"
        $wikiDescription = "Содержат шаблон<code><nowiki>{{rq|empty}}</nowiki></code>.`n"
    } elseif ( $checkType -like "Isolated" ) {
        $checkTitle = "Изолированные статьи"
        $wikiDescription = "В другие статьи Википедии нужно добавить ссылки на эти статьи.`n"
    } elseif ( $checkType -like "LinksUnanvailable" ) {
        $checkTitle = "Недоступные ссылки"
        $wikiDescription = "Нужно обновить ссылку, найти страницу в [http://web.archive.org/ архиве] или подобрать другой источник.`n"
    } elseif ( $checkType -like "NoLinksInLinks" ) {
        $checkTitle = "Статьи без ссылок в разделе «Ссылки»"
        $wikiDescription = "Если в «Ссылках» есть источники без http-сылок, то их, возможно, стоит переместить в  раздел «Литература».`n"
    } elseif ( $checkType -like "NoCats" ) {
        $checkTitle = "Не указаны категории"
        $wikiDescription = "Иногда категории назначаются шаблонами, тогда указывать категории напрямую не нужно. В таком случае "
        $wikiDescription += "категоризирующий шаблон следует учитывать при составлении этого списка.`n"
    } elseif ( $checkType -like "NoSources" ) {
        $checkTitle = "Статьи без источников"
        $wikiDescription = "Статьи без разделов «Ссылки», «Литература», «Источники», примечаний или других признаков наличия источников.`n"
    } elseif ( $checkType -like "PoorDates" ) {
        $checkTitle = "Неформатные даты в cite web"
        $wikiDescription = "Используйте формат <code>YYYY-MM-DD</code> ([[ВП:ТД]]).`n"
    } elseif ( $checkType -like "SNPREP" ) {
        $checkTitle = "[[ВП:СН-ПРЕП|СН-ПРЕП]]"
        $wikiDescription += "Страницы, в тексте которых есть <code><nowiki>.<ref</nowiki></code> "
        $wikiDescription += "или <code><nowiki>.{{sfn</nowiki></code>. Сноска должна стоять перед точкой, "
        $wikiDescription += "кроме случаев, когда точка является частью сокращения.`n"
    } elseif ( $checkType -like "TemplateRegexp" ) {
        $checkTitle = "Страницы с шаблоном [[Шаблон:$bypassArgument|]]"
        $FunctionParameters = @{checkTemplate = $bypassArgument}
        $wikiDescription = ""
    } elseif ( $checkType -like "WPLinks" ) {
        $checkTitle = "Ссылки на ВП как внешние"
        $wikiDescription = "<nowiki>[http://ссылки]</nowiki> нужно поменять на <nowiki>[[ссылки]]</nowiki>.`n"
    } else {
        throw "Unknown check: $checkType"
    }

    $checkFunction = "CheckWikipages-$checkType-Single"
    $pagesCounter = 0
    $wikiTextBody = ""
    foreach ($page in $checkPages) {
        # $Results = &$MockFunctionName @FunctionParameters
        $wikiTextThisPage = &$checkFunction -page $page @FunctionParameters
        if ($wikiTextThisPage -notlike "") { $pagesCounter++ }
        $wikiTextBody += $wikiTextThisPage
    }

    if ( ($pagesCounter -gt 0) -or ($returnEmpty) ){
        $wikiText = "=== $checkTitle ===`n"
        $wikiText += $wikiDescription
        $wikiText += $wikiTextBody
    } else {
        $wikiText = ""
    }

    "$pagesCounter pages: $checkType $bypassArgument" | Append-Log
    $problemStat = New-ProblemStat -name "$checkType $bypassArgument" -text $checkTitle `
         -counter $pagesCounter -total $checkPages.Count
    $result = "" | select `
        @{n='wikitext';e={$wikiText}},
        @{n='problemstat';e={$problemStat}}
    return $result
}
