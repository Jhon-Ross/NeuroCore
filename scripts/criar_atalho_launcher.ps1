# ============================================================================
# SCRIPT: criar_atalho_launcher.ps1
# CRIA ATALHO .lnk NA AREA DE TRABALHO PARA O NEUROCORE LAUNCHER DESKTOP
# 2 cliques para abrir.
# ============================================================================
# Modo de uso:
#   powershell -ExecutionPolicy Bypass -File .\scripts\criar_atalho_launcher.ps1
# ============================================================================
# - Se existir build release/debug (target/release/NeuroCore.exe), usa o .exe.
# - Senão, aponta para "npm run tauri:dev" dentro do frontend/ (2 cliques ainda
#   funciona via PowerShell, sem precisar buildar).
# ============================================================================

$ErrorActionPreference = "Stop"

$raizProjeto = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $raizProjeto "frontend"
$workDir = $frontendDir

# Possíveis locais onde o .exe buildado aparece
$exeRelease = Join-Path $frontendDir "src-tauri\target\release\NeuroCore.exe"
$exeDebug   = Join-Path $frontendDir "src-tauri\target\debug\NeuroCore.exe"

# Escolhe Target
$targetExe = $null
if (Test-Path $exeRelease) { $targetExe = $exeRelease }
elseif (Test-Path $exeDebug) { $targetExe = $exeDebug }

if ($targetExe) {
    $TargetPath     = $targetExe
    $Arguments      = ""
    $Descricao      = "NeuroCore Launcher Desktop (build release/debug · Tauri v2)"
    $icone          = $targetExe
    $WorkDirFinal   = Split-Path -Parent $targetExe
}
else {
    # Modo dev: chama powershell + npm run tauri:dev dentro do frontend/.
    # Garante que npm/powershell são encontrados no PATH do usuário.
    $psExe = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    $TargetPath     = $psExe
    $Arguments      = '-NoProfile -ExecutionPolicy Bypass -Command "& { Set-Location ''' + $frontendDir + ''' ; npm run tauri:dev ; exit $LASTEXITCODE }"'
    $Descricao      = "NeuroCore Launcher Desktop (modo dev · npm run tauri:dev · 2 cliques)"
    try {
        $iconeExe = Join-Path $frontendDir "src-tauri\icons\icon.ico"
        $icone = if (Test-Path $iconeExe) { $iconeExe } else { (Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe") }
    } catch { $icone = $psExe }
    $WorkDirFinal   = $frontendDir
}

# Caminho atalho na Desktop do usuário
$desktop = [Environment]::GetFolderPath("Desktop")
$atalho  = Join-Path $desktop "NeuroCore Launcher.lnk"

Write-Host ""
Write-Host "========================================================"  -ForegroundColor Cyan
Write-Host " NeuroCore · Criar Atalho Launcher Desktop (2 cliques) " -ForegroundColor Yellow
Write-Host "========================================================"  -ForegroundColor Cyan
Write-Host " Raiz projeto       : $raizProjeto"
Write-Host " Frontend dir       : $frontendDir"
Write-Host " TargetPath         : $TargetPath"
if ($Arguments) { Write-Host " Arguments          : $Arguments" }
Write-Host " Working Directory  : $WorkDirFinal"
Write-Host " Ícone              : $icone"
Write-Host " Atalho (saída)     : $atalho"
Write-Host ""

try {
    $shell = New-Object -ComObject WScript.Shell
    $sc = $shell.CreateShortcut($atalho)
    $sc.TargetPath       = $TargetPath
    if ($Arguments) { $sc.Arguments = $Arguments }
    $sc.WorkingDirectory = $WorkDirFinal
    $sc.Description      = $Descricao
    try { $sc.IconLocation = "$icone,0" } catch {}
    $sc.WindowStyle = 1   # 1 = Normal (default)
    $sc.Save()

    Write-Host "OK · Atalho criado com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Próximos passos:"                     -ForegroundColor Yellow
    Write-Host "  1. Vá para a Área de Trabalho"
    Write-Host "  2. Dê 2 cliques em ""NeuroCore Launcher.lnk"""
    if (-not $targetExe) {
        Write-Host ""
        Write-Host " (Modo dev ativado: primeiro abrir pode demorar ~10-30s" -ForegroundColor DarkCyan
        Write-Host "  enquanto compila Rust + sobe Next.js dev server)"     -ForegroundColor DarkCyan
    }
    exit 0
}
catch {
    Write-Host "ERRO ao criar atalho:" -ForegroundColor Red
    Write-Host $_.Exception.Message     -ForegroundColor Red
    exit 1
}
