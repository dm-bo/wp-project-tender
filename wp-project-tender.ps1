
### Defining functions ###

. "$PSScriptRoot/functions.ps1"
. "$PSScriptRoot/wp-functions-aux.ps1"
. "$PSScriptRoot/wp-functions-checks.ps1"

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
#$area = "Football"
$area = "Vietnam"
#>

## default values ##

# checks
$checkCiteWeb = $true
$checkDirectWebarchive = $true
$communesSearch = $false
# do not work on these pages
$excludePages = @()
# output
$outputfile = "C:\Users\Dm\Desktop\wp\badlinks-$area.txt"
# performance optimizations
$removeEasternNames = $false # replacing eastern names has no sence in this context

## custom values

if ($area -like "Vologda"){
    $projectTemplate = "Шаблон:Статья%20проекта%20Вологда"
} elseif ($area -like "Vietnam") {
    $projectTemplate = "Шаблон:Статья%20проекта%20Вьетнам" 
    $outputfile = "C:\Users\Dm\Desktop\wp\viet-badlinks.txt"
    $communesSearch = $true
} elseif ($area -like "Holocaust") {
    $projectTemplate = "Шаблон:Статья%20проекта%20Холокост"
    $checkCiteWeb = $false
    $checkDirectWebarchive = $false
} elseif ($area -like "Belarus") {
    $projectTemplate = "Шаблон:Статья%20проекта%20Белоруссия"
    $checkCiteWeb = $false
    $checkDirectWebarchive = $false
    $excludePages = @("Белоруссия/Шапка")
} elseif ($area -like "Israel") {
    $projectTemplate = "Шаблон:Статья%20проекта%20Израиль"
    $checkCiteWeb = $false
    $checkDirectWebarchive = $false
    #$excludePages = @("Белоруссия/Шапка")
} elseif ($area -like "SverdlovskObl") {
    $projectTemplate = "Шаблон:Статья%20проекта%20Свердловская область"
} elseif ($area -like "Tatarstan") {
    $projectTemplate = "Шаблон:Статья%20проекта%20Татарстан"
    #$checkCiteWeb = $false
    #$checkDirectWebarchive = $false
    #$excludePages = @("Белоруссия/Шапка")
} elseif ($area -like "Football") {
    "WARNING: working on FOOTBALL" | Append-Log
    $projectTemplate = "Шаблон:Статья%20проекта%20Футбол"
    throw "Not ready for almost 30k pages"
} elseif ($area -like "cybersport") {
    $projectTemplate = "Шаблон:Статья проекта Киберспорт"
} elseif ($area -like "Karelia") {
    $projectTemplate = "Шаблон:Статья проекта Карелия"
} else {
    "INFO: Please set variable `$area first!"
    throw "no valid area selected"
}

"INFO: working on $($area.ToUpper())" | Append-Log
Start-Sleep -Seconds 5

$vietPages = Get-PagesByTemplate -Template $projectTemplate | where {$_ -notin $excludePages }
$vietPages = $vietPages | sort
"$($vietPages.Count) page names found." | Append-Log

### Получение контента и состояния патрулирования ###

$startTimeBatched = Get-Date
$batchsize = 5 
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
# save backup for testing
$vietPagesContentOrig = $vietPagesContent
$vietPagesContent | where {$_.Content -like ""} | % { "WARNING: no content for $($_.Title)" | Append-Log }

##### HACK! HACK! HACK! #####
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
    if ($mc.groups.count -gt 0){
        #"== $($page.Title) =="
        #$mc.groups | select -ExpandProperty Value 
        #$mc.groups | select -ExpandProperty Value | % { $linksOlolo += $_ }
        $linksOloloTemp = @()
        $mcValues = $mc.groups | select -ExpandProperty Value
        foreach ($value in $mcValues) {
            $linksOloloTemp += "" | select `
            @{n='link';e={$value -replace "\|$","" -replace "^\[\[" -replace "\]\]$" }}, `
            @{n='page';e={$page.title}}
            # $linksOloloTemp | group -Property link | sort -Descending -Property Count | select Count,Name
        }

        #$linksOlolo += $linksOloloTempNormalized
        $linksOlolo += $linksOloloTemp
    }
    
    if (([string]$i -like "*00") -or ($i -eq $vietPagesContent.Count)){
        "Extracting wikilinks: $i/$($vietPagesContent.Count) pages processed"
    }
    
    if ($i -gt 40){
        #break
    }
}
$spentOlolo = (Get-Date) - $startOlolo
"$($linksOlolo.Count) internal links extracted in $([Math]::Round($spentOlolo.TotalSeconds,2)) seconds." | Append-Log


#####
### Looking for problems
#####

$problemStats = @()
$fullAnnounce = ""

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

$fullAnnounce += "== Оформление ==`n"

## Неоформленные ссылки ##

$fullAnnounce += "=== Голые ссылки ===`n"
$nakedCount = 0
foreach ($page in $vietPagesContent){
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
        $fullAnnounce += "[[$($page.Title)]]:`n"
        $seminaked | % { $fullAnnounce += "* <nowiki>$_</nowiki>`n" }
        $naked | % { $fullAnnounce += "* <nowiki>$_</nowiki>`n" }
        $nakedCount++
    }
}
"$nakedCount pages with naked links" | Append-Log

## Статьи без ссылок или их требования ##

# Статьи без ссылок в разделе "Ссылки"
$fullAnnounce += "=== Статьи без ссылок в разделе «Ссылки» ===`n"
$fullAnnounce += "Если в «Ссылках» есть источники без http-сылок, то их, возможно, стоит переместить в  раздел «Литература».`n"
$noLinksInLinksCounter = 0
foreach ($page in $vietPagesContent){
    $good = $false
    if (($page.Content -notmatch "http[s]{0,1}://") -and ($page.Content -match "==[ ]*Ссылки[ ]*==") -and
        ($page.Content -notmatch "{{ВС}}") -and ($page.Content -notmatch "{{Ethnologue\|") -and
        ($page.Content -notmatch "{{WAD\|") -and
        ($page.Content -notmatch "{{ВТ-ЭСБЕ\|") -and
        ($page.Content -notmatch "{{IMDb name\|") -and
        ($page.Content -notmatch "{{Шахматные ссылки[ \n]*\|") -and
        ($page.Content -notmatch "{{ЭЕЭ[ \n]*\|") -and
        ($page.Content -notmatch "{{MacTutor Biography[ \n]*\|") -and
        ($page.Content -notmatch "{{Сотрудник РАН[ \n]*\|") -and
        ($page.Content -notmatch "{{Math-Net.ru[ \n]*\|") -and
        ($page.Content -notmatch "{{oopt.aari.ru[ \n]*\|") -and
        ($page.Content -notmatch "{{Warheroes[ \n]*\|"))
    {
        $fullAnnounce += "* [[$($page.Title)]]`n"
        $noLinksInLinksCounter++
    }
}
"$noLinksInLinksCounter pages with no links iIn links section" | Append-Log

# Статьи без примечаний в разделе "Примечания"
$fullAnnounce += "=== Статьи без примечаний в разделе «Примечания» ===`n"
$fullAnnounce += "Не считает примечания, подтянутые из ВД. В любом случае, было бы неплохо добавить сноски в тело статьи.`n"
$noRefsCounter = 0
foreach ($page in $vietPagesContent){
    if (($page.Content -notmatch "<ref") -and ($page.Content -notmatch "{{sfn") -and ($page.Content -match "==[ ]*Примечания[ ]*==")){
        $fullAnnounce += "* [[$($page.Title)]]`n"
        $noRefsCounter++
    }
}
"$noRefsCounter pages with no refs in References section" | Append-Log

# Статьи с прямыми интервики-ссылками
$fullAnnounce += "=== Статьи с прямыми интервики-ссылками ===`n"
$fullAnnounce += "Нужно заменить на шаблон iw или добавить прямую ссылку на статью в РуВП, если она уже есть.`n"
$directInterwikiCounter = 0
foreach ($page in $vietPagesContent){
    if ($page.Content -match "\[\[\:[a-z]{2,3}\:[^\:]*\]\]"){
        $fullAnnounce += "* [[$($page.Title)]]`n"
        $directInterwikiCounter++
    }
}
"$directInterwikiCounter pages with direct interwiki links" | Append-Log

# <!-- Заголовок добавлен ботом -->
$fullAnnounce += "=== Заголовок добавлен ботом ===`n"
$fullAnnounce += "Нужно проверить, что заголовок правильный, и убрать html-комментарий ''<nowiki><!-- Заголовок добавлен ботом --></nowiki>''`n"
$botTitleCounter = 0
foreach ($page in $vietPagesContent){
    if ($page.Content -match "<!-- Заголовок добавлен ботом -->") {
        $fullAnnounce += "* [[$($page.title)]]`n"
        $botTitleCounter++
    }
}
"$botTitleCounter pages with bot-added link titles" | Append-Log

## Не содержат [[Категория:
$fullAnnounce += "=== Не указаны категории ===`n"
$fullAnnounce += "Иногда категории назначаются шаблонами, тогда указывать категории напрямую не нужно. В таком случае категоризирующий "
$fullAnnounce += "шаблон следует учитывать при составлении этого списка.`n"
$noCatCounter = 0
foreach ($page in $vietPagesContent){
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
        ($page.Content -notmatch "\{\{Вьетнам на Олимпийских играх\}\}")
    ) {
        #"WARNING: $($page.Title) has no categories" | Append-Log
        $fullAnnounce += "* [[$($page.Title)]]`n"
        $noCatCounter++
    }
}
"$noCatCounter pages have no categories" | Append-Log

## Direct links to Google books
$fullAnnounce += "=== Прямые ссылки на Google books ===`n"
$fullAnnounce += "Их желательно поменять на [[Шаблон:книга]].`n"
$linkToGoogleBooksCounter = 0
foreach ($page in $vietPagesContent){
    $good = $false
    if ($page.Content -match "\[http[s]\:\/\/books\.google\.") {
        $fullAnnounce += "* [[$($page.Title)]]`n"
        $linkToGoogleBooksCounter++
    }
}
"$linkToGoogleBooksCounter pages with direct links to Google books" | Append-Log

# [web.archive
if ($checkDirectWebarchive -eq $true) {
    $fullAnnounce += "=== Прямые ссылки на web.archive.org ===`n"
    $fullAnnounce += "Желательно заменить их на [[Ш:cite web]]  параметрами archiveurl и archivedate.`n"
    $cou = 0
    foreach ($page in $vietPagesContent){
        $mc = [regex]::matches($page.content, "\[http[s]*://web.archive.org[^ \]\n]*")
        if ($mc.groups.count -gt 0){
            #Write-Host -ForegroundColor Yellow "$($page.Title) has direct links to web.archive.org ($($mc.groups.count))"
            $fullAnnounce += "* [[$($page.Title)]] ($($mc.groups.count))`n"
            $mc.groups.value -replace "[http[s]*://web.archive.org/web/[0-9]*/","" | % {$fullAnnounce += "** $_`n"}
            $cou++
        }
        # if ($page.title -like "Карельские имена") { throw "Stop here" }
    }
    "$cou pages have direct links to web.archive.org" | Append-Log
    $problemStats += New-ProblemStat -name 'DirectWebarchive' -text 'Прямые ссылки на web.archive.org' `
        -counter $cou -total $vietPagesContent.Count
} else {
    $fullAnnounce += "=== Прямые ссылки на web.archive.org (отключено) ===`n"
}

## .<ref> — применить СН-ПРЕП
$fullAnnounce += "=== [[ВП:СН-ПРЕП|СН-ПРЕП]] ===`n"
$fullAnnounce += "Страницы, в тексте которых есть <code><nowiki>.<ref</nowiki></code> "
$fullAnnounce += "или <code><nowiki>.{{sfn</nowiki></code>. Сноска должна стоять перед точкой, "
$fullAnnounce += "кроме случаев, когда точка является частью сокращения.`n"
$cou = 0
foreach ($page in $vietPagesContent){
    $mc = [regex]::matches($page.content, ".{6}(\.<ref[ >]|\.{{sfn\|)")
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
            $fullAnnounce += "* [[$($page.title)]]`n"
            $cou++
        }
    }
}
"$cou страниц с проблемами СН-ПРЕП" | Append-Log
$problemStats += New-ProblemStat -name 'SN_PREP' -text 'СН-ПРЕП' `
    -counter $cou -total $vietPagesContent.Count

## ;Пумпурум — поменять на разделы
$fullAnnounce += "=== ;Недоразделы ===`n"
$fullAnnounce += "Использована кострукция <code><nowiki>;Что-то</nowiki></code>. Скорее всего, "
$fullAnnounce += "её следует заменить, например, на <code><nowiki>=== Что-то ===</nowiki></code>.`n"
$cou = 0
foreach ($page in $vietPagesContent){
    $pageSections = Get-WPPageSections -content $page.content
    <#
    # for testing purposes
    "== $($page.title) =="
    foreach ($s in $pageSections){
        " "*$s.level + $s.name
    }
    $pageSections[2] | fl
    #>
    $hasSemi = $false
    foreach ($section in ($pageSections | where {$_.name -notmatch "Литература|Примечания"})){
        if ($section.content -match "\n;") {
            $hasSemi = $true
        }
    }
    if ($hasSemi){
        $fullAnnounce += "* [[$($page.Title)]]`n"
        $cou++
    }
}
"$cou страниц с ;Недоразделами" | Append-Log
$problemStats += New-ProblemStat -name 'SemicolonSections' -text ';Недоразделы' `
    -counter $cou -total $vietPagesContent.Count

## Нет ссылок
$fullAnnounce += "=== Мало внутренних ссылок ===`n"
$cou = 0
$toolow = 0.9
$toohigh = 20
foreach ($page in $vietPagesContent){
    $enc = [System.Text.Encoding]::UTF8
    $enccont = $enc.GetBytes($page.Content)
    $pageSize = $enccont.Count
    if ($pageSize -gt 20480) {
        $mc = [regex]::matches($page.content, "\[\[[^\]:]*\]\]")
        $linksPerKB = [math]::Round($mc.groups.count / ($pageSize / 1024), 2)
        if ($linksPerKB -gt $toohigh){
            $color = "Magenta"
            Write-Host -ForegroundColor $color "* $linksPerKB — [[$($page.title)]] ($($mc.groups.count)/$pageSize)"
            $fullAnnounce += "* [[$($page.title)]] ($linksPerKB, $($mc.groups.count)/$pageSize) — а здесь наоборот, слишком много`n"
        } elseif ($linksPerKB -gt $toolow) {
            # $color = "Green"
        } else {
            $fullAnnounce += "* [[$($page.title)]] ($linksPerKB, $($mc.groups.count)/$pageSize)`n"
            $cou++
        }
        # Write-Host -ForegroundColor $color "* $linksPerKB — [[$($page.title)]] ($($mc.groups.count)/$pageSize)"
    }
}
"$cou pages have too few internal links" | Append-Log
$problemStats += New-ProblemStat -name 'tooFewWikilinks' -text 'Мало внутренних ссылок' `
    -counter $cou -total $vietPagesContent.Count

## Много ссылок на даты
$fullAnnounce += "=== Статьи с наиболее перевикифицированными датами ===`n"
$yearLinks = @()
foreach ($link in $linksOlolo){
    if (($link.link -match "^[0-9]* год$") -or
        ($link.link -match "^[0-9]* (января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)$")){
        $yearLinks += $link
    }
}
# $yearLinks | Group-Object -Property Page | sort -Property Count -Descending | select -First 20 | select Count,Name
"$($yearLinks.Count) links to dates" | Append-Log 
$yearLinks | Group-Object -Property Page | sort -Property Count -Descending | select Count,Name `
  | select -First 20 | % { $fullAnnounce += "* [[$($_.Name)]] ($($_.Count))`n" }
"Dates estimated" | Append-Log

# Архивировано 20220820034353 года.
# FIXME * [[Отрицание (фильм)]] (  ;   ;   ;   )
$fullAnnounce += "=== Страницы с неформатными датами в cite web ===`n"
$fullAnnounce += "Используйте формат <code>YYYY-MM-DD</code> ([[ВП:ТД]]).`n"
$poorDatesCounter = 0
foreach ($page in $vietPagesContent){
    $mc = [regex]::matches($page.content, "{{cite web[^{}]+({{[^}]+}})*[^{}]+}}")
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
            $fullAnnounce += "* [[$($page.title)]] ($($badDates -join "; "))`n"
            $poorDatesCounter ++
        }
    }
}
"$poorDatesCounter pages have poor dates in cite web" | Append-Log
$problemStats += New-ProblemStat -name "poorDates" -text 'Неформатные даты в cite web' `
     -counter $poorDatesCounter -total $vietPagesContent.Count

# квадратные километры
$fullAnnounce += "=== Страницы с кв км или кв. км ===`n"
$fullAnnounce += "Желательно поменять на км².`n"
$badSquareKmCounter = 0
foreach ($page in $vietPagesContent){
    if (($page.content -match "кв. км") -or
         ($page.content -match "кв км"))
    {
        $fullAnnounce += "* [[$($page.title)]]`n"
        $badSquareKmCounter++
    }
}
"$badSquareKmCounter pages have bad square kilometers" | Append-Log
$problemStats += New-ProblemStat -name "badSquareKm" -text 'Содержат кв км или кв. км' `
     -counter $badSquareKmCounter -total $vietPagesContent.Count

## Декоммунизация
if ($communesSearch -eq $true) {
    $fullAnnounce += "== Декоммунизация ==`n"
    $fullAnnounce += "Это актуально только для ПРО:Вьетнам, в прочих случаях должно быть выключено.`n"
    $fullAnnounce += "В ПРО:Вьетнам ''коммуны'' (равно как ''приходы'' и, в большинстве случаев, ''деревни'') следует заменить на ''общины''.`n"
    $communesCou = 0
    foreach ($page in $vietPagesContent){
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
                $fullAnnounce += "* [[$($page.Title)]] ($($commicount))`n"
                $communesCou++
            }
        }
    }
    "$communesCou communes found" | Append-Log
}

### Поиск плохих шаблонов ###
if ($checkCiteWeb -eq $true) {
    $fullAnnounce += "== Шаблоны оформления ссылок ==`n"
    $fullAnnounce += "Обычно эти шаблоны следует заменить на [[Ш:cite web]], [[Ш:книга]], [[Ш:статья]] или [[Ш:Официальный сайт]].`n"
    
    ### TODO продолжить стату ###

    ## включения через API ##
    # Это медленнее
    $badTemplates = @("Шаблон:Citation", "Шаблон:Cite press release", "Шаблон:PDFlink")
    foreach ($badTemplate in $badTemplates) {
        $templatedPages = Get-PagesByTemplate -Template "$badTemplate" -namespace 0
        $fullAnnounce += "=== Страницы с шаблоном [[$badTemplate|]] ===`n"
        $vietPages | where {$_ -in $templatedPages} | % { $fullAnnounce += "* [[$_]]`n"}
    }
    "Templates over API have been processed" | Append-Log 

    ## Регэкспами ##
    # Это быстрее
    $badSlowTemplates = @("Wayback", "webarchive", "Архивировано", "Проверено",
        "ISBN", "h")
    foreach ($badSlowTemplate in $badSlowTemplates) {
        $fullAnnounce += "=== Страницы с шаблоном [[Шаблон:$badSlowTemplate|]] ===`n"
        $badTemplaneCounter = 0
        foreach ($page in $vietPagesContent){
            $mc = [regex]::matches($page.content, "{{$badSlowTemplate\|[^\}]{0,200}}}|{{$badSlowTemplate}}")
            if ($mc.groups.count -gt 0){
                $fullAnnounce += "* [[$($page.title)]] ($($mc.groups.count))`n"
                $badTemplaneCounter++
            }
        }
        "$badSlowTemplate — $badTemplaneCounter" | Append-Log 
    }

    $fullAnnounce += "=== Страницы с *icon-шаблонами ===`n"
    $badTemplaneCounter = 0
    foreach ($page in $vietPagesContent){
        $mc = [regex]::matches($page.content, "{{[a-zA-Z]{2} icon}}")
        if ($mc.groups.count -gt 0){
            $fullAnnounce += "* [[$($page.title)]] ($($mc.groups.count))`n"
            $badTemplaneCounter++
        }
    }
    "$badTemplaneCounter страниц с *icon-шаблонами" | Append-Log

    $fullAnnounce += "=== Страницы с ref-шаблонами ===`n"
    $badTemplaneCounter = 0
    foreach ($page in $vietPagesContent){
        $mc = [regex]::matches($page.content, "{{ref-[a-zA-Z]+\|[^\}]{0,200}}}|{{ref-[a-zA-Z]+}}")
        if ($mc.groups.count -gt 0){
            $fullAnnounce += "* [[$($page.title)]] ($($mc.groups.count))`n"
            $badTemplaneCounter++
        }
    }
    "$badTemplaneCounter страниц с Ref-шаблонами" | Append-Log
} else {
    $fullAnnounce += "== Шаблоны оформления ссылок (отключено) ==`n"
}

### Связность ###

$fullAnnounce += "== Связность ==`n"

## Изолированные статьи ##
$fullAnnounce += "=== Страницы с шаблоном [[Шаблон:изолированная статья|]] ===`n"
$fullAnnounce += "В другие статьи Википедии нужно добавить ссылки на эти статьи.`n"
$isolatedCounter = 0
foreach ($page in $vietPagesContent){
    $mc = [regex]::matches($page.content, "{{изолированная статья\|[^\}]{0,200}}}|{{изолированная статья}}")
    if ($mc.groups.count -gt 0){
        $fullAnnounce += "* [[$($page.title)]] ($($mc.groups.count))`n"
        $isolatedCounter++
    }
}
"$isolatedCounter isolated pages" | Append-Log
$problemStats += New-ProblemStat -name "isolated" -text 'Изолированные' `
     -counter $isolatedCounter -total $vietPagesContent.Count

### Проблемы с источниками ###

$fullAnnounce += "== Проблемы с контентом и проверяемостью ==`n"

# Очень короткие статьи
$checkResult = CheckWikipages-Empty -pages $vietPagesContent
$fullAnnounce += $checkResult.wikitext
$problemStats += $checkResult.problemstat

# $fullAnnounce = ""
$fullAnnounce += "=== Статьи без источников ===`n"
$fullAnnounce += "Статьи без разделов «Ссылки», «Литература», «Источники», примечаний или других признаков наличия источников.`n"
$noSourcesCount = 0
$pagesNoSourcesAtAll = @()
foreach ($page in $vietPagesContent){
    <#
    if (($page.content -match "{{rq\|[^\}]{0,20}sources[\|}]") -or
        ($page.content -match "{{Нет источников\|") -or
        ($page.content -match "{{Нет ссылок\|") -or
        ($page.Content -match "{{список однофамильцев}}")){
    #>
    if (($page.Content -match "<ref") -or
        ($page.Content -match "{{sfn\|") -or
        ($page.Content -match "==[ ]*Ссылки[ ]*==") -or
        ($page.Content -match "==[ ]*Литература[ ]*==") -or
        ($page.Content -match "==[ ]*Источники[ ]*==") -or
        ($page.Content -match "\{\{IMDb name\|")
        )
    {
        
    } else {
        $pagesNoSourcesAtAll += $page.Title
        $fullAnnounce += "* [[$($page.Title)]]`n"
        $noSourcesCount++
    }
}
"$noSourcesCount with no sources" | Append-Log

# Страницы с запросом источников
$checkResult = CheckWikipages-SourceRequest -pages $vietPagesContent -pagesNoSourcesAtAll $pagesNoSourcesAtAll
$fullAnnounce += $checkResult.wikitext
$problemStats += $checkResult.problemstat

# Недоступные ссылки
$checkResult = CheckWikipages-LinksUnanvailable -pages $vietPagesContent
$fullAnnounce += $checkResult.wikitext
$problemStats += $checkResult.problemstat

# rq|renew  
## включения через API ##
$badTemplates = @("Шаблон:Аффилированные источники", "Шаблон:Спам-ссылки", "Шаблон:Обновить")
foreach ($badTemplate in $badTemplates) {
    $templatedPages = Get-PagesByTemplate -Template "$badTemplate" -namespace 0
    $fullAnnounce += "=== Страницы с шаблоном [[$badTemplate|]] ===`n"
    $vietPages | where {$_ -in $templatedPages} | % { $fullAnnounce += "* [[$_]]`n"}
}

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
|$([Math]::Round(100*$notpatrolled.Count/$vietPages.Count,2)) %
|-
|Голые ссылки
|$nakedCount
|$([Math]::Round(100*$nakedCount/$vietPages.Count,2)) %
|-
|Статьи без источников
|$noSourcesCount
|$([Math]::Round(100*$noSourcesCount/$vietPages.Count,2)) %`n"

foreach ($problem in $problemStats){
    $fullAnnounce += "|-`n"
    $fullAnnounce += "|$($problem.text)`n"
    $fullAnnounce += "|$($problem.counter)`n"
    $fullAnnounce += "|$($problem.percent)`n"
}

$fullAnnounce += "|}`n"

### Вывод. Конец ###

$fullAnnounce += "На этом всё.`n"
$fullAnnounce += "`n"
$fullAnnounce += "Отзывы и предложения, пожалуйста, пишите сюда: [[Обсуждение участника:Klientos]].`n"
$fullAnnounce += "`n"
$fullAnnounce += "<!-- $(Get-Date) -->`n"

$fullAnnounce > $outputfile

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
    if ($page.Content -match "dzen.ru"){
        Write-Host -ForegroundColor Yellow "$($page.Title) has dzen!"
    }
    if ($page.Content -match "zen.ya"){
        Write-Host -ForegroundColor Yellow "$($page.Title) has dzen!"
    }
    if ($page.Content -match "tr-page.ya"){
        Write-Host -ForegroundColor Yellow "$($page.Title) has autotranslated source!"
    }
    <#
    if ($page.Content -match ".{16}translat.{16}"){
        $Matches.Values
        Write-Host -ForegroundColor Yellow "$($page.Title) has trans!"
    }
    if ($page.Content -match ".{16}youtube.{16}"){
        $Matches.Values
        Write-Host -ForegroundColor Yellow "$($page.Title) has you!"
    }
    #>
}

### UNDER CONSTRUCTION ###

## [http://en.wikipedia.org/wiki/Dror_Feiler]

## Примечания без секции

# Ш: Грубый перевод, плохой перевод, недоперевод, Закончить перевод, rq|translate, rq|checktranslate 

# это отдельно
## --вьет-стабы-- и вьет-гео-стабы не в проекте. Статьи в категории, но не в проекте.

# too much '{{lang' - write PoC



## Bad headers
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

# <!-- Bot retrieved archive -->



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



