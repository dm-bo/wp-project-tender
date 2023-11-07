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
function CheckWikipages-BotArchives-Single {
    param (
        $page = ""
    )
    if ($page.Content -match "<!-- Bot retrieved archive -->")
    {
        return "* [[$($page.title)]]`n"
    } else {
        return ""
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
# TODO also need check commas, colons etc.
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



