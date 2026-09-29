# 🏢 09 - Arquitetura B2B Multi-Canal e Multi-Tenant (Visão de Futuro do Prometeu como Plataforma)

> **Data da Conversa:** Manhã de sábado, 29/09/2026 (imediatamente após o FAQ Arquitetural 08)
> **Autor:** Jhon Ross (pergunta + decisão "abraçar oficialmente") + TRAE (respostas e consolidação)
> **Status:** ✅ **ARQUITETURA DESENHADA E ABRAÇADA OFICIALMENTE.** NÃO É "um dia quem sabe". É a versão futura oficial do NeuroCore.
> **Quando começar a implementar:** DEPOIS do Marco 12 "02/10 Prometeu 4 Regiões Falando". Só saímos pra implementação do 09 quando o cérebro pessoal estiver 100% entregue da maratona.
> **Pai (Galho de origem):** [00 - Genese](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/00%20-%20Genese%20-%20A%20Ideia%20Completa%20do%20NeuroCore.md)
> **Irmãos diretos:** [08 - FAQ Arquitetural](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/08%20-%20Visao%20de%20Futuro%20e%20FAQ%20Arquitetural%20-%2029-09-2026.md) · [05 - Frontend/Tauri](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/05%20-%20Arquitetura%20Launcher%20e%20Frontend%20-%20Nextjs%20e%20Tauri.md) · [02 - Maratona 02/10](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/02%20-%20Meta%20Maratona%2002-10%20-%20Prometeu%20Falando%20e%20Trabalhando.md)

---

## 📜 Resumo do documento

Jhon perguntou:
> "Consigo usar o NeuroCore para auxiliar empresas — tipo bot no WhatsApp, Telegram, Discord, chat no site, tudo usando a mesma base de conhecimento do Prometeu sem pagar API de chat bot?"

Resposta oficial consolidada aqui:
**SIM, ABSOLUTAMENTE. E a arquitetura já cabe 100% dentro do que já construímos SEM REESCREVER NADA do core/orchestrator.py, core/hybrid_router.py, specialists/ e memória. Basta adicionar uma camada B2B por fora, um isolamento tenant-id, conectores de canal e RAG por empresa.**

Este documento é o "manual de construção passo a passo" para a versão plataforma do Prometeu.

---

## 🎯 TL;DR: o que é o Prometeu B2B

O Prometeu pessoal é o cérebro.
O Prometeu B2B é o mesmo cérebro, com:
- isolamento por empresa (tenant_id)
- base de conhecimento separada por empresa
- conectores para canais (chat site, Telegram, Discord, WhatsApp)
- RAG injectando o contexto DAQUELA empresa antes do prompt
- guardrails, compliance LGPD e escala para humano
- analytics por tenant e SLA

Ou seja: **UM CÉREBRO · MUITOS CANAIS · VÁRIAS EMPRESAS.**

---

## 1️⃣ Visão Geral em 4 Camadas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CLIENTES FINAIS (USUÁRIOS)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Chat Site│  │ Telegram │  │ Discord  │  │ WhatsApp │  │Form/Slack/Email│ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
└───────┼──────────────┼──────────────┼──────────────┼───────────────┼───────────┘
        │ mensagem bruta do canal    │              │                │
        ▼ transforma em formato padrao interno (Mensagem Unificada)
┌─────────────────────────────────────────────────────────────────────────────┐
│                 📡 CAMADA 1 - CONECTORES (ADAPTERS LEVES)                    │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐│
│  │ WebChat.py │ │ Telegram.py│ │ Discord.py │ │WhatsApp.py │ │ Form/Email.py││
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └──────┬───────┘│
└────────┼───────────────┼───────────────┼───────────────┼───────────────┼────────┘
         └───────────────┴───────┬───────┴───────────────┴───────────────┘
                                 ▼
          MSG PADRAO INTERNA = { tenant_id, canal_id, usuario_id, mensagem, timestamp, metadata }
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│           🏢 CAMADA 2 - GATEWAY B2B (PORTÃO ANTES DO CÉREBRO)                │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 🔐 Tenant Engine  (core/tenant_manager.py)                            │  │
│  │   • Valida licença da empresa • Isola TUDO por tenant_id              │  │
│  │   • Carrega persona / regras / guardrails SOMENTE DAQUELA empresa     │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 📚 Knowledge Store por empresa  (core/knowledge_store.py)            │  │
│  │   • Base da Clínica / Loja / Studio / Site do cliente                │  │
│  │   • PDFs, FAQs, Site, Preços, Horários, Políticas, Catálogo          │  │
│  │   • Indexação vetorial RAG POR TENANT (nunca compartilha NADA!)       │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 🧠 RAG Tenant Context Builder (core/rag_tenant_builder.py)           │  │
│  │   Pega a pergunta do usuário → busca N trechos mais similares        │  │
│  │   → coloca no prompt do orquestrador com header:                     │  │
│  │   "Responda usando APENAS a base da empresa abaixo. Se não souber,   │  │
│  │    chame handover() para o humano."                                   │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 🛡️ Guardrails e Compliance (core/guardrails_b2b.py)                │  │
│  │   • Bloqueia tópicos proibidos pela empresa                          │  │
│  │   • NÃO INVENTA preço / horário / contrato / garantia                │  │
│  │   • Nível confiança < 0.65 → handover humano automático              │  │
│  │   • LGPD / Logs auditoria por tenant / anonimização                  │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
└──────────────────────────────────────┼──────────────────────────────────────┘
                                       │
             ┌─────────────────────────┴─────────────────────────┐
             │  Mesmo contrato do orquestrador que já temos HOJE │
             │  NENHUM RETRABALHO. Apenas repassamos mensagem!   │
             ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│            🧠 CAMADA 3 - CÉREBRO PROMETEU (NOSSO PRODUTO JÁ EXISTENTE!)     │
│                                                                              │
│  [core/orchestrator.py] → [core/hybrid_router.py] → [specialists/*]          │
│                    └─→ [Ollama local :11434 ou GPU ponte remota Bionic]      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼  resposta final estruturada
┌──────────────────────────────────────────────────────────────────────────────┐
│      🗂️ CAMADA 4 - SISTEMAS AUXILIARES B2B (TUDO ISOLADO POR TENANT)        │
│                                                                              │
│  ┌────────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │ Histórico por      │  │ Escalada Humano  │  │ Analytics B2B Dashboard  │  │
│  │ usuário + empresa  │  │ Handover Contexto│  │ Tickets resolvidos / NPS │  │
│  │ memory_manager_tenant│ │ Fila / SLA      │  │ tempo resposta / tópicos │  │
│  │ SQLite → Qdrant    │  │ (core/handover.py)│ │ por empresa / canal      │  │
│  └────────────────────┘  └──────────────────┘  └──────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2️⃣ Fluxo real de uma mensagem (exemplo clínica saúde)

Cenário: cliente entra no site da clínica do Dr. Carlos e escreve:
> "Qual horário de atendimento no sábado? Vocês atendem convênio Unimed?"

Pipeline passo a passo:

1. `canal = webchat` → `mensagem bruta` chega no widget do site.
2. `connectors/webchat.py` transforma em mensagem padrão:
   ```json
   { "tenant_id": "clinica_dr_carlos",
     "canal_id": "webchat",
     "usuario_id": "guest-71A3F",
     "mensagem": "Qual horário de sábado? Atendem Unimed?",
     "timestamp": "2026-09-29T10:14:00-03:00",
     "metadata": { "pagina_origem": "/contato" } }
   ```
3. `core/b2b_gateway.py` recebe e passa pelo Tenant Engine. Valida licença da clínica ativa → OK.
4. `core/knowledge_store.py` carrega a base da clínica: PDFs internos, preços, horários, convênios cadastrados.
5. `core/rag_tenant_builder.py` busca os trechos mais similares:
   - "Horários de sábado: 08h às 12h exclusivo para retorno e pequenos procedimentos."
   - "Convênios aceitos: Unimed, Bradesco, SulAmérica."
6. Monta prompt:
   > Você é o assistente virtual da Clínica Dr. Carlos.
   > Responda apenas usando essa base. Se não souber, passe para atendente.
   > Base abaixo: ...
   > Pergunta: "Qual horário sábado? Atendem Unimed?"
7. Envia ao `core/orchestrator.py` (NENHUMA ALTERAÇÃO NO CÓDIGO).
8. `core/guardrails_b2b.py` analisa confiança da resposta: 0.91 → alto.
9. Resposta volta via conector WebChat para o cliente:
   > "Olá! No sábado atendemos das 08h às 12h (retornos e pequenos procedimentos). Sim, atendemos o convênio Unimed. Posso te passar para um atendente confirmar horário disponível?"
10. Tudo é salvo em `tenants/clinica_dr_carlos/sessions.db` e histórico.

---

## 3️⃣ Encaixe NOS ARQUIVOS que já temos — NÃO QUEBRA NADA

### O que NÃO mexemos (100% reutilizado):

| Módulo existente | Onde? |
|---|---|
| 🎼 Orquestrador LangGraph | [core/orchestrator.py](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/core/orchestrator.py) |
| 🔀 Hybrid Router (local ou ponte GPU remota) | [core/hybrid_router.py](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/core/hybrid_router.py) |
| 🧩 ABC BaseSpecialist e 7 especialistas | [core/base_specialist.py](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/core/base_specialist.py) / [specialists/__init__.py](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/specialists/__init__.py) |
| 🖥️ UI 3 colunas (futuro Dashboard B2B) | [frontend/src/app/page.tsx](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/frontend/src/app/page.tsx) |
| 🎮 Sistema de XP pessoal (continua seu) | [core/progress_rpg.py](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/core/progress_rpg.py) |
| 📜 Logger estruturado JSONL (basta adicionar `tenant_id` opcional) | [core/logger.py](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/core/logger.py) |
| 💾 Memory Manager (adicionamos `tenant_id` como coluna opcional) | [core/memory_manager.py](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/core/memory_manager.py) |

### O que É NOVO (tudo fora, sem tocar no core):

```
NeuroCore/
├── core/
│   ├── b2b_gateway.py                 ← PORTA ÚNICA DE ENTRADA B2B
│   ├── tenant_manager.py              ← licença + isolamento empresa
│   ├── knowledge_store.py             ← upload PDFs/site indexa RAG por tenant
│   ├── rag_tenant_builder.py          ← injeta contexto EMPRESA ESPECÍFICA no prompt
│   ├── guardrails_b2b.py              ← LGPD, nao inventa preço, escala humano
│   └── handover.py                    ← fila atendente humano + contexto salvo
│
├── connectors/                        ← PASTA NOVA, 1 adapter leve por canal
│   ├── connector_base.py              ← ABC tipo BaseSpecialist (unifica msg)
│   ├── webchat.py                     ← PRIORIDADE 1 (chat no site SaaS)
│   ├── telegram.py                    ← PRIORIDADE 2
│   ├── discord.py                     ← PRIORIDADE 3
│   └── whatsapp_meta.py               ← PRIORIDADE 8 (por último)
│
└── tenants/                           ← DADOS POR EMPRESA · FORA DA SUA MEMÓRIA PESSOAL!
    ├── clinica_dr_carlos/
    │   ├── knowledge_base/            ← PDFs, FAQ, preços, horários
    │   ├── rag_snapshot/              ← índice vetorial Qdrant isolado
    │   ├── sessions.db                ← histórico de chat dos clientes
    │   ├── analytics.sqlite           ← tickets, NPS, SLA
    │   └── persona_rules.json         ← tom de voz, regras, avatar, nome do bot
    └── loja_gamer_xyz/                ← OUTRA EMPRESA, TUDO ISOLADO
```

---

## 4️⃣ Regra de OURO de Isolamento: PESSOAL ≠ EMPRESA

> **NUCA MISTURE A MEMÓRIA DO JHON COM A MEMÓRIA DO CLIENTE.**

| Dado | Onde mora? | Acesso autorizado |
|---|---|---|
| 💬 Sua conversa pessoal com Prometeu | `G:\memory\sqlite_db\prometeu_main.db` | SÓ JHON |
| 🎮 XP / Feitos / Wall of Wins | `G:\memory\prometeu_rpg.json` + [06-Wall of Wins](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/06%20-%20Feitos%20e%20Marcos%20do%20Prometeu%20-%20Wall%20of%20Wins.md) | SÓ JHON |
| 📝 Ritual Diário seu / training queue | `G:\memory\training_queue\` | SÓ JHON |
| 🗂️ Sessão atendimento Clínica Dr. Carlos | `tenants/clinica_dr_carlos/sessions.db` | SÓ `tenant_id = clinica_dr_carlos` |
| 📚 Base de conhecimento Loja Gamer | `tenants/loja_gamer_xyz/knowledge_base/` | SÓ `tenant_id = loja_gamer_xyz` |
| 📊 Analytics e NPS da empresa X | `tenants/empresa_x/analytics.sqlite` | SÓ empresa X e Jhon (dono da plataforma) |

**Implementação técnica:**
- `B2B_Gateway.py` roda num **processo separado** da instância pessoal do Prometeu.
- `progress_rpg.py` NUNCA é importado no processo B2B.
- Toda query no Memory Manager B2B SEMPRE leva `tenant_id IS NOT NULL AND tenant_id = %s`.

---

## 5️⃣ Canais: Ordem Correta de Implementação (NÃO COMECE PELO WHATSAPP)

| Prioridade | Canal | Dificuldade | Custo por msg | Por que essa ordem? |
|---|---|---|---|---|
| 1️⃣ | **Chat no Site / WebChat Widget** | ⭐⭐ (baixa) | R$ 0 | Mais profissional, mais controlado, cliente cola 1 `<script>` no site, zero burocracia. **MVP VENCE AQUI.** |
| 2️⃣ | **Telegram** | ⭐⭐⭐ | R$ ~0 | Ótimo MVP pequenas empresas, grupos, notificações. Documentação excelente. |
| 3️⃣ | **Discord** | ⭐⭐⭐ | R$ ~0 | Comunidade, suporte técnico, lojas gamer, times internos. |
| 4️⃣ | **Slack / Teams** | ⭐⭐⭐⭐ | R$ ~0 | B2B teams interno enterprise. Fazer só quando houver demanda de empresa grande. |
| 5️⃣ | **Instagram DM / Messenger** | ⭐⭐⭐⭐⭐ | R$ variável | Meta Graph API. Tem regras. Fazer depois da plataforma madura. |
| 6️⃣ | **WhatsApp OFICIAL (Meta Business)** | ⭐⭐⭐⭐⭐⭐⭐ | **SIM, CUSTO POR CONVERSA / MENSAGEM.** | SÓ FAZER QUANDO A PLATAFORMA ESTIVER MADURA E VOCÊ TIVER PREÇO REAL. NÃO USE SOLUÇÕES NÃO OFICIAIS PARA CLIENTES PAGANTES. RISCO DE BLOQUEIO E FRAGILIDADE. |

---

## 6️⃣ Custos: O que é GRÁTIS vs o que pode custar

### O que fica GRÁTIS por padrão (motivo do diferencial de mercado):
- **API de LLM / Inferência.** Roda local Ollama na sua GPU, ou GPU amiga via Tailscale. Você NÃO paga por token.
- Orquestrador, roteador, especialistas, logger, memória, tudo.
- Telegram, Discord: custo zero para MVP.

### O que PODE ter custo:
| Item | Observação | Estimativa real |
|---|---|---|
| WhatsApp Oficial Meta | Sim, normalmente custo por conversa/mensagem. | R$ 50 a R$ 500/mês por empresa pequena. Passa pro cliente. |
| Hospedagem da plataforma (se não quiser seu PC 24h ligado) | VPS / Cloud / Dedicado. | R$ 60 a R$ 400/mês. Você pode embutir no preço. |
| GPU Remota Runpod (quando volume alto) | Teto BLOQUEÁVEL no Hybrid Router. | R$ 50 a R$ 500/mês. Passa pro cliente quando ultrapassar. |
| Domínio / SSL / Widget hospedado | Pequeno. | R$ 10 a R$ 50/mês total. |
| LGPD e auditoria logs avançado | Enterprise. | Começa R$ 0 local, depois escalona. |

---

## 7️⃣ Ordem de Implementação Cronológica (Pensada pra NÃO ABANDONAR)

> **REGRA DE OURO ANTES DE LER A TABELA ABAIXO:**
> NÃO TOQUE NISSO ATÉ FECHAR O MARCO #12 "4 REGIÕES CEREBRAIS FUNCIONANDO" DA MARATONA DIA 4 (02/10).
> Seu cérebro pessoal vem PRIMEIRO. A plataforma vem DEPOIS.

| Fase | O que construir | Entrega concreta | Prazo estimado |
|---|---|---|---|
| 🟢 0 | **NENHUM CÓDIGO NOVO AINDA (hoje)** | Apenas este documento 09 desenhado. | 0h (concluído neste doc) |
| 🟢 1 | `b2b_gateway.py` + `tenant_manager.py` + `knowledge_store.py` (MVP scaffold) | Arquitetura mínima rodando 1 empresa fake localmente, sem conector. | 1~2 dias |
| 🟢 2 | `rag_tenant_builder.py` + 1 empresa real de teste (amigo/parente que tem empresa) | RAG responde corretamente com base real daquela empresa. Nada de inventar preço. | +2 dias |
| 🟢 3 | `connectors/webchat.py` + Widget HTML embutível | Cliente cola `<script src=".../prometeu.js" data-tenant="clinica_dr_carlos"></script>` no site e BOT FUNCIONA. | +2 dias |
| 🟡 4 | `core/handover.py` + Botão Falar com Atendente + Contexto salvo | SLA, fila, humano pega conversa sem repetir pergunta. | +1 dia |
| 🟡 5 | `connectors/telegram.py` | 2 canais ativos: WebChat + Telegram | +1 dia |
| 🟠 6 | `guardrails_b2b.py` + LGPD + Analytics Dashboard básico no frontend | Plataforma pronta pra COBRAR do primeiro cliente piloto. | +2~3 dias |
| 🟠 7 | `connectors/discord.py` + Dashboard Tenant por empresa | Comunidade e suporte técnico. | +1~2 dias |
| 🔴 8 | `connectors/whatsapp_meta.py` + conformidade + preço real | Canal WhatsApp Oficial | +4~7 dias + custos Meta |

---

## 8️⃣ Modelo de Receita (3 opções que se complementam):

1. **Assinatura mensal por empresa**
   - **Plano Básico:** R$ 97 / mês = 1 empresa · 1 canal (WebChat) · RAG 100 documentos · analytics básico
   - **Plano Pro:** R$ 197 / mês = até 3 canais (WebChat + Telegram + Discord) · RAG ilimitado · handover · SLA 8h
   - **Plano Enterprise:** R$ 497~ / mês = WhatsApp oficial · multi-usuário · SLA 2h · LGPD completo · customização widget

2. **Setup Inicial One-Time**
   - R$ 500 a R$ 1500 por empresa: importar base, PDFs, site, treinar RAG, configurar persona, customizar widget com identidade visual da empresa, dashboard inicial.

3. **Por interação / Pay-as-you-go (empresas que não querem assinatura)**
   - Como inferência é local, custo marginal é MUITO baixo. Margem alta:
     - R$ 0,15 por atendimento resolvido 100% por bot
     - R$ 0,50 por interação complexa + handover

💡 Diferencial de mercado absurdo que a maioria dos concorrentes NÃO TEM:
> "Nós não pagamos API de LLM por token, porque nossa plataforma roda o modelo localmente ou em GPU própria. Então eu consigo preço mais baixo e margem mais alta ao mesmo tempo."

---

## 9️⃣ Os 3 Riscos MORTAIS que a gente não brinca

| Risco | Como mitigar SEMPRE |
|---|---|
| **1. Vazar sua memória pessoal ou memória da empresa A na B** | `tenant_id` obrigatório em TUDO. Qualquer query sem `tenant_id` retorna erro. Memory Manager separado pessoal / tenants. Processos Python separados. Ambiente pessoal não importa `b2b_gateway.py`. |
| **2. Inventar preço / garantia / política e ferrar cliente** | Guardrails + prompt header "responder APENAS base da empresa" + Nível de Confiança < 0.65 = passa para humano. Validação de pós-resposta (não mencionar nada fora de trechos indexados). |
| **3. Sua RX 7600 não aguentar 10 empresas ao mesmo tempo** | 1 e 2 empresas = sua casa resolve. 3+ = fila assíncrona de mensagens + workers + GPU Remota via Tailscale/Bionic que já tem plano no 08. Ou um servidor GPU barato colocado no escritório. Sempre tem saída. |

---

## 🔟 Compromissos OFICIAIS deste documento 09:

✅ **Decisão #1:** Prometeu não vai virar "só uma plataforma B2B".  
Primeiro o Prometeu pessoal. O B2B é uma camada por fora, não o centro.

✅ **Decisão #2:** NÃO MISTURAMOS memória pessoal e memória de empresa.  
Pastas separadas. `tenant_id` em tudo. Processos separados.

✅ **Decisão #3:** NÃO começamos pelo WhatsApp.  
Começamos por WebChat. WhatsApp é o ÚLTIMO canal.

✅ **Decisão #4:** MVP = 1 empresa real + 1 canal + 1 base + 1 RAG.  
Sem tentar entregar 6 canais no primeiro mês.

✅ **Decisão #5:** Primeiro cliente é um piloto.  
Amigo, parente, conhecido, loja do bairro. Empresa pequena. NÃO tentar vender para enterprise no primeiro mês.

---

## 📚 Referências cruzadas com o resto da árvore:

- Pergunta da Ponte GPU Remota = resolvida no [08 - FAQ Arquitetural #Pergunta 2](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/08%20-%20Visao%20de%20Futuro%20e%20FAQ%20Arquitetural%20-%2029-09-2026.md) — essa plataforma vai usar a ponte Bionic/Tailscale pra escalar.
- Pergunta do RAG = resolvida no [08 #Pergunta 3](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/08%20-%20Visao%20de%20Futuro%20e%20FAQ%20Arquitetural%20-%2029-09-2026.md) — a versão B2B usa RAG por tenant.
- Maratona 02/10 = [02 - Meta Maratona](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/02%20-%20Meta%20Maratona%2002-10%20-%20Prometeu%20Falando%20e%20Trabalhando.md). **Só saímos do 09 quando o Marco #12 do dia 4 estiver concluído.**
