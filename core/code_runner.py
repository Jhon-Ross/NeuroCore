# ============================================================================
# NEUROCORE · CODE RUNNER SEGURO (Subprocess Sandbox Local)
#
# Executa blocos de código (Python, PowerShell, Node.js) gerados pelo Prometeu
# com limites rígidos de tempo (timeout), filtros de segurança anti-destrutivos,
# e captura confiável de stdout/stderr sem risco de deadlock no Windows.
# ============================================================================

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import log

# Raiz do projeto
RAIZ_PROJETO = Path(__file__).resolve().parent.parent

# Padrões perigosos para bloqueio imediato (hard constraint de segurança)
PADROES_PERIGOSOS: List[re.Pattern] = [
    re.compile(r"\brm\s+(-rf?|--recursive|-rRf?|/[FfSsQq])\b", re.IGNORECASE),
    re.compile(r"\b(rmdir|rd)\s+(/s|/S)", re.IGNORECASE),
    re.compile(r"\bformat\s+[A-Za-z]:", re.IGNORECASE),
    re.compile(r"\bdel\s+(/f|/F|/s|/S)", re.IGNORECASE),
    re.compile(r"\berase\s+(/f|/F|/s|/S)", re.IGNORECASE),
    re.compile(r"\b(reg\s+delete|regsvr32\s+/u|schtasks\s+/delete)\b", re.IGNORECASE),
    re.compile(r"\b(taskkill\s+/f|taskkill\s+/F)\b", re.IGNORECASE),
    re.compile(r"\b(netsh\s+winsock\s+reset|sfc\s+/scannow|dism\s+/online)\b", re.IGNORECASE),
    re.compile(r"\bshutdown\s+(/s|/r|/l)", re.IGNORECASE),
    re.compile(r"\bdd\s+if=", re.IGNORECASE),
    re.compile(r"\b(:(){ :|:& };:)\b"),  # fork bomb
]


def _obter_python_executavel(gui: bool = False) -> str:
    """Retorna o caminho do python no .venv do projeto, ou sys.executable."""
    if gui and sys.platform == "win32":
        venv_pythonw = RAIZ_PROJETO / ".venv" / "Scripts" / "pythonw.exe"
        if venv_pythonw.exists():
            return str(venv_pythonw)
    venv_python = RAIZ_PROJETO / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _detectar_perigo(codigo: str) -> Optional[str]:
    """Retorna descrição se o código violar padrões de segurança destrutivos."""
    for pat in PADROES_PERIGOSOS:
        if pat.search(codigo):
            return f"Comando potencialmente destrutivo detectado: `{pat.pattern[:60]}`"
    return None


def normalizar_linguagem(lang: str) -> str:
    """Normaliza o identificador de linguagem extraído do markdown."""
    l = (lang or "").lower().strip()
    if l in ("python", "py", "python3"):
        return "python"
    if l in ("powershell", "ps", "ps1", "pwsh"):
        return "powershell"
    if l in ("javascript", "js", "node", "nodejs"):
        return "javascript"
    if l in ("typescript", "ts"):
        return "typescript"
    if l in ("bash", "sh", "shell"):
        return "bash"
    return l or "python"


def executar_codigo(
    codigo: str,
    linguagem: str = "python",
    timeout_segundos: int = 15,
    conceder_xp: bool = True,
) -> Dict[str, Any]:
    """
    Executa o bloco de código de forma isolada e segura.

    Args:
        codigo: Código-fonte a ser executado.
        linguagem: "python", "powershell", "javascript", "bash".
        timeout_segundos: Limite de tempo (padrão 15s).
        conceder_xp: Se True e o código rodar com sucesso, concede XP à skill 'codigo'.

    Returns:
        Dict com sucesso, stdout, stderr, codigo_retorno, tempo_ms, xp_ganho.
    """
    t_inicio = time.perf_counter()
    codigo_limpo = (codigo or "").strip()
    lang = normalizar_linguagem(linguagem)

    if not codigo_limpo:
        return {
            "sucesso": False,
            "stdout": "",
            "stderr": "Nenhum código fornecido para execução.",
            "codigo_retorno": -1,
            "tempo_ms": 0.0,
            "linguagem": lang,
            "xp_ganho": 0,
        }

    # 1. Checagem de segurança
    perigo = _detectar_perigo(codigo_limpo)
    if perigo:
        log.warn("code_runner_bloqueio_seguranca", {"motivo": perigo, "codigo_preview": codigo_limpo[:80]})
        return {
            "sucesso": False,
            "stdout": "",
            "stderr": (
                f"🔒 Execução bloqueada por segurança.\n"
                f"Motivo: {perigo}\n"
                f"O Prometeu não executa comandos potencialmente destrutivos via Code Runner."
            ),
            "codigo_retorno": 403,
            "tempo_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
            "linguagem": lang,
            "xp_ganho": 0,
        }

    temp_path: Optional[Path] = None
    eh_gui = False

    try:
        # Detecta se é aplicativo gráfico visual (Tkinter / PyQt)
        if lang == "python":
            eh_gui = bool(
                re.search(
                    r"\b(import\s+tkinter|from\s+tkinter|import\s+customtkinter|from\s+customtkinter|import\s+PyQt|from\s+PyQt)\b",
                    codigo_limpo,
                )
            )

        # Se for app gráfico, executa desacoplado no Windows para a janela abrir sem travar o runner
        if lang == "python" and eh_gui:
            python_exe = _obter_python_executavel(gui=True)
            temp_path = Path(tempfile.gettempdir()) / f"prometeu_gui_{int(time.time() * 1000)}.py"
            temp_path.write_text(codigo_limpo, encoding="utf-8")

            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

            proc = subprocess.Popen(
                [python_exe, str(temp_path)],
                cwd=str(RAIZ_PROJETO),
                creationflags=creation_flags,
            )

            tempo_ms = round((time.perf_counter() - t_inicio) * 1000, 2)
            xp_ganho = 0
            if conceder_xp:
                try:
                    from core.progress_rpg import rpg
                    rpg.adicionar_xp(
                        habilidade="codigo",
                        quantidade=3,
                        motivo="Execução de aplicativo gráfico via Code Runner",
                        tags=["code_runner", "gui", "tkinter"],
                    )
                    xp_ganho = 3
                except Exception as e:
                    log.warn("code_runner_falha_xp", {"erro": str(e)})

            return {
                "sucesso": True,
                "stdout": (
                    f"🚀 Aplicativo gráfico iniciado com sucesso no Windows! (PID: {proc.pid})\n"
                    f"A janela interativa está aberta na sua Área de Trabalho.\n"
                    f"Você pode interagir livremente com os botões e recursos visuais."
                ),
                "stderr": "",
                "codigo_retorno": 0,
                "tempo_ms": tempo_ms,
                "linguagem": lang,
                "xp_ganho": xp_ganho,
            }

        # Monta comando conforme a linguagem (modo script em lote padrão)
        if lang == "python":
            python_exe = _obter_python_executavel(gui=False)
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", encoding="utf-8", delete=False
            ) as f:
                f.write(codigo_limpo)
                temp_path = Path(f.name)

            cmd = [python_exe, str(temp_path)]

        elif lang == "powershell":
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".ps1", encoding="utf-8", delete=False
            ) as f:
                f.write(codigo_limpo)
                temp_path = Path(f.name)

            cmd = [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(temp_path),
            ]

        elif lang == "javascript":
            node_exe = shutil.which("node")
            if not node_exe:
                return {
                    "sucesso": False,
                    "stdout": "",
                    "stderr": "Ambiente Node.js não foi encontrado no PATH do sistema.",
                    "codigo_retorno": 127,
                    "tempo_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
                    "linguagem": lang,
                    "xp_ganho": 0,
                }

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".js", encoding="utf-8", delete=False
            ) as f:
                f.write(codigo_limpo)
                temp_path = Path(f.name)

            cmd = [node_exe, str(temp_path)]

        elif lang == "bash":
            # Tenta Git Bash se estiver no Windows
            git_bash = Path(r"C:\Program Files\Git\bin\bash.exe")
            bash_exe = str(git_bash) if git_bash.exists() else shutil.which("bash")

            if not bash_exe:
                # Fallback: executa comandos shell simples via PowerShell
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".ps1", encoding="utf-8", delete=False
                ) as f:
                    f.write(codigo_limpo)
                    temp_path = Path(f.name)
                cmd = ["powershell.exe", "-NoProfile", "-NonInteractive", "-File", str(temp_path)]
            else:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".sh", encoding="utf-8", delete=False
                ) as f:
                    f.write(codigo_limpo)
                    temp_path = Path(f.name)
                cmd = [bash_exe, str(temp_path)]

        else:
            return {
                "sucesso": False,
                "stdout": "",
                "stderr": f"Linguagem '{lang}' não suportada para execução direta no momento.",
                "codigo_retorno": 400,
                "tempo_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
                "linguagem": lang,
                "xp_ganho": 0,
            }

        # Executa processo com timeout e buffer seguro (anti-deadlock)
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_segundos,
            encoding="utf-8",
            errors="replace",
            cwd=str(RAIZ_PROJETO),
        )

        tempo_ms = round((time.perf_counter() - t_inicio) * 1000, 2)
        sucesso = proc.returncode == 0
        xp_ganho = 0

        # Concessão de XP no sistema RPG caso sucesso
        if sucesso and conceder_xp:
            try:
                from core.progress_rpg import rpg
                res_xp = rpg.adicionar_xp(
                    habilidade="codigo",
                    quantidade=3,
                    motivo=f"Execução com sucesso via Code Runner ({lang})",
                    tags=["code_runner", lang],
                )
                xp_ganho = 3
                log.info("code_runner_xp_concedido", {"lang": lang, "novo_xp": res_xp.get("novo_xp")})
            except Exception as e:
                log.warn("code_runner_falha_xp", {"erro": str(e)})

        return {
            "sucesso": sucesso,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "codigo_retorno": proc.returncode,
            "tempo_ms": tempo_ms,
            "linguagem": lang,
            "xp_ganho": xp_ganho,
        }

    except subprocess.TimeoutExpired:
        tempo_ms = round((time.perf_counter() - t_inicio) * 1000, 2)
        return {
            "sucesso": False,
            "stdout": "",
            "stderr": f"⏱️ Timeout: A execução excedeu o limite de {timeout_segundos} segundos e foi interrompida.",
            "codigo_retorno": 124,
            "tempo_ms": tempo_ms,
            "linguagem": lang,
            "xp_ganho": 0,
        }

    except Exception as e:
        tempo_ms = round((time.perf_counter() - t_inicio) * 1000, 2)
        log.error("code_runner_erro_inesperado", {"erro": str(e)}, exception=e)
        return {
            "sucesso": False,
            "stdout": "",
            "stderr": f"Erro interno ao executar código: {e}",
            "codigo_retorno": -1,
            "tempo_ms": tempo_ms,
            "linguagem": lang,
            "xp_ganho": 0,
        }

    finally:
        # Limpeza do arquivo temporário (apenas para scripts batch normais)
        if temp_path and temp_path.exists() and not eh_gui:
            try:
                temp_path.unlink()
            except Exception:
                pass
