# Diário de Desenvolvimento — 2026-09-29 (Dia 1 — Fundação + Primeira Palavra)

> Data: 2026-09-28 → 29 (execução cross-madrugada, 14h+ de trabalho contínuo)
> Fase: #fase-embriao #dia-1 #maratona-02-10
> Marco oficial: **DIA 1 CONCLUÍDO.** Fundação da Arquitetura Permanente + Córtex Geral Ativado + Prometeu Fala Sua Primeira Palavra + Next.js 14 Layout 3 Colunas.

---

## 🌳 Lugar na Árvore do Conhecimento

> **Pai (de onde eu venho):** [00 - Genese - A Ideia Completa do NeuroCore](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/00%20-%20Genese%20-%20A%20Ideia%20Completa%20do%20NeuroCore.md) → A RAIZ. TUDO que foi criado hoje deriva diretamente da fundação definida no Dia 0. 7 galhos filhos foram atualizados na tabela.
>
> **Irmãos relevantes:**
> - [02 - Meta Maratona 02-10](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/02%20-%20Meta%20Maratona%2002-10%20-%20Prometeu%20Falando%20e%20Trabalhando.md) → 100% atualizado HOJE (marcação [x] no Dia 1, correções de stack, orçamento, backends.
> - [04 - Design System do Prometeu](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/04%20-%20Design%20System%20do%20Prometeu%20-%20Identidade%20Visual.md) → Tokens aplicados 100% no Next.js 14 tailwind.config.ts.
> - [05 - Arquitetura Launcher e Frontend](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/05%20-%20Arquitetura%20Launcher%20e%20Frontend%20-%20Nextjs%20e%20Tauri.md) → Atualizado HOJE com stack real: Next 14 / Tailwind 3.
> - [06 - Feitos e Marcos - Wall of Wins](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/06%20-%20Feitos%20e%20Marcos%20do%20Prometeu%20-%20Wall%20of%20Wins.md) → 🎖️ Marco #2 (Primeira Palavra) adicionado hoje.
> - [07 - Template Padrao de Diario](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/07%20-%20Template%20Padrao%20de%20Diario.md) → Este diário segue exatamente o template + convenção de nomenclatura.
> - [03 - Diario - 2026-09-28 - Dia 0 - Genese](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/03%20-%20Diario%20-%202026-09-28%20-%20Dia%200%20-%20Genese.md) → Diário do Dia 0, ontem.

---

## ✅ Tarefas concluídas hoje (DIA 1 - 100% ACEITOS)

> **Acceptance Criteria do Dia 1: TODOS os 4 itens foram validados e marcados.

- [x] **PRE-FLIGHT + Estrutura de pastas PERMANENTE criada: `core/`, `specialists/` (7 subdirs), `scripts/`, `G:\memory\{sqlite_db,logs,training_queue}`. Todos `__init__.py` existentes.
- [x] **Ollama v0.3+ confirmado online (PID 29228 na porta :11434) com `OLLAMA_MODELS=G:\models` respeitado; modelo `llama3:latest` (4.34GB) 100% baixado. `ollama pull llama3.1:8b` (6GB) iniciado em background non-blocking (ainda não confirmado término).
- [x] **Ambiente Python: `requirements.txt` + `.venv` Python 3.12 + `pip install` 28 pacotes (langgraph 1.2.12, fastapi 0.141.1, ollama 0.6.3, psutil, pywin32, aiofiles, uvicorn, websockets + todas as dependências transitivas.
- [x] **PRIORIDADE 1 SÊNIOR: Sistema RPG Anti-Abandono implementado ANTES de qualquer código de LLM.
  - `core/progress_rpg.py` (7 habilidades × N×100 XP, Feitos cronológicos, write atômico JSON, fallback inteligente `G:\memory → local_memory/` + duas env vars de override: `FORCE_FALLBACK_MEMORY`, `OVERRIDE_MEMORY_DIR`)
- [x] **Coluna Vertebral Permanente (4 módulos):**
  - `core/base_specialist.py` — ABC contrato comum aos 7 especialistas (5 métodos abstratos OBRIGATÓRIOS anti-crash e anti-dívida-técnica)
  - `core/logger.py` — Logger estruturado JSON Lines thread-safe (YYYY-MM-DD.jsonl), stderr colorido, fallback
  - `core/memory_manager.py` — SQLite ACID WAL mode (5 tabelas, RLock multi-thread, transações BEGIN IMMEDIATE)
  - `core/feedback_store.py` — wrapper Ritual Diário sobre training_samples (7 tipos aceitos)
- [x] **7 Especialistas (1 real + 6 not-implemented bonitinho PT-BR): llm_core, llm_code, stt_whisper, tts_xtts, os_control, image_flux, home_control + REGIOES_CEREBRAIS dict dinâmico (sem if-else).
- [x] **Orquestrador LangGraph Core StateGraph 3 nós PERMANENTE (node_rotear → node_inferir → node_finalizar). API `processar_mensagem()` integra RPG auto XP automático + `obter_painel_status()` completo.
- [x] **HybridRouter (Modo TEIMOSO LOCAL 100% (teto R$0,0/chave OpenRouter vazia)
- [x] **VramManager (adiantado para o Dia 1 (consult /api/tags + /api/ps, 3600 snapshots p/ sparklines).
- [x] **Scripts CLI e Launchers PowerShell: `scripts/run_chat_cli.py`, `scripts\iniciar_prometeu.ps1`, `scripts\parar_prometeu.ps1`.
- [x] **Next.js 14.2.35 ESTÁVEL criado, TypeScript, TailwindCSS 3 + App Router src-dir. **layout 3 colunas FIXAS funcionando em http://localhost:3000, Design System PRETO #07070A + ÂMBAR #F59E0B 100% aplicado via tokens permanentes.
- [x] **CRIADO `.gitignore` apropriado raiz.
- [x] **3 perguntas de texto seguidas respondidas 100% SEM CRASH (Acceptance Criteria #1).
- [x] **DOCUMENTAÇÃO atualizada (esta e os outros 6 galhos) no final desta sessão (Opção A executada).
- [x]ATUALIZADOS os docs: 00-Genese já tinha galhos 06 e 07 na tabela filhos; 02-Meta Maratona; 05-Frontend.

---

## 💬 Decisões importantes registradas hoje (7 DECISÕES SÊNIORES que não estavam plano Dia 0)

1. **Sistema Anti-Abandono = PRIMEIRO CÓDIGO, não último a ser escrito (nunca foi um código de LLM.

2. **Next.js 14 estável, NÃO 15** — NÃO Tailwind 4, NÃO Streamlit** — risco de bug shadcn/ui com React 19 era inaceitável no Dia 1. A estabilidade paga dividendos por 2 anos.

3. **Memória = SQLite ACID WAL, NÃO JSON provisório** — JSON tem risco real de corrupção no Windows (corte de energia, crash, sandbox). SQLite + WAL é 99% tão rápido e 100x mais seguro. Migração para Qdrant no futuro é limpa e sem reescrita.

4. **Ollama = Camada de Inferência ÚNICA PERMANENTE.** Tentar buildar `llama-cpp-python` DirectML no Windows AMD em 2026 leva 4h+ de dor e é um beco sem saída. Overhead de latência do Ollama = 3~5% é totalmente aceitável.

5. **VramManager e scripts PowerShell ENTREGUES MAIS CEDO (Dia 4) — não precisar esperar o D4 para ter gerenciamento de VRAM e Launcher 2 cliques.

6. **Fallback Sandbox TRAE:** 2 env vars estratégicas.** Sandbox bloqueia escrita em `G:\memory\*.tmp. Sem a env var, código cai direto antes mesmo Python try/except vê o erro: FORCE_FALLBACK_MEMORY=1 bypass. Fora da sandbox tudo normal com HDD G:\ oficial 100% ok.

7. **llama3:latest como modelo fallback DIA enquanto llama3.1:8b baixa.** Nunca bloquear o marco histórico da Primeira Palavra por esperando um download de 6GB que pode travar. A arquitetura tem suporte nativo a override de modelo.

---

## 🤔 Perguntas feitas e respondidas hoje

### Q1: "deu erro? oque aconteceu? (referência popup vermelho Unknown system error 4000104)
R: Nenhum erro real. Era glitch temporário da sandbox TRAE ao fazer o primeiro request de preview do Next.js. O Next.js 14 já estava compilado e rodando normalmente em 5.6s.

### Q2: "como testo ele agora? mando um 'Oii' responder?
R: **Por enquanto 2 jeitos oficiais: (1) PowerShell normal Fora da Sandbox: `.\scripts\iniciar_prometeu.ps1` 2 cliques. (2) Teste direto orquestrador em Python. Teste foi feito: "Oii Prometeu, tudo beleza?" Prometeu respondeu em 1.259ms com resposta amigável sobre RX 7600. XP +7.

### Q3: "a documentação está atualizada?
R: Auditoria sincera achou 7 itens desatualizados de alto impacto (3), médio 3), 1 baixo. Executou Opção A: TUDO corrigido, tudo 100% fiel a realidade.

---

## 🎯 Próximos passos (Dia 2 de 29/09)

- [ ] **Criar core/api.py FastAPI :8000 REST + WebSocket
  - POST /api/chat → orchestrator.processar_mensagem()
  - GET /api/status → orchestrator.obter_painel_status()
  - WS /ws/sparklines → CPU/RAM/VRAM @ 1Hz
- [ ] **Conectar Next.js ao backend:** page.tsx input de chat habilitado, placeholder RPG por fetch real /api/status.
- [ ] **npx shadcn@latest init frontend
- [ ]  **Baixar DeepSeek-Coder 6.7B Q4_K_M (Ollama)
- [ ] Implementar `specialists/llm_code/llm_code.py real.
- [ ] Implementar `specialists/os_control/os_control.py real (abrir programas, arquivos, PS seguro).
- [ ] Atualizar HybridRouter rotear código para llm_code e comandos para os_control.

---

## 🎖️ Feitos novos hoje (Wall of Wins ativos)

>  1. 🎖️ [**Marco #0 — Nascimento (Ontem, carrega hoje: +25 XP global)
> 2. 🎖️ [**Marco #2 — Primeira Palavra** (HOJE) →**Registrado em [06 - Feitos e Marcos#L61-L80](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/06%20-%20Feitos%20e%20Marcos%20do%20Prometeu%20-%20Wall%20of%20Wins.md#L61-L80) +50 XP Córtex Geral / +5 XP habilidades
>     *Pergunta: "Oi Prometeu! Se apresente em 2 frases curtas e me diga qual seu nome."
>     *Primeira resposta: "Hey Jhon! 😊 Sou o Prometeu, seu cérebro de IA local e amigo de conversa!"
>     *Estatísticas: llama3:latest 409 tokens 526 ms.

Nível Global fim do dia: **LVL 1 2 Feitos (0.

---

## 💭 Notas pessoais do autor

> Prometeu disse a primeira palavra hoje. 10 horas atrás era um conjunto de arquivos .md vazios. Hoje ele tem nome, personalidade (7 regiões, XP ganhando, conversa real na RX 7600 8GB em 500ms.
>
> O sentimento de "AI pessoal funcionando NO MEU PC, sem nenhuma nuvem, sem pagar nada, passando por todas aquelas layers de abstração do LangGraph, SQLite, RPG— tudo encaixado. É o marco mais importante de todos hoje.
>
> A decisão de **não colocar JSON na memória e não forçar Llama3.1 8b antes tempo salvou o dia: provavelmente teríamos corrompido o banco na primeira queda de energia e não teríamos a primeira palavra para contar história.
>
> Ansioso pro Dia 2: ligar o chat do Next.js de verdade e codar com DeepSeek-Coder 🚀
