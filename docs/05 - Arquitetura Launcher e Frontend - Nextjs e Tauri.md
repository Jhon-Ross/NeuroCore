# 05 - Arquitetura Launcher + Front-end — Next.js + Tauri = App Desktop e Web (mesmo código)

> Data de criação: 2026-09-28
> Status: #frontend #nextjs #tauri #launcher
> Objetivo: Documentar a escolha do stack do front-end e do launcher desktop, como o Jhon pediu: "dois cliques abre um app como se fosse um jogo/programa, sem navegador visível, mas faz TUDO que o navegador faz."

---

## 🌳 Lugar na Árvore do Conhecimento

> **Pai (de onde eu venho):** [00 - Genese - A Ideia Completa do NeuroCore](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/00%20-%20Genese%20-%20A%20Ideia%20Completa%20do%20NeuroCore.md) → A RAIZ. Define que o projeto terá interface SaaS Premium e evolução infinita.
>
> **Irmãos relevantes:**
> - [04 - Design System do Prometeu](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/04%20-%20Design%20System%20do%20Prometeu%20-%20Identidade%20Visual.md) → Este documento DEFINE COMO a interface deve parecer. O documento 05 define COM QUE TECNOLOGIA implementar esse design.
> - [02 - Meta Maratona 02-10](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/02%20-%20Meta%20Maratona%2002-10%20-%20Prometeu%20Falando%20e%20Trabalhando.md) → Plano diário de construção do front: Next.js desde o Dia 1.
> - [03 - Diario - 2026-09-28 - Dia 0 - Genese](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/03%20-%20Diario%20-%202026-09-28%20-%20Dia%200%20-%20Genese.md) → Decisão de NÃO usar Streamlit, ir direto Next.js permanente.

---

## 🗣️ Traduzindo a sua dúvida em termos técnicos

Você pediu:
> "Quero um Launcher pra dar dois cliques e abrir o painel de controle pra iniciar a pagina no navegador OU como um app, programa ou jogo onde abre aquela tela e conseguimos mexer mas sem utilizar o navegador mas fazer tudo que fosse possivel fazer no navegador entende?"

**Resumo da ópera**: Você quer o que a indústria chama de **Aplicativo Desktop Híbrido**. É um app que dá a sensação de programa nativo (dois cliques no ícone, janela própria, aparece na barra de tarefas como programa normal, não parece que tá no Chrome), mas por baixo usa a mesma engine do navegador (HTML/CSS/JS/React) pra renderizar tudo. Tudo que você consegue fazer no navegador (chat, botão de voz, gráficos de status da VRAM) funciona exatamente igual no app desktop.

Exemplos de programas que funcionam EXATAMENTE assim hoje: Discord, Slack, VS Code, Spotify Desktop, Figma Desktop, Obsidian. Ou seja, é 100% padrão de mercado.

---

## ✅ Stack Escolhido (definitivo, não muda)

> **⚠️ DECISÃO SÊNIOR CORRIGIDA NO DIA 1 (28/09)**:
> Não usamos **Next.js 15 / React 19 / TailwindCSS 4**. Todos são muito novos em setembro/2026 e quebravam a instalação do `shadcn/ui` (nosso acelerador de componentes). Abaixo, a stack **REAL e PERMANENTE** que de fato está instalada em `frontend/`:

| Camada | Tecnologia | Por quê? |
|---|---|---|
| 🧩 **UI / Front-end** | **Next.js 14.2.35 ESTÁVEL + React 18 + TypeScript + TailwindCSS 3 + shadcn/ui (iniciar Dia 2)** | Decisão de estabilidade. Next 14 é a versão LTS de mercado em 2026. Evitamos bugs de compatibilidade de shadcn/ui com React 19. shadcn/ui = componentes prontos SaaS Premium/Enterprise (igual Linear/Vercel/Notion). TailwindCSS implementa a paleta PRETO #07070A + ÂMBAR #F59E0B do [04 - Design System](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/04%20-%20Design%20System%20do%20Prometeu%20-%20Identidade%20Visual.md). |
| 🚀 **Launcher Desktop (o "app de dois cliques")** | **Tauri v2 (Rust no núcleo)** | Alternativa MODERNA e MUITO MELHOR ao Electron (que é o que o Discord/VS Code usam antigamente). Peso final do app instalado: ~5~10MB (contra ~200MB do Electron). Usa **WebView nativo do Windows** (Edge WebView2) — já vem pré-instalado em todo Windows 10/11. Zero bloatware. |
| 🔗 **Comunicação front ↔ Cérebro Prometeu** | **FastAPI REST + WebSocket (core/api.py :8000)** | Já planejado na arquitetura permanente. Tanto o Next.js no navegador quanto o launcher Tauri conversam com o **mesmo backend FastAPI**. Nenhuma lógica duplicada. `GET /api/status` entrega o painel inteiro, `POST /api/chat` roda uma mensagem, `WS /ws/sparklines` entrega CPU/RAM/VRAM em 1Hz.

### 💡 O que isso significa na prática para VOCÊ:

1. **Mesmo código, duas experiências**:
   - Clica no `Prometeu Launcher.exe` no Desktop → abre janela nativa de app (igual Discord). Uso diário.
   - Digita `http://localhost:3000` no navegador qualquer outra máquina da sua rede Wi-Fi → abre EXATAMENTE a mesma interface, exatamente o mesmo Prometeu. Acesso remoto dentro de casa.
   - Nenhuma diferença de funcionalidade entre os dois modos.

2. **Back-end rodando em segundo plano**:
   - O cérebro do Prometeu (FastAPI + modelos carregados na VRAM) roda como serviço ou como processo do PowerShell.
   - O launcher só é a "janela para ver e controlar o cérebro" — se você fechar o launcher, o cérebro pode continuar rodando ouvindo comandos de voz por exemplo, e você abre o launcher de novo depois pra ver o histórico.

---

## 🏗️ Como tudo se encaixa (Arquitetura de comunicação)

```
┌────────────────────────────────────────────────────────────────────┐
│ SEU PC (DESKTOP-JHON)                                              │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │  PROMETEU CORE (Python + FastAPI + llama.cpp DirectML)   │      │
│  │  ← executado via PowerShell / Windows Service            │      │
│  │  porta 8000: REST + WebSocket                            │      │
│  │  carrega modelos em G:\models\ na RX 7600 8GB VRAM      │      │
│  └──────────────────────────┬───────────────────────────────┘      │
│                             │ HTTP / WS em localhost:8000           │
│           ┌─────────────────┼─────────────────┐                    │
│           │                 │                 │                    │
│ ┌─────────▼───────┐ ┌───────▼────────┐ ┌──────▼────────────────┐  │
│ │  NEXT.JS WEB    │ │  TAURI LAUNCHER│ │  OUTRO PC/CELULAR     │  │
│ │  (localhost:3000│ │  EXE DESKTOP   │ │  na rede Wi-Fi        │  │
│ │  Chrome/Edge)   │ │  (App de dois  │ │  acessa 192.168.x.x   │  │
│ │                 │ │   cliques)     │ │  :3000                │  │
│ └─────────────────┘ └────────────────┘ └───────────────────────┘  │
│                                                                    │
│  G:\models\ (90GB de modelos)                                     │
│  G:\memory\ (10GB de memória/aprendizado)                         │
└────────────────────────────────────────────────────────────────────┘
```

---

## 📅 Ordem de implementação (alinhada com a maratona 02/10)

**DECISÃO CORRETA**: NENHUM front-end provisório. **Vamos direto pro Next.js permanente desde o primeiro dia.** Não perdemos tempo criando Streamlit e apagando depois. O que a gente tem no dia 02/10 é o **Next.js v0.1** (versão incompleta, faltando detalhes de UI polida, mas NADA é jogado fora — a gente só adiciona telas e componentes depois, sem reescrever estrutura).

| Marco | O que roda | Estado real (atualizado pós D1 28/09) |
|---|---|---|
| **DIA 1 (28/09)** | Criar esqueleto PERMANENTE de **Next.js 14.2.35 ESTÁVEL + TailwindCSS 3 + TypeScript App Router src-dir** dentro de `frontend/`. shadcn/ui pra Dia 2. Layout 3 colunas FIXAS (sidebar 240px | chat central | painel direito RPG 320px) com Design System PRETO #07070A + ÂMBAR #F59E0B 100% aplicado. | ✅ **CONCLUÍDO.** Tudo funcionando em http://localhost:3000. Painel direito já mostra Nível Global LVL 1, 7 habilidades (Córtex Geral ATIVO), 2 Feitos (Wall of Wins), sparklines placeholder de CPU/RAM/VRAM/API. Input de chat só será conectado no Dia 2 via FastAPI. |
| **DIA 2 (29/09)** | Conectar Next.js ao backend FastAPI via REST + WebSocket. Primeira tela de Chat por texto funcionando no navegador. Instalar shadcn/ui. | 📅 Agendado. Chat do navegador passa a enviar mensagens de verdade pro orquestrador Python, resposta aparece na UI, painel RPG lê `/api/status` real. |
| **DIA 3 (30/09)** | Implementar: (1) botão de voz no chat (gravador de áudio → API → Whisper → XTTS) (2) Painel de Status com sparklines reais de CPU/RAM/VRAM via WebSocket (3) tela de Automação SO com botões. | 📅 Agendado. |
| **DIA 4 (01/10)** | Polimento do layout 3 colunas, estética SaaS premium, botão de microfone global na topbar, upgrade dos scripts iniciar/parar prometeu.ps1 para lançar FastAPI :8000 + Next :3000 juntos. | 📅 Agendado. |
| **🎂 DIA D 02/10** | **Next.js v0.1 100% funcional** rodando em `http://localhost:3000` + backend FastAPI em `:8000`. | 📅 Meta da maratona. |
| **Fase 2 (semana 3~4)** | 🚀 **Tauri v2** empacota o Next.js que já existe dentro do Launcher Desktop (.exe de 2 cliques). | 📅 Empacotamento sem alterar o código do Next.js existente. |

---

## 🚀 Como o Launcher Tauri Vai Ser pra Você

### Dia a dia:

1. **Você baixa o arquivo `Prometeu-Launcher-Setup.exe` (ou `.msi`) de ~10MB.**
2. **Dois cliques pra instalar** (como qualquer jogo/programa). Cria atalho no Desktop e menu Iniciar.
3. **Dois cliques no atalho:**
   - O launcher detecta se o core do Prometeu já tá rodando. Se não tiver, ele sobe o `python -m core.api` automaticamente em segundo plano (você não vê o terminal se não quiser).
   - Abre uma janela preta/âmbar linda, com a interface que a gente definiu no Design System.
   - Parece que você abriu o Discord ou o Steam. Nenhuma barra de endereço de navegador visível.
4. **Você fecha a janela:** o launcher pergunta "Manter Prometeu rodando em segundo plano ouvindo a voz?" → se sim, fecha só a janela, o core continua vivo e acordado se você falar "ei Prometeu". Se não, desliga tudo.

---

## 🔗 Links relacionados

- [[04 - Design System do Prometeu]] (cores preto + âmbar, layout 3 colunas, tipografia)
- [[00 - Gênese — A Ideia Completa do NeuroCore]] (requisito de estética SaaS Premium Enterprise)
- [[02 - Meta Maratona 02/10]] (ordem de implementação: Streamlit dia 3, Next.js semana seguinte, Tauri Fase 2)
