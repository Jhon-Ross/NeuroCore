# 04 - Design System do Prometeu — Identidade Visual + Front-end

> Data de criação: 2026-09-28
> Status: #identidade-visual #design-system #saaS-premium
> Objetivo: Definir as escolhas visuais permanentes do Prometeu — cores, tipografia, layout do dashboard, para nunca mais termos que discutir isso.

---

## 🌳 Lugar na Árvore do Conhecimento

> **Pai (de onde eu venho):** [00 - Genese - A Ideia Completa do NeuroCore](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/00%20-%20Genese%20-%20A%20Ideia%20Completa%20do%20NeuroCore.md) → A RAIZ. Contém o requisito explícito do autor: UI estilo SaaS Premium/Enterprise, estética minimalista, zero elementos amadores.
>
> **Irmãos relevantes:**
> - [02 - Meta Maratona 02-10](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/02%20-%20Meta%20Maratona%2002-10%20-%20Prometeu%20Falando%20e%20Trabalhando.md) — Dia 3 (30/09): Implementar sparklines do painel de status + layout 3 colunas no Next.js, seguindo EXATAMENTE este design system.
> - [05 - Arquitetura Launcher e Frontend](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/05%20-%20Arquitetura%20Launcher%20e%20Frontend%20-%20Nextjs%20e%20Tauri.md) — Stack tecnológica do front (Next.js + TailwindCSS + shadcn/ui) que implementa este design system.
> - [03 - Diario - 2026-09-28 - Dia 0 - Genese](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/03%20-%20Diario%20-%202026-09-28%20-%20Dia%200%20-%20Genese.md) — Decisão da paleta PRETO + ÂMBAR e os ajustes do painel com sparklines.

---

## 🎯 Premissa fundamental de design

Estética **SaaS Premium / Enterprise**, estilo minimalista e moderno. NADA de elementos "amadores". Zero gradients coloridos gritantes, zero emojis por todo canto, zero sombras gigantes fake. O painel deve parecer um produto pago de R$ 200/mês (como Linear, Raycast, Vercel, Notion).

---

## 🎨 Paleta de Cores Permanente (Tema Dark, o único tema que existe)

O Prometeu é um titã grego que roubou o fogo dos deuses. A identidade visual tem que refletir isso: PRETO (vazio, universo, poder ancestral) + UMA ÚNICA cor de destaque (o fogo roubado) em tons quentes.

### Paleta Primária (Fogo do Olimpo)

| Token | Valor Hex | Uso |
|---|---|---|
| `--bg-0` (preto profundo - fundo principal) | `#07070A` | Fundo das telas, painel principal |
| `--bg-1` (cinza muito escuro - elevação 1) | `#0D0D12` | Cards, containers elevados, sidebars |
| `--bg-2` (cinza escuro - elevação 2) | `#15151C` | Inputs, botões secundários, hover em cards |
| `--bg-3` (cinza - elevação 3) | `#1F1F2A` | Divisórias, bordas internas, linhas divisoras |
| `--border` (borda ultra-fina) | `#2A2A38` | Todas as bordas visíveis (espessura 1px, sem gradiente) |

### Acentos (O Fogo de Prometeu - Laranja Âmbar Quente)

| Token | Valor Hex | Uso |
|---|---|---|
| `--accent` (laranja âmbar suave - o fogo) | `#F59E0B` | Botão primário, indicador de voz ativa, "prometeu está pensando...", status de sucesso do launcher |
| `--accent-hover` (laranja um pouco mais quente) | `#F97316` | Hover do botão primário |
| `--accent-dim` (laranja 30% opacidade - brilho fraco) | `rgba(245, 158, 11, 0.12)` | Glow suave atrás de elementos de destaque (sombra interna sutil) |
| `--accent-text` (cor do texto do botão primário) | `#0C0A04` | Texto escuro em cima do fundo âmbar (contraste alto, leitura fácil) |

### Semântica

| Token | Valor Hex | Uso |
|---|---|---|
| `--success` | `#10B981` | Operações concluídas (ex: "modelo carregado na VRAM", "voz detectada") |
| `--warning` | `#EAB308` | Avisos (ex: "VRAM em 85%", "fallback para API externa ativado") |
| `--danger` | `#EF4444` | Erros (ex: "falha ao carregar modelo", "microfone não encontrado") |
| `--info` | `#3B82F6` | Informação neutra (ex: "memória RAM: 18GB de 32GB usados") |

### Tipografia (Textos)

| Token | Valor Hex | Uso |
|---|---|---|
| `--text-1` (branco puro - títulos) | `#F1F5F9` | Títulos grandes, nome do Prometeu no topo, valores grandes de métricas |
| `--text-2` (cinza claro - corpo principal) | `#CBD5E1` | Corpo de texto, mensagens do chat do usuário, descrições |
| `--text-3` (cinza médio - secundário) | `#94A3B8` | Legendas, timestamps, labels secundárias, placeholders de input |
| `--text-4` (cinza apagado - desativado) | `#64748B` | Textos desabilitados, labels de itens inativos, info irrelevante |

---

## 🔤 Tipografia

Família de fontes permanente. Não muda nunca:

| Uso | Fonte | Peso |
|---|---|---|
| **Interface geral (textos, UI, botões)** | **Inter** (padrão enterprise do mercado) | 400, 500, 600, 700 |
| **Código (respostas do llm_code, blocos ```)** | **JetBrains Mono** (padrão de IDE premium) | 400, 500 |
| **Números de métricas (VRAM, RAM, tokens/s)** | **JetBrains Mono** (alinhamento perfeito de dígitos) | 500, 600 |
| **Nome do Prometeu + Logo (opcional)** | **Space Grotesk SemiBold** (moderna, levemente futurista, sem ser exagerada) | 600, 700 |

Tamanhos padrão:
- Título principal da página: `32px` / `36px` (Space Grotesk 700)
- Subtítulo: `18px` / `24px` (Inter 500, --text-2)
- Texto corpo: `14px` / `20px` (Inter 400, --text-2)
- Código inline/bloco: `13px` / `18px` (JetBrains Mono 400)
- Legendas pequenas: `12px` / `16px` (Inter 400, --text-3)

---

## 🖼️ Layout Fixo do Dashboard Principal

Sempre o mesmo layout, em TODAS as telas. Não tem surpresa. Sempre 3 colunas (ou 2 quando a lateral de detalhes estiver fechada).

```
┌────────────────────────────────────────────────────────────────────────────┐
│  🔥 Prometeu        🔍 Busca global          ⚙️ Perfil/Jhon    🔴 Mic   ▢ X │
├──────────────┬───────────────────────────────────────────┬─────────────────┤
│              │                                           │                 │
│  Sidebar     │  Área Central Principal                  │  Painel de      │
│  Larga       │  (Conteúdo dinâmico: Chat, Código,       │  Status do      │
│  240px       │   Imagens, Automação, Casa...)           │  Cérebro        │
│              │                                           │  320px          │
│  🧠 Chat     │                                           │                 │
│  💻 Código   │  ← conteúdo troca aqui conforme          │ ┌─────────────┐ │
│  🎨 Imagens  │    o item da sidebar selecionado         │ │ 🟢 PROMETEU  │ │
│  🎧 Voz      │                                           │ │ Online       │ │
│  🖥️ SO       │                                           │ ├─────────────┤ │
│  🏠 Casa     │                                           │ │ GPU RX 7600 │ │
│  📚 Memória  │                                           │ │ ┌──────────┐│ │
│  📊 Analytics│                                           │ │ │ ▁▂▃▅▇█▆▄▂││ │  ← sparkline VRAM 60s
│              │                                           │ │ └──────────┘│ │
│  [+ Região   │                                           │ │ 6.2GB/8GB  │ │
│   em breve]  │                                           │ ├─────────────┤ │
│              │                                           │ │ CPU 5700X3D │ │
│              │                                           │ │ ┌──────────┐│ │
│              │                                           │ │ │ ▅▇█▆▄▅▇█▆││ │  ← sparkline CPU 60s
│              │                                           │ │ └──────────┘│ │
│              │                                           │ │ 42% / 16t   │ │
│              │                                           │ ├─────────────┤ │
│              │                                           │ │ RAM DDR4   │ │
│              │                                           │ │ ┌──────────┐│ │
│              │                                           │ │ │ ▂▄▅▆▇█▇▆▅▄││ │  ← sparkline RAM 60s
│              │                                           │ │ └──────────┘│ │
│              │                                           │ │ 18GB/32GB  │ │
│              │                                           │ ├─────────────┤ │
│              │                                           │ │ 🔌 API Ext │ │
│              │                                           │ │ ┌──────────┐│ │
│              │                                           │ │ │___________││ │  ← sparkline latência API (0 se OFF)
│              │                                           │ │ └──────────┘│ │
│              │                                           │ │ OFF / R$0  │ │
│              │                                           │ ├─────────────┤ │
│              │                                           │ │ 🎙️ Mic: OK │ │
│              │                                           │ │ 🔊 Spk: OK │ │
│              │                                           │ │ 💾 18GB d  │ │  ← 18GB de dados na memória semântica
│              │                                           │ └─────────────┘ │
└──────────────┴───────────────────────────────────────────┴─────────────────┘
```

### Regras do layout:
1. **Largura mínima**: 1200px (abaixo disso o painel lateral de status some e o layout vira 2 colunas).
2. **Sidebar esquerda**: Sempre fixa. Cada ícone = uma região do cérebro. Regiões ainda não ativadas (imagens, casa) aparecem com `[EM BREVE]` cinza.
3. **Topbar**: Sempre fixa. Mostra o nome 🔥 Prometeu (com o acento âmbar), um botão grande de microfone (ao clique = começa a ouvir você), e o status geral.
4. **Painel de Status da direita**: O "sinal vital do Prometeu". **Sempre vivo, atualizado a cada 1 segundo via WebSocket.** É o painel MAIS IMPORTANTE da interface. Elementos obrigatórios:
   - **Status geral**: "Online" (verde) / "Pensando..." (Âmbar piscando) / "Erro" (Vermelho)
   - **GPU / VRAM**: Número + **gráfico sparkline de 60 segundos atrás** (linha minúscula, sem eixos, 40px de altura). Você vê em tempo real a VRAM subir quando ele carrega um modelo.
   - **CPU**: Mesmo formato. Uso total + sparkline de 60s.
   - **RAM**: Mesmo formato. GB usados + sparkline.
   - **API Externa (fallback)**: Mostra se o hybrid router está usando API externa, a latência média, e um contador de custo estimado em R$ (se houver). Quando está OFF, o sparkline fica zerado.
   - **Periféricos**: Status do microfone (OK / Mudo / Não detectado) e do alto-falante.
   - **Uso da memória de aprendizado**: Quanto GB dos 10GB de `G:\memory` já foram usados.
   - Todos os sparklines seguem a regra: **cor âmbar `#F59E0B` se uso >70%, cor info `#3B82F6` se uso <70%, cor danger `#EF4444` se >95%.**

---

## 💬 Tela de Chat (primeira tela que o usuário vê)

```
🧠 Chat (selecionado na sidebar)

 Jhon Ross (você)           ───────────────────────────────────► 21:42
 ┌──────────────────────────────────────────────────────────┐
 │ Boa noite Prometeu, tudo bem? Me explica o que é pensa-  │
 │ mento crítico em 2 frases.                               │
 └──────────────────────────────────────────────────────────┘

 🔥 Prometeu                          [Córtex Geral · Llama 3.1 8B · local] ◄── tag
 ┌──────────────────────────────────────────────────────────┐
 │ Pensamento crítico é questionar informações antes de     │
 │ aceitá-las como verdade, em vez de repetir cegamente o   │
 │ que ouviu. Significa separar fatos de opinião, detectar  │
 │ vieses e só então formar uma conclusão própria.          │
 └──────────────────────────────────────────────────────────┘
                                                              🔁 Copiar 🔊 Ouvir

 ┌─────────────────────────────────────────────────────────────────┐
 │ 🎙️  Fale algo ou digite...                                        [Enter] enviar │
 └─────────────────────────────────────────────────────────────────┘
  [🎤 Pressionar para falar] — botão âmbar grande abaixo do input
```

### Regras do chat:
- Mensagens do Prometeu sempre com a tag pequena acima informando **qual região cerebral gerou a resposta + qual modelo + se foi local ou API**. Isso te dá transparência total.
- Botões sempre presentes abaixo da resposta do Prometeu: Copiar / Ouvir (para TTS ler em voz alta).
- Se o Prometeu tiver que chamar uma região diferente (ex: você pediu código e ele acionou llm_code), a tag muda para `💻 Código · DeepSeek-Coder 6.7B · local`.

---

## 🚀 Laucher (App Desktop "Tela Cheia" sem navegador)

Nome do arquivo `.exe`: **Prometeu Launcher**
Como funciona: você dá 2 cliques no ícone no Desktop e abre uma janela de aplicativo NATIVA (como se fosse um jogo, Photoshop ou Discord). **NÃO abre Chrome, Edge ou nenhum navegador visível.** Parece um programa nativo de verdade.

Tecnicamente:
- Front-end = **Next.js** (mesmo código se você abrir no navegador ou no launcher)
- Empacotador de desktop = **Tauri v2** (Rust no backend da janela, 5MB de arquivo final, zero bloatware)
- Janela: título "Prometeu", tamanho padrão 1600x900, lembra a janela do app Steam/Discord/Linear.

---

## 🔗 Links relacionados

- [[05 - Arquitetura Launcher + Front-end — Next.js + Tauri]] (detalhes técnicos da pilha)
- [[00 - Gênese — A Ideia Completa do NeuroCore]] (estética SaaS premium mencionada como requisito do autor)
