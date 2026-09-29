# ============================================================================
# SCRIPT: scripts\parar_prometeu.ps1
# ESQUELETO — Finaliza o ambiente do Prometeu com seguranca
#
# (Dia 1 = esqueleto. Nas fases posteriores, vai matar FastAPI, Tauri, etc.)
#
# O que ele faz HOJE:
#   1. Lista processos Python e Ollama que estao rodando o NeuroCore
#   2. Pede confirmacao e mata os processos selecionados
# ============================================================================

[CmdletBinding()]
param(
    [switch]$Forcar   # Nao pede confirmacao (forca o encerramento)
)

Write-Host -ForegroundColor DarkCyan @'
  ╔══════════════════════════════════════════════════════════════════╗
  ║   🛑 PARAR PROMETEU — Encerramento Seguro do Ambiente            ║
  ╚══════════════════════════════════════════════════════════════════╝
'@

Write-Host -ForegroundColor Gray "  Procurando processos relacionados ao NeuroCore..."
Write-Host ""

# Coleciona candidatos
$candidatos = @()

$procPython = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*\NeuroCore\.venv*" -or
    $_.MainWindowTitle -like "*Prometeu*" -or
    $_.MainWindowTitle -like "*run_chat_cli*"
}
foreach ($p in $procPython) {
    $candidatos += [PSCustomObject]@{Tipo="Python"; Processo=$p; Nome="$($p.ProcessName) PID $($p.Id)"}
}

$procOllama = Get-Process ollama -ErrorAction SilentlyContinue
foreach ($p in $procOllama) {
    $candidatos += [PSCustomObject]@{Tipo="Ollama"; Processo=$p; Nome="$($p.ProcessName) PID $($p.Id)"}
}

if ($candidatos.Count -eq 0) {
    Write-Host -ForegroundColor Green "  ✅ Nenhum processo ativo do Prometeu/Ollama detectado. Tudo limpo!"
    exit 0
}

Write-Host -ForegroundColor Yellow "  Processos encontrados:"
$candidatos | ForEach-Object -Begin {$i=1} -Process {
    Write-Host ("    {0}. [{1}] {2}" -f $i, $_.Tipo, $_.Nome)
    $i++
}
Write-Host ""

if (-not $Forcar) {
    $resposta = Read-Host "  Confirmar encerramento de TODOS os $($candidatos.Count) processo(s)? (s/N)"
    if ($resposta -notmatch "^[sSyY]") {
        Write-Host -ForegroundColor Gray "  Cancelado. Nada foi encerrado."
        exit 0
    }
}

$mortos = 0
foreach ($c in $candidatos) {
    try {
        Stop-Process -Id $c.Processo.Id -Force -ErrorAction Stop
        Write-Host -ForegroundColor Green "  ✅ Encerrado: $($c.Nome)"
        $mortos++
    } catch {
        Write-Host -ForegroundColor Red  "  ❌ Falhou: $($c.Nome) — $_"
    }
}

Write-Host ""
Write-Host -ForegroundColor Green "  Encerrados $mortos / $($candidatos.Count) processos."
