
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
$area = "Crimea"
$area = "Myriad"
$area = "Astronomy"
$area = "Bollywood"
#$area = "Football"
$area = "Vietnam"
#>

## default values ##

# checks
$checksDisabled = @()
$checkCiteWeb = $true
$checkDirectWebarchive = $true
$communesSearch = $false
# do not work on these pages
$excludePages = @()
# output
$outputfile = "C:\Users\Dm\Desktop\wp\badlinks-$area.txt"
# performance optimizations
$removeEasternNames = $false # replacing eastern names has no sence in this context
$printEmptySections = $true

# Test: triggering exceptions
$vietPages = @()

## custom values

if ($area -like "Vologda"){
    $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Вологда" | where {$_ -notin $excludePages } | sort  
} elseif ($area -like "Vietnam") {
    $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Вьетнам" | where {$_ -notin $excludePages } | sort  
    $communesSearch = $true
    $printEmptySections = $false
} elseif ($area -like "Holocaust") {
    $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Холокост" | where {$_ -notin $excludePages } | sort

    $checkCiteWeb = $false
    #
    $checkDirectWebarchive = $false
    #
    $checksDisabled = @("DirectWebarchive")

    $printEmptySections = $false
} elseif ($area -like "Belarus") {
    $excludePages += @("Белоруссия/Шапка")
    $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Белоруссия" | where {$_ -notin $excludePages } | sort
    $checkCiteWeb = $false
    $checkDirectWebarchive = $false
} elseif ($area -like "Israel") {
    $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Израиль" | where {$_ -notin $excludePages } | sort
    $checkCiteWeb = $false
    $checkDirectWebarchive = $false
    #$excludePages = @("Белоруссия/Шапка")
} elseif ($area -like "SverdlovskObl") {
    $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Свердловская область" | where {$_ -notin $excludePages } | sort
} elseif ($area -like "Tatarstan") {
    $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Татарстан" | where {$_ -notin $excludePages } | sort
} elseif ($area -like "Football") {
    "WARNING: working on FOOTBALL" | Append-Log
    $projectTemplate = "Шаблон:Статья%20проекта%20Футбол"
    throw "Not ready for almost 30k pages"
} elseif ($area -like "cybersport") {
    $vietPages = Get-PagesByTemplate -Template "Шаблон:Статья проекта Киберспорт" | where {$_ -notin $excludePages } | sort
} elseif ($area -like "Karelia") {
    $projectTemplate = "Шаблон:Статья проекта Карелия"
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
    throw "no pages found"
}

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

$problemStats2 = @{}
$fullAnnounce2 = @{}

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


#### New Age checks ####
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
    @("Communes","")            # Декоммунизация
    )
foreach ($checkArr in @($checkArrs | ? {$_[0] -notin $checksDisabled} )){
    $checkName = $checkArr[0]
    # FIXME: DO NUT NEED if
    if ($checkArr[1] -notlike ""){
            $FuncParams = @{bypassArgument = $checkArr[1]}
    } else {
        #"Empty arg" | Append-Log
    }
    $fullAnnounce2[$checkName], $problemStats2[$checkName] = CheckWikipages-Router `
            -checkPages $vietPagesContent -checkType $checkName `
            -returnEmpty $printEmptySections -returnModeVersion 2 `
            $FuncParams
    $fullAnnounce += $fullAnnounce2[$checkName]
    $problemStats += $problemStats2[$checkName]
}

### Поиск плохих шаблонов ###
if ($checkCiteWeb -eq $true) {
    $fullAnnounce += "== Шаблоны оформления ссылок ==`n"
    $fullAnnounce += "Обычно эти шаблоны следует заменить на [[Ш:cite web]], [[Ш:книга]], [[Ш:статья]] или [[Ш:Официальный сайт]].`n"
    
    $badSlowTemplates = @("Citation", "Cite press release", "PDFlink", "Wayback", "webarchive",
         "Архивировано", "Проверено", "ISBN", "h")
    foreach ($badSlowTemplate in $badSlowTemplates) {
        $checkResult = CheckWikipages-Router -checkPages $vietPagesContent -checkType TemplateRegexp `
             -returnEmpty $printEmptySections -bypassArgument $badSlowTemplate
        $fullAnnounce += $checkResult.wikitext
        $problemStats += $checkResult.problemstat
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
# $yearLinks | Group-Object -Property Page | sort -Property Count -Descending | select -First 20 | select Count,Name
"$($yearLinks.Count) links to dates" | Append-Log 
$yearLinks | Group-Object -Property Page | sort -Property Count -Descending | select Count,Name `
  | where {$_.Name -notin $chronologies}| select -First 20 | % { $fullAnnounce += "* [[$($_.Name)]] ($($_.Count))`n" }
"Dates estimated" | Append-Log

### Связность ###

$fullAnnounce += "== Связность ==`n"

# Изолированные статьи
$checkResult = CheckWikipages-Router -checkPages $vietPagesContent -checkType Isolated -returnEmpty $printEmptySections
$fullAnnounce += $checkResult.wikitext
$problemStats += $checkResult.problemstat

### Проблемы с источниками ###

$fullAnnounce += "== Проблемы с контентом и проверяемостью ==`n"

# Очень короткие статьи
#$checkResult = CheckWikipages-Empty -pages $vietPagesContent
$checkResult = CheckWikipages-Router -checkPages $vietPagesContent -checkType Empty -returnEmpty $printEmptySections
$fullAnnounce += $checkResult.wikitext
$problemStats += $checkResult.problemstat

# no sources
$fullAnnounce += "=== Статьи без источников ===`n"
$fullAnnounce += "Статьи без разделов «Ссылки», «Литература», «Источники», примечаний или других признаков наличия источников.`n"
$noSourcesCount = 0
$pagesNoSourcesAtAll = @()
foreach ($page in $vietPagesContent){
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

<#
# Статьи без источников
# not ready to use
$checkResult = CheckWikipages-Router -checkPages $vietPagesContent -checkType NoSources -returnEmpty $printEmptySections
$fullAnnounce += $checkResult.wikitext
$problemStats += $checkResult.problemstat
#>

# Страницы с запросом источников
$checkResult = CheckWikipages-SourceRequest -pages $vietPagesContent -pagesNoSourcesAtAll $pagesNoSourcesAtAll
$fullAnnounce += $checkResult.wikitext
$problemStats += $checkResult.problemstat

# Недоступные ссылки
$checkResult = CheckWikipages-Router -checkPages $vietPagesContent -checkType LinksUnanvailable -returnEmpty $printEmptySections
$fullAnnounce += $checkResult.wikitext
$problemStats += $checkResult.problemstat

# Шаблоны проблем с контентом 
foreach ($badSlowTemplate in @("Аффилированные источники", "Спам-ссылки", "Обновить")) {
    $checkResult = CheckWikipages-Router -checkPages $vietPagesContent -checkType TemplateRegexp `
            -returnEmpty $printEmptySections -bypassArgument $badSlowTemplate
    $fullAnnounce += $checkResult.wikitext
    $problemStats += $checkResult.problemstat
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
}

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

### UNDER CONSTRUCTION ###

## [http://en.wikipedia.org/wiki/Dror_Feiler]
# e. g. Чанфу

## Примечания без секции

# Ш: Грубый перевод, плохой перевод, недоперевод, Закончить перевод, rq|translate, rq|checktranslate

# 1.564.400

# {{l6e|en}}

# это отдельно
## --вьет-стабы-- и вьет-гео-стабы не в проекте. Статьи в категории, но не в проекте.

# too much '{{lang' - write PoC

# cite news

### Нет карточки
$templCards = Get-PagesByCategory -Category "Шаблоны-карточки по алфавиту"
$hasCard = $false
foreach ($page in $vietPagesContent){
    foreach ($templ in $topLevelTemplates[0..3]) {
        if ($templ -in $templCards){
            $hasCard = $true
        }
    }
}


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



