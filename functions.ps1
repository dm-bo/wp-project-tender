# This goes first
function Assert-IsNonInteractiveShell {
    $NonInteractive = [Environment]::GetCommandLineArgs() | Where-Object{ $_ -like '-NonI*' }

    if ([Environment]::UserInteractive -and -not $NonInteractive) {
        # We are in an interactive shell.
        return $false
    }

    return $true
}

# This goes ASAP (depends on Assert-IsNonInteractiveShell)
function Append-Log {
    param (
        [Parameter(ValueFromPipeline,Mandatory=$true)]
        $InputString,
        # Also log last entry from $Error
        # Useful when called from "catch" section
        [switch]$AppendError = $false
    )
    process
    {
        # Decorating depends on Error Level (guessing)
        if ($InputString -like "WARNING*") {
            # $prefix = "WARNING"
            # https://stackoverflow.com/questions/67236548/variables-that-contains-the-color-of-a-text-in-powershell
            $format1 = @{ ForegroundColor = "Yellow" }
        } elseif ($InputString -like "ERROR*") {
            # $prefix = "ERROR"
            $format1 = @{ ForegroundColor = "White" }
        } elseif (($InputString -like "CRITICAL*") -or ($InputString -like "FATAL*")) {
            # $prefix = "CRITICAL"
            $format1 = @{ BackgroundColor = "DarkRed" }
        } elseif ($InputString -like "INFO*") {
            # $prefix = "CRITICAL"
            $format1 = @{ ForegroundColor = "Cyan" }
        } else {
            # $prefix = "INFO"
            $format1 = @{ ForegroundColor = "White" }
        }
        
        if ($InputString -is [string]) {
            #$logentry = "$(Get-Date -UFormat "%Y-%m-%d %T") $prefix`: $InputString"
            $logentry = "$(Get-Date -UFormat "%Y-%m-%d %T")  $InputString"
            if (Assert-IsNonInteractiveShell) {
                $logentry | Out-File -FilePath $log -Append
            } else {
                $logentry | Write-Host @format1
            }
            if ($AppendError){
                "`$Error is the following: $($Error[0].ToString())" | Append-Log
            }
        } else {
            #throw "Input object is not a string."
            "$(Get-Date -UFormat "%Y-%m-%d %T") WARNING: Cannot create log entry - not a string" | Append-Log
        }
    }
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
        @{n='percent';e={"<!-- statPercent:$name -->$($([Math]::Round(100*$counter/$total,2))) %`n"}}
    return $newProblemStat
}
