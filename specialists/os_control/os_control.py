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
# WHITELISTS PARA AS FERRAMENTAS DE LEITURA (Adicionado 30/09 Noite — Dia3)
# Nenhuma ferramenta de leitura toca em arquivos FORA destas regras.
# --------------------------------------------------------------------
# Diretórios PERMITIDOS PARA LEITURA (igual escrita + não destrutivos)
DIRETORIOS_PERMITIDOS_LEITURA: List[Path] = [
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path(r"C:\Users\Jhon Ross\Documents\trae_projects\NeuroCore"),
    Path(r"G:\memory"),
    Path(r"G:\models"),  # permite ler metadata dos modelos baixados
    Path(tempfile.gettempdir()),
]

# Extensões de ARQUIVOS DE TEXTO permitidos para ler (evita ler binários / secrets)
EXTENSOES_TEXTO_PERMITIDAS: set[str] = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".toml", ".json",
    ".md", ".txt", ".log", ".jsonl", ".csv", ".yaml", ".yml",
    ".ini", ".cfg", ".conf", ".env.example", ".ps1", ".bat",
    ".html", ".css", ".sql", ".c", ".h", ".sh",
}

# Extensões BLOQUEADAS MESMO EM LEITURA (contêm senhas / segredos normalmente)
EXTENSOES_BLOQUEADAS_LEITURA: set[str] = {
    ".env", ".p12", ".pem", ".key", ".crt", ".pfx", ".keystore",
    ".zip", ".rar", ".7z", ".exe", ".dll", ".bin", ".dat",
}

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

            # 2. Detectar tipo de ação: abrir_programa | criar_arquivo | listar_pasta |
            #    ler_arquivo_texto | listar_pasta_avancado | pesquisar_palavra | powershell_seguro
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
            if tipo == "ler_arquivo_texto":
                return self._acao_ler_arquivo_texto(acao_original, modo_simulacao, t_inicio, metadados)
            if tipo == "listar_pasta_avancado":
                return self._acao_listar_pasta_avancado(acao_original, modo_simulacao, t_inicio, metadados)
            if tipo == "pesquisar_palavra":
                return self._acao_pesquisar_palavra_em_pasta(acao_original, modo_simulacao, t_inicio, metadados)
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
            r"^(ei\s+|prometeu[,.:\s]*|por favor[,.:\s]*|por gentileza[,.:\s]*|pra mim[,.:\s]*|pfv[,.:\s]*|pls[,.:\s]*|sff[,.:\s]|poderia[s]?\s+|quero\s+que\s+(você|voce|vc)\s+|quero\s+|me\s+(dá|da|faz|fazer|abre|abrir|mostra|explica|diz|conta|pesquisa|procura|encontra)\s+)",
            "",
            a,
        ).strip()

        # ---- PRIORIDADE 0: LEITURA DE ARQUIVO (ex: "lê core/api.py", "explica o arquivo orchestrator.py") ----
        tem_ler = bool(re.search(
            r"\b(lê|leia|ler|leia\s+o\s+arquivo|mostra\s+o\s+arquivo|abre\s+o\s+arquivo|exibe\s+o\s+conteudo|visualiza\s+o\s+arquivo|qual\s+o\s+conteudo)\b",
            a,
        ))
        if tem_ler:
            return "ler_arquivo_texto"
        if (".py" in a or ".md" in a or ".ts" in a or ".tsx" in a or ".rs" in a or
                ".json" in a or ".txt" in a or ".log" in a or ".csv" in a or ".toml" in a or ".yaml" in a or ".yml" in a):
            # Se mencionou caminho/extensao de arquivo mas NÃO pediu criar (criar já foi checado acima?)
            if not ("cria" in a or "criar" in a or "escreve" in a or "escrever" in a or "novo arquivo" in a):
                # Se tem verbo de leitura / explicar / analisar
                if re.search(r"\b(explica|analisa|revis|mostra|diz|lê|ler|abre|visualiza|qual)\b", a):
                    return "ler_arquivo_texto"

        # ---- PRIORIDADE 1: PESQUISA DE PALAVRA EM PASTA (ex: "procura deadlock nos arquivos de core") ----
        if re.search(
            r"\b(procura|pesquisa|busca|encontra|grep|achar|procure|pesquise|busque|encontre)\b",
            a,
        ):
            return "pesquisar_palavra"

        # ---- PRIORIDADE 2: LISTAR PASTA AVANÇADO (filtro ext / ordenar / árvore) ----
        if ("lista" in a or "listar" in a or "mostra arquivos" in a or "quais arquivos" in a):
            if any(k in a for k in [".py", "só python", "apenas python", "arquivos python",
                                     ".md", "markdown", "ordenado por data", "ordena por data",
                                     "árvore", "arvore", "tree", "2 níveis", "2 niveis"]):
                return "listar_pasta_avancado"

        # Se contiver termos explícitos de programação SEM abrir executavel, NÃO é comando de abrir executável
        if any(k in a for k in ["python", "código", "codigo", "função", "funcao", "script", "desenvolva", "algoritmo"]):
            return "desconhecido"

        # abrir programa: exige verbo de ação explícito + nome do programa da whitelist
        tem_prog = any(k in a for k in PROGRAMAS_PERMITIDOS) or any(k in limpo for k in PROGRAMAS_PERMITIDOS)
        abriu_match = bool(re.search(
            r"\b(abre|abrir|abri|inicia|iniciar|start|executa|executar|roda|rodar|liga)\b",
            a,
        ))
        if abriu_match and tem_prog:
            return "abrir_programa"
        # criar arquivo
        if ("cria " in a or "criar " in a or "escreve " in a or
                "escrever " in a or "gera arquivo" in a or "criar arquivo" in a or
                "novo arquivo" in a or "arquivo " in limpo[:50]):
            return "criar_arquivo"
        # listar pasta (simples)
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

    # =====================================================================
    # NOVAS AÇÕES (30/09 Noite — Dia3 Oficial): Leitura e Pesquisa Arquivos
    # Segurança: whitelist de PASTAS + EXTENSÕES; nenhum env/env/.pem é lido
    # =====================================================================

    # ----------------------------- ler_arquivo_texto -----------------------------
    def _acao_ler_arquivo_texto(self, acao: str, simulacao: bool, t_inicio: float,
                                meta: Dict[str, Any]) -> ResultadoInferencia:
        """Lê um arquivo texto do projeto/Docs/Memory. Tudo whitelist."""
        meta = {**meta, "tipo": "ler_arquivo_texto"}

        # 1. Extrai o caminho do arquivo
        caminho_raw = self._extrair_caminho_arquivo(acao, acao_tipo="leitura")
        if not caminho_raw:
            # Tenta heurística simples: pega último token com . ext permitida
            for tok in acao.split():
                tok_limpo = tok.strip('"').strip("'").strip(",")
                ext = Path(tok_limpo).suffix.lower()
                if ext in EXTENSOES_TEXTO_PERMITIDAS:
                    caminho_raw = tok_limpo
                    break
        if not caminho_raw:
            return self._resultado(
                sucesso=False,
                erro_mensagem=(
                    "Não consegui identificar qual arquivo você quer que eu leia.\n"
                    "Tente: `lê o arquivo core/api.py` ou `mostra docs/03 - Diario.md`."
                ),
                t_inicio=t_inicio, metadados={**meta, "heuristica": "falhou_extrair_caminho"},
            )

        # 2. Parse Path + Whitelist pasta
        try:
            caminho = Path(caminho_raw)
            if not caminho.is_absolute():
                caminho = Path(__file__).resolve().parents[2] / caminho
            caminho = caminho.resolve()
        except Exception as e:
            return self._resultado(
                sucesso=False, erro_mensagem=f"Caminho inválido: `{caminho_raw}` ({e})",
                t_inicio=t_inicio, metadados={**meta, "caminho_raw": caminho_raw},
            )

        if not any(self._eh_subpasta_de(caminho, raiz) for raiz in DIRETORIOS_PERMITIDOS_LEITURA):
            return self._resultado(
                sucesso=False,
                erro_mensagem=(
                    "📁 CAMINHO BLOQUEADO POR SEGURANÇA (fora da whitelist de leitura).\n"
                    f"Pastas permitidas: {', '.join(str(p) for p in DIRETORIOS_PERMITIDOS_LEITURA)}."
                ),
                t_inicio=t_inicio, metadados={**meta, "caminho": str(caminho)},
            )

        # 3. Whitelist extensão texto (bloqueia .env/.bin/.exe/.key)
        ext = caminho.suffix.lower()
        if ext in EXTENSOES_BLOQUEADAS_LEITURA:
            return self._resultado(
                sucesso=False,
                erro_mensagem=(
                    f"🔒 EXTENSÃO {ext} BLOQUEADA POR SEGURANÇA (contém potencialmente segredos/binários).\n"
                    "Permitidas: .py .md .ts .tsx .rs .toml .json .txt .log .csv .yaml .yml etc."
                ),
                t_inicio=t_inicio, metadados={**meta, "ext": ext},
            )
        if ext not in EXTENSOES_TEXTO_PERMITIDAS:
            return self._resultado(
                sucesso=False,
                erro_mensagem=(
                    f"⚠️ Extensão {ext} não está na whitelist de texto permitido.\n"
                    f"Permitidas: {sorted(EXTENSOES_TEXTO_PERMITIDAS)}"
                ),
                t_inicio=t_inicio, metadados={**meta, "ext": ext},
            )

        # 4. Verifica existência e tamanho (max 100KB — evita travar com logs gigantes)
        if not caminho.is_file():
            return self._resultado(
                sucesso=False, erro_mensagem=f"Arquivo não encontrado: `{caminho}`",
                t_inicio=t_inicio, metadados={**meta, "caminho": str(caminho)},
            )
        try:
            tamanho_bytes = caminho.stat().st_size
        except OSError as e:
            return self._resultado(
                sucesso=False, erro_mensagem=f"Sem permissão para ler: `{caminho}` ({e})",
                t_inicio=t_inicio, metadados={**meta, "caminho": str(caminho)},
            )
        TAMANHO_MAX_BYTES = 100 * 1024  # 100 KB
        LINHAS_MAX_DEFAULT = 200
        if tamanho_bytes > TAMANHO_MAX_BYTES:
            return self._resultado(
                sucesso=False,
                erro_mensagem=(
                    f"Arquivo muito grande: {tamanho_bytes/1024:.1f} KB > limite 100KB.\n"
                    "Use: `lê as linhas 100 a 300 de core/api.py` para pedir em pedaços."
                ),
                t_inicio=t_inicio, metadados={**meta, "caminho": str(caminho), "tamanho": tamanho_bytes},
            )

        # 5. Extrai range de linhas (se tiver "de 10 a 50")
        m_linhas = re.search(r"linhas?\s*(\d+)\s*(?:a\s*(\d+)|até\s*(\d+))?", acao.lower())
        linhas_de = 1
        linhas_ate = LINHAS_MAX_DEFAULT
        if m_linhas:
            try:
                linhas_de = max(1, int(m_linhas.group(1)))
                ate = m_linhas.group(2) or m_linhas.group(3)
                linhas_ate = int(ate) if ate else linhas_de + LINHAS_MAX_DEFAULT
                if linhas_ate < linhas_de:
                    linhas_de, linhas_ate = linhas_ate, linhas_de
            except Exception:
                pass
        try:
            with open(caminho, "r", encoding="utf-8", errors="replace") as fh:
                todas_linhas = fh.readlines()
            total_linhas = len(todas_linhas)
            linhas_ate = min(linhas_ate, total_linhas)
            linhas_selecionadas = todas_linhas[linhas_de - 1: linhas_ate]
            qtd_lida = len(linhas_selecionadas)
            conteudo_lido = "".join(linhas_selecionadas)
        except Exception as e:
            return self._resultado(
                sucesso=False, erro_mensagem=f"Erro ao ler arquivo: {e}", erro_tecnico=str(e),
                t_inicio=t_inicio, metadados={**meta, "caminho": str(caminho)},
            )

        # 6. Monta resposta formatada (com números de linha)
        linhas_numeradas = []
        for idx, linha in enumerate(linhas_selecionadas, start=linhas_de):
            linhas_numeradas.append(f"{idx:>4} | {linha.rstrip()}")
        bloco = "\n".join(linhas_numeradas)
        cabecalho = (
            f"✅ Leitura concluída. Arquivo: `{caminho}`\n"
            f"   · Tamanho: {tamanho_bytes} bytes — Total de linhas: {total_linhas}\n"
            f"   · Exibindo: L{linhas_de} a L{linhas_ate} ({qtd_lida} linhas)\n"
            f"   · Segurança: Whitelist pastas + Whitelist extensões OK\n"
            f"```\n"
        )
        rodape = "\n```\n"
        if total_linhas > linhas_ate:
            rodape += (
                f"\nℹ️ Arquivo tem mais {total_linhas - linhas_ate} linhas depois. "
                f"Peça: `continua da linha {linhas_ate+1} até {linhas_ate+200}`."
            )
        return self._resultado(
            sucesso=True, conteudo=cabecalho + bloco + rodape,
            t_inicio=t_inicio,
            metadados={
                **meta, "caminho": str(caminho),
                "total_linhas": total_linhas, "linhas_exibidas": qtd_lida,
                "linha_inicio": linhas_de, "linha_fim": linhas_ate,
                "tamanho_bytes": tamanho_bytes, "ext": ext,
            },
        )

    # -------------------------- listar_pasta_avancado --------------------------
    def _acao_listar_pasta_avancado(self, acao: str, simulacao: bool, t_inicio: float,
                                    meta: Dict[str, Any]) -> ResultadoInferencia:
        """Lista pasta avançada: filtro por extensão (.py), ordena por data, árvore 2 níveis."""
        meta = {**meta, "tipo": "listar_pasta_avancado"}
        caminho_raw = self._extrair_caminho_arquivo(acao, acao_tipo="listar") or \
                      str(Path(__file__).resolve().parents[2])
        try:
            caminho = Path(caminho_raw)
            if not caminho.is_absolute():
                caminho = Path(__file__).resolve().parents[2] / caminho
            caminho = caminho.resolve()
        except Exception as e:
            return self._resultado(
                sucesso=False, erro_mensagem=f"Caminho inválido: `{caminho_raw}` ({e})",
                t_inicio=t_inicio, metadados={**meta, "caminho_raw": caminho_raw},
            )
        if not any(self._eh_subpasta_de(caminho, raiz) for raiz in DIRETORIOS_PERMITIDOS_LEITURA):
            return self._resultado(
                sucesso=False,
                erro_mensagem="📁 CAMINHO BLOQUEADO POR SEGURANÇA (fora whitelist leitura).",
                t_inicio=t_inicio, metadados={**meta, "caminho": str(caminho)},
            )
        if not caminho.is_dir():
            return self._resultado(
                sucesso=False, erro_mensagem=f"Não é uma pasta: `{caminho}`",
                t_inicio=t_inicio, metadados={**meta, "caminho": str(caminho)},
            )

        # Parse filtros do pedido
        filtro_ext = None
        a_lower = acao.lower()
        if ".py" in a_lower or "só python" in a_lower or "arquivos python" in a_lower:
            filtro_ext = ".py"
        elif ".md" in a_lower or "markdown" in a_lower:
            filtro_ext = ".md"
        elif ".tsx" in a_lower:
            filtro_ext = ".tsx"
        elif ".ts" in a_lower:
            filtro_ext = ".ts"
        elif ".rs" in a_lower:
            filtro_ext = ".rs"

        ordenar_por_data = ("ordena" in a_lower or "ordenado" in a_lower or "data" in a_lower)
        arvore = ("árvore" in a_lower or "arvore" in a_lower or "tree" in a_lower or "níveis" in a_lower or "niveis" in a_lower)
        MAX_ITENS_POR_NIVEL = 100
        MAX_NIVEIS_ARVORE = 2 if arvore else 1

        try:
            itens: List[Dict[str, Any]] = []

            def _varrer(p: Path, nivel: int = 0):
                if nivel > MAX_NIVEIS_ARVORE:
                    return
                with os.scandir(p) as it:
                    for entry in sorted(it, key=lambda e: (e.is_dir(), e.name.lower())):
                        if len(itens) >= MAX_ITENS_POR_NIVEL * (MAX_NIVEIS_ARVORE + 1):
                            return
                        ext_e = os.path.splitext(entry.name)[1].lower()
                        if filtro_ext and entry.is_file() and ext_e != filtro_ext:
                            continue
                        try:
                            st = entry.stat()
                            size_kb = round(st.st_size / 1024, 2) if entry.is_file() else None
                            mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))
                        except OSError:
                            size_kb = None
                            mtime = "?"
                        itens.append({
                            "nome": entry.name,
                            "is_dir": entry.is_dir(),
                            "tamanho_kb": size_kb,
                            "mtime": mtime,
                            "nivel": nivel,
                            "caminho": entry.path,
                        })
                        if entry.is_dir() and nivel < MAX_NIVEIS_ARVORE:
                            _varrer(Path(entry.path), nivel + 1)
            _varrer(caminho)
        except OSError as e:
            return self._resultado(
                sucesso=False, erro_mensagem=f"Sem permissão para listar: {e}",
                t_inicio=t_inicio, metadados={**meta, "caminho": str(caminho)},
            )

        if ordenar_por_data:
            itens.sort(key=lambda x: (x["is_dir"], x["mtime"]), reverse=True)

        # Formata saída em árvore ou tabela
        saida_linhas = [
            f"✅ Listagem avançada de: `{caminho}`",
            f"   · Itens encontrados: {len(itens)}"
            + (f" — Filtro: **{filtro_ext}**" if filtro_ext else " — Filtro: nenhum")
            + (f" — Ordenado por **data modificação**" if ordenar_por_data else "")
            + (f" — Modo **árvore {MAX_NIVEIS_ARVORE} níveis**" if arvore else " — Modo lista plana"),
            "",
        ]
        prefixos = ["", "  └─ ", "    └─ "]
        for item in itens:
            icon = "📁" if item["is_dir"] else "📄"
            tam = (
                " dir" if item["is_dir"]
                else (f"{item['tamanho_kb']:>6.1f} KB" if item["tamanho_kb"] is not None else "      ? ")
            )
            prefixo = prefixos[min(item["nivel"], len(prefixos) - 1)]
            saida_linhas.append(
                f"  {prefixo}{icon} [{item['mtime']}] {tam:<10}  {item['nome']}"
            )
        if len(itens) >= MAX_ITENS_POR_NIVEL * (MAX_NIVEIS_ARVORE + 1) - 10:
            saida_linhas.append(
                f"\nℹ️  Limite de {MAX_ITENS_POR_NIVEL * (MAX_NIVEIS_ARVORE + 1)} itens atingido. "
                "Peça uma subpasta específica para ver mais."
            )
        return self._resultado(
            sucesso=True, conteudo="\n".join(saida_linhas),
            t_inicio=t_inicio,
            metadados={
                **meta, "caminho": str(caminho), "itens": len(itens),
                "filtro_ext": filtro_ext, "ordenar_por_data": ordenar_por_data, "arvore": arvore,
            },
        )

    # ---------------------- pesquisar_palavra_em_pasta ----------------------
    def _acao_pesquisar_palavra_em_pasta(self, acao: str, simulacao: bool, t_inicio: float,
                                         meta: Dict[str, Any]) -> ResultadoInferencia:
        """Pesquisa string/regex (case-insensitive) em arquivos permitidos. Nada de .env."""
        meta = {**meta, "tipo": "pesquisar_palavra"}
        # Extrai termo entre aspas ou primeiro token entre verbos
        termo = None
        m_aspas = re.search(r'["\']([^"\']{1,100})["\']', acao)
        if m_aspas:
            termo = m_aspas.group(1)
        else:
            # heurística: remove "procura|pesquisa|busca|por|em|nos arquivos|de"
            tokens = re.sub(
                r"\b(procura|pesquisa|busca|encontra|achar|procure|pesquise|busque|encontre|por|nos?|arquivos?|na|no|pasta|pastas|do|da|de|eu)\b",
                " ",
                acao.lower(),
            ).split()
            tokens = [t for t in tokens if t and len(t) >= 3 and t not in {"o", "a", "os", "as"}]
            if tokens:
                termo = tokens[0]
        if not termo or len(termo) < 2:
            return self._resultado(
                sucesso=False,
                erro_mensagem=(
                    "Não identifiquei o termo para pesquisar. "
                    "Tente: `pesquisa deadlock nos arquivos do core` ou `procura \"erro_mensagem\"`."
                ),
                t_inicio=t_inicio, metadados={**meta, "termo_heuristica": termo},
            )

        # Pastas a pesquisar (heurística: menciona "core" / "docs" / "G:\memory" etc?)
        pastas_alvo: List[Path] = [Path(__file__).resolve().parents[2] / "core",
                                   Path(__file__).resolve().parents[2] / "specialists",
                                   Path(__file__).resolve().parents[2] / "docs"]
        # se usuário mencionar "docs" / "projeto inteiro" / "frontend"
        a_lower = acao.lower()
        if "tudo" in a_lower or "inteiro" in a_lower or "projeto" in a_lower or "todos" in a_lower:
            pastas_alvo = [Path(__file__).resolve().parents[2]]  # raiz projeto
        elif "docs" in a_lower or "documentos" in a_lower or "obsidian" in a_lower:
            pastas_alvo = [Path(__file__).resolve().parents[2] / "docs"]
        elif "frontend" in a_lower:
            pastas_alvo = [Path(__file__).resolve().parents[2] / "frontend" / "src"]
        elif "memory" in a_lower or "memória" in a_lower or "memoria" in a_lower:
            pastas_alvo = [Path(r"G:\memory"),
                           Path(__file__).resolve().parents[2] / "local_memory"]

        # Filtro extensão: se mencionar "py" / "md"
        filtro_ext_pesq: Optional[str] = None
        if " arquivo python" in a_lower or " arquivos py" in a_lower or " .py " in a_lower:
            filtro_ext_pesq = ".py"
        elif " .md " in a_lower or "markdown" in a_lower:
            filtro_ext_pesq = ".md"
        elif "tsx" in a_lower:
            filtro_ext_pesq = ".tsx"
        elif "frontend" in a_lower:
            filtro_ext_pesq = ".tsx"

        MAX_ARQUIVOS_VARRIDOS = 500
        MAX_OCORRENCIAS = 100
        MAX_LINHAS_RESULTADO = 60
        ocorrencias: List[Dict[str, Any]] = []
        arquivos_varridos = 0
        arquivos_pulados_seguranca = 0
        try:
            termo_regex = re.compile(re.escape(termo), re.IGNORECASE)
            for raiz in pastas_alvo:
                if not raiz.exists() or not raiz.is_dir():
                    continue
                for root, dirs, files in os.walk(raiz):
                    if arquivos_varridos >= MAX_ARQUIVOS_VARRIDOS or len(ocorrencias) >= MAX_OCORRENCIAS:
                        break
                    # Pula .git, node_modules (não temos node_modules mas defeso)
                    dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules", ".venv", "dist", "build"}]
                    for nome_arquivo in files:
                        if arquivos_varridos >= MAX_ARQUIVOS_VARRIDOS or len(ocorrencias) >= MAX_OCORRENCIAS:
                            break
                        ext_a = os.path.splitext(nome_arquivo)[1].lower()
                        if ext_a in EXTENSOES_BLOQUEADAS_LEITURA:
                            arquivos_pulados_seguranca += 1
                            continue
                        if filtro_ext_pesq and ext_a != filtro_ext_pesq:
                            continue
                        if ext_a not in EXTENSOES_TEXTO_PERMITIDAS:
                            continue
                        caminho_arq = Path(root) / nome_arquivo
                        # Whitelist pasta (redundante mas segurança dobrada)
                        if not any(self._eh_subpasta_de(caminho_arq, r) for r in DIRETORIOS_PERMITIDOS_LEITURA):
                            arquivos_pulados_seguranca += 1
                            continue
                        arquivos_varridos += 1
                        try:
                            arq_tamanho = caminho_arq.stat().st_size
                            if arq_tamanho > 512 * 1024:  # > 512KB pula
                                continue
                            with open(caminho_arq, "r", encoding="utf-8", errors="replace") as fh:
                                for i, linha in enumerate(fh, start=1):
                                    if len(ocorrencias) >= MAX_OCORRENCIAS:
                                        break
                                    if termo_regex.search(linha):
                                        ocorrencias.append({
                                            "arquivo": str(caminho_arq),
                                            "arquivo_nome": nome_arquivo,
                                            "linha": i,
                                            "conteudo": linha.strip()[:160],
                                        })
                        except (OSError, UnicodeDecodeError):
                            continue
        except Exception as e:
            return self._resultado(
                sucesso=False, erro_mensagem=f"Pesquisa falhou: {e}", erro_tecnico=str(e),
                t_inicio=t_inicio, metadados={**meta, "termo": termo},
            )

        saida_linhas = [
            f"✅ Pesquisa concluída: `{termo}`",
            f"   · Pastas pesquisadas: {', '.join(str(p) for p in pastas_alvo if p.exists())}",
            f"   · Arquivos varridos: {arquivos_varridos}"
            + (f" — Filtro extensão: **{filtro_ext_pesq}**" if filtro_ext_pesq else "")
            + (f" — Arquivos pulados por segurança (whitelist): {arquivos_pulados_seguranca}"
               if arquivos_pulados_seguranca else ""),
            f"   · Ocorrências encontradas: **{len(ocorrencias)}** (máx {MAX_OCORRENCIAS})",
            "",
        ]
        if not ocorrencias:
            saida_linhas.append("ℹ️  Nenhuma ocorrência encontrada. Tente outro termo.")
        else:
            saida_linhas.append("Resultados:")
            exibidas = 0
            arquivo_anterior = None
            for o in ocorrencias:
                if exibidas >= MAX_LINHAS_RESULTADO:
                    break
                if arquivo_anterior != o["arquivo"]:
                    saida_linhas.append(f"\n📄 **{o['arquivo_nome']}** — `{o['arquivo']}`")
                    arquivo_anterior = o["arquivo"]
                saida_linhas.append(f"   · L{o['linha']:>4}:  `{o['conteudo']}`")
                exibidas += 1
            if len(ocorrencias) > MAX_LINHAS_RESULTADO:
                saida_linhas.append(
                    f"\nℹ️  Mais {len(ocorrencias) - MAX_LINHAS_RESULTADO} ocorrências. "
                    "Especifique pasta/extensão para refinar a busca."
                )

        return self._resultado(
            sucesso=True, conteudo="\n".join(saida_linhas),
            t_inicio=t_inicio,
            metadados={
                **meta, "termo": termo,
                "arquivos_varridos": arquivos_varridos,
                "ocorrencias": len(ocorrencias),
                "pastas_alvo": [str(p) for p in pastas_alvo],
                "filtro_ext": filtro_ext_pesq,
                "arquivos_pulados_seguranca": arquivos_pulados_seguranca,
            },
        )

    # ----------------------------- helper extrai caminho -----------------------------
    @staticmethod
    def _extrair_caminho_arquivo(acao: str, acao_tipo: str = "leitura") -> Optional[str]:
        """Extrai caminho arquivo/pasta de uma frase natural. Retorna None se não achar."""
        a = acao.strip()
        # 1. Aspas (duplas ou simples) — maior prioridade
        m = re.search(r'["\']([^"\']{1,500})["\']', a)
        if m:
            return m.group(1)
        # 2. Caminho absoluto Windows: C:\... ou G:\...
        m = re.search(r"([A-Za-z]:\\[^:\s\"'<>|?*]{1,400})", a)
        if m:
            return m.group(1)
        # 3. Caminho relativo: algo como core/api.py, docs/03.md, src/components/X.tsx
        m = re.search(
            r"([A-Za-z0-9_\-\.]+(?:[/\\][A-Za-z0-9_\-\. ]+){0,10}[/\\]?[A-Za-z0-9_\- ]+\.[A-Za-z0-9]{2,10})",
            a,
        )
        if m:
            return m.group(1)
        # 4. Para listar pastas: "pasta core" / "pasta G:\memory"
        if acao_tipo == "listar":
            m = re.search(r"pasta\s+(?:(?:do|da|de|dos|das)\s+)?([^\s,.;!?\"']{1,200})", a.lower())
            if m:
                nome = m.group(1).strip()
                # Mapear apelidos comuns
                apelidos = {
                    "projeto": str(Path(__file__).resolve().parents[2]),
                    "neurocore": str(Path(__file__).resolve().parents[2]),
                    "core": str(Path(__file__).resolve().parents[2] / "core"),
                    "docs": str(Path(__file__).resolve().parents[2] / "docs"),
                    "specialists": str(Path(__file__).resolve().parents[2] / "specialists"),
                    "frontend": str(Path(__file__).resolve().parents[2] / "frontend"),
                    "desktop": str(Path.home() / "Desktop"),
                    "documentos": str(Path.home() / "Documents"),
                    "memory": r"G:\memory",
                    "memória": r"G:\memory",
                    "memoria": r"G:\memory",
                    "models": r"G:\models",
                    "modelos": r"G:\models",
                }
                return apelidos.get(nome, nome)
        return None

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

