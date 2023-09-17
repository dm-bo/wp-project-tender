
# returns wikicode for a problem list
function CheckWikipages-Empty {
    param (
        $pages = @()
    )
    $wikiText = "=== ����� �������� ������ ===`n"
    $emptyPagesCounter = 0
    foreach ($page in $pages){
        if ($page.content -match "{{rq\|[^\}]{0,30}empty[\|}]")
        {
            $wikiText += "* [[$($page.title)]]`n"
            $emptyPagesCounter++
        }
    }
    "$emptyPagesCounter pages are too short" | Append-Log
    $problemStat = New-ProblemStat -name "Empty" -text '����� �������' `
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
    $wikiText = "=== �������� � �������� ���������� ===`n"
    $pagesCounter = 0
    foreach ($page in $pages){
        if ((($page.content -match "{{rq\|[^\}]{0,20}sources[\|}]") -or
             ($page.content -match "{{��� ����������\|") -or
             ($page.content -match "{{��� ������\|")) -and
            ($page.Title -notin $pagesNoSourcesAtAll))
        {
            $wikiText += "* [[$($page.title)]]`n"
            $pagesCounter++
        }
    }
    "$pagesCounter pages have source request" | Append-Log
    $problemStat = New-ProblemStat -name "SourceRequest" -text '������ ���������' `
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
    $fullAnnounce += "=== ����������� ������ ===`n"
    $fullAnnounce += "����� �������� ������, ����� �������� � [http://web.archive.org/ ������] ��� ��������� ������ ��������.`n"
    $linksUnanvailableCounter = 0

    foreach ($page in $pages){
        $mc = [regex]::matches($page.content, "http[s]*://[^:]*{{����������� ������\|[^\}]{0,200}}}|{{����������� ������}}")
        if ($mc.groups.count -gt 0){
            $fullAnnounce += "* [[$($page.title)]] ($($mc.groups.count))`n"
            #""
            #"== [[$($page.title)]] == "
            foreach ($m in $mc.Value) {
                if ($m -match "^[^ \n\|\]{]*"){
                    #$Matches.Values
                    if (($Matches.Values -like "{{�����������") -or ($Matches.Values -like "")){
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
    $problemStat = New-ProblemStat -name "LinksUnanvailable" -text '����������� ������' `
         -counter $linksUnanvailableCounter -total $pages.Count
    $result = "" | select `
        @{n='wikitext';e={$wikiText}},
        @{n='problemstat';e={$problemStat}}
    return $result
}


