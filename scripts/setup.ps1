<#
.SYNOPSIS
  생활법률(AMP) 개발 환경 준비 스크립트 (Windows PowerShell 5.1 이상).

.DESCRIPTION
  저장소 루트를 기준으로 동작하므로 어느 폴더에서 실행해도 됩니다.
    1) server/.env, app/.env 가 없을 때만 각 .env.example 에서 복사 (이미 있으면 절대 덮어쓰지 않음)
    2) app/.env 의 EXPO_PUBLIC_API_URL 한 줄만 http://<PC IPv4>:8000 (또는 -ApiUrl 값)으로 변경
    3) server/.venv 생성 + pip install -r requirements.txt   (-SkipServer 로 건너뜀)
    4) app 폴더에서 npm ci                                    (-SkipApp 으로 건너뜀)
    5) scripts/check_env.py 로 환경 점검                       (-SkipCheck 로 건너뜀)
  비밀 값(server/.env 의 키)과 판례 DB는 만들지 않습니다. 팀 비공개 Drive에서 받아 넣으세요(docs/SETUP.md).

.PARAMETER ApiUrl
  자동 탐지 대신 app/.env 에 넣을 API 주소. 예) https://xxxx.trycloudflare.com, http://192.168.0.31:8000
.PARAMETER KeepApiUrl
  app/.env 의 EXPO_PUBLIC_API_URL 을 바꾸지 않습니다(다른 팀원 서버 주소를 유지할 때).
.PARAMETER Port
  자동 탐지 주소에 붙일 서버 포트. 기본 8000.
.PARAMETER Python
  server/.venv 를 만들 Python 3.11 이상. 경로 또는 명령. 예) C:\Python312\python.exe, "py -3.12"
.PARAMETER SkipServer
  server venv 생성과 pip install 을 건너뜁니다.
.PARAMETER SkipApp
  app 의 npm ci 를 건너뜁니다.
.PARAMETER SkipCheck
  마지막 환경 점검을 건너뜁니다.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -SkipServer -SkipApp -ApiUrl https://xxxx.trycloudflare.com
#>
[CmdletBinding()]
param(
    [string]$ApiUrl,
    [switch]$KeepApiUrl,
    [ValidateRange(1, 65535)][int]$Port = 8000,
    [string]$Python,
    [switch]$SkipServer,
    [switch]$SkipApp,
    [switch]$SkipCheck
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$MinServerPython = [version]'3.11'
$MinNode = [version]'22.13'

# ------------------------------------------------------------------ 출력

function Write-Step([string]$Message) {
    Write-Host ''
    Write-Host "==> $Message" -ForegroundColor Cyan
}
function Write-Ok([string]$Message) { Write-Host "  [OK]   $Message" -ForegroundColor Green }
function Write-Info([string]$Message) { Write-Host "  [INFO] $Message" }
function Write-SetupWarn([string]$Message) { Write-Host "  [WARN] $Message" -ForegroundColor Yellow }

# ------------------------------------------------------------------ 외부 명령

# 외부 명령을 실행하고 종료 코드가 0이 아니면 멈춘다.
# PowerShell 5.1 은 Stop 모드에서 외부 명령의 stderr(npm/pip 경고)를 오류로 바꾸므로 잠시 Continue 로 둔다.
function Invoke-Native {
    param([string]$Exe, [string[]]$Arguments, [string]$What)
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $Exe @Arguments | Out-Host
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previous
    }
    if ($code -ne 0) { throw "$What 실패 (종료 코드 $code)" }
}

# Python 명령을 실행해 버전을 돌려준다. 실행되지 않으면 $null.
# 인자에 큰따옴표와 % 를 쓰지 않는다(PowerShell 5.1 인자 전달, .bat 래퍼 대비).
function Get-PythonVersion([string[]]$Command) {
    $exe = $Command[0]
    $rest = @()
    if ($Command.Count -gt 1) { $rest = @($Command[1..($Command.Count - 1)]) }
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    try {
        $output = & $exe @rest -c 'import sys; print(*sys.version_info[:3])' 2>$null
        if ($LASTEXITCODE -ne 0) { return $null }
    } catch {
        return $null
    } finally {
        $ErrorActionPreference = $previous
    }
    foreach ($line in @($output)) {
        if ("$line" -match '^(\d+) (\d+) (\d+)$') {
            return [version]("{0}.{1}.{2}" -f $Matches[1], $Matches[2], $Matches[3])
        }
    }
    return $null
}

function New-PythonChoice([string[]]$Command, [version]$Version) {
    return [pscustomobject]@{ Command = $Command; Version = $Version; Label = ($Command -join ' ') }
}

# server/.venv 를 만들 Python 3.11 이상을 찾는다. 3.12 를 먼저 찾는다(권장 버전).
function Find-ServerPython([string]$Requested) {
    if ($Requested) {
        if (Test-Path -LiteralPath $Requested -PathType Leaf) {
            $command = @((Resolve-Path -LiteralPath $Requested).Path)
        } else {
            $command = @($Requested -split '\s+' | Where-Object { $_ })
        }
        $version = Get-PythonVersion $command
        if (-not $version) { throw "-Python '$Requested' 을(를) 실행하지 못했습니다." }
        if ($version -lt $MinServerPython) { throw "-Python '$Requested' 은(는) Python $version 입니다. 3.11 이상(3.12 권장)이 필요합니다." }
        return New-PythonChoice $command $version
    }

    $candidates = New-Object System.Collections.ArrayList
    foreach ($minor in @('3.12', '3.13', '3.11')) { [void]$candidates.Add(@('py', "-$minor")) }
    [void]$candidates.Add(@('python'))
    [void]$candidates.Add(@('python3'))
    foreach ($candidate in $candidates) {
        $version = Get-PythonVersion $candidate
        if ($version -and $version -ge $MinServerPython) { return New-PythonChoice $candidate $version }
    }

    # uv 로 설치한 Python
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        $previous = $ErrorActionPreference
        $ErrorActionPreference = 'SilentlyContinue'
        try { $found = @(& uv python find '>=3.11' 2>$null) } catch { $found = @() } finally { $ErrorActionPreference = $previous }
        if ($found.Count -gt 0 -and "$($found[0])".Trim()) {
            $command = @("$($found[0])".Trim())
            $version = Get-PythonVersion $command
            if ($version -and $version -ge $MinServerPython) { return New-PythonChoice $command $version }
        }
    }

    # 기본 설치 위치 (py 런처 없이 설치한 경우): python.org 사용자/전체 설치, uv 관리 폴더
    $roots = @()
    if ($env:LOCALAPPDATA) { $roots += (Join-Path $env:LOCALAPPDATA 'Programs\Python') }
    if ($env:ProgramFiles) { $roots += $env:ProgramFiles }
    if ($env:APPDATA) { $roots += (Join-Path $env:APPDATA 'uv\python') }
    $found = @()
    foreach ($root in $roots) {
        foreach ($dir in @(Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue)) {
            if ($dir.Name -match '^Python3(\d{2})$' -or $dir.Name -match '^cpython-3\.(\d{2})[.-]') {
                $exe = Join-Path $dir.FullName 'python.exe'
                if (Test-Path -LiteralPath $exe) {
                    $minor = [int]$Matches[1]
                    $rank = switch ($minor) { 12 { 0 } 13 { 1 } 11 { 2 } default { 3 } }
                    $found += [pscustomobject]@{ Exe = $exe; Rank = $rank; Minor = $minor }
                }
            }
        }
    }
    foreach ($item in @($found | Sort-Object Rank, Minor)) {
        $version = Get-PythonVersion @($item.Exe)
        if ($version -and $version -ge $MinServerPython) { return New-PythonChoice @($item.Exe) $version }
    }
    throw ('Python 3.11 이상(3.12 권장)을 찾지 못했습니다. https://www.python.org/downloads/ 에서 3.12 를 설치한 뒤 다시 실행하거나, ' +
           '-Python 으로 경로를 지정하세요. 예) -Python "C:\Python312\python.exe"')
}

# 점검 스크립트용: 표준 라이브러리만 쓰므로 Python 3.8 이상이면 된다.
function Find-AnyPython([string]$VenvPython) {
    $candidates = @()
    if (Test-Path -LiteralPath $VenvPython) { $candidates += , @($VenvPython) }
    $candidates += , @('py', '-3')
    $candidates += , @('python')
    $candidates += , @('python3')
    foreach ($candidate in $candidates) {
        $version = Get-PythonVersion $candidate
        if ($version -and $version -ge [version]'3.8') { return New-PythonChoice $candidate $version }
    }
    return $null
}

# ------------------------------------------------------------------ IPv4 탐지

# 켜져 있는 Wi-Fi/이더넷 어댑터의 IPv4 후보. 가상 어댑터(Hyper-V, WSL, VirtualBox, VMware, VPN 등)와
# 169.254.x.x(APIPA), 127.x 는 뺀다. 기본 게이트웨이가 있는 어댑터, 그중 Wi-Fi 를 앞에 둔다.
function Get-LanIPv4Candidates {
    $virtualPattern = 'Virtual|Hyper-V|vEthernet|VMware|VirtualBox|VBox|WSL|Docker|Loopback|Bluetooth|TAP-|Tunnel|VPN|WireGuard|Tailscale|ZeroTier|Npcap|Teredo|isatap|Pseudo'
    $ethernetTypes = @('Ethernet', 'GigabitEthernet', 'FastEthernetT', 'FastEthernetFx', 'Ethernet3Megabit')
    $result = @()
    foreach ($nic in [System.Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces()) {
        if ($nic.OperationalStatus -ne [System.Net.NetworkInformation.OperationalStatus]::Up) { continue }
        $typeName = $nic.NetworkInterfaceType.ToString()
        $isWifi = $typeName -eq 'Wireless80211'
        if (-not $isWifi -and ($ethernetTypes -notcontains $typeName)) { continue }
        if (("{0} {1}" -f $nic.Name, $nic.Description) -match $virtualPattern) { continue }
        $properties = $nic.GetIPProperties()
        $hasGateway = $false
        foreach ($gateway in $properties.GatewayAddresses) {
            $address = $gateway.Address
            if ($address.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork -and $address.ToString() -ne '0.0.0.0') {
                $hasGateway = $true
            }
        }
        foreach ($unicast in $properties.UnicastAddresses) {
            if ($unicast.Address.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) { continue }
            $ip = $unicast.Address.ToString()
            if ($ip.StartsWith('169.254.') -or $ip.StartsWith('127.')) { continue }
            $kind = 'Ethernet'
            if ($isWifi) { $kind = 'Wi-Fi' }
            $result += [pscustomobject]@{
                Address = $ip; Name = $nic.Name; Description = $nic.Description; Kind = $kind; HasGateway = $hasGateway
            }
        }
    }
    return @($result | Sort-Object @{ Expression = { -not $_.HasGateway } }, @{ Expression = { $_.Kind -ne 'Wi-Fi' } })
}

# ------------------------------------------------------------------ .env 한 줄 바꾸기

# KEY=... 줄만 바꾸고 나머지 줄, 줄바꿈(CRLF/LF), BOM 유무는 그대로 둔다. 키가 없으면 끝에 한 줄 추가한다.
function Set-EnvValue([string]$Path, [string]$Key, [string]$Value) {
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
    $offset = 0
    if ($hasBom) { $offset = 3 }
    $strict = New-Object System.Text.UTF8Encoding($false, $true)
    try {
        $text = $strict.GetString($bytes, $offset, $bytes.Length - $offset)
    } catch {
        throw "$Path 이(가) UTF-8 이 아니어서 수정하지 않았습니다. UTF-8 로 다시 저장한 뒤 실행하세요."
    }
    $newLine = "`n"
    if ($text.Contains("`r`n")) { $newLine = "`r`n" }
    $pattern = '^[ \t]*(?:export[ \t]+)?' + [regex]::Escape($Key) + '[ \t]*='
    $wanted = "$Key=$Value"
    $lines = [regex]::Split($text, '(?<=\n)')
    $found = $false
    $old = $null
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $body = $lines[$i].TrimEnd([char[]]@([char]13, [char]10))
        if ($body -cmatch $pattern) {
            $found = $true
            $old = $body
            if ($body -ne $wanted) { $lines[$i] = $wanted + $lines[$i].Substring($body.Length) }
        }
    }
    if ($found) {
        $newText = -join $lines
    } else {
        $separator = ''
        if ($text.Length -gt 0 -and -not $text.EndsWith("`n")) { $separator = $newLine }
        $newText = $text + $separator + $wanted + $newLine
    }
    $changed = ($newText -cne $text)
    if ($changed) {
        $encoded = (New-Object System.Text.UTF8Encoding($false)).GetBytes($newText)
        if ($hasBom) { $encoded = [byte[]](@(0xEF, 0xBB, 0xBF) + $encoded) }
        [System.IO.File]::WriteAllBytes($Path, $encoded)
    }
    return [pscustomobject]@{ Changed = $changed; Found = $found; Old = $old; New = $wanted }
}

# ------------------------------------------------------------------ 단계

function Copy-EnvFromExample([string]$Target, [string]$Example, [string]$Label) {
    if (Test-Path -LiteralPath $Target) {
        Write-Info "$Label 이미 있음 -> 그대로 둡니다(덮어쓰지 않음)"
        return
    }
    if (-not (Test-Path -LiteralPath $Example -PathType Leaf)) {
        Write-SetupWarn "$Label.example 이 없어 $Label 을 만들지 못했습니다. git checkout -- $Label.example 로 되살린 뒤 다시 실행하세요."
        return
    }
    [System.IO.File]::Copy($Example, $Target, $false)  # 세 번째 인자 false: 이미 있으면 덮어쓰지 않고 오류
    Write-Ok "$Label 생성 ($Label.example 복사)"
}

function Update-ApiUrl([string]$AppEnv) {
    if ($KeepApiUrl) {
        Write-Info 'EXPO_PUBLIC_API_URL 유지 (-KeepApiUrl)'
        return
    }
    if (-not (Test-Path -LiteralPath $AppEnv -PathType Leaf)) {
        Write-SetupWarn 'app/.env 가 없어 API 주소를 설정하지 못했습니다.'
        return
    }
    if ($ApiUrl) {
        $trimmed = $ApiUrl.Trim().TrimEnd('/')
        $uri = $null
        $valid = [System.Uri]::TryCreate($trimmed, [System.UriKind]::Absolute, [ref]$uri)
        if (-not $valid -or ($uri.Scheme -ne 'http' -and $uri.Scheme -ne 'https') -or -not $uri.Host -or $trimmed -match '\s' -or $trimmed -cnotmatch '^https?://') {
            throw "-ApiUrl '$ApiUrl' 형식이 틀렸습니다. 예) http://192.168.0.31:8000, https://xxxx.trycloudflare.com"
        }
        $target = $trimmed
        Write-Info "-ApiUrl 지정: $target"
    } else {
        $candidates = @(Get-LanIPv4Candidates)
        if ($candidates.Count -eq 0) {
            Write-SetupWarn 'Wi-Fi/이더넷 IPv4 를 찾지 못해 EXPO_PUBLIC_API_URL 을 그대로 둡니다. -ApiUrl 로 직접 지정하세요.'
            return
        }
        $chosen = $candidates[0]
        $target = "http://$($chosen.Address):$Port"
        $gatewayNote = ''
        if (-not $chosen.HasGateway) { $gatewayNote = ', 기본 게이트웨이 없음' }
        Write-Info "탐지한 IPv4: $($chosen.Address) ($($chosen.Kind) '$($chosen.Name)'$gatewayNote)"
        if ($candidates.Count -gt 1) {
            $others = ($candidates | Select-Object -Skip 1 | ForEach-Object { "$($_.Address)($($_.Kind) '$($_.Name)')" }) -join ', '
            Write-Info "다른 후보: $others  -> 휴대폰과 같은 네트워크가 아니면 -ApiUrl 로 지정하세요."
        }
    }
    $result = Set-EnvValue -Path $AppEnv -Key 'EXPO_PUBLIC_API_URL' -Value $target
    if (-not $result.Changed) {
        Write-Ok "app/.env EXPO_PUBLIC_API_URL 이미 $target (변경 없음)"
    } elseif ($result.Found) {
        # 주소 칸에 키를 잘못 넣었을 수 있으므로 주소 형태가 아니면 이전 값을 보이지 않는다.
        $oldValue = $result.Old -replace '^[ \t]*(?:export[ \t]+)?EXPO_PUBLIC_API_URL[ \t]*=[ \t]*', ''
        if ($oldValue -cnotmatch '^https?://[^\s@?#]+$') { $oldValue = '(이전 값은 표시하지 않음)' }
        Write-Ok "app/.env EXPO_PUBLIC_API_URL 변경: $oldValue -> $target (다른 줄은 그대로)"
    } else {
        Write-Ok "app/.env 에 EXPO_PUBLIC_API_URL=$target 줄을 추가했습니다."
    }
}

function Install-Server([string]$ServerDir, [string]$VenvPython) {
    $venvDir = Join-Path $ServerDir '.venv'
    if (Test-Path -LiteralPath $VenvPython) {
        $version = Get-PythonVersion @($VenvPython)
        if (-not $version) { throw "server\.venv 가 손상되어 실행되지 않습니다. server\.venv 폴더를 지운 뒤 다시 실행하세요." }
        if ($version -lt $MinServerPython) {
            throw "server\.venv 가 Python $version 으로 만들어져 있습니다. 3.11 이상이 필요하니 server\.venv 폴더를 지운 뒤 다시 실행하세요."
        }
        Write-Info "기존 server\.venv 사용 (Python $version)"
    } else {
        $choice = Find-ServerPython $Python
        Write-Info "Python $($choice.Version) 로 server\.venv 생성: $($choice.Label)"
        $command = @($choice.Command)
        $rest = @()
        if ($command.Count -gt 1) { $rest = @($command[1..($command.Count - 1)]) }
        Invoke-Native $command[0] ($rest + @('-m', 'venv', $venvDir)) 'venv 생성'
        if (-not (Test-Path -LiteralPath $VenvPython)) { throw "venv 를 만들었지만 $VenvPython 이 없습니다." }
    }

    # uv 등으로 만든 venv 에는 pip 이 없을 수 있다.
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & $VenvPython -m pip --version 2>$null | Out-Null; $hasPip = ($LASTEXITCODE -eq 0) } finally { $ErrorActionPreference = $previous }
    if (-not $hasPip) {
        Write-Info 'venv 에 pip 이 없어 ensurepip 으로 설치합니다.'
        Invoke-Native $VenvPython @('-m', 'ensurepip', '--upgrade') 'ensurepip'
    }
    $requirements = Join-Path $ServerDir 'requirements.txt'
    $previousUnbuffered = $env:PYTHONUNBUFFERED
    $env:PYTHONUNBUFFERED = '1'
    try {
        Invoke-Native $VenvPython @('-m', 'pip', 'install', '--disable-pip-version-check', '-r', $requirements) 'pip install'
    } finally {
        $env:PYTHONUNBUFFERED = $previousUnbuffered
    }
    Write-Ok 'server 의존성 설치 완료'
}

function Install-App([string]$AppDir) {
    if (-not (Get-Command node.exe -ErrorAction SilentlyContinue)) {
        throw 'Node.js 를 찾지 못했습니다. Node.js 22.13 이상(LTS)을 설치한 뒤 새 터미널에서 다시 실행하세요.'
    }
    $nodeText = "$(& node.exe --version)".Trim()
    $nodeVersion = $null
    if ($nodeText -match '^v?(\d+\.\d+\.\d+)') { $nodeVersion = [version]$Matches[1] }
    if ($nodeVersion -and $nodeVersion -lt $MinNode) {
        Write-SetupWarn "Node.js $nodeText 입니다. 22.13 이상을 권장합니다."
    } else {
        Write-Info "Node.js $nodeText"
    }
    if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw 'npm 을 찾지 못했습니다. Node.js 를 다시 설치하세요.' }
    Push-Location -LiteralPath $AppDir
    try {
        # npm.ps1 대신 npm.cmd 를 불러 실행 정책 영향을 받지 않게 한다.
        Invoke-Native 'npm.cmd' @('ci', '--no-audit', '--no-fund') 'npm ci'
    } finally {
        Pop-Location
    }
    Write-Ok 'app 의존성 설치 완료 (npm ci)'
}

function Invoke-EnvCheck([string]$CheckScript, [string]$VenvPython) {
    $choice = Find-AnyPython $VenvPython
    if (-not $choice) {
        Write-SetupWarn 'Python 을 찾지 못해 점검을 건너뜁니다.'
        return 0
    }
    $command = @($choice.Command)
    $rest = @()
    if ($command.Count -gt 1) { $rest = @($command[1..($command.Count - 1)]) }
    # 점검 결과(한글)를 PowerShell 이 읽는 콘솔 인코딩에 맞춰 출력하게 한다.
    $codePage = 65001
    try { $codePage = [Console]::OutputEncoding.CodePage } catch { }
    $previousEncoding = $env:PYTHONIOENCODING
    $env:PYTHONIOENCODING = "cp$($codePage):replace"
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $command[0] @rest $CheckScript | Out-Host
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previous
        $env:PYTHONIOENCODING = $previousEncoding
    }
    return $code
}

# ------------------------------------------------------------------ 실행

try {
    $scriptDir = $PSScriptRoot
    if (-not $scriptDir) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
    $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $scriptDir '..')).Path
    $ServerDir = Join-Path $RepoRoot 'server'
    $AppDir = Join-Path $RepoRoot 'app'
    $VenvPython = Join-Path $ServerDir '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath (Join-Path $ServerDir 'requirements.txt')) -or -not (Test-Path -LiteralPath (Join-Path $AppDir 'package.json'))) {
        throw "저장소 루트를 찾지 못했습니다: $RepoRoot (scripts 폴더를 옮기지 마세요)"
    }
    if ($KeepApiUrl -and $ApiUrl) { throw '-ApiUrl 과 -KeepApiUrl 은 함께 쓸 수 없습니다.' }

    Write-Host "생활법률 개발 환경 준비 (저장소: $RepoRoot)"

    Write-Step '1/5 환경 파일 (.env)'
    Copy-EnvFromExample (Join-Path $ServerDir '.env') (Join-Path $ServerDir '.env.example') 'server/.env'
    Copy-EnvFromExample (Join-Path $AppDir '.env') (Join-Path $AppDir '.env.example') 'app/.env'

    Write-Step '2/5 앱이 접속할 API 주소 (app/.env 의 EXPO_PUBLIC_API_URL)'
    Update-ApiUrl (Join-Path $AppDir '.env')

    Write-Step '3/5 서버 Python 환경 (server/.venv)'
    if ($SkipServer) { Write-Info '건너뜀 (-SkipServer)' } else { Install-Server $ServerDir $VenvPython }

    Write-Step '4/5 앱 패키지 (npm ci)'
    if ($SkipApp) { Write-Info '건너뜀 (-SkipApp)' } else { Install-App $AppDir }

    Write-Step '5/5 환경 점검 (scripts/check_env.py)'
    $checkCode = 0
    if ($SkipCheck) {
        Write-Info '건너뜀 (-SkipCheck)'
    } else {
        $checkCode = Invoke-EnvCheck (Join-Path $RepoRoot 'scripts\check_env.py') $VenvPython
    }

    Write-Step '다음 단계'
    Write-Host '  서버(새 터미널): cd server; .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000'
    Write-Host '  서버 응답 확인 : server\.venv\Scripts\python.exe scripts\check_env.py --health'
    Write-Host '  앱(새 터미널)  : cd app; npx expo start --clear'
    Write-Host '  다른 팀원 서버에 붙기: 이 스크립트를 -SkipServer -SkipApp -ApiUrl http://<그 PC IPv4>:8000 으로 실행'
    Write-Host '  다시 실행할 때 지금 주소를 유지하려면 -KeepApiUrl'
    if ($checkCode -ne 0) {
        Write-Host ''
        Write-Host '점검에서 실패 항목이 있습니다. 위 [FAIL] 줄을 확인하세요.' -ForegroundColor Yellow
        exit 1
    }
    exit 0
} catch {
    Write-Host ''
    Write-Host "[실패] $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
