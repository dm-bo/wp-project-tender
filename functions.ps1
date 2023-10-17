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
            $format1 = @{ ForegroundColor = "Red" }
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
