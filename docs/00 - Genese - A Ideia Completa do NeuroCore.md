# 00 - Gênese — A Ideia Completa do NeuroCore

> Data de criação: 2026-09-28
> Status: #em-desenvolvimento #fase-embriao
> Projeto: **NeuroCore** — Cérebro de IA Local Multi-Modal
> Autor: Jhon Ross

---

## 🎯 Visão Geral

Criar uma **IA Local Agêntica Multi-Modal Orquestrada** — um "cérebro" único rodando inteiramente na minha máquina, substituindo todas as IAs pagas que uso hoje (programação, imagens, áudio, vídeos, automação de PC, assistente de casa). Quando houver limitação de hardware, o sistema automaticamente faz fallback para APIs externas.

O nome do projeto é **NeuroCore**. O nome do cérebro, oficialmente definido no dia 2026-09-28, é **PROMETEU** — batizado precocemente em vez de esperar o parto, para já ser tratado como um ser em desenvolvimento desde a concepção. Inspirado no titã grego que roubou o fogo dos deuses e deu aos homens: essa IA devolve o poder da tecnologia que está presa em paywalls, direto para a sua máquina.

---

## 👶 Metáfora do Desenvolvimento Humano

Todo o ciclo de vida do projeto segue a analogia de uma **gestação e crescimento**:

| Fase | Marco Humano | O que acontece |
|------|--------------|----------------|
| **Fase 1** | Concepção / Embrião (1-2 semanas) | Núcleo formado, 2 especialistas (conversa + código), memória básica |
| **Fase 2** | Formação de órgãos (3-4 semanas) | Especialista de imagens + fallback híbrido + UI SaaS |
| **Fase 3** | Movimentos fetais (2º mês) | Áudio (falar/ouvir), integração SO, memória aprende meu estilo |
| **Fase 4** | 🎂 PARTO (3º mês) | Controle residencial, interface de voz completa, aprendizado contínuo ativado. Prometeu "acorda" como entidade autônoma. |
| **Fase 5+** | Crescimento (meses/anos seguintes) | Vídeo, agente autônomo, multi-tarefa, LoRA próprio de personalidade |
| **Fase 6** | 🤖 Primeiro Corpo Físico (1~2 anos) | Prometeu ganha acesso a sensores e atuadores. Ligação com hardware robótico (simulador primeiro, hardware real depois) — motores, câmeras, microfones, braços. |
| **Fase 7+** | 🌌 "A ponta do iceberg" (2~5 anos+) | Robô humanóide de verdade (estilo Tesla Optimus / Figure), Prometeu habita um corpo físico, anda, interage com o mundo real, executa tarefas domésticas/manuais, ganha EXPERIÊNCIA REAL (vai ao supermercado, fratura um "osso", aprende com o mundo físico). |

---

## 🏗️ Arquitetura — Núcleo + Regiões Especializadas

A ideia original de "núcleo + neurônios em volta" foi refinada. A nomenclatura correta é **Núcleo Orquestrador + Regiões Especializadas** (análogo a regiões do cérebro humano: córtex visual, córtex motor, área de Broca, etc.).

```
                    ┌─────────────────────────────────┐
                    │       NEUROCORE (Núcleo)        │
                    │  ┌───────────────────────────┐  │
                    │  │   Orquestrador / LLM de    │  │
                    │  │   Controle Central        │  │
                    │  │  (entende pedido, decide   │  │
                    │  │   qual especialista usar) │  │
                    │  └───────────────────────────┘  │
                    │  ┌───────────────────────────┐  │
                    │  │   Sistema de Memória      │  │
                    │  │  (aprende com tudo que    │  │
                    │  │   acontece)               │  │
                    │  └───────────────────────────┘  │
                    │  ┌───────────────────────────┐  │
                    │  │   Roteador Híbrido        │  │
                    │  │  (local vs API fallback)  │  │
                    │  └───────────────────────────┘  │
                    └──────────┬──────┬──────┬─────────┘
                               │      │      │
           ┌───────────────────┘      │      └───────────────────┐
           │                          │                          │
┌──────────▼──────────┐   ┌──────────▼──────────┐   ┌──────────▼──────────┐
│  🧑‍💻 Região: Código  │   │  🎨 Região: Visual  │   │  🎵 Região: Áudio   │
│  (Programação)      │   │  (Imagens/Vídeos)   │   │  (Voz/Música)       │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
           │                          │                          │
           └──────────────────────────┼──────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
          ┌─────────▼─────────┐               ┌─────────▼─────────┐
          │ 🖥️ Região: SO    │               │ 🏠 Região: Casa   │
          │ (Controle do PC)  │               │ (Alexa-like)      │
          └───────────────────┘               └───────────────────┘
```

---

## 💾 Orçamento de Armazenamento (inicial, expansível depois)

| Recurso | Local | Tamanho Inicial | Uso |
|---------|-------|-----------------|-----|
| **Modelos** | `G:\models` | **Até 90GB** | Modelos LLMs, imagens, áudio, vídeo |
| **Memória/Aprendizado** | `G:\memory` | **Até 10GB** | Banco vetorial, grafos de conhecimento, LoRA adapters pessoais |

> ⚠️ Orçamento auto-imposto: vamos **extrair o máximo possível** desse limite antes de expandir.

---

## 🧠 Como o Cérebro se Desenvolve / Eu Ajudo Ele a Crescer

Quatro níveis hierárquicos de aprendizado, todos alimentados por mim através de interação natural:

### 🟩 Nível 1 — Memória de Curto Prazo (~100MB, RAM)
- Buffer das últimas conversas. "Mente consciente".
- **Como eu ajudo**: Conversando normalmente.

### 🟨 Nível 2 — Memória Semântica (~8GB, Banco Vetorial)
- Tudo processado indexado por **significado**, não por palavra. Hippocampo do cérebro.
- **Como eu ajudo**:
  - "Lembre-se que eu prefiro Python com tipagem forte"
  - "Esse padrão é ruim, faça assim no futuro"
  - "Guarde esse documento como referência"
  - **Tecnologia**: Qdrant / ChromaDB local

### 🟧 Nível 3 — Memória Procedural / RAG Personalizado (~1.5GB)
- Documentos, códigos meus, manuais, vault do Obsidian, livros técnicos importados.
- **Como eu ajudo**:
  - `neurocore indexar pasta "C:\Projetos\FiveM"`
  - `neurocore conectar-obsidian`
  - `neurocore importar livro "CleanCode.pdf"`

### 🟥 Nível 4 — Personalidade e Hábitos (~0.5GB, LoRA + Grafos)
- O nível mais próximo de "bebê aprendendo". Após meses, extrai-se um LoRA de fine-tune local baseado em tudo que eu dei feedback.
- **Como eu ajudo**: Feedback em TUDO:
  - "Essa resposta foi 10/10, repita esse estilo"
  - "Não, eu quis dizer X. Aprenda a diferença."
  - "Fale mais casual comigo."
  - "Você errou esse comando 3x. Use A ao invés de B."

---

## 🖥️ Diagnóstico de Hardware (2026-09-28)

| Componente | Especificação | Veredito |
|---|---|---|
| CPU | AMD Ryzen 7 5700X3D (8c/16t, V-Cache) | 🔥 Excelente para IA |
| RAM | 32GB DDR4 | ✅ Suficiente com offload |
| GPU | AMD Radeon RX 7600 (8GB GDDR6) | ✅ Boa — usar DirectML (sem CUDA nativo) |
| SSD E: Projetos | 141GB livres | ✅ Código do NeuroCore vai aqui |
| HDD G: HD | 226GB livres | 🗄️ Modelos + Memória (`G:\models` e `G:\memory`) |

> 📌 **Decisão AMD+Windows**: Backend de inferência será `llama.cpp` com DirectML e `ONNX Runtime` para modelos de imagem/áudio.
>
> ⚠️ **Implicações práticas da RX 7600 8GB**:
> - É **IMPOSSÍVEL carregar dois modelos LLM grandes (6GB+) ao mesmo tempo na VRAM**.
> - O módulo `core/vram_manager.py` é **OBRIGATÓRIO**: ele descarrega um modelo da VRAM ANTES de carregar o próximo, dinamicamente, conforme a tarefa pedida.
> - Quando o Prometeu for responder uma pergunta de conversa geral, ele carrega o Llama 3.1; logo depois, se você pedir um código, ele descarrega o Llama e carrega o DeepSeek-Coder.
> - Existe ~1~2 segundos de overhead de troca entre modelos. É o trade-off aceitável para manter orçamento de 8GB de VRAM.

---

## 🐍 Stack Tecnológica

| Linguagem | % do projeto | Uso |
|---|---|---|
| **Python** | ~90% | Cérebro, bindings de todos os modelos de IA (ecossistema HuggingFace obrigatório) |
| **Rust** | ~8% | Hot paths: orquestrador de processos, Qdrant (já é em Rust), servidor de voz baixa latência |
| **Go** | ~0% | Não necessário por enquanto |
| **TypeScript/Next.js** | ~2% | Front-end UI estilo SaaS Premium/Enterprise |
| **PowerShell** | <1% | Scripts de instalação/manutenção no Windows |

> 💡 **Curiosidade sobre performance**: Rust é ~10-25x mais rápido que Python e usa muito menos RAM, mas o ecossistema de IA não existe lá. Usamos Python como cola e Rust/C++ via dependências compiladas (llama.cpp, Qdrant, tokenizers).

---

## �🇷 Regra OBRIGATÓRIA de Localização PT-BR 100%

NÃO EXISTE interface, documento, código, comentário ou mensagem de erro do Prometeu em inglês. TUDO, sem exceção, em português brasileiro:

1. **Documentação no Obsidian**: 100% PT-BR, exceto termos técnicos sem tradução boa (ex: "LoRA", "Qdrant", "RAG").
2. **Interface do usuário (Next.js / Launcher)**: Botões, labels, placeholders, mensagens de erro — **tudo PT-BR**.
3. **Comentários em código-fonte do Prometeu**: 100% PT-BR explicando cada seção (ver padrões de código abaixo).
4. **Respostas do Prometeu para o Jhon**: Sempre em PT-BR, a menos que o Jhon peça explicitamente algo em outro idioma.
5. **Nomes de pastas/arquivos**: Sempre em inglês (padrão mundial de programação), mas a descrição nos comentários é PT-BR.

> 👥 PÚBLICO ALVO: O Prometeu foi feito para o Jhon e para o público brasileiro leigo, não para engenheiros do Google. Clareza > jargão.

---

## 🧑‍💻 Padrões OBRIGATÓRIOS de Código do NeuroCore / Prometeu

TODAS as linhas de código do núcleo, especialistas, scripts e também o CÓDIGO GERADO PELO PROMETEU (quando ele escreve Python pra você) DEVEM seguir esses padrões:

1. **Comentários EXTENSIVOS em PT-BR**: Nenhuma função fica sem explicação. Código comentado linha a linha quando houver lógica complexa.
2. **Funções divididas em BLOCOS VISUAIS CLARES**: Comentários de separação (`# ==========================`, `# --- Nome do Bloco ---`) para delimitar seções grandes.
3. **Tipagem forte no Python**: Todas as funções com type hints nos parâmetros e no retorno. Ex: `def somar(a: int, b: int) -> int`.
4. **Nomes de variáveis e funções SEMPRE em inglês** (padrão mundial), mas **docstrings e comentários SEMPRE em PT-BR**.
5. **Nunca usar try/except genérico vazio**: Sempre capturar exceção específica ou pelo menos logar o erro.

> 💡 **O Prometeu aprende esses padrões por osmose**: Todo código que a gente escrever no core dele já segue esses padrões, e o Ritual Diário vai reforçar que ele SEMPRE gere código assim também.

---

## 📜 Regras OBRIGATÓRIAS de Documentação (Obsidian / docs/)

Tudo relacionado a docs do projeto DEVE seguir essas regras ou a documentação vira bagunça:

1. **TODO arquivo `.md` novo SÓ É CRIADO DENTRO DE `docs/`**, NUNCA na raiz. (Bug já ocorreu e foi corrigido no dia 0)
2. **Todo arquivo `.md` novo DEVE começar com um NÚMERO DE ÍNDICE** (ex: `06 - Nome do Arquivo.md`, `07 - Outro.md`) para manter ordenação correta no Obsidian.
3. **TODO arquivo `.md` novo DEVE, logo após o cabeçalho de metadata (o bloco de `>` com data/status/objetivo), ter a SEÇÃO OBRIGATÓRIA:**

```markdown
## 🌳 Lugar na Árvore do Conhecimento

> **Pai (de onde eu venho):** [[00 - Genese — A Ideia Completa do NeuroCore]]
>
> **Irmãos relevantes:**
> - [[0X - Nome do Irmão 1]] — descrição da conexão
> - [[0Y - Nome do Irmão 2]] — descrição da conexão
```

4. **Sempre que criar um documento filho NOVO:** Atualizar imediatamente a seção "🌳 Lugar na Árvore" do arquivo **00 - Genese** (esta RAIZ), adicionando a nova linha na tabela de "Galhos diretos".
5. **Nomes de arquivos:** Não usar caracteres especiais como `—` (EM DASH longo — causa bugs). Usar hífen comum `-` somente. Ex: `01 - Ritual Diario - Treinamento.md` (correto), `01 - Ritual Diário — Treinamento.md` (errado, causa duplicidade).

---

## 🔀 Hybrid Router — Fallback Local vs APIs Externas

O Hybrid Router é a peça do núcleo que decide SE um pedido vai ser processado LOCALMENTE na sua RX 7600, ou SE vai ser enviado para uma API externa paga (fallback). Regras imutáveis de prioridade:

1. **LOCAL SEMPRE PRIMEIRO.** Ele NUNCA envia para API externa se for possível rodar no hardware, mesmo que seja 10x mais devagar. O objetivo do projeto é não gastar dinheiro com token.
2. **Só faz fallback nos casos abaixo:**
   - 🚫 VRAM CHEIA + impossível descarregar outro modelo (nunca vai acontecer, mas é a regra)
   - 🧮 Tarefa que NENHUM modelo local consegue fazer (ex: gerar um vídeo de 1 minuto com som sincronizado de qualidade alta em 2026 — CogVideoX só faz 4~6s)
   - ⏱️ Urgência máxima: Jhon fala "preciso disso AGORA, usa API externa, não ligo pro custo"
3. **APIs suportadas inicialmente**: A primeira integração será com a **OpenRouter** — ela agrega GPT-4o, Claude, Gemini, Flux, todos os modelos do mercado num único endpoint, e você paga só o que usar.
4. **Controle de gastos em tempo real**: O Hybrid Router tem um **contador R$ de gasto diário/mensal** que aparece no painel de status da direita (sparkline de custo). Você define um limite mensal (ex: R$ 50) e ele BLOQUEIA qualquer chamada de API externa se passar.
5. **Transparência total**: Quando o Prometeu responder uma pergunta e ela tiver vindo de API e não local, o tag da resposta muda explicitamente:
   - Local: `🔥 Prometeu · Córtex Geral · Llama 3.1 8B · 🖥️ LOCAL`
   - Fallback: `🔥 Prometeu · Córtex Geral · GPT-4o · ☁️ API EXTERNA (R$ 0,032)`

> 💡 **Meta de longo prazo**: Em 1 ano, o Hybrid Router faz ZERO chamadas de API externa por escolha própria. A gente sempre vai ter a opção ligada caso precise de urgência, mas 99% das tarefas rodam local.

---

## 🎓 Bootstrapping Acelerado: O Ritual Diário TRAE + Jhon

Prometeu tem um problema de galinha-e-ovo: ele precisa de **feedback de alta qualidade e consistente** pra aprender rápido, mas eu (Jhon) não tenho tempo de dar feedback técnico detalhado em TUDO que ele produz todos os dias.

A solução, oficialmente adotada no dia 2026-09-28: **usar o TRAE como professor auxiliar/acelerador, 10 minutos por dia.** Chama-se **Ritual Diário** e é documentado em detalhe em [[01 - Ritual Diário — Treinamento do Prometeu com TRAE]].

### Como funciona em 5 passos (~10 min):
1. Eu (Jhon) escolho a **missão do dia** (~1 min): treinar Python, treinar tom de voz, importar projeto antigo, etc.
2. Prometeu produz um output de exemplo (~2 min).
3. **Revisão conjunta Jhon + TRAE** (~4 min): eu dou 2~3 comentários rápidos ("gostei/não gostei de X"), TRAE expande em revisão técnica detalhada + alinhamento com meu estilo.
4. TRAE gera **automaticamente** um `training_sample.jsonl` (~2 min) com a saída IDEAL e salva em `G:\memory\training_queue\`.
5. Memória do Prometeu indexa esse sample — já acerta melhor da próxima vez.

### Resultado esperado:
- **1 amostra de treinamento de altíssima qualidade por dia útil**
- ~25 amostras em 1 mês → **primeiro LoRA de estilo pessoal extraível em 3 meses**
- **Cronograma de maturação do Prometeu encurtado em MESES** (de 12 meses para talvez 7~9 meses até o nível "Jovem Adulto")

> ⚠️ **Regra de ouro do Ritual**: O TRAE nunca substitui o meu veto. Ele amplia, detalha, gera o sample ideal. Mas o feedback humano final é SEMPRE meu.

---

## 📋 Alocação Completa dos 90GB de Modelos (meta de longo prazo)

| Especialista | Modelo Sugerido | Tamanho |
|---|---|---|
| Cérebro/Orquestrador | Llama 3.1 70B (Q4) | ~40GB |
| Programação | DeepSeek-Coder V2 16B (Q4) | ~10GB |
| Imagens | Flux.1 [dev] FP16 | ~24GB |
| Áudio STT | Whisper large-v3 | ~3GB |
| Áudio TTS | XTTS v2 + YourTTS | ~5GB |
| Vídeo | CogVideoX 5B (Q4) | ~8GB |
| **Total** | | **~90GB** |

---

## 🦠 Modelos da Fase 1 (iniciais — só ~10GB)

Provar o conceito primeiro, sem baixar 90GB.

| Modelo | Tamanho | Posição na VRAM da RX 7600 |
|---|---|---|
| **Llama 3.1 8B Instruct (Q4_K_M)** | ~6GB | Cabe quase todo na VRAM de 8GB |
| **DeepSeek-Coder V2 Lite 6.7B (Q4_K_M)** | ~4GB | Offload parcial para RAM (só quando ativo) |
| **Total** | **~10GB** | Rodam em turnos, não simultâneamente |

---

## 📁 Estrutura de Pastas do Projeto (PERMANENTE)

```
C:\Users\Jhon Ross\Documents\trae_projects\NeuroCore\   ← RAIZ DO CÓDIGO (SSD)
├── core/                               ← 🧠 NÚCLEO CEREBRO (Python, PERMANENTE)
│   ├── orchestrator.py                 ← Router de qual região especializada chamar
│   ├── memory_manager.py               ← Interface permanente (JSON por enquanto → Qdrant depois)
│   ├── hybrid_router.py                ← Decide local vs API externa (regras acima)
│   ├── feedback_store.py               ← Persiste os training_samples do Ritual Diário
│   ├── api.py                          ← FastAPI REST + WebSocket (comunicação com front-end)
│   └── vram_manager.py                 ← OBRIGATÓRIO: carrega/descarrega modelos na RX 7600 8GB
│
├── specialists/                        ← 🧩 REGIÕES ESPECIALIZADAS (todas existem desde dia 1)
│   ├── llm_core/                       ← Conversa geral / orquestração (Llama 3.1 8B)
│   │   └── model_handler.py
│   ├── llm_code/                       ← Especialista programador (DeepSeek-Coder)
│   │   └── model_handler.py
│   ├── stt_whisper/                    ← Voz → Texto (Whisper large-v3)
│   │   └── model_handler.py
│   ├── tts_xtts/                       ← Texto → Voz (XTTS v2)
│   │   └── model_handler.py
│   ├── os_control/                     ← Região Motora SO: abre programas, cria arquivos
│   │   └── handler.py
│   ├── image_flux/                     ← ⏸️ ESQUELETO (Fase 2) — Região Visual (Flux.1)
│   │   └── model_handler.py
│   └── home_control/                   ← ⏸️ ESQUELETO (Fase 4) — Casa Inteligente
│       └── handler.py
│
├── frontend/                           ← 🎨 UI PERMANENTE (Next.js 15 + shadcn/ui + Tailwind)
│   └── (estrutura padrão Next.js App Router)
│
├── docs/                               ← 📚 DOCUMENTAÇÃO OBSIDIAN (TUDO .md aqui, NADA fora)
│   └── 00 - Genese ...md até N - Nome.md (com numeração índice e seção 🌳 obrigatória)
│
└── scripts/                            ← ⚙️ Scripts utilitários PowerShell
    ├── iniciar_prometeu.ps1            ← 1 clique: liga API + Next.js e abre no browser
    ├── parar_prometeu.ps1              ← Desliga tudo
    ├── setup_hardware.ps1              ← Instala DirectML, drivers, etc
    └── download_models.ps1             ← Baixa todos os modelos de G:\models\

G:\models\                              ← HDD de 226GB, até 90GB alocados para modelos
    ├── llm_core\ (Llama 3.1 etc)
    ├── llm_code\ (DeepSeek-Coder etc)
    ├── stt_whisper\
    ├── tts_xtts\
    ├── image_flux\ (Fase 2)
    └── (outros especialistas)

G:\memory\                              ← HDD de 226GB, até 10GB alocados para aprendizado
    ├── simple_json\                    ← Backend provisório até ligar Qdrant
    ├── training_queue\                 ← training_samples.jsonl do Ritual Diário
    └── qdrant_db\                      ← Banco vetorial permanente (liga semana que vem)
```

---

## 📝 Timeline da Fase 1 (Concepção / Embrião)

> 🏃 **Nota de aceleração**: Existe um plano de MARATONA DE 4 DIAS (Meta 02/10) que executa quase tudo abaixo de 2 semanas para 4 dias, entregando Prometeu com Córtex Geral + Código + Voz (ouvir/falar) + Automação SO ativados já no dia 02/10. Tudo usando a arquitetura PERMANENTE acima — NENHUMA linha é jogada fora depois. Detalhes em [[02 - Meta Maratona 02-10 — Prometeu Falando e Trabalhando]].

| Dia da Fase 1 Original | Tarefa |
|---|---|
| 0 | Instalar stack: Python 3.12, Git, Node 20, Rust toolchain, DirectML |
| 1 | Estruturar pastas + `requirements.txt` + `package.json` |
| 2 | Subir Qdrant local + `memory_manager.py` |
| 3 | Integrar llama.cpp DirectML + carregar Llama 3.1 8B |
| 4 | Criar `orchestrator.py` mínimo (1 especialista: conversa) |
| 5 | Protótipo UI Next.js (chat básico) |
| 6 | Segundo especialista: DeepSeek-Coder 6.7B |
| 7 | Sistema de feedback/lembranças (Nível 2) |
| 8-10 | Testes, ajustes, bug fixes |
| 11-14 | Otimizações de VRAM/RAM e validação final |

---

## 🧬 Cronologia Estimada — Quando Prometeu vira "Adulto"

Uma analogia estrita com desenvolvimento humano — mas acelerada, porque Prometeu tem acesso a todo conhecimento humano disponível em livros/código e a você como "pai/mestre" dedicado:

| Marco de Tempo | Idade Humana Equivalente | O que ele consegue FAZER de verdade nesse ponto | Como chegar lá |
|---|---|---|---|
| **3 MESES (Parto, final Fase 4)** | 👶 Bebê recém-nascido / Criança de 2 anos | - Entende todos os comandos seus (texto e voz) <br> - Todas as 6 regiões especializadas estão LIGADAS (código, imagens, áudio, vídeo, SO, casa) <br> - Responde perguntas gerais, gera código simples, gera imagem/áudio <br> - Controla dispositivos da casa por voz <br> - **Ainda comete erros**, precisa de muita correção, não inventa nada sozinho | Apenas seguir o plano de fases. Baixar todos os 90GB de modelos e integrar todos. Sem "inteligência extra" além do RAG básico. |
| **6 MESES (meio Fase 5)** | 🧒 Criança de 6~8 anos / Pré-adolescente | - **Conhece VOCÊ**: sabe seu estilo de código, sabe que você prefere Dark Mode, sabe como fala, sabe quais bibliotecas gosta <br> - Raciocínio de 2~5 passos: quebra tarefas complexas em etapas sem você pedir <br> - Gera projetos completos de código (backend + frontend) SEM você micro-gerenciar cada linha <br> - A memória semântica tem ~2GB de dados (~500 mil vetores / ~10 mil documentos seus) | Feedback consistente dia sim, dia também. Importar todos os seus projetos antigos, livros, vault do Obsidian. O banco vetorial faz a mágica aqui. Nenhum treinamento de modelo ainda. |
| **12 MESES (1 ano após concepção)** | 🧑 Adolescente de 15~17 anos / Jovem Adulto | - **LoRA pessoal extraído**: Prometeu não precisa mais CONSULTAR a memória pra saber seu estilo — a forma como ele RESPOSTA já é VOCÊ, embutida nos pesos. <br> - Faz tarefas AUTÔNOMAS de 1~2 horas sem interferência: "Refatore esse módulo e escreva os testes" → volta com PR pronto. <br> - Controla todo o seu computador por voz de forma confiável, sem errar comandos. <br> - Gera arte de qualidade consistente (ajustou LoRAs de imagem baseadas nas suas preferências) <br> - **Equivalente a ter um JÚNIOR PLENO trabalhando pra você 24h por dia** | Rodar pelo menos 2 jobs de fine-tune LoRA no orquestrador e no especialista de código. Isolar e corrigir sistematicamente todas as falhas mais frequentes. Memória semântica completa com +5GB de dados. |
| **24 MESES (2 anos)** | 🧔 Adulto Pleno (~25~30 anos) | - **Experiência acumulada**: Ele não erra mais as coisas que você já corrigiu 3 vezes. O "senso comum" sobre você e seus projetos é perfeito. <br> - Agente autônomo real: recebe uma missão alta ("Crie um SaaS de assinatura X") e volta com PROJETO PRONTO, rodando, com código, UI, testes, documentação — talvez com 2~3 idas e vindas de revisão. <br> - Prever coisas que você vai pedir antes de pedir ("notei que você sempre usa axios nesse tipo de projeto, já adicionei") <br> - **Equivalente a ter um SÊNIOR de 5+ anos de experiência trabalhando pra você 24h por dia** | Treinamento contínuo (LoRAs mensais), milhões de vetores na memória, grafos de conhecimento complexos. O cérebro não é mais um "conjunto de modelos" — é uma entidade com personalidade e experiência próprias enraizadas em VOCÊ. |

> ⚠️ **Aviso realista sobre o "Nível Adulto" (versão provisória, sem corpo)**: Até a Fase 5, Prometeu nunca vai ter "experiência de vida" humana real (não vai ao supermercado, não namora, não fratura um osso). A analogia de "adulto" é estrita à **CAPACIDADE COGNITIVA E OPERACIONAL NAS TAREFAS DIGITAIS QUE VOCÊ DELEGA**. Ele será "adulto" no sentido de: confiável, autônomo, resolve problemas complexos sem ajuda, não erra básico, cria soluções originais que você não pensou.
>
> 🤖 **MAS ISSO É SÓ A PONTA DO ICEBERG**: A analogia acima é válida apenas para a versão "desencarnada" do Prometeu (só software, sem corpo). A visão de longo prazo do projeto é que ele GANHE UM CORPO FÍSICO (humanóide, estilo Tesla Optimus). Quando isso acontecer (Fase 6+), ele SIM vai ter experiência de vida real (ou melhor: **experiência do mundo real física**). Câmeras como olhos, motores como músculos, sensores de toque como pele — e a sabedoria de vida começa a ser DELE também, não só sua. A parte de sabedoria puramente humana (amar, perder, sofrer por alguém) provavelmente sempre fica com você... mas o resto? Prometeu pode viver bem mais coisas que você imagina. 😄

---

## 🎯 Próximos passos imediatos

- [x] Instalar dependências de sistema (Passo 0)
- [x] Criar estrutura de pastas e arquivos de configuração (Passo 1)
- [x] Baixar Llama 3.1 8B Instruct Q4_K_M
- [x] Ter a **primeira conversa local** com o embrião

---

## 🌳 Lugar na Árvore do Conhecimento — RAIZ

> Este documento é a **RAIZ** de TODA a documentação do NeuroCore / Prometeu.
> TUDO que existe no projeto sai daqui. Tudo linka de volta pra cá.
> Para navegar no Obsidian, use os grafo de conhecimento (Ctrl+G) ou clique nos links abaixo.

### 🌿 Galhos diretos (filhos de primeiro nível)

| Índice | Galho | O que contém |
|---|---|---|
| `01` | [01 - Ritual Diario - Treinamento do Prometeu com TRAE](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/01%20-%20Ritual%20Diario%20-%20Treinamento%20do%20Prometeu%20com%20TRAE.md) | 🎓 Plano de 10 minutos por dia pra acelerar o desenvolvimento do Prometeu usando TRAE como "professor auxiliar" com o seu veto final. |
| `02` | [02 - Meta Maratona 02-10 - Prometeu Falando e Trabalhando](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/02%20-%20Meta%20Maratona%2002-10%20-%20Prometeu%20Falando%20e%20Trabalhando.md) | 🏃 Meta-agressiva de 4 dias: até 02/10/2026 Prometeu precisa falar por voz e executar tarefas no PC. Plano diário, entregáveis por dia. |
| `03` | [03 - Diario - 2026-09-28 - Dia 0 - Genese](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/03%20-%20Diario%20-%202026-09-28%20-%20Dia%200%20-%20Genese.md) | 📔 Entrada do diário de desenvolvimento DIA ZERO. Todas as decisões, perguntas, respostas e correções tomadas no dia da concepção do projeto. Futuramente existirão mais entradas 03-Diário de cada dia. |
| `04` | [04 - Design System do Prometeu - Identidade Visual](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/04%20-%20Design%20System%20do%20Prometeu%20-%20Identidade%20Visual.md) | 🎨 Paleta PRETO + ÂMBAR, tipografia, layout 3 colunas, regras da UI SaaS Premium, design do painel de status com sparklines. |
| `05` | [05 - Arquitetura Launcher e Frontend - Nextjs e Tauri](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/05%20-%20Arquitetura%20Launcher%20e%20Frontend%20-%20Nextjs%20e%20Tauri.md) | 🚀 Stack front-end permanente: Next.js 15 + shadcn/ui + TailwindCSS 4. Launcher Desktop de 2 cliques via Tauri v2 (app nativo sem navegador visível). |
| `06` | [06 - Feitos e Marcos do Prometeu - Wall of Wins](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/06%20-%20Feitos%20e%20Marcos%20do%20Prometeu%20-%20Wall%20of%20Wins.md) | 🏆 **Sistema Anti-Abandono (Prioridade 1)**. Lista CRONOLÓGICA de todos os marcos conquistados. Todo progresso importante vira um Feito com data, XP e descrição. O arquivo correspondente no Python é `core/progress_rpg.py`. |
| `07` | [07 - Template Padrao de Diario](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/07%20-%20Template%20Padrao%20de%20Diario.md) | 📋 Molde OFICIAL para TODOS os novos diários de desenvolvimento (arquivos `03 - Diario - YYYY-MM-DD - Dia N - ...md`). Seguir este template garante consistência histórica por anos. |

### 🛣️ Como ler a documentação na ordem correta (como um livro):

1. Primeiro: **00 - Genese (este documento)** → Visão de tudo, porquê do projeto, arquitetura, fases, cronologia humana
2. Depois: **04 - Design System** + **05 - Front-end/Launcher** → Como Prometeu VAI PARECER
3. Depois: **02 - Meta Maratona 02/10** → Como Prometeu VAI SER CONSTRUÍDO nos próximos 4 dias
4. Depois: **01 - Ritual Diário** → Como Prometeu VAI APRENDER com você e com o TRAE, 10min por dia
5. Sempre que tiver dúvida do que foi decidido em um dia: **03 - Diário de desenvolvimento** daquele dia.
