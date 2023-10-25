# returns boolean; true if user id is not 0
function Get-WPSessionStatus {
    param (
        $session = $session
    )
    $URL = "https://ru.wikipedia.org/w/api.php"
    $PARAMS_3 = @{
        "action"= "query";
        "meta"= "userinfo";
        "format"= "json"
    }
    $rq3 = Invoke-WebRequest -Uri $URL -Method POST -Body  $PARAMS_3 -WebSession $session
    $JSONCont3 = $rq3.Content | ConvertFrom-Json
    if ($JSONCont3.query.userinfo.id -ne 0){
        return $true
    }
    return $false
}

# returns authorized session
function Get-WPAuthorizedSession {
    param (
        $login = "",
        $pass  = ""
    )

    # First, get token

    $URL = "https://ru.wikipedia.org/w/api.php"
    $PARAMS_1 = @{
        'action' = "query";
        'meta'   = "tokens";
        'type'   = "login";
        'format' = "json"
    }
    $rq1 = Invoke-WebRequest -Uri $URL -Method GET -Body $PARAMS_1 -SessionVariable session
    $JSONCont1 = $rq1.Content | ConvertFrom-Json
    $logintoken = $JSONCont1.query.tokens.logintoken
    #"login token is $logintoken"
    #$session

    # Second, return authorized session

    $PARAMS_2 = @{
        'action'= "login";
        'lgname'= $login;
        'lgpassword'= $pass;
        'lgtoken'= $logintoken;
        'format'= "json"
    }

    $rq2 = Invoke-WebRequest -Uri $URL -Method POST -Body  $PARAMS_2 -WebSession $session
    $JSONCont2 = $rq2.Content | ConvertFrom-Json
    #$JSONCont2
    if (Get-WPSessionStatus -session $session) {
        return $session
    }
    return ""
}

# needs authenticated session
function Set-WPPageText {
    param (
        $session = "",
        $title = "",
        $newtext = "",
        $summary = "change made via API"
    )

    if ( -not (Get-WPSessionStatus -session $session )){
        return $false
    }

    # GET request to fetch CSRF token
    $PARAMS_4 = @{
        "action" = "query";
        "meta"   = "tokens";
        "format" = "json"
    }
    $rq4 = Invoke-WebRequest -Uri $URL -Method GET -Body  $PARAMS_4 -WebSession $session
    $JSONCont4 = $rq4.Content | ConvertFrom-Json
    $csrftoken = $JSONCont4.query.tokens.csrftoken

    # POST request to edit a page
    $PARAMS_5 = @{
        "action"   = "edit";
        "title"    = $title;
        "token"    = $csrftoken;
        "text"     = $newtext;
        "summary"  = $summary;
        "nocreate" = 1;
        "format"   = "json"
    }

    $rq5 = Invoke-WebRequest -Uri $URL -Method POST -Body  $PARAMS_5 -WebSession $session
    $JSONCont5 = $rq5.Content | ConvertFrom-Json
    if ($JSONCont5.edit.result -like "Success"){ 
        return $true
    }
    return $false
}

# gets template name
# returns array of page names
function Get-PagesByTemplate {
    param (
        $Template = "xxx",
        $namespace = "1"
    )
    $URL = "http://ru.wikipedia.org/w/api.php?action=query&titles=$Template&prop=transcludedin&tilimit=500&tinamespace=$namespace&format=json"
    $nextURL = $URL
    $result = @()
    while ($nextURL){
        $rq = Invoke-WebRequest -Uri $nextURL -Method GET
        $JSONCont = $rq.Content | ConvertFrom-Json
        #$JSONCont.query.pages.3975406
        $pageID = @($JSONCont.query.pages.PSObject.Properties)[0].Name
        $pageInfo = $JSONCont.query.pages.$pageID
        #$pageInfo.transcludedin | select -First 5
        #$JSONCont.continue
        $nextSuffix = $JSONCont.continue.ticontinue
        foreach ($title in $pageInfo.transcludedin.title) {
            if ($namespace -eq 1) {
                $result += $title -replace "Обсуждение:",""
            } else {
                $result += $title
            }
        }
        # Write-Host "$Template`: $($pageInfo.transcludedin.Count) pages retrieved, $($result.Count) in total."
        if ($JSONCont.continue){
            $nextURL = "$URL&ticontinue=$nextSuffix"
        } else {
            $nextURL = $null
            #"No continue, breaking the loop"
        }
    }
    return $result
}

# gets short name
function Get-PagesByCategory {
    param (
        $Category = "xxx"
    )
    $result = @()
    $URL = "https://ru.wikipedia.org/w/api.php?action=query&cmlimit=500&list=categorymembers&cmtitle=Категория%3A$Category&format=json"
    $nextURL = $URL
    while ($nextURL){
        $i++
        $rq = Invoke-WebRequest -Uri $nextURL -Method GET
        $JSONCont = $rq.Content | ConvertFrom-Json
        $result += $JSONCont.query.categorymembers.title
        if ($JSONCont.continue){
            $nextSuffix = $JSONCont.continue.cmcontinue
            $nextURL = "$URL&cmcontinue=$nextSuffix"
            #$nextURL
        } else {
            $nextURL = $null
            #"No continue, breaking the loop"
        }
        #"$i - $($result.Count), $($JSONCont.query.categorymembers[0])"
    }
    return $result
}

# Returns an object for $problemStats array
function New-ProblemStat {
    param (
        $name = "(not set)",
        $counter = "0",
        $text = "(not set)",
        $total = 1
    )
    $newProblemStat = "" | select `
        @{n='name';e={$name}},
        @{n='text';e={$text}},
        @{n='counter';e={"<!-- statValue:$name -->$counter"}},
        @{n='percent';e={"<!-- statPercent:$name -->$($([Math]::Round(100*$counter/$total,2))) %"}},
        @{n='timestamp';e={Get-Date}}
    return $newProblemStat
}

# gets only content as string
# returns array of objects name,level,content 
function Get-WPPageSections {
    param (
        $content = ""
    )
    # $content= $page.content
    $pageSections = @()
    $sectionContents = $content -split "=[=]+[ ]*[^=]*[ ]*=[=]+"
    $sectionNames = [regex]::matches($content, "=[=]+[ ]*[^=]*[ ]*=[=]+")
    if ($sectionNames.groups.count -gt 0){
        $pageSections += "" | select @{n='name';e={"(head)"}},
            @{n='level';e={"1"}},
            @{n='content';e={$sectionContents[0]}}
        $i=1
        foreach ($sectionName in $sectionNames){
            if ($sectionName.Value -match "^[=]*") {
                $pageSections += "" | select @{n='name';e={$sectionName.Value -replace "^[ =]*" -replace "[ =]*$"}},
                    @{n='level';e={$Matches.Values.Length}},
                    @{n='content';e={$sectionContents[$i]}}
            } else {
                "ERROR: bad title selected ()" | Append-Log
            }
            $i++
        }
    }
    return $pageSections

}

# gets only content as string
# returns hashtable or list of names
function Get-WPPageTemplates {
    param (
        $pageContent = "",
        $returnWhat = "names"
    )
    $pageContent = $pageContent -replace "{{{!}}" -replace "{{!}}}"
    $pageContent = $pageContent -replace "{{{[^}]*}}}"
    #$pageContent | Append-Log
    $depth_limit = 10
    $templates = @{}
    $templateNames = @()
    $i = 0
    $searchMore = $true
    while ($searchMore){
        $i++
        #""
        #"=== ITERATION $i ===" | Append-Log
        #""
        $mc = [regex]::matches($pageContent, "{{[^\{}]*}}")
        #$content | Append-Log
        #"$($mc.groups.count) lowest-level templates" | Append-Log 
        if ($mc.groups.count -gt 0){
            #"$($mc.groups.count) lowest-level templates" | Append-Log
            foreach ($m in $mc){
                #"Next value is $($m) ($($m.Value.Length))"
                $templ_guid = New-Guid 
                $templateName = (($m -split '\|' )[0] -replace "{{" -replace "}}" -replace "\n").Trim()
                #"Next template is $templ_name ($($m.Value.Length))"
                #$m | fl *
                #$pageContent = $pageContent -replace $m.Value
                $pageContent = $pageContent -replace "$([regex]::Escape($m.Value))","__TWH=$templ_guid`_"
                $templates["$templ_guid"] = "" | select `
                    @{n="title";e={($m -split '\|' )[0] -replace "{{" -replace "}}" -replace "\n"}},
                    @{n="content";e={[regex]::Escape($m.Value)}}
                $templateNames += $templateName
                #$content.Length
                if ($pageContent -match [regex]::Escape("<ref>|url=")){
                    throw "bad replace"
                }
            }
        } else {
            #"Break when completed." | Append-Log
            $searchMore = $false
        }
        if ($i -ge $depth_limit){
            #"Break by limit." | Append-Log
            $searchMore = $false
        }
        #$pageContent | Append-Log
    }
    #"Returning $($templates.Count) templates, $($templateNames.Count) template names" | Append-Log
    #return $templates,$templateNames
    if ($returnWhat -like "names") {
        return $templateNames
    } elseif ($returnWhat -like "hash") {
        return $templates
    } else {
        throw "unknown returnWhat value: $returnWhat"
    }
}

# gets date as a string
# returns bool 
function Get-WPDateFormat {
    param (
        $date = "xxx"
    )
    $date = $date -replace " "
    return (($date -match "^[0-9]{4}-[0-9]{2}-[0-9]{2}$") -or 
                ($date -match "^[0-9]{4}-[0-9]{2}$") -or ($date -match "^[0-9]{4}$") -or
                ($date -match "^[ ]*$") -or ($date -match "^$"))
}


# under construction
function Get-WPMultipages {
    param (
        $options = @{}
    )

    $URL = "http://ru.wikipedia.org/w/api.php"
    $continue = $true
    $result = @()
    
    #action=query&format=json&prop=linkshere&lhlimit=500&formatversion=2&lhnamespace=0&lhshow=!redirect&titles=$vietPageBatch"
    $options = @{
        'action' = "query";
        'format' = "json";
        'formatversion'   = "2";
        'prop'   = "linkshere";
        'lhlimit'   = "500";
        'lhnamespace'   = "0";
        'lhshow'   = "!redirect";
        'titles'   = "Каасъягер, Сандер|Кан Мин|Киберспорт|Киберспорт в Казахстане|Киберспорт в России"
    }
    
    $nextOptions = $options
    while ($continue){
        $rq = Invoke-WebRequest -Uri $URL -Method GET -Body $nextOptions
        $JSONCont = $rq.Content | ConvertFrom-Json
        
        if ($JSONCont.continue) {
            $continue = $true
            $JSONCont.continue
            $nextOptions = $options
            $continueOption = $JSONCont.continue.PSObject.Members | ? {$_.MemberType -eq "NoteProperty"} | % { $nextOptions += @{$_.Name = $_.Value} }
        } else {
            $continue = $false
        }

        "Hi"
        $JSONCont.query.pages | select pageid,ns,title,@{n='cou';e={$_.linkshere.Count}}

    }
    return $result
}