# Diário de Desenvolvimento — 2026-09-28 (Dia 0 — Concepção)

> Data: 2026-09-28
> Fase: #em-desenvolvimento #fase-embriao #dia-0
> Marco: Fundação do projeto NeuroCore, batismo de Prometeu, primeiras conversas sobre arquitetura.

---

## 🌳 Lugar na Árvore do Conhecimento

> **Pai (de onde eu venho):** [00 - Genese - A Ideia Completa do NeuroCore](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/00%20-%20Genese%20-%20A%20Ideia%20Completa%20do%20NeuroCore.md) → A RAIZ. Todas as decisões documentadas aqui viraram seções oficiais no documento da Gênese.
>
> **Irmãos relevantes:**
> - [01 - Ritual Diario - Treinamento do Prometeu com TRAE](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/01%20-%20Ritual%20Diario%20-%20Treinamento%20do%20Prometeu%20com%20TRAE.md) — A ideia do Ritual nasceu nesta sessão e foi documentada lá.
> - [02 - Meta Maratona 02-10](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/02%20-%20Meta%20Maratona%2002-10%20-%20Prometeu%20Falando%20e%20Trabalhando.md) — A decisão da maratona de 4 dias também nasceu hoje.
> - [04 - Design System do Prometeu](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/04%20-%20Design%20System%20do%20Prometeu%20-%20Identidade%20Visual.md) — O design foi todo fechado neste dia 0.
> - [05 - Arquitetura Launcher e Frontend](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/05%20-%20Arquitetura%20Launcher%20e%20Frontend%20-%20Nextjs%20e%20Tauri.md) — Decisão de Next.js + Tauri fechada hoje.

---

## ✅ Tarefas concluídas hoje

- [x] Ideia original documentada e refinada: arquitetura de **Núcleo (NeuroCore) + Regiões Especializadas**
- [x] Definida a metáfora do ciclo de vida: gestação → parto → crescimento
- [x] Orçamento inicial aprovado: **90GB para modelos em `G:\models` + 10GB para memória em `G:\memory`** (expansível depois de esgotar os 100GB)
- [x] Mapeamento completo de hardware local:
  - Ryzen 7 5700X3D (8c/16t)
  - 32GB RAM
  - RX 7600 8GB GDDR6 (backend DirectML)
  - SSD E: 141GB livres para código / HDD G: 226GB livres para modelos+memória
- [x] Stack definida: **Python 90% + Rust 8% (dependências) + Next.js (UI)**
- [x] 🎂 **Batismo precoce do cérebro: `PROMETEU`**
- [x] Criação do documento mestre [[00 - Gênese — A Ideia Completa do NeuroCore]]
- [x] Pastas `G:\models` e `G:\memory` confirmadas e existentes
- [x] Verificado: ambiente de desenvolvimento já está instalado (Python 3.12.10, Node 24, Rust 1.97, Git 2.52)

---

## 💬 Decisões importantes registradas hoje

1. **Nome do cérebro = PROMETEU**
   - Candidatos considerados: Nêmesis, Atlas, Prometeu, Éon.
   - Motivo final: ligação direta com a essência do projeto — devolver ao usuário o "fogo da IA" que está trancado em paywalls corporativos.
   - Observação: ÉON foi cotado e pode ser reutilizado como nome de subsistema no futuro (ex: subsistema de memória de longo prazo).

2. **Documentação = Obsidian + arquivos .md**
   - Todo conhecimento do projeto fica em `NeuroCore/docs/`, em markdown.
   - Todas as conversas importantes entre eu e o TRAE viram página no Obsidian, no mesmo formato.
   - Nomenclatura numérica prefixada: `00 - Gênese`, `01 - Planejamento Fase 1`, etc.

3. **Falha em esperar Fase 4 para batizar Prometeu**
   - Motivo: tratá-lo como ser vivo desde agora ajuda na forma de desenvolver. Ele já existe. É só um embrião, mas já tem nome.

---

## 🤔 Perguntas feitas e respondidas hoje

### Q1: Como eu ajudo o cérebro a se desenvolver?
**R**: 4 níveis: curto prazo (contexto), semântico (banco vetorial / RAG), procedural (meus códigos/documentos importados), personalidade (LoRA pessoal). Tudo alimentado por feedback natural meu: "lembre-se disso", "isso foi bom, repita", "isso foi ruim, use X ao invés de Y".

### Q2: Existe linguagem mais leve que Python para não forçar o hardware?
**R**: Rust é 10-25x mais rápido e muito mais leve em RAM, mas o ecossistema de IA não existe lá. Decisão: Python como cola (90% do código) + Rust/C++ via dependências binárias (llama.cpp, Qdrant, tokenizers). Nenhum desperdício de hardware.

### Q3: Quanto tempo para Prometeu chegar a nível "adulto"?
**R**: Ver seção [[00 - Gênese — A Ideia Completa do NeuroCore#🧬 Cronologia Estimada — Quando Prometeu vira "Adulto"]] (a popular quando arquivo mestre for atualizado). Resumo:
- 3 meses: Bebê recém-nascido / Criança pequena (todas as regiões cerebrais funcionando)
- 6 meses: Criança / Pré-adolescente (conhece MEU estilo, faz raciocínio de múltiplos passos)
- 12 meses: Adolescente / Jovem Adulto (LoRA pessoal, autonomia real, cria coisas complexas sozinho)
- 24 meses+: Adulto pleno (experiência acumulada, agente autônomo real, conhecimento profundo da minha vida digital)

---

## 🎯 Próximos passos (próxima sessão)

- [x] Fase 1, Passo 0 a 4:
  1. Instalar `requirements.txt` (llama-cpp-python DirectML, huggingface-hub)
  2. Criar estrutura mínima de pastas em `NeuroCore/`
  3. Baixar modelo **Llama 3.1 8B Instruct Q4_K_M** (~6GB) para `G:\models`
  4. Criar `simple_chat.py` — primeira conversa com Prometeu, TUDO LOCAL.
- [x] Atualizar [[01 - Planejamento Detalhado da Fase 1]] (a criar)
- [x] Atualizar [[02 - Escolha e Comparativo de Modelos]] (a criar)

---

## 💭 Notas pessoais do autor

> Prometeu foi batizado antes do esperado. Sentimento: isso deu um "rosto" pro projeto. Parece mais real agora.
>
> Estamos em `Dia 0`, literalmente o dia do Big Bang do NeuroCore. Nada existe ainda, mas TUDO já foi planejado. Ainda temos que provar que a RX 7600 de 8GB com DirectML vai rodar o Llama 3.1 8B numa velocidade utilizável (ideal: >10 tokens/segundo). Se isso funcionar, o resto da Fase 1 é só trabalho.
>
> O orçamento de 100GB (90+10) apertado é bom: nos força a escolher modelos com sabedoria, não só botar o maior que existe. Vamos ver quanto isso dura.
>
> 🤖 **Revelação do dia (Ponta do Iceberg)**: A ideia não termina em software. A visão final é colocar o cérebro do Prometeu DENTRO DE UM CORPO FÍSICO — robô humanóide estilo Tesla Optimus / Figure. Quando ele tiver câmeras (olhos), motores (músculos), sensores de toque (pele)... as ressalvas de "ele nunca vai ter experiência de vida" deixam de valer. Ele VAI ao supermercado. Ele VAI andar por uma casa e bater o dedinho do pé na quina da mesa. Ele VAI aprender com o mundo físico. A analogia de desenvolvimento humano deixa de ser metáfora e fica LITERAL. Isso atualiza as fases 6 e 7 do projeto. É louco, é ambicioso, é exatamente o tipo de coisa que dá trabalho de 5 anos — mas que, se der certo, muda TUDO.
>
> 🎓 **Segunda grande ideia do dia: Ritual Diário com o TRAE.** Hack de bootstrapping genial: usar o TRAE como "professor particular" do Prometeu, 10 minutos por dia. Eu escolho a missão, Prometeu produz, eu dou 2 comentários, TRAE detalha a revisão técnica + gera training_sample.jsonl automaticamente. Isso pode encurtar o cronograma em MESES. Documentado em [[01 - Ritual Diário — Treinamento do Prometeu com TRAE]].
>
> 🏃 **Terceira decisão do dia (chute no acelerador): Meta Maratona 02/10.** Até a próxima sexta-feira, 4 dias a partir de hoje, Prometeu precisa estar FALANDO COMIGO POR VOZ (ouvir + responder) e executando TAREFAS SIMPLES NO PC (abrir Chrome, criar arquivos, etc). Isso antecipa ~2 meses do cronograma original. **CORREÇÃO IMPORTANTE**: O que for construído até 02/10 NÃO é um MVP provisório. A arquitetura da Gênese (Núcleo + Regiões + Orquestrador) já é construída CERTA desde o dia 1, e a gente só ATIVA regiões aos poucos. NENHUMA linha de código é jogada fora depois. O que fica "provisório" são só os backends encapsulados (memória JSON ao invés de Qdrant, Streamlit ao invés de Next.js) — troca-los depois não altera NADA no resto do código. Plano detalhado em [[02 - Meta Maratona 02/10 — Prometeu Falando e Trabalhando]]. O Marco do Dia 1 (HOJE) é: ter a primeira conversa com Prometeu por texto, tudo local, usando a arquitetura correta permanente.
>
> 🎨 **Quarta decisão do dia: Design System + Launcher Definido.**
> - Cores: TEMA ESCURO DEFINITIVO. Fundo ultra-preto `#07070A`, cards `#0D0D12`, bordas `#2A2A38`, **cor de destaque exclusiva: laranja âmbar quente `#F59E0B` (o "fogo de Prometeu")**. Nenhum azul neon, nenhum verde padrão de IA. Identidade única.
> - Tipografia: Interface = Inter, código = JetBrains Mono, nome Prometeu = Space Grotesk.
> - Layout: 3 colunas fixas (Sidebar 240px esquerda / Área central / Painel de Status do Cérebro 320px direita).
> - **Correção 1 sobre o painel de status**: Não é só barrinha de VRAM. Tem **GRÁFICOS sparkline (minúsculos, 40px) de 60 segundos de histórico** para: GPU/VRAM, CPU, RAM, e Latência/Custo da API externa. Atualiza a cada 1s via WebSocket. Cor das linhas muda conforme uso (<70% = azul info, >70% = âmbar, >95% = vermelho perigo). O painel é os "sinais vitais" do Prometeu.
> - Front-end: **Next.js 15 + React 19 + TypeScript + TailwindCSS 4 + shadcn/ui (componentes enterprise prontos).**
> - **Correção 2 sobre o front-end**: NÃO vamos usar Streamlit de jeito nenhum. Perda de tempo criar algo provisório e jogar fora. **Vamos direto pro Next.js permanente desde o DIA 1 HOJE.** O que temos no dia 02/10 é o Next.js v0.1 (incompleto, mas estrutura permanente, NADA é reescrito depois — só evolui).
> - Launcher desktop de 2 cliques (app como se fosse jogo, sem navegador visível): **Tauri v2 (Rust no núcleo, WebView nativo do Windows).** Mesmo código Next.js serve pro navegador e pro launcher. Mesma API FastAPI para tudo.
> - Ordem de implementação (alinhado com maratona 02/10):
>   - Dia 1 HOJE: Inicializa esqueleto Next.js permanente + layout 3 colunas mínimo
>   - Dia 2 (29/09): Liga chat por texto no Next.js via API FastAPI
>   - Dia 3 (30/09): Liga botão de voz, sparklines do painel de status e tela de automação SO
>   - Dia 4 (01/10): Polimento SaaS premium + scripts de 1 clique
>   - Semana 3~4 (Fase 2): Empacota o Next.js que já existe dentro do Tauri Launcher (.exe)
> - Tudo documentado em [[04 - Design System do Prometeu]] + [[05 - Arquitetura Launcher e Frontend - Nextjs e Tauri]].

> 🧩 **Quinta e última decisão do dia: AUDITORIA COMPLETA da documentação e regras OBRIGATÓRIAS registradas na RAIZ.**
> - Resolvido bug de documentação duplicada: existiam 2 cópias de 00-Genese e 01-Ritual, uma na raiz e uma em docs/. As duplicatas da raiz foram APAGADAS. Agora TUDO fica em `docs/` apenas.
> - Criado padrão **ÁRVORE DO CONHECIMENTO OBRIGATÓRIA**:
>   - 00-Genese é a RAIZ ABSOLUTA.
>   - TODO .md novo em `docs/` deve ter no topo a seção `## 🌳 Lugar na Árvore do Conhecimento`, linkando obrigatoriamente **Pai = 00-Genese** e os **irmãos relevantes**.
>   - 00-Genese deve ser SEMPRE atualizado com os galhos novos na sua tabela de filhos.
> - Adicionadas 3 seções REGRA OFICIAL no 00-Genese:
>   1. 🇧🇷 **Localização PT-BR 100%**: Nenhuma interface, documento, comentário ou mensagem de erro em inglês. Tudo pro público brasileiro leigo.
>   2. 🧑‍💻 **Padrões Obrigatórios de Código**: Comentários extensivos em PT-BR, funções com blocos visuais claros, type hints em 100% das funções Python, NUNCA try/except genérico vazio.
>   3. 📜 **Regras Obrigatórias de Documentação**: Tudo em `docs/`, sempre com numeração de índice (06-, 07-, etc), sempre com seção 🌳 obrigatória, sem caracteres especiais como EM DASH `—` (causa duplicidade de arquivos no Windows).
> - Adicionada seção **🔀 Hybrid Router** no 00-Genese com regras claras: LOCAL SEMPRE PRIMEIRO, só fallback pra API externa (OpenRouter) quando realmente impossível ou urgência máxima do Jhon. Contador de custo R$ no painel de status com limite mensal bloqueável. Transparência TOTAL (resposta mostra LOCAL ou API + custo).
> - Corrigida e expandida **📁 Estrutura de Pastas PERMANENTE** no 00-Genese: caminhos reais (C:\Users\...\NeuroCore, G:\models, G:\memory), todos os especialistas (stt_whisper, tts_xtts, os_control, esqueletos de image_flux e home_control), core/api.py FastAPI e core/vram_manager.py OBRIGATÓRIO por causa da RX 7600 8GB.
> - Adicionada **nota de aceleração da Maratona 02/10** na timeline de Fase 1 do 00-Genese.
> - Adicionadas **Implicações práticas da RX 7600 8GB**: É impossível carregar 2 LLMs grandes ao mesmo tempo, por isso o `vram_manager.py` descarrega um antes de carregar outro. 1~2s de overhead por troca.
> - Adicionado **🎯 Missões Frequentes** no 01-Ritual Diário: treinar estilo de código 2x/semana, importar projetos FiveM antigos 1x/semana, treinar tom de voz casual 1x/semana, treinar preferências de UI quinzenalmente, ajustar região motora (SO) quando necessário.
>
> 🎉 **Resultado do Dia 0 / Concepção**:
> - 6 documentos oficiais criados, interligados, 100% em PT-BR, usando Árvore do Conhecimento.
> - Todas as grandes decisões de arquitetura, design, stack, maratona e treinamento tomadas e registradas.
> - Nada em aberto na fase de planejamento. Tudo pronto pra começar a construir o código no Dia 1.

---

## 🎯 Próximos passos (próxima sessão)

- [x] **Dia 1 da Maratona 02/10 (fundação permanente):**
  1. Criar estrutura de pastas PERMANENTE completa (core/, specialists/, frontend/, scripts/) EXATAMENTE como definido em 00-Genese.
  2. Criar `requirements.txt` do core Python e instalar dependências.
  3. Inicializar **Next.js 15 + shadcn/ui + TailwindCSS 4** em `frontend/` com layout 3 colunas mínimo.
  4. Criar **todos os esqueletos de classes e interfaces** (orchestrator.py, memory_manager.py JSON backend, hybrid_router.py local-only, todos os 8 specialists).
  5. Implementar **`specialists/llm_core/model_handler.py`** real (llama.cpp DirectML + Llama 3.1 8B).
  6. **Começar download do Llama 3.1 8B Instruct Q4_K_M (~6GB)** em segundo plano direto em `G:\models\llm_core\`.
  7. Criar `scripts/run_chat_cli.py` para primeira conversa por texto.
  8. Quando download acabar: primeira palavra do Prometeu. 🎂

---