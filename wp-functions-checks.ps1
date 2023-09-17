
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

# returns wikicode for a problem list
function CheckWikipages-LinksUnanvailable {
    param (
        $pages = @()
    )
    $fullAnnounce += "=== Недоступные ссылки ===`n"
    $fullAnnounce += "Нужно обновить ссылку, найти страницу в [http://web.archive.org/ архиве] или подобрать другой источник.`n"
    $linksUnanvailableCounter = 0

    foreach ($page in $pages){
        $mc = [regex]::matches($page.content, "http[s]*://[^:]*{{Недоступная ссылка\|[^\}]{0,200}}}|{{Недоступная ссылка}}")
        if ($mc.groups.count -gt 0){
            $fullAnnounce += "* [[$($page.title)]] ($($mc.groups.count))`n"
            #""
            #"== [[$($page.title)]] == "
            foreach ($m in $mc.Value) {
                if ($m -match "^[^ \n\|\]{]*"){
                    #$Matches.Values
                    if (($Matches.Values -like "{{Недоступная") -or ($Matches.Values -like "")){
                        $fullAnnounce += "** (unknown)`n"
                    } else {
                        $fullAnnounce += "** $($Matches.Values)`n"
                    }
                } else {
                    throw "bad match"
                }
            }
            #throw "wait"
        }
    }

    "$linksUnanvailableCounter have unavailable URLs" | Append-Log
    $problemStat = New-ProblemStat -name "LinksUnanvailable" -text 'Недоступные ссылки' `
         -counter $linksUnanvailableCounter -total $pages.Count
    $result = "" | select `
        @{n='wikitext';e={$wikiText}},
        @{n='problemstat';e={$problemStat}}
    return $result
}


