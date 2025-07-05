function Load-DotEnv {
    param (
        [string]$Path = ".env"
    )

    if (-not (Test-Path $Path)) {
        Write-Warning "'.env' file not found at '$Path'."
        return
    }

    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if ($line -notmatch '^\s*#' -and $line -match '^([^=]+?)\s*=\s*(.*)$') {
            $key = $Matches[1].Trim()
            $value = $Matches[2].Trim()

            # Remove quotes if present
            if ($value.StartsWith('"') -and $value.EndsWith('"')) {
                $value = $value.Substring(1, $value.Length - 2)
            } elseif ($value.StartsWith("'") -and $value.EndsWith("'")) {
                $value = $value.Substring(1, $value.Length - 2)
            }

            Set-Item -Path Env:$key -Value $value
            Write-Host "Loaded environment variable: $key"
        }
    }
}