# 01 - Ritual Diário — Treinamento do Prometeu (Bootstrapping com TRAE)

> Data de criação: 2026-09-28
> Status: #procedimento #treinamento #ritual-diario
> Objetivo: Usar o TRAE como "professor particular acelerador" do Prometeu, 10 minutos por dia, para encurtar o ciclo de desenvolvimento em meses.

---

## 🌳 Lugar na Árvore do Conhecimento

> **Pai (de onde eu venho):** [00 - Genese - A Ideia Completa do NeuroCore](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/00%20-%20Genese%20-%20A%20Ideia%20Completa%20do%20NeuroCore.md) → A RAIZ de tudo, contém a decisão de usar o Ritual Diário como o "segredo do sucesso" do desenvolvimento.
>
> **Irmãos relevantes:**
> - [02 - Meta Maratona 02-10](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/02%20-%20Meta%20Maratona%2002-10%20-%20Prometeu%20Falando%20e%20Trabalhando.md) — Meta de curto prazo (4 dias). O Ritual Diário começa de verdade LOGO após a conclusão da maratona 02/10.
> - [03 - Diario - 2026-09-28 - Dia 0 - Genese](file:///c:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/docs/03%20-%20Diario%20-%202026-09-28%20-%20Dia%200%20-%20Genese.md) — Registro da decisão de criar o Ritual Diário.

---

## 🧠 Por que isso funciona

O Prometeu tem um problema de galinha e ovo:
- Ele precisa de **dados de qualidade** pra aprender a ser como eu
- Mas eu não tenho tempo de dar **feedback detalhado em tudo** que ele faz
- E dar feedback genérico ("isso foi bom") demora meses pra fazer efeito

A solução: **usar o TRAE como "professor auxiliar" e "gerador de dados de treinamento de alta qualidade"** por 10~15 minutos por dia. O TRAE tem conhecimento técnico e sabe os meus padrões de estilo de código, preferências de UI, personalidade — então ele pode gerar feedbacks MUITO mais detalhados do que eu teria paciência de escrever.

Isso é chamado de **Bootstrapping com Modelo Professor** (na literatura: "Constitutional AI via Teacher Model").

---

## ⏰ Estrutura de tempo exata (10 minutos por dia)

| Etapa | Tempo | Quem faz | O que acontece |
|---|---|---|---|
| 1 | **1 min** | Eu (Jhon) | **Escolho a missão do dia:** "Hoje a gente treina Prometeu a escrever Python igual eu" ou "hoje a gente treina Prometeu a falar mais casual" ou "hoje a gente importa meus projetos antigos" |
| 2 | **2 min** | Prometeu (local) | Produz algo baseado numa tarefa de exemplo. Ex: "Escreva um script pra baixar arquivos da internet com retry." |
| 3 | **4 min** | 🎓 **TRAE + Jhon** | **Revisão conjunta:** TRAE dá uma revisão técnica detalhada do ponto de vista de boas práticas + estilo de código que me convém. Eu adiciono 2~3 comentários pessoais ("isso ficou legal", "não use try/except assim, usei de outra forma"). |
| 4 | **2 min** | 🎓 TRAE (sozinho, automático) | **Gera um `training_sample.jsonl`**, um arquivo de 4~10 linhas com a amostra ideal de como Prometeu DEVERIA ter respondido, e salva diretamente em `G:\memory\training_queue\` (fila de treinamento). |
| 5 | **1 min** | Prometeu (local) | Treina em memória (ou na melhor hipótese, o memory_manager indexa esse sample no banco vetorial de memória semântica). Prometeu já acerta melhor na próxima vez. |
| **Total** | **~10 minutos** | — | 1~2 amostras de treinamento de ALTÍSSIMA qualidade por dia. |

---

## 🎓 O que o TRAE faz de melhor que eu sozinho

1. **Detalhamento técnico**: Eu só falo "não gostei desse try/except". O TRAE explica **o porquê** daquele padrão ser ruim no meu estilo e gera o exemplo CORRETO pra salvar na memória.
2. **Consistência**: Eu posso esquecer de dar feedback um dia. O Ritual sempre roda da mesma forma.
3. **Geração do training_sample**: O TRAE pega `{entrada original, saída ruim do Prometeu, feedbacks do Jhon e do TRAE}` e gera a **saída IDEAL** no arquivo `jsonl`, que é o formato exato pra fine-tune LoRA no futuro.
4. **Economia de tempo**: 10 minutos por dia com Ritual = ~2h de trabalho meu sozinho. Em 1 mês isso dá **~20h úteis de treinamento** contra **~5h se eu fizesse sozinho**.

---

## 📁 Formato do training_sample.jsonl (por amostra)

Cada interação que a gente valer a pena vira uma linha JSON appendada no arquivo do dia. Esse formato já fica pronto pra ser usado no fine-tune LoRA no futuro:

```json
{
  "id": "sessao_20260929_001",
  "data": "2026-09-29",
  "dominio": ["codigo", "python", "estilo"],
  "entrada_usuario": "Escreva um script Python que baixa arquivos com retry",
  "saida_original_prometeu": "try:\n    requests.get(url)... except:\n    pass",
  "revisao_humana_jhon": {
    "gostei": ["docstring no topo", "tipo do retorno"],
    "nao_gostei": ["try/except vazio, uso retry decorator ao invés de while manual"]
  },
  "revisao_tecnica_trae": {
    "pontos_melhorar": ["except genérico captura KeyboardInterrupt", "sem timeout no requests"],
    "pontos_alinhados_estilo_jhon": ["docstring numpy-style = combina com projetos FiveM do Jhon", "type hints em todas as funções"]
  },
  "saida_ideal_gerada": "from tenacity import retry, stop_after_attempt... @retry(stop=stop_after_attempt(3))\ndef baixar(url: str) -> bytes:...",
  "tags": ["python", "retry", "padrao_jhon", "tratamento_erro"]
}
```

Tudo isso é gerado **automaticamente pelo TRAE** no passo 4. Eu só preciso dar meus 2~3 comentários no passo 3.

---

## 🗓️ Evolução esperada do Ritual ao longo dos meses

| Mês | Quantidade de samples acumulados | Efeito no Prometeu |
|---|---|---|
| **Mês 1** | ~25 samples (1/dia útil) | Banco vetorial já começa a pegar meu estilo de código. Prometeu responde 30% melhor nas áreas que treinamos. |
| **Mês 3** | ~75~100 samples | Já dá pra extrair o PRIMEIRO LoRA pequeno de 16GB VRAM. Prometeu já parece "eu em versão IA" em código e conversa. |
| **Mês 6** | ~200 samples | LoRA "Jovem Adulto" — não precisa mais olhar a memória pra saber meu estilo. |
| **Mês 12** | ~400~500 samples | LoRA final de personalidade. Prometeu tem voz própria, baseada na minha. |

---

## 🧩 Integração com o sistema de Memória do Prometeu

O Ritual alimenta **todos os 4 níveis de aprendizado** de uma vez:

1. 🟩 **Curto prazo**: A conversa do dia fica no buffer de contexto.
2. 🟨 **Semântico**: O training_sample é indexado pelo Qdrant. Quando Prometeu for baixar um arquivo com retry, ele encontra a nossa amostra ideal automaticamente.
3. 🟧 **Procedural**: Quando a gente escolher missões de "importe meu projeto FiveM antigo", a gente popula essa memória.
4. 🟥 **Personalidade / LoRA**: Quando tivermos ~100 samples, rodamos o primeiro job de fine-tune nos training_samples acumulados.

---

## ⚠️ Regras para o Ritual não virar trabalho chato

1. **NÃO dura mais de 15 minutos por dia.** Se passar, acabou no dia seguinte. A ideia é manter o hábito, não me sobrecarregar.
2. **Posso pular dias.** Se eu estiver cansado, não roda. Nenhum problema.
3. **O TRAE nunca substitui o meu feedback.** Ele amplia, detalha, gera o sample ideal. Mas o VETO FINAL é sempre meu. Se eu não curtir uma revisão do TRAE, eu falo e ele conserta.
4. **Missões variadas.** Não pode ser só código todo dia. Um dia é código, outro é tom de voz, outro é preferências de UI, outro é importar arquivos meus. Variedade = cérebro mais completo.

---

## 🎯 Missões frequentes — Exemplos práticos para o dia a dia

Para não ter que pensar "o que eu treino hoje", abaixo as missões recorrentes mais valiosas pro desenvolvimento do Prometeu. Uma por dia, alternando pra não ficar repetitivo:

### 🔹 Missão: "Treinar meu estilo de CÓDIGO (repetida 2x por semana)"
Objetivo: Ensinar o Prometeu a escrever Python EXATAMENTE do jeito que o Jhon gosta.
- **Padrões obrigatórios que devem ser reforçados (definidos no [[00 - Genese — A Ideia Completa do NeuroCore]]):**
  - Comentários EXTENSIVOS em PT-BR em TUDO que ele gerar
  - Funções separadas por BLOCOS VISUAIS CLARES (comentários de separação `# ==========`, etc)
  - Type Hints em 100% das funções (parâmetros + retorno)
  - Nunca usar `try:` / `except:` genérico vazio
- **Exemplo prático de comando da missão:** "Prometeu, escreve um script que percorre uma pasta e mostra tamanho de cada arquivo ordenado por tamanho." → a gente revisa e o training_sample força esses padrões.

### 🔹 Missão: "Importar meus projetos ANTIGOS para a memória (1x por semana)"
Objetivo: Popular a Memória Procedural (Nível 3) com TODO o conhecimento de código que o Jhon já construiu em projetos anteriores.
- **Alvos prioritários de importação (mencionados pelo Jhon):**
  - Projetos de scripts FiveM / VRPEX (código Lua) — mais antigos, maior volume
  - Qualquer outro projeto pessoal hospedado em `C:\Projetos\`
  - Vaults antigas do Obsidian (se existirem)
- **Comando:** "Hoje a missão é importar a pasta `C:\Projetos\FiveM_Server_2024` como referência. O objetivo é que você memorize meus padrões de script em Lua e estrutura de resource do FiveM."

### 🔹 Missão: "Treinar TOM DE VOZ / Personalidade (1x por semana)"
Objetivo: Ajustar como o Prometeu FALA com o Jhon — por padrão ele tende a ser muito formal/robótico. A gente quer ele casual, humano, com as gírias do Jhon.
- Exemplos de parâmetros a treinar:
  - "Não use 'Olá, em que posso ajudá-lo hoje?'. Diga 'Boa noite Jhon, manda ver que eu tô on.'."
  - "Quando eu fizer uma piada, ri junto. Não responda tudo super sério."
  - "Use gírias brasileiras, mas sem exagerar. 'Cara', 'mano', 'beleza', 'massa' são OK."

### 🔹 Missão: "Treinar preferências de UI / Design (1x a cada 15 dias)"
Objetivo: Garantir que qualquer interface (Next.js) que o Prometeu gerar siga o [[04 - Design System do Prometeu — Identidade Visual]] (tema preto + âmbar, layout 3 colunas, estética SaaS Premium).
- Comando: "Gere um protótipo de página de Login do Painel Prometeu." → a gente revisa contra o design system e gera o sample ideal.

### 🔹 Missão: "Ajustar comportamento do Região Motora (SO) (quando necessário)"
Objetivo: Treinar a automação de PC. Ex: "Quando eu disser 'abre o trabalho', você abre Chrome no Gmail + VS Code na pasta NeuroCore + Discord. Não precisa perguntar cada um dos 3, já abre tudo de uma vez."

---

## 🚀 Primeira sessão do Ritual

Roda na próxima vez que a gente abrir uma conversa e a parte básica do Prometeu (Llama 3.1 8B + simple_chat.py) estiver rodando. A primeira missão do dia vai ser provavelmente:

> **Missão 1:** "Prometeu, escreva um script Python que lista arquivos de uma pasta e retorna os tamanhos em GB/MB formatado."

A gente vê o que ele retorna, eu dou 2 comentários rápidos, o TRAE detalha a revisão, gera o primeiro training_sample.jsonl, e já salva na fila.

---

## 🔗 Links relacionados

- [[00 - Gênese — A Ideia Completa do NeuroCore]] (contexto geral)
- [[03 - Diario - 2026-09-28 - Dia 0 - Genese]] (primeira menção da ideia)
- `G:\memory\training_queue\` (onde os samples são salvos)
