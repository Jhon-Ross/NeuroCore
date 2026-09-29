# 02 - Meta Maratona 02/10 — Prometeu Falando + Trabalhando no PC em 4 dias

> Data de criação: 2026-09-28
> Prazo final: **2026-10-02 (sexta-feira)**
> Status: #meta #maratona #arquitetura-correta-desde-o-dia-1
> Objetivo: Até 02/10, Prometeu deve ser capaz de: (1) conversar comigo POR VOZ (falar e ouvir), e (2) executar tarefas SIMPLES no meu PC automaticamente.

---

## 🌳 Lugar na Árvore do Conhecimento

> **Pai (de onde eu venho):** [00 - Genese - A Ideia Completa do NeuroCore](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/00%20-%20Genese%20-%20A%20Ideia%20Completa%20do%20NeuroCore.md) → A RAIZ de tudo. Contém o planejamento macro de fases. Esta maratona acelera partes da Fase 1 e Fase 2 de 2 meses para 4 dias.
>
> **Irmãos relevantes:**
> - [01 - Ritual Diario - Treinamento do Prometeu com TRAE](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/01%20-%20Ritual%20Diario%20-%20Treinamento%20do%20Prometeu%20com%20TRAE.md) — Começa de verdade LOGO após o marco 02/10 ser conquistado.
> - [03 - Diario - 2026-09-28 - Dia 0 - Genese](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/03%20-%20Diario%20-%202026-09-28%20-%20Dia%200%20-%20Genese.md) — Registro da decisão da maratona e das correções (remoção do Streamlit, Next.js desde o dia 1).
> - [04 - Design System do Prometeu](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/04%20-%20Design%20System%20do%20Prometeu%20-%20Identidade%20Visual.md) — Definição de como o painel de status com sparklines deve parecer no dia 03/30.
> - [05 - Arquitetura Launcher e Frontend](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/05%20-%20Arquitetura%20Launcher%20e%20Frontend%20-%20Nextjs%20e%20Tauri.md) — Stack: Next.js permanente desde o dia 1, Tauri Launcher empacota na Fase 2.

---

## ✅ Decisão Correta: Arquitetura PERMANENTE desde o dia 1. NADA é jogado fora depois.

Eu errei na versão anterior do plano ao sugerir um MVP descartável. A sua intuição é 100% correta:

> 🎯 **Regra de ouro do NeuroCore/Prometeu**: Tudo que construímos hoje é uma peça de um quebra-cabeça infinito. NADA é reescrito do zero depois. NADA é "fita isolante e prego". A gente constrói a base CERTA desde a primeira linha de código, e só vai **adicionando peças** ao longo das fases.

A maratona de 02/10 **não cria um MVP provisório**, ela **ativa 4 das 6 regiões especializadas do NeuroCore**, usando exatamente a arquitetura que a gente definiu na Gênese. A estrutura de pastas, o `orchestrator.py`, o `memory_manager.py`, os especialistas em `specialists/` — tudo isso já é PERMANENTE. O dia 02/10 é só um marco intermediário no ciclo de vida infinito do Prometeu.

---

## ✅ O que VAI estar LIGADO em 02/10 (4 de 6 Regiões Ativadas)

A arquitetura é a mesma da Gênese. A diferença é que até 02/10 a gente **não liga as 6 regiões todas ainda** — a gente liga 4 e deixa as outras 2 com implementação mínima (esqueleto pronto para preencher depois).

| Região (especialista) | Até 02/10 | Estado |
|---|---|---|
| **1. 🧠 Córtex Geral (Llama 3.1 8B)** | ✅ 100% LIGADO | Conversa geral, orquestração simples |
| **2. 🧑‍💻 Região Código (DeepSeek-Coder 6.7B)** | ✅ 100% LIGADO | Especialista programador |
| **3. 🎧 Região Auditiva (Whisper large-v3)** | ✅ 100% LIGADO | Voz → Texto (entende você falar) |
| **4. 🗣️ Região Fonação (XTTS v2)** | ✅ 100% LIGADO | Texto → Voz (ele fala de volta) |
| **5. 🖥️ Região Motora do SO (Automação PC)** | ✅ 80% LIGADO | Abre programas, cria arquivos, executa comandos seguros. (versão 1, incrementada na Fase 3) |
| **6. 🎨 Região Visual (Flux / Imagens)** | ⏸️ **Esqueleto pronto** | Não ativado ainda. Interface da região existe no código (arquivo vazio pronto pra preencher), mas não é carregado na memória. Ativação = Fase 2. |
| **7. 🏠 Região Casa (Controle Residencial)** | ⏸️ **Esqueleto pronto** | Interface existe (arquivo vazio pronto pra preencher). Ativação = Fase 4. |
| **Memória (Qdrant)** | 🟨 Implementação MÍNIMA (JSON) | A estrutura do `memory_manager.py` já é a PERMANENTE, mas por baixo tá usando JSON por enquanto (simples de instalar). A gente só troca o backend pro Qdrant na semana que vem sem mexer em NENHUMA outra linha de código. |
| **Front-end Next.js SaaS Premium** | 🟨 Implementação MÍNIMA (Streamlit) | A interface entre front e core é uma API REST permanente. Por enquanto usamos Streamlit como UI rápida — quando migrarmos pro Next.js, a API de comunicação é a MESMA. Nenhuma linha do core muda. |
| **Hybrid Router (fallback API)** | ⏸️ **Esqueleto pronto** | A interface `hybrid_router.py` existe, mas por enquanto sempre escolhe "local". Ativação = Fase 2. |

---

## ❌ O que NÃO vai estar LIGADO em 02/10 (Ainda)

| Item | Quando liga |
|---|---|
| UI Next.js SaaS Premium/Enterprise | Fase 2 (semana 3~4) |
| Qdrant + memória semântica completa + Ritual Diário automatizado | Final da Fase 1 (semana 2, após 02/10) |
| Região Visual (geração de imagens Flux) | Fase 2 |
| Clonagem da sua voz (LoRA XTTS) | Fase 3 / Fase 4 |
| Vídeo | Fase 5+ |
| Região Casa (Controle residencial / Alexa-like) | Fase 4 |
| Hybrid Router (fallback APIs quando não aguentar) | Fase 2 |
| Automação COMPLETA de PC (mouse, preencher formulários) | Fase 3 (melhorias na região motora) |
| Robô humanoide 😂 | Fase 7 (2~5 anos) |

---

## 📅 Plano dos 4 Dias — Ativando Regiões, não construindo MVP

Hoje é dia **28/09 (segunda-feira)**. Prazo final **02/10 (sexta-feira)**. 4 dias úteis de maratona.

### 🟢 Dia 1 — (28/09): Fundação da Arquitetura + Córtex Geral LIGADO + Next.js Criado
> ✅ **DIA 1 CONCLUÍDO EM 28/09.** Todos os itens abaixo entregues e validados com 3 perguntas reais de teste (Acceptance Criteria 100%).
- [x] Criar estrutura de pastas **PERMANENTE** (igual da Gênese — `core/`, `specialists/7 subdirs`, `scripts/`, `frontend/`, `G:\memory\sqlite_db|logs|training_queue`) + `__init__.py` vazios
- [x] Criar `requirements.txt` **PERMANENTE** (langgraph>=0.2, fastapi, uvicorn, ollama-python, psutil, pywin32, aiofiles, websockets) + .venv Python 3.12 criado e 28 pacotes instalados
- [x] Criar `frontend/` **PERMANENTE**: inicializar **Next.js 14.2.35 ESTÁVEL** (evita bug shadcn/ui com Next 15/React 19) + **TailwindCSS 3** + TypeScript + App Router + src-dir (não Next 15, não Tailwind 4). shadcn/ui é agendado para Dia 2 (não era obrigatório pro esqueleto D1). Layout 3 colunas FIXAS (sidebar 240px | chat central flex | painel direito RPG 320px) 100% funcional em http://localhost:3000. Design System PRETO #07070A + ÂMBAR #F59E0B aplicados via tailwind.config.ts tokens PERMANENTES.
- [x] Criar interfaces permanentes (esqueletos de 7 especialistas) + coluna vertebral permanente:
  - [x] `core/base_specialist.py` — ABC contrato OBRIGATÓRIO com 5 métodos abstratos (load/unload/infer/is_loaded/get_recursos_usados) + ResultadoInferencia padrão
  - [x] `core/logger.py` — Logger estruturado JSON Lines (YYYY-MM-DD.jsonl) thread-safe com RLock, 5 níveis, rotação diária automática, fallback `local_memory/logs/`
  - [x] `core/memory_manager.py` — **SQLite ACID WAL mode** (PRAGMA journal_mode=WAL synchronous=NORMAL foreign_keys=ON) com 5 tabelas permanentes (chat_sessions, chat_messages, training_samples, user_preferences, system_state). RLock multi-thread. Não é JSON provisório.
  - [x] `core/feedback_store.py` — Wrapper amigável sobre training_samples para o Ritual Diário (7 tipos aceitos)
  - [x] `core/progress_rpg.py` — PRIORIDADE 1: Sistema RPG Anti-Abandono (7 habilidades, N×100 XP, Feitos Wall of Wins, resumo UI, atomic write JSON, fallback G:\memory → local_memory/ com 2 env vars)
  - [x] `core/orchestrator.py` — **Orquestrador NeuroCore com LangGraph Core StateGraph de 3 nós permanentes**: `node_rotear (HybridRouter)` → `node_inferir (REGIOES_CEREBRAIS)` → `node_finalizar`. Compila com `.compile()`. Métodos públicos `processar_mensagem()` + `obter_painel_status()`. Auto-salva SQLite histórico + XP automático.
  - [x] `core/hybrid_router.py` — Decisão Roteamento: SEMPRE LOCAL PRIMEIRO. Força modo teimoso local por padrão (teto R$ 0,0 e chave OpenRouter vazia)
  - [x] `core/vram_manager.py` — ✅ **ENTREGUE MAIS CEDO DO QUE O PLANO (Dia 1 ao invés de Dia 4)** — consulta Ollama /api/tags + /api/ps com snapshot histórico 3600 amostras (1h de sparklines), descarrega tudo exceto via keep-alive 5s
  - [x] `specialists/llm_core/llm_core.py` — classe `EspecialistaLlmCore` (não model_handler.py): **implementação real 100%** via ollama-python conectando `http://localhost:11434`. Modelo padrão atual: `llama3:latest` (já baixado 4.34GB) como fallback até conclusão do `ollama pull llama3.1:8b`.
  - [x] `specialists/llm_code/llm_code.py` — classe `EspecialistaLlmCode` (Fase 2): NotImplemented bonitinho PT-BR explicando "amanhã ligamos"
  - [x] `specialists/stt_whisper/stt_whisper.py` — classe `EspecialistaSttWhisper` (Fase 3): NotImplemented PT-BR
  - [x] `specialists/tts_xtts/tts_xtts.py` — classe `EspecialistaTtsXtts` (Fase 3): NotImplemented PT-BR
  - [x] `specialists/os_control/os_control.py` — classe `EspecialistaOsControl` (Fase 2): NotImplemented PT-BR
  - [x] `specialists/image_flux/image_flux.py` — classe `EspecialistaImageFlux` (Fase 5): NotImplemented PT-BR
  - [x] `specialists/home_control/home_control.py` — classe `EspecialistaHomeControl` (Fase 4): NotImplemented PT-BR
  - [x] `specialists/__init__.py` — `REGIOES_CEREBRAIS` dict dispatch dinâmico (evita if-else hardcoded no orquestrador)
- [x] Baixar modelo base via Ollama: `llama3:latest` 4.34GB 100% concluído e funcionando. `ollama pull llama3.1:8b` (6GB) iniciado em background non-blocking (terminal PID 460) — continua rodando após final do D1, sem bloquear nada
- [x] Criar `scripts/run_chat_cli.py` (ponto de entrada PERMANENTE do chat CLI com comandos /rpg /sessoes /status /nova /limpar /ajuda /sair integrados com orquestrador e SQLite)
- [x] Criar `scripts\iniciar_prometeu.ps1` — ✅ **ENTREGUE MAIS CEDO (Dia1, não Dia4)** — Launcher PowerShell 4 passos: verifica Ollama online → .venv → valida script cli → executa
- [x] Criar `scripts\parar_prometeu.ps1` — ✅ **ENTREGUE MAIS CEDO (Dia1, não Dia4)** — Esqueleto encerrador (detecta processos python/.venv + ollama, -Forcar opcional)

### 🔵 Dia 2 (29/09): Regiões de Código + SO LIGADAS + API FastAPI + Chat Next.js Funcional
- [ ] Preencher `specialists/llm_code/llm_code.py` — classe `EspecialistaLlmCode` (modelo: DeepSeek-Coder 6.7B Q4_K_M via Ollama)
- [ ] Preencher `specialists/os_control/os_control.py` — classe `EspecialistaOsControl` (abrir programas, PowerShell seguro, arquivos txt/py)
- [ ] **Ajustar `core/orchestrator.py` / `specialists/__init__.py` REGIOES_CEREBRAIS**:
  - Frases como "escreva um código Python para..." devem rotear automaticamente para `llm_code`.
  - Frases como "abra o Chrome" / "crie um arquivo no desktop" devem rotear para `os_control`.
- [ ] Criar `core/api.py` (API REST **PERMANENTE**, FastAPI + WebSocket :8000) — comunicação com o Next.js
  - `POST /api/chat` — recebe mensagem, chama `orchestrator.processar_mensagem()`, retorna resposta JSON
  - `GET  /api/status` — retorna `orchestrator.obter_painel_status()` (RPG + VRAM + sessões + especialistas)
  - `WS   /ws/sparklines` — streaming CPU/RAM/VRAM (1Hz) pro painel direito
- [ ] Conectar **Next.js** (já existente desde ontem) ao backend via `core/api.py`. Primeira tela de Chat por texto funcionando no navegador :3000.
- [ ] Rodar `cd frontend && npx shadcn@latest init` para instalar componentes shadcn/ui (padrão New-York ou Default).
- [ ] Baixar via Ollama:
  - **DeepSeek-Coder 6.7B Q4_K_M** → `ollama pull deepseek-coder:6.7b-instruct-q4_K_M` (vai pro `OLLAMA_MODELS=G:\models` automaticamente)
- [ ] Atualizar `scripts\run_chat_cli.py`: comando `/codigo` envia pra llm_code, `/so` envia pra os_control
- [ ] **Nota**: STT (Whisper) e TTS (XTTS) foram RE-AGENDADOS pro **Dia 3** (não D2) conforme arquitetura original de ativação fase a fase.

### 🟣 Dia 3 (30/09): Regiões Sensoriais (Voz Audição + Fonação) + Painel Sparklines
- [ ] Preencher `specialists/stt_whisper/stt_whisper.py` — classe `EspecialistaSttWhisper` (Whisper large-v3 ou small via faster-whisper)
- [ ] Preencher `specialists/tts_xtts/tts_xtts.py` — classe `EspecialistaTtsXtts` (XTTS v2 — português brasileiro PT-BR fine-tuned se disponível)
- [ ] Atualizar `core/orchestrator.py`: integração áudio (ainda não precisa ficar no D3 — pode ser só CLI primeiro)
- [ ] **No Next.js (já existe)**: Implementar:
  - Botão de voz no chat (grava áudio do microfone via browser → envia para API /stt → Whisper transcreve → gera resposta → API /tts → XTTS fala de volta no player do navegador)
  - **Painel de Status do Cérebro (coluna direita)**: sparklines CPU/RAM/VRAM atualizando em tempo real a cada 1s via WebSocket `/ws/sparklines`.
  - Tela de Automação SO com botões para abrir programas e testar.
- [ ] Baixar:
  - Whisper large-v3 (se ainda não tiver)
  - XTTS v2 modelo + voz PT-BR feminina/masculina

### 🟠 Dia 4 (01/10): Polimento Next.js + Scripts de 1 Clique + Atualização Launcher .ps1
> ✅ **Atenção**: Os itens abaixo que já foram **entregues no Dia 1** estão marcados `[x] — Concluído D1`. Nenhuma ação extra necessária.
- [x] **Módulo core/vram_manager.py** (PERMANENTE) — ✅ **CONCLUÍDO NO DIA 1**. Carrega/descarrega modelos da RX 7600 8GB, consulta Ollama /api/tags e /api/ps, histórico 3600 snapshots para sparklines. Ajustes finos (troca inteligente entre llm_core e llm_code) são feitos durante o D2 e D3 conforme necessidade real.
- [ ] **No Next.js (já existe)**: Polimento estético SaaS premium, botão global de microfone na topbar, sidebar com todas as regiões (inativas em cinza inclusive). Trocar dados placeholder do RPG por fetch real em `/api/status`.
- [ ] Testar fluxo COMPLETO de ponta a ponta:
  - [ ] "Boa noite Prometeu" → Microfone browser → Whisper (API /stt) → LLM → XTTS (API /tts) fala de volta no browser
  - [ ] "Abre o Google Chrome" → Orquestrador detecta → OS Control abre Chrome
  - [ ] "Escreve um script de calculo IMC em Python e salva no Desktop" → llm_code gera → os_control salva arquivo
  - [ ] "Me explica o que é pensamento crítico em 2 frases" → llm_core responde, XTTS fala
  - [ ] Painel de status reflete em tempo real todo o uso de CPU/RAM/VRAM via WebSocket
- [x] Criar `scripts/iniciar_prometeu.ps1` (script de 1 clique original): ✅ **CONCLUÍDO NO DIA 1** (esqueleto: valida Ollama + .venv + roda CLI). **Reescrita no D4**: Liga API FastAPI (:8000) + Next.js Dev Server (:3000) e abre `http://localhost:3000` no navegador padrão.
- [x] Criar `scripts/parar_prometeu.ps1`: ✅ **CONCLUÍDO NO DIA 1** (esqueleto detecta processos). **Reescrita no D4**: encerra suavemente :8000 + :3000 + prompt confirmação.

### 🎂 Dia 5 — DIA D (02/10): Marco Conquistado
- [ ] Sessão de demonstração final: Prometeu com 4 regiões LIGADAS, **Next.js v0.1 100% funcional** (permanente, sem UI provisória), tudo usando a arquitetura correta da Gênese. Acesso em `http://localhost:3000`
- [ ] Documentar bugs e melhorias para a próxima semana.
- [ ] Próximo marco pós 02/10: Ativar memória Qdrant + Tauri Launcher (empacota Next.js em .exe) + Ritual Diário automático.

---

## 🧮 Orçamento de armazenamento do marco 02/10 (~18GB, abaixo dos 100GB)

**DECISÃO ARQUITETURAL DIA 1 — NÃO USAMOS PASTAS SEPARADAS POR ESPECIALISTA**.
Todos os modelos são gerenciados **100% pelo Ollama** via variável de ambiente `OLLAMA_MODELS=G:\models`. Nenhuma cópia manual, nenhuma estrutura de subpastas `G:\models\llm_core\`. O Ollama armazena tudo em `G:\models\blobs\` com hashes SHA e gerencia duplicações automaticamente. Basta rodar `ollama pull NOME_DO_MODELO`.

| Modelo | Tamanho esperado | Comando de download | Status em 28/09 (fim D1) |
|---|---|---|---|
| Llama 3:latest (fallback D1) | ~4.34 GB | `ollama pull llama3:latest` | ✅ **100% baixado e funcionando** (usado na Primeira Palavra) |
| Llama 3.1 8B Q4_K_M (Córtex Geral padrão) | ~6 GB | `ollama pull llama3.1:8b` | 🔄 **Download em background non-blocking** (iniciado 28/09 23:23, PID 460) |
| DeepSeek-Coder 6.7B Instruct Q4_K_M (llm_code) | ~4.2 GB | `ollama pull deepseek-coder:6.7b-instruct-q4_K_M` | ⚪ Agendado Dia 2 |
| Whisper large-v3 (stt_whisper) | ~2.9 GB | `ollama pull whisper:large-v3` OU CT2 local | ⚪ Agendado Dia 3 |
| XTTS v2 + voz PT-BR (tts_xtts) | ~4.5 GB | Download manual Coqui/TTS → `G:\memory\models_tts\` | ⚪ Agendado Dia 3 |
| **Total modelos 02/10 (estimado)** | **~22 GB** | | (folga de 68GB para os 90GB totais de G:\models) |
| Memória persistente (SQLite + Logs JSONL + Ritual) | < 500 MB até o 02/10 | `G:\memory\sqlite_db` + `G:\memory\logs` + `G:\memory\training_queue` | ✅ Pastas existentes e em uso (fallback para `local_memory\` dentro do projeto caso TRAE sandbox bloqueie escrita em G: via env var `FORCE_FALLBACK_MEMORY=1`) |

---

## 🧩 Backends Provisórios vs Permanentes (O que trocamos depois sem reescrever nada)

Esses são os únicos "atalhos" que a gente usa até 02/10. Como todos são encapsulados por interfaces permanentes (classes abstratas ABC), a troca não impacta NENHUMA outra parte do código:

| Componente | Backend DIA 1 (atual) | Backend permanente (troca sem refatoração) | Quando troca |
|---|---|---|---|
| Memória do Prometeu (`memory_manager.py`) | **SQLite ACID WAL mode** (5 tabelas, RLock multi-thread, transações BEGIN IMMEDIATE). NÃO é mais JSON provisório — corrigido no D1 por risco de corrupção. | **Qdrant** (banco vetorial local, <10GB) para memória semântica + procedimental; SQLite continua como KV store / sessions / feedback. | Semana que vem, logo após 02/10. |
| Front-end UI | **Next.js 14.2.35 ESTÁVEL + React 18 + TailwindCSS 3** em `frontend/` com App Router + src-dir. NÃO usamos Next 15 (risco bug shadcn/ui com React 19) nem Tailwind 4 (muito novo). shadcn/ui agendado Dia 2. | **Next.js** evolui pra v0.2, v1.0, v1.1 etc adicionando telas e polimento. Atualizações de minor versão somente depois de checar compatibilidade shadcn/ui. | Nunca é trocado, só evolui. Troca de versão 14 → 15 é planejada com teste, não espontânea. |
| Hybrid Router (`hybrid_router.py`) | Modo TEIMOSO: SEMPRE retorna "local" (força tudo rodar na RX 7600). Teto R$ 0,0 configurado, chave OpenRouter vazia intencionalmente. | Roteamento inteligente local vs API externa (OpenRouter agregador) com contador de custo R$ visível no painel e bloqueio automático ao atingir teto mensal definido pelo Jhon. | Fase 2 (outubro ~semana 4), quando 4 regiões estiverem ligadas e quiser testar um modelo mais forte p/ código complexo. |
| Modelos LLM geral + código | 100% gerenciados pelo Ollama em `OLLAMA_MODELS=G:\models` (blobs SHA, deduplicação automática). Nenhuma cópia manual. | Continua 100% Ollama pra tudo que for LLM de texto. Apenas STT/TTS/Imagens saem do Ollama (bibliotecas especializadas). | Nunca troca para LLM — Ollama é a camada de inferência permanente do NeuroCore. |
| Região Visual (imagens) | Esqueleto vazio, não carregado | **Flux.1 [dev]** 24GB | Fase 2 |
| Região Casa | Esqueleto vazio, não carregado | **Home Assistant / Matter** | Fase 4 |
| Launcher Desktop (.exe de 2 cliques) | Não pronto em 02/10. Acesso pelo navegador `localhost:3000` | **Tauri v2** empacota o mesmo Next.js existente dentro de .exe | Fase 2 (semana 3~4). Nenhuma linha do Next.js muda. |

---

## 🚀 Regras da Maratona (versão correta, arquitetura permanente)

1. **Prioridade: NADA é jogado fora.** Toda linha de código hoje é uma peça permanente.
2. **Se der bug de VRAM cheia**: O `vram_manager.py` (dia 4) descarrega um modelo antes de carregar outro. Nunca vamos rodar dois LLMs grandes ao mesmo tempo — na prática não precisamos.
3. **Cada dia tem seu Marco irrenunciável.** Dia 1 = primeira conversa por texto usando a arquitetura correta. Se isso não acontecer hoje, o resto atrasa.
4. **Se tudo der MUITO certo nos dias 1 e 2**, a gente pode adiantar UI e automação SO pro dia 3 sem problemas.

---

## 🔗 Links relacionados

- [[00 - Gênese — A Ideia Completa do NeuroCore]] (arquitetura permanente, evolução infinita)
- [[01 - Ritual Diário — Treinamento do Prometeu com TRAE]] (começa logo após 02/10, quando a memória Qdrant for ligada)
- [[03 - Diario - 2026-09-28 - Dia 0 - Genese]] (decisões do dia fundação)
