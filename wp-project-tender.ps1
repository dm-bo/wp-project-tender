## One-time part ##

# Defining functions

. "$PSScriptRoot/functions.ps1"
. "$PSScriptRoot/wp-functions-aux.ps1"
. "$PSScriptRoot/wp-functions-checks.ps1"

"=== STARTED AT $(Get-Date) ===" | Append-Log

# Authorizing

# vars $login and $pass comes from here
. "$PSScriptRoot/wp-authorizing.ps1"

$session = Get-WPAuthorizedSession -login $login -pass $pass
if (Get-WPSessionStatus) {
    "User is authorized" | Append-Log
} else {
    "WARNING: User is not authorized" | Append-Log
}

# Checklist

# Basically, an incomplete list of checks that script can do
# Name, Option
$checkArrs = @(
    @("NakedLinks",""),         # Голые ссылки
    @("NoLinksInLinks",""),     # Статьи без ссылок в разделе "Ссылки"
    @("NoRefs",""),             # Статьи без примечаний в разделе "Примечания"
    @("DirectInterwikis",""),   # Статьи с прямыми интервики-ссылками
    @("WPLinks",""),            # Ссылки на Википедию
    @("BotTitles",""),          # <!-- Заголовок добавлен ботом -->
    @("NoCats",""),             # Не содержат [[Категория:
    @("DirectGoogleBooks",""),  # Direct links to Google books
    @("DirectWebarchive",""),   # [web.archive
    @("SNPREP",""),             # .<ref | .{{sfn — СН-ПРЕП
    @("SemicolonSections",""),  # ;Пумпурум — поменять на разделы
    @("TooFewWikilinks",""),    # Мало внутренних ссылок
    @("PoorDates",""),          # неформатные даты в cite web (Архивировано 20220820034353 года.)
    @("BadSquareKm",""),        # плохие квадратные километры
    @("TemplateRegexp","Citation"),
    @("TemplateRegexp","Cite press release"),
    @("TemplateRegexp","PDFlink"),
    @("TemplateRegexp","Wayback"),
    @("TemplateRegexp","webarchive"),
    @("TemplateRegexp","Архивировано"),
    @("TemplateRegexp","Проверено"),
    @("TemplateRegexp","ISBN"),
    @("TemplateRegexp","h"),
    @("IconTemplates", ""),
    @("RefTemplates",""),
    @("Isolated",""),
    @("Empty",""),
    @("NoSources", ""),
    @("SourceRequest", ""),
    @("LinksUnanvailable", ""),
    @("TemplateRegexp","Аффилированные источники"),
    @("TemplateRegexp","Спам-ссылки"),
    @("TemplateRegexp","Обновить")
    )

# TODO function to find by regexp
# TODO Get descriptions out of functions


## Iterate over areas

### Get project page names ###

<#
$area = "Belarus"
$area = "Tatarstan"
$area = "Israel"
$area = "cybersport"
$area = "Holocaust"
$area = "Vologda"
$area = "SverdlovskObl"
$area = "Karelia"
#$area = "Astronomy"
#$area = "Bollywood"
$area = "Vietnam"
#>

$areas = @("Vietnam", "Karelia", "Vologda", "cybersport", "Tatarstan", "Holocaust", "Belarus", "Israel", "SverdlovskObl")
$areas = @("Vietnam")

foreach ($area in $areas) {

    # Get content for $batchsize pages per request
    $batchsize = 10
    # do not process these checks
    $checksDisabled = @()
    # do not work on these pages
    $excludePages = @()
    # performance optimizations
    $removeEasternNames = $false # replacing eastern names has no sence in this context
    $printEmptySections = $false
    # output
    $outputfile = "C:\Users\Dm\Desktop\wp\badlinks-$area.txt"
    # a text before anything else
    $prologue = ""
    # no posting by default
    $postResultsPage = ""
    # a comment the the edit
    $summary = "плановое обновление"
    # new array for page names
    $vietPages = @()

    if ($area -like "Vologda"){
        $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Вологда" | where {$_ -notin $excludePages } | sort  
    } elseif ($area -like "Vietnam") {
        $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Вьетнам" | where {$_ -notin $excludePages } | sort 
        # FIXME dirty ""
        # FIXME move to includable modules
        $checkArrs += @(@("Communes",""), @("",""))  # Декоммунизация
        # $checkArrs[$checkArrs.Count-1]
        $postResultsPage = "Участник:Klientos/Ссылки проекта Вьетнам"
    } elseif ($area -like "Holocaust") {
        $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Холокост" | where {$_ -notin $excludePages } | sort
        #
        $checksDisabled = @("DirectWebarchive#",
            "TemplateRegexp#Citation",
            "TemplateRegexp#Cite press release",
            "TemplateRegexp#PDFlink",
            "TemplateRegexp#Wayback",
            "TemplateRegexp#webarchive",
            "TemplateRegexp#Архивировано",
            "TemplateRegexp#Проверено",
            "TemplateRegexp#ISBN",
            "TemplateRegexp#h",
            "IconTemplates#",
            "RefTemplates#")
        $prologue = "Исправленные проблемы просьба убирать из списка!`n"
    } elseif ($area -like "Belarus") {
        $excludePages += @("Белоруссия/Шапка")
        $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Белоруссия" | where {$_ -notin $excludePages } | sort
        $checksDisabled = @("DirectWebarchive#",
            "TemplateRegexp#Citation",
            "TemplateRegexp#Cite press release",
            "TemplateRegexp#PDFlink",
            "TemplateRegexp#Wayback",
            "TemplateRegexp#webarchive",
            "TemplateRegexp#Архивировано",
            "TemplateRegexp#Проверено",
            "TemplateRegexp#ISBN",
            "TemplateRegexp#h",
            "IconTemplates#",
            "RefTemplates#")
    } elseif ($area -like "Israel") {
        $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Израиль" | where {$_ -notin $excludePages } | sort
        $checksDisabled = @("DirectWebarchive#",
            "TemplateRegexp#Citation",
            "TemplateRegexp#Cite press release",
            "TemplateRegexp#PDFlink",
            "TemplateRegexp#Wayback",
            "TemplateRegexp#webarchive",
            "TemplateRegexp#Архивировано",
            "TemplateRegexp#Проверено",
            "TemplateRegexp#ISBN",
            "TemplateRegexp#h",
            "IconTemplates#",
            "RefTemplates#")
    } elseif ($area -like "SverdlovskObl") {
        $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Свердловская область" | where {$_ -notin $excludePages } | sort
    } elseif ($area -like "Tatarstan") {
        $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Татарстан" | where {$_ -notin $excludePages } | sort
    } elseif ($area -like "cybersport") {
        $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Киберспорт" | where {$_ -notin $excludePages } | sort
        $postResultsPage = "Проект:Киберспорт/Недостатки статей"
    } elseif ($area -like "Karelia") {
        $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Карелия" | where {$_ -notin $excludePages } | sort
    } elseif ($area -like "Myriad") {
        $projectTemplate = "Шаблон:10000"
    } elseif ($area -like "Astronomy") {
        $vietPagesSO = Get-PagesByCategory -Category "Статьи проекта Астрономия высшей важности" | ? { $_ -like "Обсуждение:*"}
        $vietPagesSO += Get-PagesByCategory -Category "Статьи проекта Астрономия высокой важности" | ? { $_ -like "Обсуждение:*"}
        $vietPagesSO | % { $vietPages += $_ -replace "Обсуждение:" }
    } elseif ($area -like "Bollywood") {
        #$vietPages = Get-PagesByCategory -Category "Кинематограф Индии"
        $cats = @("Кинематограф Индии")
        #throw "not implemented yet"
        $vietPages = $pags
    } else {
        "INFO: Please set variable `$area first!"
        throw "no valid area selected"
    }

    "INFO: working on $($area.ToUpper())" | Append-Log
    Start-Sleep -Seconds 5

    #$vietPages = Get-PagesByTemplate -Template $projectTemplate | where {$_ -notin $excludePages }
    #$vietPages = $vietPages | sort
    "$($vietPages.Count) page names found." | Append-Log
    if ($vietPages.Count -eq 0){
        "No pages found for $area, proceeding to the next area" | Append-Log
    }

    ### Получение контента и состояния патрулирования ###

    $startTimeBatched = Get-Date
    $batches = [math]::Ceiling( $vietPages.Count / $batchsize )
    $vietPagesContent = @()
    for ($i=0;$i -lt $batches;$i++){
        $batchbegin = $i * $batchsize
        $batchend = (($batchbegin + $batchsize - 1), ($vietPages.Count - 1) | Measure -Min).Minimum
        $vietPageBatch = $vietPages[$batchbegin..$batchend] -join "|" -replace "&","%26"
            #if ($vietPageBatch -like "*Topf*"){
            #    throw "Topf!"
            #}
        "($i/$batches) [$batchbegin..$batchend] $vietPageBatch"
        $URL = "https://ru.wikipedia.org/w/api.php?action=query&format=json&prop=flagged%7Crevisions&formatversion=2&rvprop=content&rvslots=*&titles=$vietPageBatch"
        $rq = Invoke-WebRequest -Uri $URL -Method GET
        $JSONCont = $rq.Content | ConvertFrom-Json
        foreach ($page in $JSONCont.query.pages){
            # $page = $JSONCont.query.pages[0]
            if ( -not $page.flagged ) {
                $pending_since = 0
            } elseif ($page.flagged.pending_since) {
                $pending_since = $page.flagged.pending_since
            } else {
                $pending_since = $null
            }
            $vietPagesContent += "" | select `
                @{n='title';e={$page.title}}, `
                @{n='content';e={$page.revisions.slots.main.content}}, `
                @{n='pending_since';e={$pending_since}}
        }
    }
    $vietPagesContent = $vietPagesContent | sort -Property title
    $stopTimeBatched = (Get-Date) - $startTimeBatched
    "$($vietPagesContent.Count) pages got their content in $([Math]::Round($stopTimeBatched.TotalSeconds)) seconds." | Append-Log
    $vietPagesContent | where {$_.Content -like ""} | % { "WARNING: no content for $($_.Title)" | Append-Log }

    ##### Extracting internal links #####
    $linksOlolo = @()
    $i = 0
    $startOlolo = Get-Date
    foreach ($page in $vietPagesContent){
        $i++
        if ($removeEasternNames){
            # performange issue here
            $content = $page.content -replace "{{Восточноазиатское имя[^}]{1,20}}}"
        } else {
            $content = $page.content
        }
        $mc = [regex]::matches($content, "\[\[[^\|\]\:]{1,255}[\]\|]{1,2}")
        #$mc = [regex]::matches($content, "\[\[[^\|\]\:]{1,255}")
        if ($mc.groups.count -gt 0){
            $linksOlolo += $mc.groups | select -ExpandProperty Value | select `
                @{n='link';e={ $_ -replace "\[" -replace "\]" -replace "\|" }}, `
                @{n='page';e={ $page.title }}
        }
        if (([string]$i -like "*00") -or ($i -eq $vietPagesContent.Count)){
            "Extracting wikilinks: $i/$($vietPagesContent.Count) pages processed"
        }
    }
    $spentOlolo = (Get-Date) - $startOlolo
    "$($linksOlolo.Count) internal links extracted in $([Math]::Round($spentOlolo.TotalSeconds,2)) seconds." | Append-Log

    #####
    ### Looking for problems
    #####

    $fullAnnounce = $prologue
    $problemStats2 = @{}
    $fullAnnounce2 = @{}

    $pagesNoSourcesAtAll = @()

    ### Не отпатрулированные статьи ###

    $fullAnnounce += "== Не отпатрулированные статьи ==`n"
    $notpatrolled = @($vietPagesContent | where {$_.pending_since -ne $null})
    $patrolled_percent = [Math]::Round(100*($vietPages.Count-$notpatrolled.Count)/$vietPages.Count,2)
    $fullAnnounce += "Patrolled $patrolled_percent % ($($vietPages.Count-$notpatrolled.Count) of $($vietPages.Count))`n"

    foreach ($notpat in ( $notpatrolled | sort -Property pending_since,title )) {
        if ( $notpat.pending_since -eq 0 ){
            $fullAnnounce += "* [[$($notpat.title)]] вообще не патрулировалась`n"
        } else {
            $fullAnnounce += "* [[$($notpat.title)]] не патрулировалась с $([datetime]$notpat.pending_since)`n"
        }
    }

    ### Оформление ###

    $fullAnnounce += "== Недостатки статей ==`n"

    ## New Age checks ##
    # Iterate over checklist
    # FIXME dirty ""
    foreach ($checkArr in @($checkArrs | ? {"$($_[0])#$($_[1])" -notin $checksDisabled} | ? {$_[0] -notlike ""} )){
        $checkName, $checkArgument = $checkArr
        $fullAnnounce2["$checkName#$checkArgument"], $problemStats2["$checkName#$checkArgument"] = 
             CheckWikipages-Router `
                -checkPages $vietPagesContent -checkType $checkName `
                -returnEmpty $printEmptySections -returnModeVersion 2 `
                -bypassArgument $checkArgument #$checkArr[1] #$FuncParams
        $fullAnnounce += $fullAnnounce2["$checkName#$checkArgument"]
        #$problemStats += $problemStats2[$checkName]
    }

    ## Много ссылок на даты
    $fullAnnounce += "=== Статьи с наиболее перевикифицированными датами ===`n"
    $yearLinks = @()
    $chronologies = $vietPagesContent.title | where {$_ -like "Хронология *"}
    foreach ($link in $linksOlolo){
        if (($link.link -match "^[0-9]* год$") -or
            ($link.link -match "^[0-9]* (января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)$")){
            $yearLinks += $link
        }
    }
    "$($yearLinks.Count) links to dates" | Append-Log 
    $yearLinks | Group-Object -Property Page | sort -Property Count -Descending | select Count,Name `
      | where {$_.Name -notin $chronologies}| select -First 20 | % { $fullAnnounce += "* [[$($_.Name)]] ($($_.Count))`n" }
    "Dates estimated" | Append-Log

    ### Стата ###

    $fullAnnounce += "== Статистика ==`n"
    $fullAnnounce += "{| class=`"wikitable`"
    !
    !кол-во
    !%
    |-
    |Всего
    |$($vietPages.Count)
    |100 %
    |-
    |Не отпатрулированные статьи
    |$($notpatrolled.Count)
    |$([Math]::Round(100*$notpatrolled.Count/$vietPages.Count,2)) %`n"

    # $problemStats2.GetEnumerator() | select -ExpandProperty Value | select Name,text 
    $problemStats = $problemStats2.GetEnumerator() | select -ExpandProperty Value | sort -Property timestamp
 
    foreach ($problem in $problemStats){
        $fullAnnounce += "|-`n"
        $fullAnnounce += "|$($problem.text)`n"
        $fullAnnounce += "|$($problem.counter)`n"
        $fullAnnounce += "|$($problem.percent)`n"
    }

    $fullAnnounce += "|}`n"

    ### Вывод. Конец ###

    $fullAnnounce += "На этом всё.`n`n"
    $fullAnnounce += "Отзывы и предложения, пожалуйста, пишите сюда: [[Обсуждение участника:Klientos]].`n`n"
    $fullAnnounce += "<!-- {{User:Klientos/project-tender " +
        "|timestamp=$(Get-Date) }} -->`n"

    $fullAnnounce > $outputfile

    if ($postResultsPage -notlike ""){
        "Results saved to file, now posting to $postResultsPage..." | Append-Log
        # "STUB POSTING" | Append-Log
        if (Set-WPPageText -session $session -title $postResultsPage -newtext $fullAnnounce -summary $summary){
            "Success." | Append-Log
        } else {
            "Failed!" | Append-Log
        }
    } else {
        "No results posting, just saved to file." | Append-Log
    }

    "$area done" | Append-Log
}

throw "good ends here"


#######
### CANDIDATES ###
#######

# Bad site links #
foreach ($page in $vietPagesContent){
    #"Working on $($page.Title)..."
    if ($page.Content -match "turbo"){
        Write-Host -ForegroundColor Yellow "$($page.Title) has turbo!"
    }
}

#######
### UNDER CONSTRUCTION ###
#######

## Примечания без секции

# Ш: Грубый перевод, плохой перевод, недоперевод, Закончить перевод, rq|translate, rq|checktranslate

# Ш:rp

# 1.564.400
foreach ($page in $vietPagesContent){
    # $templateNames = Get-WPPageTemplates -pageContent $content
    $mc = [regex]::matches($page.content, "[\.\,][0-9]{3}[\.\,][0-9]{3}")
    if ($mc.groups.count -gt 0){
        "* [[$($page.title)]] ($($mc.groups.count))`n"
    } else {
        # return ""
    }
}

# too much '{{lang', {{l6e - write PoC

# cite news

# really short pages

# <!-- Bot retrieved archive -->
foreach ($page in $vietPagesContent){
    # $templateNames = Get-WPPageTemplates -pageContent $content
    $mc = [regex]::matches($page.content, "<!-- Bot retrieved archive -->")
    if ($mc.groups.count -gt 0){
        "* [[$($page.title)]] ($($mc.groups.count))`n"
    } else {
        # return ""
    }
}

# Direct external links

#$vietPagesContent2 = @($vietPagesContent | where {$_.title -like "Во *"})
foreach ($page in $vietPagesContent){
    CheckWikipages-DirectExternalLinks-Single -page $page
}
# FIXME check is now relaxed, i. e.
#  pages=[http is allowed
#  direct links in "Literature" is allowed
function CheckWikipages-DirectExternalLinks-Single {
    param (
        $page = ""
    )
        $pageSections = Get-WPPageSections -content $page.content
        $result = ""
        $hasBad = $false
        $cou = 0
        foreach ($section in ($pageSections | where {$_.name -notmatch "Ссылки|Литература"})){
            $mc0 = [regex]::matches($section.content, ".{9}\[http[s]*://[^\]]*]")
            $mc = $mc0 | 
                ? { $_.Value -notmatch ">\[http" } |
                ? { $_.Value -notmatch "страницы=\[http" }
            if ($mc.groups.count -gt 0){
                #"$($mc.groups.count) matches in $($section.name)" | Append-Log
                $hasBad = $true
                $cou += $mc.groups.count
                foreach ($m in $mc.Value) {

                }
                $mc.Value |
                    % { $result += "** <nowiki>$_</nowiki> ($($section.name))`n" }
            }
            #if (($page.tiltle -like "Во Динь Туан"){
            #    "hasbad: $hasBad" | Append-Log
            #
            #    throw "ww-w-wait"
            #}
        }
        if ($hasBad) {
            return "* [[$($page.title)]] ($cou)`n" + $result
        }
        return ""
}

# Disambigs v2

function Update-DisambigStatus {
    param (
        $disPages = ""
    )
    # merge, and some replaces to not break the URL
    #$disPageBatch = $disPages.link -join "|" -replace "&","%26" # -replace "\+","%2B" 
    $disPageBatch = ($batchUnknown.link | % {$_ -replace "#.*"}) -join "|" -replace "&","%26" -replace "\+","%2B" 
    "INFO: should work on $disPageBatch" | Append-Log
    $URL = "https://ru.wikipedia.org/w/api.php?action=query&format=json&prop=flagged%7Crevisions&formatversion=2&prop=categories&cllimit=1000&titles=$disPageBatch"
    $URL | Append-Log
    # $URL = "https://ru.wikipedia.org/w/api.php?action=query&format=json&prop=flagged%7Crevisions&formatversion=2&prop=categories&cllimit=100&titles=UTC+7"
    $rq = Invoke-WebRequest -Uri $URL -Method GET
    $JSONCont = $rq.Content | ConvertFrom-Json
    # 
    #$JSONCont.query.pages[0]
    $maybeDisPages = $JSONCont.query.pages
    foreach ($maybeDisPage in $maybeDisPages){
        if ($maybeDisPage.missing) {
            # TODO Can make a list of red links here
            Write-Host -ForegroundColor Magenta "$($maybeDisPage.title) does not exist"
            $global:disOrNot[$maybeDisPage.title] = $false
            #throw "missing"
        } elseif ( -not $maybeDisPage.categories){
            # FIXME redirects omitted
            "WARNING: $($maybeDisPage.title) has no cats, possibly redirect" | Append-Log
            $global:disOrNot[$maybeDisPage.title] = $false

            #throw "maybe redir"
        } elseif ("Категория:Страницы значений по алфавиту" -in $maybeDisPage.categories.title){
            #"WARNING: $($maybeDisPage.title) disambig!" | Append-Log
            $global:disOrNot[$maybeDisPage.title] = $true
            # throw "Hilo!"
        } else {
            #"$($maybeDisPage.title) okay!" | Append-Log
            $global:disOrNot[$maybeDisPage.title] = $false
        }
    }
    return $JSONCont
}

#$disOrNot["UTC+7"]
#$Bytes = [system.Text.Encoding]::UTF8.GetBytes(" ")
#$disOrNot = @{}
$startDis = Get-Date
$disambigs = @()
$cannotCheck = @()
# $cannotCheck | fl *
$i=0
$batchsize = 20
$batchUnknown = @()
foreach ($il in $linksOlolo) {
    $i++
    $illink = $il.link.Trim() -replace " "," " -replace "#.*","" -replace "  "," " -replace "_"," "
    if ($disOrNot[$illink] -like ""){
        #"$($il.link) status unknown" | Append-Log
        if ($batchUnknown.link -notlike "#*"){
            $batchUnknown += $il
        }
    } elseif ($disOrNot[$illink] -like $false) {
        # Write-Host -ForegroundColor Green "$($il.link)..."
    } elseif ($disOrNot[$illink] -like $true) {
        # Write-Host -ForegroundColor Red "$($il.link)..."
        $disambigs += $il
    }

    if ($batchUnknown.Count -ge $batchsize){
        "===== $i / $($linksOlolo.Count) =====" | Append-Log
        #$disPageBatch = $batchUnknown.link -join "|" -replace "&","%26"
        #"INFO: should work on $disPageBatch" | Append-Log
        $response = Update-DisambigStatus -disPages $batchUnknown
        #$response.query.pages | ? {$_.title -like "UTC+7"}
        foreach ($b in $batchUnknown){
                $blink = $b.link.Trim() -replace " "," " -replace "#.*" -replace "  "," " -replace "_"," "
                if ($disOrNot[$blink] -like ""){
                    "ERROR: $($b.link) status unknown $($b.page)" | Append-Log
                    #throw "Why unknown?"
                    $cannotCheck += $b
                } elseif ($disOrNot[$blink] -like $false) {
                    #Write-Host -ForegroundColor Green "NEW: $($b.link)..."
                } elseif ($disOrNot[$blink] -like $true) {
                    Write-Host -ForegroundColor DarkYellow "NEW: $($b.link)..."
                    $disambigs += $b
                }
        }

        
        #if ( @($batchUnknown | ? {$_.link -like "*#*"}).Count -gt 0) {
        #    throw "awa"
        #}

        $batchUnknown = @()
    }
    #if ($i -gt 5000){";;;Demo ends here"; break}
    #if ([string]$i -like "*00"){
    #}
}
$stopDis = Get-Date
$dailauDis = $stopDis-$startDis
$dailauDis
$cannotCheck.Count
$disambigs.Count

$result = ""
$disGroups = $disambigs | Group-Object -Property page
foreach ($disGroup in $disGroups){
    $result += "* [[$($disGroup.name)]]`n"
    foreach ($link in $disGroup.Group){
        $result += "** [[$($link.link)]]`n"
    }
}


# Категория:Википедия:Cite web (недоступные ссылки без архивной копии) 
# (e. g. бонсаи)

# Тихоокеанский театр военных действий Второй мировой войны#.D0.92.D0.BE.D0.BB.D0.BD.D0.B0 .D0.BF.D0.BE.D0.B1.D0.B5.D0.B4 .D0.AF.D0.BF.D0.BE.D0.BD.D0.B8.D0.B8 .28.D0.B4.D0.B5.D0.BA.D0.B0.D0.B1.D1.80.D1.8C 1941 .E2.80.94 .D0.BC.D0.B0.D0.B9 1942.29
# very bad link (see ololo)

# это отдельно
## --вьет-стабы-- и вьет-гео-стабы не в проекте. Статьи в категории, но не в проекте.

#######
### EXPERIMENTAL ###
#######

## Нет карточки ##

$templCards = Get-PagesByCategory -Category "Шаблоны-карточки по алфавиту"
$hasCard = $false
foreach ($page in $vietPagesContent){
    foreach ($templ in $topLevelTemplates[0..3]) {
        if ($templ -in $templCards){
            $hasCard = $true
        }
    }
}

##

# Милок (уезд) {{{...}}}
$cards = Get-PagesByCategory "Шаблоны-карточки по алфавиту"
$cardNames = $cards | % {$_ -replace "Шаблон:"}
$cardNamesLocal = @("Военное подразделение", "вооруженный конфликт", "Book", "Битва",
    "Государственный деятель2", "Военный", "Университет", "Яз-группа", "Католическая епархия",
    "Infobox company", "АЕ", "Народ")
<#
$pageTitle = "Милок (уезд)"
$URL = "https://ru.wikipedia.org/w/api.php?action=query&format=json&prop=flagged%7Crevisions&formatversion=2&rvprop=content&rvslots=*&titles=$pageTitle"
$rq = Invoke-WebRequest -Uri $URL -Method GET
$JSONCont = $rq.Content | ConvertFrom-Json
$content = $JSONCont.query.pages.revisions.slots.main.content
#>
foreach ($page in $vietPagesContent){
    # $templateNames = Get-WPPageTemplates -pageContent $content
    $templateNames = Get-WPPageTemplates -pageContent $page.content
    if ((($templateNames | ? {($_ -in $cardNames) -or ($_ -in $cardNamesLocal)}).count -eq 0) -and
        (($templateNames | ? {$_ -like "Карточка *"}).Count -eq 0)) {
        "* [[$($page.Title)]] (possibly $($templateNames[0]) | $($templateNames[1]) | $($templateNames[$templateNames.Count-1])) ``n"
        # throw "no card (possibly $($templateNames[$templateNames.Count-1]))"
    }
}
#$cardNames | where { $_ -like "Военное*" }
#$templateNames[$templateNames.Count-1] -in $cardNames
#$Bytes = [system.Text.Encoding]::UTF8.GetBytes($templateNames[9])


## Bad headers ##

# Highly experimental
# TODO fix strarter ,,, — 
foreach ($page in $vietPagesContent){
    # $page.Content -notmatch "<ref"
    #$contentNoTemplates = 
    ""
    "-------------------------$($page.title)-------------------------------------"
    $contentHeader = $page.Content[0..80] -join ""
    $contentCleared = $page.Content -replace "{{[^}]{0,30}}}","" -replace "{{[^}]*}}","" -replace "\([^\)]{0,20}\)",""  -replace "\([^\)]*\)","" 
    $header = $contentCleared[0..200] -join ""
    # ($page.Content[0..20] -join "" -split "—")[0]
    if ($header -notmatch "—") {
        write-host -ForegroundColor Yellow "$($page.title) — odd header, not contains '—'"
    } else {
        $intro = ($header -split "—")[0]
        $intro
        if (($intro -match "\(") -or ($intro -match "\)")){
            write-host -ForegroundColor Yellow "$($page.title) — odd header, not unpaired '()'"
        }
        if ($intro -match ",[ ]*,") {
            write-host -ForegroundColor Red "$($page.title) — odd header, commas attack!"
            #break
        }
    }
    if ($page.Content -match "\n'''[^—]*'''[^—]*—.*\n"){
        $intro2 = $Matches[0]
        $intro2Cleared = $intro2 -replace "\([^\)]{0,20}\)",""  -replace "\([^\)]*\)","" 
        write-host -ForegroundColor Cyan $intro2Cleared
    } else {
        write-host -ForegroundColor Magenta "No intro2 detected!"
        $page.Content[0..80] -join ""
    }
}


#######
### Просто статистика
#######

# URLs in cite web
$urlLinksPages = @()
$urlLinks = @()
foreach ($page in $vietPagesContent){
    #"== $($page.title) =="
    $mc = [regex]::matches($page.content, "{{[ ]*cite web[^}]*\|[ ]*url[ ]*=[^\|]*")
    if ($mc.groups.count -gt 0){
        #if ($page.Content -match "archiveurl[ ]*=[^\|]*http[s]\:\/\/books\.google\.")
        foreach ($cw in $mc.groups) {
            $cwArr = $cw.Value -replace " ","" -split "\|url="
            $urlLinks += $cwArr[$cwArr.Count-1]
            if ($cwArr[$cwArr.Count-1] -notlike "http*://*"){
                "WARNING: $($cwArr[$cwArr.Count-1]) @ $($page.title)"
                "   $cw"
            }
        }
    }
    if ($page.title -like "Бла1"){
        $mc.groups
        throw "wait a minuite"
    }
}
"$($urlLinks.Count) ссылок в шаблоне cite web"
$urlLinksArchive = @()
foreach ($urlLink in $urlLinks){
    if ($urlLink -like "*web.archive.org*") {
    #if ($urlLink -like "*e.org*") {
        "Matched: $urlLink"
        $urlLinksArchive += $urlLink
    }
}
$urlLinksArchive.Count

# URLs NOT in cite web
$simpleLinks = @()
$simpleLinksPages = @()
$fullAnnounce = "=== [Ссылки] без cite web ==="
foreach ($page in $vietPagesContent){
    $mc = [regex]::matches($page.content, "\[http[s]*://[^ ]*")
    if ($mc.groups.count -gt 0){
        "* [[$($page.title)]] ($($mc.groups.count))"
        $simpleLinksPages += $page.title
        foreach ($cw in $mc.groups) {
            $arcLink = $cw.Value -replace "\[",""
            $arcLink
            $simpleLinks += $arcLink
        }
    }
}
"$($simpleLinks.Count) внешних ссылок без шаблона cite web"
"$($simpleLinksPages.Count) статей с внешними ссылками без шаблона cite web"



