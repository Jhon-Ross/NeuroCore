# ============================================================================
# SCRIPT: scripts\iniciar_prometeu.ps1
# LAUNCHER 1 CLIQUE PARA WINDOWS POWERSHELL
#
# O que ele faz (na ordem):
#   1. Garante que a politica de execução local permite scripts (assina nao precisa)
#   2. Verifica se OLLAMA está rodando (se não, inicia ollama serve em background)
#   3. Garante que .venv existe, e se nao cria (nunca vimos essa situacao, mas seguro)
#   4. Roda o run_chat_cli.py (conversa por terminal)
#
# Como usar:
#   Clique com botão direito no arquivo → "Executar com PowerShell"
#   OU: Abra PowerShell na raiz do NeuroCore e digite: .\scripts\iniciar_prometeu.ps1
# ============================================================================

[CmdletBinding()]
param(
    [switch]$ModoDesenvolvimento  # se passado, nao limpa a tela no inicio
)

$ErrorActionPreference = "Continue"

# ------------------------------------------------------------------
# Cores no terminal PowerShell
# ------------------------------------------------------------------
function Write-Ambar([string]$Texto)  { Write-Host -ForegroundColor DarkYellow $Texto }
function Write-Verde([string]$Texto)  { Write-Host -ForegroundColor Green $Texto }
function Write-Vermelho([string]$Texto){ Write-Host -ForegroundColor Red $Texto }
function Write-Cinza([string]$Texto)  { Write-Host -ForegroundColor DarkGray $Texto }
function Write-Branco([string]$Texto) { Write-Host -ForegroundColor White $Texto }

# ------------------------------------------------------------------
# Passo 0: Caminhos
# ------------------------------------------------------------------
$RAIZ = Split-Path -Parent $PSScriptRoot   # NeuroCore\ (scripts esta um nivel abaixo)
Set-Location $RAIZ
$VENV_PY = Join-Path $RAIZ ".venv\Scripts\python.exe"
$SCRIPT_CLI = Join-Path $RAIZ "scripts\run_chat_cli.py"
$OLLAMA_EXE = "ollama"

Write-Ambar "╔══════════════════════════════════════════════════════════════════╗"
Write-Ambar "║   🔥 LAUNCHER PROMETEU — Chat CLI                                ║"
Write-Ambar "╚══════════════════════════════════════════════════════════════════╝"
Write-Cinza  "  Diretorio raiz do NeuroCore: $RAIZ"

# ------------------------------------------------------------------
# Passo 1: Verificar Ollama instalado + rodando
# ------------------------------------------------------------------
Write-Branco "`n[1/4] Verificando servico Ollama..."
try {
    $ollamaExiste = Get-Command ollama -ErrorAction SilentlyContinue
    if (-not $ollamaExiste) {
        Write-Vermelho "  ❌ Ollama NAO INSTALADO."
        Write-Vermelho "     Baixe em https://ollama.com/download/windows e reinicie."
        Read-Host "Pressione ENTER para sair"
        exit 1
    }
    $procOllama = Get-Process ollama -ErrorAction SilentlyContinue
    if (-not $procOllama) {
        Write-Cinza "  Ollama nao estava rodando. Iniciando ollama serve em background..."
        Start-Process $OLLAMA_EXE -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 3
    }
    try {
        Invoke-RestMethod "http://localhost:11434/api/tags" -TimeoutSec 3 | Out-Null
        Write-Verde "  ✅ Ollama ONLINE em http://localhost:11434"
    } catch {
        Write-Vermelho "  ⚠️  Ollama iniciado mas nao respondeu ainda. Tudo bem, o orquestrador tenta de novo."
    }
} catch {
    Write-Vermelho "  Aviso: erro checando Ollama: $_"
}

# ------------------------------------------------------------------
# Passo 2: .venv
# ------------------------------------------------------------------
Write-Branco "`n[2/4] Verificando ambiente virtual Python..."
if (-not (Test-Path $VENV_PY)) {
    Write-Vermelho "  ❌ .venv NAO EXISTE em $VENV_PY"
    Write-Cinza  "  Criando .venv e instalando requirements... (isso demora 1-2 min)"
    try {
        py -3.12 -m venv (Join-Path $RAIZ ".venv")
        & $VENV_PY -m pip install --upgrade pip
        & $VENV_PY -m pip install -r (Join-Path $RAIZ "requirements.txt")
        Write-Verde "  ✅ .venv criado e dependencias instaladas."
    } catch {
        Write-Vermelho "  FALHOU criacao do venv. Erro: $_"
        Read-Host "Pressione ENTER para sair"
        exit 2
    }
} else {
    Write-Verde "  ✅ .venv OK"
}

# ------------------------------------------------------------------
# Passo 3: Script CLI existe
# ------------------------------------------------------------------
Write-Branco "`n[3/4] Verificando script de chat..."
if (-not (Test-Path $SCRIPT_CLI)) {
    Write-Vermelho "  ❌ Arquivo nao encontrado: $SCRIPT_CLI"
    Read-Host "Pressione ENTER para sair"
    exit 3
}
Write-Verde "  ✅ scripts\run_chat_cli.py OK"

# ------------------------------------------------------------------
# Passo 4: Executa o chat CLI
# ------------------------------------------------------------------
Write-Branco "`n[4/4] Iniciando chat com o Prometeu...`n"
if (-not $ModoDesenvolvimento) { Clear-Host }

& $VENV_PY $SCRIPT_CLI

$codSaida = $LASTEXITCODE
Write-Cinza "`n  Launcher encerrado (código $codSaida)."
