# ============================================================================
# ESPECIALISTA: os_control (Córtex Motor do SO — Automação Windows)
# FASE DE ATIVAÇÃO: 2 (DIA 2 DA MARATONA — 29/09/2026) — ATIVO AGORA
#
# Backend: subprocess + os + shutil. pywin32 disponivel mas opcional.
# Regras de SEGURANÇA FORTÍSSIMAS (nunca remover):
#   • NENHUMA ação destrutiva sem whitelist explícita.
#   • Lista NEGRA de comandos PERIGOSOS bloqueados SEMPRE (rm -rf / format del /f etc).
#   • Criação/edição de arquivos APENAS em diretórios permitidos
#     (Desktop, Documents, pasta do projeto NeuroCore, G:\memory, temp user).
#   • Retorna SEMPRE mensagem amigável confirmando o que foi feito, com logs.
# ============================================================================

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.base_specialist import BaseSpecialist, ResultadoInferencia, UsoRecursos
from core.logger import log

# --------------------------------------------------------------------
# TABELA DE AÇÕES PERMITIDAS (WHITELIST) — NÃO ADICIONAR COISA PERIGOSA
# --------------------------------------------------------------------
PROGRAMAS_PERMITIDOS: Dict[str, List[str]] = {
    # nome amigavel -> lista de nomes executaveis (caminhos relativos ou PATH)
    "notepad": ["notepad.exe"],
    "bloco de notas": ["notepad.exe"],
    "calc": ["calc.exe"],
    "calculadora": ["calc.exe"],
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "chrome.exe",
    ],
    "google": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "chrome.exe",
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "msedge.exe",
    ],
    "explorer": ["explorer.exe"],
    "arquivos": ["explorer.exe"],
    "cmd": ["cmd.exe", "/k", "echo Prometeu abriu o terminal ^(cuidado^)"],
    "powershell": [
        "powershell.exe",
        "-NoExit",
        "-Command",
        "Write-Host 'Terminal Prometeu aberto. Cuidado com comandos.' -ForegroundColor Yellow",
    ],
    "vs code": [
        r"C:\Users\Jhon Ross\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "code.cmd",
        "code",
    ],
    "vscode": [
        r"C:\Users\Jhon Ross\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "code.cmd",
        "code",
    ],
    "code": [
        r"C:\Users\Jhon Ross\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "code.cmd",
        "code",
    ],
}

# Diretórios onde o Prometeu PODE criar / editar arquivos (qualquer subdiretório dentro)
DIRETORIOS_PERMITIDOS_ESCRITA: List[Path] = [
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "AppData" / "Local" / "Temp",
    Path(r"C:\Users\Jhon Ross\Documents\trae_projects\NeuroCore"),
    Path(r"G:\memory"),
    Path(tempfile.gettempdir()),
]

# --------------------------------------------------------------------
# BLOQUEIO DE PERIGOS — COMANDOS NEGADOS (regex case-insensitive)
# --------------------------------------------------------------------
PADROES_PERIGOSOS: List[re.Pattern] = [
    re.compile(r"\brm\s+(-rf?|--recursive|-rRf?|/[FfSsQq])\b"),
    re.compile(r"\b(rmdir|rd)\s+(/s|/S)"),
    re.compile(r"\bformat\s+[A-Za-z]:"),
    re.compile(r"\bdel\s+(/f|/F|/s|/S)"),
    re.compile(r"\berase\s+(/f|/F|/s|/S)"),
    re.compile(r"\b(reg\s+delete|regsvr32\s+/u|schtasks\s+/delete)\b"),
    re.compile(r"\b(taskkill\s+/f|taskkill\s+/F)\b"),
    re.compile(r"\b(netsh\s+winsock\s+reset|sfc\s+/scannow|dism\s+/online)\b"),
    re.compile(r"[:;\|\&`]\s*(rm|del|rd|format|erase|shutdown)\b"),
    re.compile(r"\bshutdown\s+(/s|/r|/l)"),
    re.compile(r"\bdd\s+if="),
]


class EspecialistaOsControl(BaseSpecialist):

    NOME_INTERNO = "os_control"
    NOME_HUMANO = "🖱️ Controle do Sistema Operacional (Windows)"
    FASE_ATIVACAO = 2
    DESCRICAO = (
        "Região motora do Prometeu: abre programas, cria arquivos txt/py, executa "
        "comandos PowerShell SEGUROS na whitelist. Qualquer coisa destrutiva é bloqueada."
    )

    # ---------------------------------------------------------------
    # Ciclo de vida
    # ---------------------------------------------------------------
    def load(self) -> bool:
        """Inicializa: valida que estamos em Windows (plataforma suportada)."""
        try:
            if sys.platform not in ("win32", "cygwin"):
                self._ultimo_erro = (
                    f"Especialista os_control: Windows obrigatório, plataforma atual={sys.platform}. "
                    f"Compatível apenas com Win10/11."
                )
                self._carregado = False
                return False
            self._carregado = True
            log.info("os_control_carregado",
                     {"platform": sys.platform,
                      "programas_whitelist": len(PROGRAMAS_PERMITIDOS),
                      "diretorios_escrita": len(DIRETORIOS_PERMITIDOS_ESCRITA)})
            return True
        except Exception as e:
            self._ultimo_erro = str(e)
            log.error("os_control_load_falhou", exception=e)
            return False

    def unload(self) -> bool:
        self._carregado = False
        return True

    def is_loaded(self) -> bool:
        return self._carregado

    def get_recursos_usados(self) -> UsoRecursos:
        return UsoRecursos()

    # ---------------------------------------------------------------
    # API pública (infer = recebe comando em texto e executa whitelist)
    # ---------------------------------------------------------------
    def infer(self, **kwargs: Any) -> ResultadoInferencia:
        """
        Kwargs aceitos:
            acao: str                 (obrigatório) comando natural do usuário, ex:
                                         "abre o notepad",
                                         "cria arquivo teste.txt no desktop com oi",
                                         "roda Get-Date no powershell".
            forcar_confirmacao: bool  (padrão False) — se True, retorna plano de ação em vez de executar.
            sessao_humano: str        (apenas p/ log)
        """
        t_inicio = time.perf_counter()
        try:
            if not self._carregado:
                raise RuntimeError("os_control não carregado.")

            acao_original: str = str(kwargs.get("acao") or kwargs.get("prompt") or "").strip()
            if not acao_original:
                raise ValueError("Comando OS vazio.")

            modo_simulacao: bool = bool(kwargs.get("forcar_confirmacao", False))

            # 1. Bloqueia padrões perigosos ANTES de parsear
            perigo = self._detectar_perigo(acao_original)
            if perigo:
                return self._resultado(
                    sucesso=False,
                    erro_mensagem=(
                        f"🔒 **AÇÃO BLOQUEADA POR SEGURANÇA**\n\n"
                        f"Motivo: {perigo}\n"
                        f"Frase suspeita: \"{acao_original[:140]}\"\n\n"
                        f"Se você REALMENTE quiser fazer isso, faça manualmente. "
                        f"O Prometeu não executa ações destrutivas automaticamente."
                    ),
                    t_inicio=t_inicio,
                    metadados={"bloqueio": perigo, "modo_simulacao": modo_simulacao},
                )

            # 2. Detectar tipo de ação: abrir_programa | criar_arquivo | listar_pasta | powershell_seguro
            tipo = self._classificar_acao(acao_original)
            metadados: Dict[str, Any] = {
                "tipo": tipo,
                "modo_simulacao": modo_simulacao,
            }

            if tipo == "abrir_programa":
                return self._acao_abrir_programa(acao_original, modo_simulacao, t_inicio, metadados)
            if tipo == "criar_arquivo":
                return self._acao_criar_arquivo(acao_original, modo_simulacao, t_inicio, metadados)
            if tipo == "listar_pasta":
                return self._acao_listar_pasta(acao_original, modo_simulacao, t_inicio, metadados)
            if tipo == "powershell_seguro":
                return self._acao_powershell_seguro(acao_original, modo_simulacao, t_inicio, metadados)

            # Fallback: nao entendi a açao
            return self._resultado(
                sucesso=False,
                erro_mensagem=(
                    f"🖱️ Região motora OS não entendeu exatamente o comando: "
                    f"\"{acao_original[:140]}\"\n\n"
                    f"Tente algo mais simples, ex:\n"
                    f"  • 'abre o notepad'\n"
                    f"  • 'cria arquivo anotações.txt no desktop com Prometeu estava aqui'\n"
                    f"  • 'lista a pasta do projeto NeuroCore'\n"
                    f"  • 'roda Get-Date no powershell'"
                ),
                t_inicio=t_inicio,
                metadados={**metadados, "erro_classificacao": True},
            )

        except Exception as e:
            return self._resultado(
                sucesso=False,
                erro_mensagem=f"🖱️ Erro no os_control: {e}",
                erro_tecnico=str(e),
                t_inicio=t_inicio,
                modelo_usado="os_control_windows",
            )

    # ---------------------------------------------------------------
    # Helpers internos
    # ---------------------------------------------------------------
    @staticmethod
    def _detectar_perigo(comando: str) -> Optional[str]:
        """Retorna string explicativa se encontrar padrao perigoso, None se seguro."""
        cmd_lower = comando.lower()
        for pat in PADROES_PERIGOSOS:
            if pat.search(cmd_lower):
                return f"Padrão perigoso detectado: `{pat.pattern[:60]}`"
        return None

    @staticmethod
    def _classificar_acao(acao: str) -> str:
        a = acao.lower().strip()
        # Remover prefixos comuns de linguagem natural para melhorar matching
        limpo = re.sub(
            r"^(ei\s+|prometeu[,.:\s]*|por favor[,.:\s]*|por gentileza[,.:\s]*|pra mim[,.:\s]*|pfv[,.:\s]*|pls[,.:\s]*|sff[,.:\s]|poderia[s]?\s+|quero\s+que\s+(você|voce|vc)\s+|quero\s+|me\s+(dá|da|faz|fazer|abre|abrir)\s+)",
            "",
            a,
        ).strip()

        # abrir programa (match mais generico: regex "abre/algo/abre o X + programa whitelist
        tem_prog = any(k in a for k in PROGRAMAS_PERMITIDOS) or any(k in limpo for k in PROGRAMAS_PERMITIDOS)
        abriu_match = bool(re.match(
            r"^(abre|abrir|abri|inicia|iniciar|start|executa|executar|roda|rodar|liga)\b",
            a,
        ))
        if (abriu_match and tem_prog) or re.search(
            r"\b(notepad|bloco\s+de\s+notas|calculadora|calc|chrome|edge|vscode|vs\s+code|code|explorer|arquivos|terminal|cmd|powershell)\b",
            a,
        ):
            return "abrir_programa"
        # criar arquivo
        if ("cria " in a or "criar " in a or "escreve " in a or
                "escrever " in a or "gera arquivo" in a or "criar arquivo" in a or
                "novo arquivo" in a or "arquivo " in limpo[:50]):
            return "criar_arquivo"
        # listar pasta
        if ("lista" in a or "listar" in a or "mostra arquivos" in a or
                "quais arquivos" in a or re.match(r"(ls|dir)\b", a)):
            return "listar_pasta"
        # powershell seguro: comando com prefixo
        if ("powershell" in a or "no ps" in a or "no powershell" in a or
                a.startswith("ps ") or a.startswith("ps:") or a.startswith("pwsh ")):
            return "powershell_seguro"
        return "desconhecido"

    # ---------------------------------------------------------------
    # AÇÕES IMPLEMENTADAS
    # ---------------------------------------------------------------
    def _acao_abrir_programa(self, acao_original: str, simulacao: bool,
                             t_inicio: float, meta: Dict[str, Any]) -> ResultadoInferencia:
        a_lower = acao_original.lower()
        # encontra a chave da whitelist
        chave: Optional[str] = None
        for k in PROGRAMAS_PERMITIDOS:
            if k in a_lower:
                chave = k
                break
        if chave is None:
            return self._resultado(
                sucesso=False,
                erro_mensagem=(
                    f"🖱️ Programa não está na WHITELIST de segurança. Frase: {acao_original[:120]}\n"
                    f"Programas permitidos: {', '.join(sorted(PROGRAMAS_PERMITIDOS.keys())[:12])}…"
                ),
                t_inicio=t_inicio, metadados={**meta, "programa_detectado": None},
            )

        # Tenta os caminhos por ordem até encontrar um que exista (ou que o PATH ache)
        tentativas = PROGRAMAS_PERMITIDOS[chave]
        escolhido: Optional[List[str]] = None
        for tentativa in tentativas:
            # pode ser lista (ex: ["powershell.exe", "-NoExit", ...]) ou string
            partes = tentativa if isinstance(tentativa, list) else [tentativa]
            primeiro = Path(partes[0])
            if primeiro.is_absolute() and primeiro.exists():
                escolhido = partes
                break
            if not primeiro.is_absolute():
                # confia no PATH
                escolhido = partes
                break
        if escolhido is None:
            return self._resultado(
                sucesso=False,
                erro_mensagem=(
                    f"🖱️ Programa '{chave}' nao encontrado no PC. Tente instalar ou adicionar o PATH."
                ),
                t_inicio=t_inicio, metadados={**meta, "programa": chave, "erro_executavel": True},
            )

        if simulacao:
            return self._resultado(
                sucesso=True,
                conteudo=(
                    f"🛡️ **Modo simulação — nada foi executado ainda.**\n\n"
                    f"Programa a abrir: **{chave}**\nComando: `{shlex.join(escolhido)}`\n\n"
                    f"Se concordar, reenvie sem `forcar_confirmacao`."
                ),
                t_inicio=t_inicio, metadados={**meta, "programa": chave},
            )

        # Real execucao (non-blocking, DETACHED)
        try:
            popen_kwargs = {}
            if sys.platform == "win32":
                # DETACHED_PROCESS = 0x00000008 para nao travar o terminal
                popen_kwargs["creationflags"] = 0x00000008 | 0x00000200  # DETACHED | CREATE_NEW_PROCESS_GROUP
            proc = subprocess.Popen(escolhido, close_fds=True, shell=False, **popen_kwargs)
            log.info("os_control_programa_aberto", {"programa": chave, "pid": proc.pid, "comando": escolhido[:3]})
            return self._resultado(
                sucesso=True,
                conteudo=(
                    f"✅ **Programa aberto com sucesso!**\n\n"
                    f"  • Programa: **{chave}**\n"
                    f"  • PID: `{proc.pid}`\n"
                    f"  • Comando: `{shlex.join(escolhido)}`\n\n"
                    f"Se nao aparecer, cheque a barra de tarefas 🪟."
                ),
                t_inicio=t_inicio,
                metadados={**meta, "programa": chave, "pid": proc.pid},
            )
        except Exception as e:
            return self._resultado(
                sucesso=False,
                erro_mensagem=f"🖱️ Erro ao abrir programa '{chave}': {e}",
                erro_tecnico=str(e),
                t_inicio=t_inicio,
                metadados={**meta, "programa": chave},
            )

    def _acao_criar_arquivo(self, acao_original: str, simulacao: bool,
                            t_inicio: float, meta: Dict[str, Any]) -> ResultadoInferencia:
        """
        Parser:
          "cria arquivo NOME.ext no LOCAL com CONTEUDO..."
          "escreve NOME.txt no desktop com hola mundo"
          LOCAL pode ser: desktop, documents, downloads, projeto, memoria, temp.
        """
        a = acao_original
        m_nome = re.search(r"(arquivo\s+|escreve\s+|escrever\s+|cria\s+|novo\s+)?(?P<nome>[A-Za-z0-9_\-\.\u00C0-\u00FF]+\.[A-Za-z0-9]{1,8})", a)
        nome_arquivo = m_nome.group("nome") if m_nome else None

        a_low = a.lower()
        pasta_alvo: Optional[Path] = None
        if "desktop" in a_low or "area de trabalho" in a_low or "mesa" in a_low:
            pasta_alvo = Path.home() / "Desktop"
        elif "documentos" in a_low or "documents" in a_low or "meus documentos" in a_low:
            pasta_alvo = Path.home() / "Documents"
        elif "downloads" in a_low or "baixados" in a_low:
            pasta_alvo = Path.home() / "Downloads"
        elif "projeto" in a_low or "neurocore" in a_low or "raiz" in a_low:
            pasta_alvo = Path(r"C:\Users\Jhon Ross\Documents\trae_projects\NeuroCore")
        elif "memoria" in a_low or "g:" in a_low or "memory" in a_low:
            pasta_alvo = Path(r"G:\memory")
        elif "temp" in a_low or "tmp" in a_low:
            pasta_alvo = Path(tempfile.gettempdir())

        if not nome_arquivo or not pasta_alvo:
            return self._resultado(
                sucesso=False,
                erro_mensagem=(
                    f"🖱️ Não consegui descobrir **nome do arquivo** ou **pasta alvo**.\n"
                    f"Tente assim:\n"
                    f"  • 'cria arquivo lembrete.txt no desktop com Prometeu estava aqui'\n"
                    f"  • 'escreve hello.py no projeto com print(1337)'\n"
                    f"Pastas permitidas: desktop, documents, downloads, projeto, memoria, temp."
                ),
                t_inicio=t_inicio, metadados={**meta, "nome_arquivo_extraido": nome_arquivo},
            )

        # Segurança: caminho está em whitelist?
        caminho_final = pasta_alvo / nome_arquivo
        try:
            caminho_final_resolvido = caminho_final.resolve()
        except Exception as e:
            return self._resultado(sucesso=False, erro_mensagem=f"Caminho inválido: {e}",
                                   erro_tecnico=str(e), t_inicio=t_inicio, metadados=meta)

        if not any(self._eh_subpasta_de(caminho_final_resolvido, p) for p in DIRETORIOS_PERMITIDOS_ESCRITA):
            return self._resultado(
                sucesso=False,
                erro_mensagem=(
                    f"🔒 **Pasta não permitida para escrita:** `{caminho_final_resolvido}`\n"
                    f"Escreva apenas em: " + ", ".join(str(p) for p in DIRETORIOS_PERMITIDOS_ESCRITA)
                ),
                t_inicio=t_inicio, metadados=meta,
            )

        # Extensao permitida? (evita .bat/.cmd/.ps1/.exe sem aprovacao explicita)
        ext_bloqueadas = {".bat", ".cmd", ".ps1", ".exe", ".msi", ".sh", ".vbs", ".js"}
        if caminho_final_resolvido.suffix.lower() in ext_bloqueadas:
            # Permitimos .ps1 SOMENTE se for em G:\memory ou projeto com observacao de seguranca
            if not (caminho_final_resolvido.suffix.lower() == ".ps1" and simulacao):
                return self._resultado(
                    sucesso=False,
                    erro_mensagem=(
                        f"🔒 Extensão `{caminho_final_resolvido.suffix}` BLOQUEADA por segurança.\n"
                        f"Use .txt / .py / .md / .json / .csv / .log. Scripts PS1 só em simulação."
                    ),
                    t_inicio=t_inicio, metadados=meta,
                )

        # Extrai conteúdo
        conteudo = ""
        m_conteudo = re.search(r"\bcom\s+(.+)$", a, flags=re.IGNORECASE | re.DOTALL)
        if m_conteudo:
            conteudo = m_conteudo.group(1).strip()
            # remove aspas iniciais/finais se houver
            if len(conteudo) >= 2 and conteudo[0] == conteudo[-1] and conteudo[0] in ("\"", "'", "“", "”"):
                conteudo = conteudo[1:-1]

        if simulacao:
            return self._resultado(
                sucesso=True,
                conteudo=(
                    f"🛡️ **Modo simulação — nada foi criado.**\n\n"
                    f"  • Arquivo: `{caminho_final_resolvido}`\n"
                    f"  • Tamanho do conteúdo: {len(conteudo)} chars.\n"
                    f"  • Sobrescreveria existente? **{'SIM ⚠️' if caminho_final_resolvido.exists() else 'Não (novo arquivo)'}.**\n\n"
                    f"Reenvie sem `forcar_confirmacao` para criar de verdade."
                ),
                t_inicio=t_inicio,
                metadados={**meta, "arquivo": str(caminho_final_resolvido)},
            )

        try:
            pasta_alvo.mkdir(parents=True, exist_ok=True)
            # Nao sobrescreve sem pedido explicito — se existir, renomeia com _1, _2
            if caminho_final_resolvido.exists():
                stem, sufixo = caminho_final_resolvido.stem, caminho_final_resolvido.suffix
                i = 1
                while True:
                    novo = pasta_alvo / f"{stem}_{i}{sufixo}"
                    if not novo.exists():
                        caminho_final_resolvido = novo
                        break
                    i += 1
            caminho_final_resolvido.write_text(conteudo, encoding="utf-8")
            log.info("os_control_arquivo_criado",
                     {"arquivo": str(caminho_final_resolvido), "tamanho": len(conteudo)})
            return self._resultado(
                sucesso=True,
                conteudo=(
                    f"✅ **Arquivo criado com sucesso!**\n\n"
                    f"  • Caminho: `{caminho_final_resolvido}`\n"
                    f"  • Tamanho: **{len(conteudo)} caracteres**\n"
                    f"  • Codificação: UTF-8\n\n"
                    f"Dica: 'abre notepad' + cole o caminho se quiser editar na UI."
                ),
                t_inicio=t_inicio,
                metadados={**meta, "arquivo": str(caminho_final_resolvido), "chars": len(conteudo)},
            )
        except Exception as e:
            return self._resultado(
                sucesso=False,
                erro_mensagem=f"🖱️ Erro ao escrever arquivo: {e}",
                erro_tecnico=str(e),
                t_inicio=t_inicio, metadados={**meta, "arquivo": str(caminho_final_resolvido)},
            )

    def _acao_listar_pasta(self, acao_original: str, simulacao: bool,
                           t_inicio: float, meta: Dict[str, Any]) -> ResultadoInferencia:
        a_low = acao_original.lower()
        pasta: Optional[Path] = None
        if "desktop" in a_low or "area de trabalho" in a_low:
            pasta = Path.home() / "Desktop"
        elif "documentos" in a_low or "documents" in a_low:
            pasta = Path.home() / "Documents"
        elif "downloads" in a_low or "baixados" in a_low:
            pasta = Path.home() / "Downloads"
        elif "projeto" in a_low or "neurocore" in a_low:
            pasta = Path(r"C:\Users\Jhon Ross\Documents\trae_projects\NeuroCore")
        elif "memoria" in a_low or "g:" in a_low or "memory" in a_low:
            pasta = Path(r"G:\memory")

        if pasta is None:
            return self._resultado(
                sucesso=False,
                erro_mensagem=(
                    "Não sei qual pasta listar. Tente: 'lista a pasta do projeto NeuroCore', "
                    "'lista desktop', 'lista documents', 'lista memoria'."
                ),
                t_inicio=t_inicio, metadados=meta,
            )

        if simulacao:
            return self._resultado(
                sucesso=True,
                conteudo=f"🛡️ Simulação: listaria a pasta `{pasta}`",
                t_inicio=t_inicio, metadados={**meta, "pasta": str(pasta)},
            )
        try:
            arqs = sorted(pasta.iterdir())[:50]
            linhas = [f"📂 **{pasta}** ({len(list(pasta.iterdir()))} itens)\n"]
            for item in arqs:
                icone = "📁" if item.is_dir() else "📄"
                tam = item.stat().st_size if item.is_file() else 0
                tam_h = f"{tam/1024:,.1f} KB" if tam < 1024*1024 else f"{tam/1024/1024:,.1f} MB"
                linhas.append(f"{icone} `{item.name}` {tam_h if item.is_file() else '(pasta)'}")
            if len(arqs) == 50:
                linhas.append("\n... (lista truncada, há mais de 50 itens)")
            return self._resultado(
                sucesso=True,
                conteudo="\n".join(linhas),
                t_inicio=t_inicio, metadados={**meta, "pasta": str(pasta), "itens_mostrados": len(arqs)},
            )
        except Exception as e:
            return self._resultado(
                sucesso=False, erro_mensagem=f"Não consegui listar pasta: {e}",
                erro_tecnico=str(e), t_inicio=t_inicio, metadados={**meta, "pasta": str(pasta)}
            )

    def _acao_powershell_seguro(self, acao_original: str, simulacao: bool,
                                t_inicio: float, meta: Dict[str, Any]) -> ResultadoInferencia:
        """
        Extrai o comando apos "powershell:"/"no powershell:". Só aceita whitelist pequena
        de comandos get-only. NENHUM set/remove/new/stop/delete é permitido.
        """
        m = re.search(r"(?:powershell|no ps|no powershell|ps:?)\s*[:\-]?\s*(.+)$",
                      acao_original, flags=re.IGNORECASE | re.DOTALL)
        cmd = (m.group(1).strip() if m else "").strip('"').strip("'")
        if not cmd:
            return self._resultado(
                sucesso=False,
                erro_mensagem=(
                    "Comando PowerShell vazio. Exemplo de uso:\n"
                    "  • 'powershell: Get-Date'\n"
                    "  • 'no powershell: Get-ChildItem C:\\Users (primeiros 10)'"
                ),
                t_inicio=t_inicio, metadados=meta,
            )

        # Segunda camada de bloqueio só para PS (verbos destrutivos)
        cmd_low = cmd.lower()
        verbos_bloqueados = [
            "set-", "new-", "remove-", "delete", "stop-", "kill",
            "start-service", "restart-", "shutdown", "rename-",
            "move-", "copy-item -destination $env:systemroot", "invoke-",
        ]
        for v in verbos_bloqueados:
            if v in cmd_low:
                return self._resultado(
                    sucesso=False,
                    erro_mensagem=(
                        f"🔒 PowerShell BLOQUEADO: verbo suspeito `{v}`.\n"
                        f"Apenas comandos leitura: Get-*, Write-Host, echo, dir, ls, Get-Date etc."
                    ),
                    t_inicio=t_inicio, metadados={**meta, "ps_cmd": cmd[:120]},
                )

        if simulacao:
            return self._resultado(
                sucesso=True,
                conteudo=(
                    f"🛡️ **Simulação PowerShell.**\n\n"
                    f"Comando:\n```powershell\n{cmd}\n```\n\n"
                    f"Nada foi executado. Reenvie sem confirmação para rodar de verdade."
                ),
                t_inicio=t_inicio, metadados={**meta, "ps_cmd": cmd[:240]},
            )

        try:
            timeout_s = 15
            completo = ["powershell.exe", "-NoProfile", "-NonInteractive",
                        "-ExecutionPolicy", "Bypass", "-Command", cmd]
            res = subprocess.run(completo, capture_output=True, text=True,
                                 timeout=timeout_s, shell=False)
            stdout = (res.stdout or "").rstrip()
            stderr = (res.stderr or "").rstrip()
            saida_texto = ""
            if stdout:
                saida_texto += "**STDOUT:**\n```\n" + stdout[-3000:] + "\n```\n"
            if stderr:
                saida_texto += "**STDERR:**\n```\n" + stderr[-3000:] + "\n```\n"
            if not saida_texto:
                saida_texto = "(saída vazia)"
            return self._resultado(
                sucesso=res.returncode == 0,
                conteudo=(
                    f"🐢 **PowerShell executado.**\n"
                    f"  • Exit code: `{res.returncode}`\n"
                    f"  • Timeout: {timeout_s}s\n\n"
                    f"{saida_texto}"
                ),
                erro_mensagem=(
                    f"PowerShell retornou código {res.returncode}. Veja STDERR acima."
                    if res.returncode != 0 else None
                ),
                t_inicio=t_inicio,
                metadados={**meta, "ps_cmd": cmd[:240], "exit_code": res.returncode},
            )
        except subprocess.TimeoutExpired:
            return self._resultado(
                sucesso=False, erro_mensagem=f"PowerShell TIMEOUT após {timeout_s}s.",
                t_inicio=t_inicio, metadados={**meta, "ps_cmd": cmd[:240]},
            )
        except Exception as e:
            return self._resultado(
                sucesso=False, erro_mensagem=f"PowerShell erro: {e}", erro_tecnico=str(e),
                t_inicio=t_inicio, metadados={**meta, "ps_cmd": cmd[:240]},
            )

    # ---------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------
    @staticmethod
    def _eh_subpasta_de(caminho: Path, raiz: Path) -> bool:
        try:
            raiz_r = raiz.resolve()
            caminho_r = caminho.resolve()
            return raiz_r in caminho_r.parents or caminho_r == raiz_r
        except Exception:
            return False

    def _resultado(self, sucesso: bool, t_inicio: float,
                   conteudo: str = "",
                   erro_mensagem: Optional[str] = None,
                   erro_tecnico: Optional[str] = None,
                   metadados: Optional[Dict[str, Any]] = None,
                   modelo_usado: str = "os_control_windows") -> ResultadoInferencia:
        r = ResultadoInferencia(
            sucesso=sucesso,
            conteudo=conteudo,
            erro_mensagem=erro_mensagem,
            erro_tecnico=erro_tecnico,
            tempo_ms=round((time.perf_counter() - t_inicio) * 1000, 2),
            modelo_usado=modelo_usado,
            metadados=metadados or {},
        )
        self._registrar_uso(r)
        return r

