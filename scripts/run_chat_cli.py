# ============================================================================
# SCRIPT: run_chat_cli.py
# LOOP DE CONVERSA POR TEXTO NO TERMINAL COM O PROMETEU
#
# Como usar:
#   cd NeuroCore
#   .\.venv\Scripts\python.exe scripts\run_chat_cli.py
#
# O script usa o Orquestrador (LangGraph Core) e todo o resto da fundação.
# Não depende do Next.js estar ligado.
# ============================================================================

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

# Garante que importa o pacote do NeuroCore da raiz do projeto
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROJETO))

# Fallback para sandbox TRAE (força escrita no SSD C: se G:\ estiver bloqueado)
if __name__ == "__main__":
    if "FORCE_FALLBACK_MEMORY" not in os.environ:
        os.environ["FORCE_FALLBACK_MEMORY"] = "0"  # Jhon usa G:\, então 0 = nao fallbacka

from core.logger import log
from core.orchestrator import orchestrator, OrquestradorNeuroCore
from core.progress_rpg import rpg


# Cores ANSI para terminal (funciona no Windows Terminal / PowerShell)
COR = {
    "reset":   "\x1b[0m",
    "amber":   "\x1b[38;5;208m",   # Laranja Âmbar = Prometeu
    "branco":  "\x1b[38;5;15m",
    "cinza":   "\x1b[38;5;245m",
    "verde":   "\x1b[38;5;40m",
    "vermelho":"\x1b[38;5;196m",
    "azul":    "\x1b[38;5;39m",
}


def cabecalho() -> None:
    print(COR["amber"])
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║   🔥 PROMETEU — Cérebro de IA Local do Jhon Ross                    ║")
    print("║   NeuroCore · 7 regiões cerebrais · 100% local RX 7600              ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print(COR["reset"])

    rpg_ui = rpg.resumo_para_ui()
    print(
        f"  {COR['cinza']}Nível Global LVL "
        f"{COR['amber']}{rpg_ui['nivel_global']}{COR['reset']}  |  "
        f"{COR['cinza']}Feitos: {COR['verde']}{rpg_ui['total_feitos']}{COR['reset']}  |  "
        f"{COR['cinza']}XP Total: {COR['amber']}{rpg_ui['xp_global_total']}{COR['reset']}  |  "
        f"{COR['cinza']}Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}{COR['reset']}"
    )
    print()
    print(f"  {COR['cinza']}Comandos especiais: /sair  /rpg  /limpar  /sessoes  /ajuda{COR['reset']}")
    print(f"  {COR['cinza']}Qualquer outra coisa = mensagem para o Prometeu{COR['reset']}")
    print()


def ajuda() -> None:
    print()
    print(f"  {COR['azul']}📘 AJUDA DO CHAT CLI:{COR['reset']}")
    print(f"    /sair      → Encerra esta sessão (histórico fica salvo no SQLite)")
    print(f"    /rpg       → Painel completo do Sistema RPG Anti-Abandono")
    print(f"    /nova      → Cria uma SESSÃO NOVA (começa um chat do zero)")
    print(f"    /limpar    → Limpa apenas a tela, mantém sessão atual")
    print(f"    /sessoes   → Lista as últimas sessões salvas no banco")
    print(f"    /status    → Painel de Status do Cérebro Prometeu")
    print(f"    /ajuda     → Mostra esta ajuda de novo")
    print()


def painel_rpg() -> None:
    """Imprime o mesmo painel de progress_rpg.py __main__"""
    rpg_ui = rpg.resumo_para_ui()
    print()
    print(f"  {COR['amber']}{'='*66}{COR['reset']}")
    print(f"  🎮 SISTEMA RPG — Nível Global {COR['amber']}{rpg_ui['nivel_global']}{COR['reset']}  |  "
          f"🎖️  {COR['verde']}{rpg_ui['total_feitos']} Feitos{COR['reset']}  |  "
          f"✨ {COR['amber']}{rpg_ui['xp_global_total']} XP{COR['reset']}")
    print(f"  {COR['amber']}{'='*66}{COR['reset']}")
    for chave, d in rpg_ui["habilidades"].items():
        progresso = int(d["porcentagem_nivel"] // 5)
        barra = "█" * progresso + "░" * (20 - progresso)
        print(
            f"  {d['label']:<26} | "
            f"LVL {COR['amber']}{d['nivel_atual']:>3}{COR['reset']} | "
            f"{COR['verde']}{barra}{COR['reset']} | "
            f"{d['porcentagem_nivel']:>5}%"
        )
    print(f"  {'─'*66}")
    print(f"  {COR['cinza']}Últimos Feitos (Wall of Wins):{COR['reset']}")
    for f in rpg_ui["ultimos_feitos"]:
        print(
            f"    🎖️  [{f['id']:>3}] {f['data_iso'][:10]}  "
            f"{COR['amber']}{f['titulo'][:65]}{COR['reset']}  "
            f"(+{f['xp_concedido']}XP)"
        )
    print()


def listar_sessoes() -> None:
    from core.memory_manager import memoria
    sessoes = memoria.listar_sessoes(limite=10)
    print()
    print(f"  {COR['azul']}📒 ÚLTIMAS 10 SESSÕES SALVAS (SQLite ACID):{COR['reset']}")
    if not sessoes:
        print(f"  {COR['cinza']}(nenhuma sessão ainda){COR['reset']}")
    for s in sessoes:
        print(f"    [ID {s['id']:>4}]  {s['atualizado_em'][:16]}  ·  {s['titulo'][:70]}")
    print()


def status_orquestrador() -> None:
    p = orchestrator.obter_painel_status()
    print()
    print(f"  {COR['azul']}🧠 PAINEL DE STATUS — CÉREBRO PROMETEU{COR['reset']}")
    print(f"    Uptime: {p['uptime_segundos']:.0f}s | VRAM: {p['vram']['resumo']}")
    print(f"    Router: FORCE_LOCAL={p['router']['modo_force_local']} | "
          f"Teto R$={p['router']['teto_mensal_reais']:.2f}")
    print(f"    Especialistas carregados:")
    for nome, est in p["especialistas"].items():
        marca = "✅" if est["carregado"] else "⏸️"
        print(f"      {marca} {nome:<14} fase={est['fase_ativacao']} chamadas={est['estatisticas']['total_chamadas']}")
    print()


def main() -> None:
    """Loop principal do chat CLI."""
    cabecalho()
    ajuda()

    # Cria uma sessão nova ou continua a ultima? Vamos criar sessao nova sempre q iniciar CLI
    from core.memory_manager import memoria
    session_id = memoria.criar_sessao_chat(titulo=f"CLI {datetime.now().strftime('%d/%m %H:%M')}")
    print(f"  {COR['verde']}✅ Sessão {session_id} criada. Pode começar a conversar!{COR['reset']}")
    print()

    while True:
        try:
            prompt = input(f"  {COR['branco']}Jhon → {COR['reset']}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n\n  {COR['cinza']}Até mais! 👋 Sessão {session_id} salva.{COR['reset']}\n")
            break

        if not prompt:
            continue

        # --- Comandos especiais ---
        if prompt.startswith("/"):
            cmd = prompt.split()[0].lower()

            if cmd in ("/sair", "/exit", "/quit", "/q"):
                print(f"\n  {COR['cinza']}Até mais Prometeu! 👋 Sessão {session_id} persistida.{COR['reset']}\n")
                break

            elif cmd in ("/ajuda", "/help", "/?"):
                ajuda()
                continue

            elif cmd in ("/rpg", "/xp", "/progresso", "/level"):
                painel_rpg()
                continue

            elif cmd in ("/limpar", "/clear", "/cls"):
                os.system("cls" if os.name == "nt" else "clear")
                cabecalho()
                continue

            elif cmd in ("/nova", "/novasessao", "/restart"):
                session_id = memoria.criar_sessao_chat(
                    titulo=f"CLI {datetime.now().strftime('%d/%m %H:%M')}"
                )
                print(f"  {COR['verde']}✅ Sessão NOVA #{session_id} criada!{COR['reset']}\n")
                continue

            elif cmd in ("/sessoes", "/historico"):
                listar_sessoes()
                continue

            elif cmd in ("/status", "/cerebro", "/brain"):
                status_orquestrador()
                continue

            else:
                print(f"  {COR['vermelho']}Comando desconhecido: {cmd}  (digite /ajuda){COR['reset']}\n")
                continue

        # --- Envia para o Prometeu via Orquestrador LangGraph ---
        print(f"  {COR['cinza']}(Prometeu pensando...){COR['reset']}", end="\r")
        try:
            resultado = orchestrator.processar_mensagem(prompt, session_id=session_id)
        except Exception as e:
            log.error("chat_cli_falhou_orquestrador", exception=e)
            print(f"  {COR['vermelho']}❌ Erro interno: {str(e)[:100]}{COR['reset']}\n")
            continue

        # --- Imprime a resposta bonita ---
        resposta = resultado["resposta_texto"] or "(resposta vazia)"
        prefixo_status = COR["amber"] if resultado["sucesso"] else COR["vermelho"]
        print(f"  {prefixo_status}Prometeu →{COR['reset']} ")
        for linha in resposta.splitlines():
            print(f"    {linha}")
        print()

        # --- Info técnica (opcional, 1 linha) ---
        info = (
            f"  {COR['cinza']}["
            f"{resultado['modelo_usado'] or '?'} · "
            f"{resultado.get('tokens_usados') or 0} tok · "
            f"{resultado.get('tempo_total_ms') or 0:.0f}ms · "
            f"+{resultado.get('xp_ganho') or 0} XP · "
            f"sessao={resultado['session_id']}]"
            f"{COR['reset']}"
        )
        print(info)
        print()


if __name__ == "__main__":
    main()
