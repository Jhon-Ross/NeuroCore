# ============================================================
# SCRIPT DE MIGRACAO MODELOS OLLAMA
# De : C:\Users\Jhon Ross\.ollama\models
# Para: G:\models
# ============================================================
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$origemModels = Join-Path $env:USERPROFILE ".ollama\models"
$destino      = "G:\models"
$tIni         = Get-Date

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   NEUROCORE: MIGRACAO MODELOS OLLAMA -> HDD G:"   -ForegroundColor Cyan
Write-Host "   C: SSD ~8GB -> G:\models (90GB reservados)"    -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# PASSO 1: PARAR OLLAMA
# ============================================================
Write-Host "[1/7] Parando ollama.exe..." -ForegroundColor Yellow
Get-Process ollama -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host ("       Matando PID {0}" -f $_.Id)
    Stop-Process -Id $_.Id -Force
}
Start-Sleep -Seconds 2
$vivo = Get-Process ollama -ErrorAction SilentlyContinue
if ($vivo) {
    taskkill /F /IM ollama.exe 2>&1 | Out-Null
    Start-Sleep -Seconds 1
}
Write-Host "       OK: Nenhum ollama.exe rodando" -ForegroundColor Green
Write-Host ""

# ============================================================
# PASSO 2: VALIDAR PASTAS
# ============================================================
Write-Host "[2/7] Validando estrutura de pastas..." -ForegroundColor Yellow
if (-not (Test-Path $origemModels)) {
    Write-Host ("       ERRO: Origem nao existe: {0}" -f $origemModels) -ForegroundColor Red
    Write-Host "       Ollama instalado? Modelos baixados?"
    pause
    exit 1
}
if (-not (Test-Path $destino)) {
    New-Item -ItemType Directory -Path $destino -Force | Out-Null
}
Write-Host ("       Origem  OK: {0}" -f $origemModels)
Write-Host ("       Destino OK: {0}" -f $destino)
Write-Host ""

# ============================================================
# PASSO 3: AUDITORIA ANTES
# ============================================================
Write-Host "[3/7] Auditoria ANTES (SSD C:)" -ForegroundColor Yellow
$filesOri = Get-ChildItem $origemModels -Recurse -File
$tamOriGB = [math]::Round(($filesOri | Measure-Object Length -Sum).Sum / 1GB, 3)
Write-Host ("       {0} arquivos / {1} GB para mover" -f $filesOri.Count, $tamOriGB)
Write-Host ""

# ============================================================
# PASSO 4: COPIAR VIA ROBOCOPY
# ============================================================
Write-Host "[4/7] Copiando arquivos (ROBOCOPY /MT:16)..." -ForegroundColor Yellow
Write-Host "       (8GB geralmente demora 3-8 minutos. NAO FECHE a janela!)"
$logRobo = Join-Path $env:TEMP ("neurocore_robo_{0}.log" -f (Get-Date -Format yyyyMMdd_HHmmss))
# OBS: Usamos & robocopy DIRETO (nao Start-Process) pois o nome de usuario
# "Jhon Ross" tem ESPACO e Start-Process -ArgumentList quebra os argumentos.
& robocopy $origemModels $destino /E /COPY:DAT /DCOPY:DAT /MT:16 /R:3 /W:2 /NFL /NDL /NC /NP /LOG:$logRobo | Out-Null
$exitRobo = $LASTEXITCODE
if ($exitRobo -ge 8) {
    Write-Host ("       ERRO ROBOCOPY cod={0}. Log: {1}" -f $exitRobo, $logRobo) -ForegroundColor Red
    if (Test-Path $logRobo) { Get-Content $logRobo -Tail 20 }
    pause
    exit 2
}
$durCopia = (Get-Date) - $tIni
Write-Host ("       OK Copia concluida em {0:N0} segundos" -f $durCopia.TotalSeconds) -ForegroundColor Green
Write-Host ""

# ============================================================
# PASSO 5: AUDITORIA DEPOIS + INTEGRIDADE
# ============================================================
Write-Host "[5/7] Auditoria DEPOIS + Integridade (tamanhos identicos)" -ForegroundColor Yellow
$filesDst = Get-ChildItem $destino -Recurse -File -ErrorAction SilentlyContinue
$tamDstGB = [math]::Round(($filesDst | Measure-Object Length -Sum).Sum / 1GB, 3)
Write-Host ("       Destino G:\models: {0} arquivos / {1} GB" -f $filesDst.Count, $tamDstGB)

$blobsOri  = Get-ChildItem (Join-Path $origemModels "blobs") -File -ErrorAction SilentlyContinue | Sort-Object Length -Descending | Select-Object -First 5
$blobsDst  = Get-ChildItem (Join-Path $destino      "blobs") -File -ErrorAction SilentlyContinue | Sort-Object Length -Descending | Select-Object -First 5
$todosOK = $true
foreach ($b in $blobsOri) {
    $bDst = $blobsDst | Where-Object { $_.Name -eq $b.Name } | Select-Object -First 1
    $ok = ($bDst -and ($bDst.Length -eq $b.Length))
    if (-not $ok) { $todosOK = $false }
    $nomeCurto = $b.Name
    if ($nomeCurto.Length -gt 22) { $nomeCurto = $nomeCurto.Substring(0,22) }
    Write-Host ("       Blob {0} ({1} MB) -> {2}" -f $nomeCurto, [math]::Round($b.Length/1MB,0), $(if($ok){"OK"}else{"DIVERGENTE"}))
}
if (-not $todosOK) {
    Write-Host "       ERRO: Integridade falhou! NAO apague a origem ainda." -ForegroundColor Red
    pause
    exit 3
}
Write-Host "       OK: Tamanhos identicos, integridade verificada" -ForegroundColor Green
Write-Host ""

# ============================================================
# PASSO 6: REABRIR OLLAMA + VALIDAR LISTA
# ============================================================
Write-Host "[6/7] Reiniciando Ollama Serve + validando lista..." -ForegroundColor Yellow
$ollamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
if (-not (Test-Path $ollamaExe)) { $ollamaExe = "ollama.exe" }

[Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $destino, "User")
$env:OLLAMA_MODELS = $destino
Write-Host ("       Variavel OLLAMA_MODELS = {0}" -f $env:OLLAMA_MODELS)

$proc = Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Hidden -PassThru -ErrorAction Stop
Write-Host ("       Novo ollama serve PID {0}" -f $proc.Id)
Write-Host "       Aguardando API :11434 ficar pronta"

for ($i = 1; $i -le 60; $i++) {
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
        Write-Host ("       API pronta em {0}s! Modelos detectados:" -f $i) -ForegroundColor Green
        foreach ($m in $resp.models) {
            Write-Host ("         - {0,-40} {1,5} GB" -f $m.name, [math]::Round($m.size/1GB,2))
        }
        break
    }
    catch { Start-Sleep -Seconds 1 }
    if ($i -eq 60) {
        Write-Host "       Aviso: API nao respondeu 60s. Tente rodar: ollama list" -ForegroundColor Yellow
    }
}
Write-Host ""

# ============================================================
# PASSO 7: APAGAR ORIGEM (PERGUNTAR)
# ============================================================
Write-Host "[7/7] Liberar SSD? Apagar a origem em C: ?" -ForegroundColor Yellow
$padrao = "N"
$caption = "       Deseja APAGAR a pasta $origemModels para liberar $tamOriGB GB do SSD ?"
$resp = Read-Host "$caption (s/N)"
$apagar = ($resp -eq "s") -or ($resp -eq "S") -or ($resp -eq "y") -or ($resp -eq "Y")
if ($apagar) {
    Write-Host ("       Apagando origem {0}" -f $origemModels)
    Remove-Item $origemModels -Recurse -Force -ErrorAction Stop
    Write-Host ("       OK: Liberados {0} GB no SSD C:" -f $tamOriGB) -ForegroundColor Green
} else {
    Write-Host "       OK: Mantive copia original no SSD."
    Write-Host "       Para apagar DEPOIS, use:"
    Write-Host ("         Remove-Item '{0}' -Recurse -Force" -f $origemModels) -ForegroundColor Gray
}
Write-Host ""

# ============================================================
# RESUMO FINAL
# ============================================================
$durTot = (Get-Date) - $tIni
Write-Host "==================================================" -ForegroundColor Green
Write-Host ("  MIGRACAO CONCLUIDA! Tempo total: {0:N1} minutos" -f $durTot.TotalMinutes)
Write-Host ("    SSD C: liberados ~{0} GB" -f $tamOriGB)
Write-Host ("    HDD G:\models: {0} GB usados / 90 GB planejados" -f $tamDstGB)
$memOk = Test-Path "G:\memory"
Write-Host ("    HDD G:\memory (10GB): {0}" -f $(if($memOk){"OK (intocado)"}else{"Nao existe"}))
Write-Host ""
Write-Host "  Proximos testes (cole no PowerShell):" -ForegroundColor Yellow
Write-Host "     ollama list"
Write-Host "     Get-ChildItem G:\models\blobs"
Write-Host "     Invoke-RestMethod http://127.0.0.1:11434/api/tags | Select-Object -Expand models"
Write-Host "=================================================="
pause
