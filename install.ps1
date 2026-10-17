# yt-autopilot installer. Run via Install.bat (double-click). No admin rights needed.
$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = Join-Path $env:LOCALAPPDATA "yt-autopilot"
$WatchRoot = Join-Path $env:USERPROFILE "YouTubeUploads"
$DesktopConfig = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
$Desktop = [Environment]::GetFolderPath("Desktop")

function Step($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }
function Ok($msg) { Write-Host "    $msg" -ForegroundColor Green }

Write-Host "=================================================" -ForegroundColor Yellow
Write-Host "   YouTube Autopilot for Claude - Installer" -ForegroundColor Yellow
Write-Host "=================================================" -ForegroundColor Yellow
Write-Host "This installs a small helper so Claude Desktop can upload your videos"
Write-Host "to YouTube and review their performance. It takes about 2 minutes."

# --- 0. Claude Desktop must be closed, otherwise it overwrites its own config on exit
Step "Checking Claude Desktop"
$claude = Get-Process -Name "Claude" -ErrorAction SilentlyContinue
if ($claude) {
    Write-Host "    Claude Desktop is open. Please close it completely (right-click the tray icon > Quit)." -ForegroundColor Yellow
    Read-Host "    Press Enter when Claude Desktop is closed"
    $claude = Get-Process -Name "Claude" -ErrorAction SilentlyContinue
    if ($claude) { Write-Host "    Closing Claude Desktop for you..."; $claude | Stop-Process -Force; Start-Sleep -Seconds 3 }
}
Ok "Claude Desktop is closed"

# --- 1. Python
Step "Checking Python 3.12"
$py = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "    Installing Python 3.12 (one-time, about 1 minute)..."
    $installed = $false
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        try {
            winget install --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements --silent --override "/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=0 Include_test=0" | Out-Null
            $installed = Test-Path $py
        } catch {}
    }
    if (-not $installed) {
        $exe = Join-Path $env:TEMP "python-3.12.10-amd64.exe"
        Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe" -OutFile $exe
        Start-Process -FilePath $exe -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=0 Include_test=0" -Wait
        $installed = Test-Path $py
    }
    if (-not $installed) { throw "Python could not be installed. Install it from python.org and run this again." }
}
Ok "Python found: $py"

# --- 2. Copy files
Step "Installing helper to $Target"
New-Item -ItemType Directory -Force -Path $Target, (Join-Path $Target "data") | Out-Null
foreach ($f in @("server.py", "config.json", "requirements.txt", "README.md")) {
    if (Test-Path (Join-Path $Here $f)) { Copy-Item (Join-Path $Here $f) (Join-Path $Target $f) -Force }
}
$secretSrc = Join-Path $Here "client_secret.json"
$secretDst = Join-Path $Target "data\client_secret.json"
if (-not (Test-Path $secretSrc) -and -not (Test-Path $secretDst)) {
    Write-Host ""
    Write-Host "    client_secret.json is not in this folder." -ForegroundColor Yellow
    Write-Host "    This helper needs your own Google sign-in file. Follow 'GOOGLE SETUP.md' (opening it now),"
    Write-Host "    then put the downloaded file in this folder as:  client_secret.json"
    $guide = Join-Path $Here "GOOGLE SETUP.md"
    if (Test-Path $guide) { Start-Process $guide }
    while (-not (Test-Path $secretSrc)) { Read-Host "    Press Enter once client_secret.json is in the folder" | Out-Null }
}
if (Test-Path $secretSrc) { Copy-Item $secretSrc $secretDst -Force }
Ok "Files copied"

# --- 3. Virtual environment + packages
Step "Setting up Python packages (about 1 minute)"
$venvPy = Join-Path $Target ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) { & $py -m venv (Join-Path $Target ".venv") }
& $venvPy -m pip install -q --no-warn-script-location --disable-pip-version-check -r (Join-Path $Target "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Package installation failed. Check your internet connection and run again." }
& $venvPy -m py_compile (Join-Path $Target "server.py")
Ok "Packages ready"

# --- 4. Watch folders + shortcuts
Step "Creating upload folders"
foreach ($d in @("incoming", "uploaded", "failed")) { New-Item -ItemType Directory -Force -Path (Join-Path $WatchRoot $d) | Out-Null }
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut((Join-Path $Desktop "YouTube Upload Inbox.lnk")); $s.TargetPath = (Join-Path $WatchRoot "incoming"); $s.Save()
$s = $ws.CreateShortcut((Join-Path $Desktop "Sign in to YouTube.lnk")); $s.TargetPath = $venvPy; $s.Arguments = "`"$Target\server.py`" --auth"; $s.WorkingDirectory = $Target; $s.Save()
Ok "Folder: $WatchRoot  (shortcut 'YouTube Upload Inbox' on Desktop)"

# --- 5. Register in Claude Desktop (merge JSON with Python so nothing else in the file is touched)
Step "Connecting to Claude Desktop"
New-Item -ItemType Directory -Force -Path (Split-Path $DesktopConfig) | Out-Null
$merge = @"
import json, sys, os, shutil, time
p = sys.argv[1]; target = sys.argv[2]
cfg = {}
if os.path.exists(p):
    shutil.copy(p, p + '.backup-' + time.strftime('%Y%m%d%H%M%S'))
    raw = open(p, encoding='utf-8-sig').read().strip()
    if raw:
        try:
            cfg = json.loads(raw)
        except Exception as e:
            sys.exit('Existing Claude Desktop config could not be read (%s). Nothing was changed.' % e)
if not isinstance(cfg, dict):
    sys.exit('Existing Claude Desktop config has an unexpected format. Nothing was changed.')
cfg.setdefault('mcpServers', {})['yt-autopilot'] = {
    'command': os.path.join(target, '.venv', 'Scripts', 'python.exe').replace('\\', '/'),
    'args': [os.path.join(target, 'server.py').replace('\\', '/')],
    'env': {'PYTHONIOENCODING': 'utf-8', 'PYTHONUTF8': '1'}}
json.dump(cfg, open(p, 'w', encoding='utf-8'), indent=2)
print('ok')
"@
$mergeFile = Join-Path $env:TEMP "yt_merge_config.py"
Set-Content -Path $mergeFile -Value $merge -Encoding UTF8
& $venvPy -I $mergeFile $DesktopConfig $Target
$mergeExit = $LASTEXITCODE
Remove-Item $mergeFile -Force
if ($mergeExit -ne 0) { throw "Could not register with Claude Desktop (see message above)." }
Ok "Registered as 'yt-autopilot' in Claude Desktop"

# --- 6. Scheduled tasks (daily stats 09:00, weekly report Monday 09:15)
Step "Scheduling daily stats and weekly report"
try {
    $set = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
    $a1 = New-ScheduledTaskAction -Execute $venvPy -Argument "`"$Target\server.py`" --daily" -WorkingDirectory $Target
    Register-ScheduledTask -TaskName "yt-autopilot daily stats" -Action $a1 -Trigger (New-ScheduledTaskTrigger -Daily -At 9:00AM) -Settings $set -Force | Out-Null
    $a2 = New-ScheduledTaskAction -Execute $venvPy -Argument "`"$Target\server.py`" --weekly" -WorkingDirectory $Target
    Register-ScheduledTask -TaskName "yt-autopilot weekly report" -Action $a2 -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9:15AM) -Settings $set -Force | Out-Null
    Ok "Tasks created"
} catch { Write-Host "    Could not create scheduled tasks ($($_.Exception.Message)). Everything else still works." -ForegroundColor Yellow }

# --- 7. Google sign-in
Step "Sign in to YouTube"
Write-Host "    A browser window will open. Sign in with the Google account that owns your YouTube channel."
Write-Host "    If Google says the app is not verified: click 'Advanced', then 'Go to yt-autopilot'."
Write-Host "    Tick all permission boxes and click Continue / Allow."
Read-Host "    Press Enter to open the sign-in"
& $venvPy (Join-Path $Target "server.py") --auth
if ($LASTEXITCODE -ne 0) { Write-Host "    Sign-in did not finish. You can retry any time with 'Sign in to YouTube' on the Desktop." -ForegroundColor Yellow }

Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "   Done! Open Claude Desktop and type:" -ForegroundColor Green
Write-Host "   check youtube auth status" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host "To upload: save a video in Downloads (or the 'YouTube Upload Inbox' folder)"
Write-Host "and tell Claude: upload <file name> to YouTube"
Read-Host "Press Enter to close"
