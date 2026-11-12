# Apresentação e defesa

Guia de estudo, roteiro de demonstração e roteiro de entrega.

## Conteúdo

- [Guia de estudo do projeto — como tudo funciona, do começo ao fim](#guia-de-estudo-do-projeto--como-tudo-funciona-do-começo-ao-fim)
- [Demonstração e reprodução da entrega](#demonstração-e-reprodução-da-entrega)
- [Roteiro de entrega do PAC](#roteiro-de-entrega-do-pac)

## Guia de estudo do projeto — como tudo funciona, do começo ao fim

_Origem: `docs/apresentacao.md` (consolidado em 2026-11-09)._

Escrito para quem **conhece o básico de tecnologia mas não é desenvolvedor** e precisa explicar o
projeto com segurança. Cada trecho diz **o que é**, **para que serve** e **onde está no código**.
Os números e nomes de arquivos foram conferidos no repositório em 08/11/2026.

> **Nota sobre autoria e transparência.** O código deste projeto foi escrito em grande parte com
> assistentes de IA (Codex e, na reta final, Claude Code), sob a sua direção. Uma prova de autoria
> mede se você **entende e consegue explicar e defender** o que foi entregue. Este guia serve a isso.
> Se alguém perguntar como foi desenvolvido, diga a verdade: você definiu o problema, as decisões
> (provedor Gemini, base sintética, perguntas de avaliação, domínio de autopeças), revisou e testou, e
> usou assistentes de IA para escrever e revisar código. Confira também as regras da sua instituição sobre
> o uso de IA; declarar o uso é mais seguro do que omiti-lo.

### Como usar este guia

| Nível | Tempo | O que ler |
|---|---|---|
| 1. Visão geral | 30 min | Seções 1 a 4 e 13 |
| 2. Fluxo completo | 1 h | Seções 5 e 6 (o caminho de uma pergunta) |
| 3. Domínio dos arquivos | 2–3 h | Seções 7 a 12 |
| 4. Defesa | 30 min | Seções 14 a 16 (perguntas da banca, números, limites) |

---

### 1. O projeto em um minuto

**Problema.** Um gestor de uma empresa precisa de números do negócio (faturamento, pedidos,
recebimentos) e hoje depende de abrir relatórios ou pedir a alguém.

**Solução.** Um **assistente de BI (Business Intelligence) pelo Telegram**. O gestor escreve em
português, como numa conversa ("Top 3 clientes por faturamento em setembro de 2026"), e recebe a
resposta com os números exatos do banco de dados.

**Como funciona, em quatro peças:**

```
Telegram  →  Backend (FastAPI)  →  Gemini (IA)  →  Banco (PostgreSQL)
 (conversa)   (o "cérebro" que       (entende a        (guarda os dados,
              coordena tudo)          pergunta)          responde com números)
```

**A ideia central de desenho.** A IA (Gemini) só **interpreta a pergunta**. Quem consulta o banco,
valida a segurança, calcula datas e **escreve a resposta com os números** é código do projeto. Assim a IA
não "inventa" números: todo valor mostrado vem do banco.

**Contexto.** Projeto do **PAC Extensionista VIII** (atividade acadêmica), baseado na proposta
"Assistente Conversacional de BI via Aplicativo de Mensagens com IA". Os dados são **100% sintéticos**
(inventados por um gerador), sem dado pessoal real. O domínio atual é uma **revenda de autopeças** de
porte pequeno a médio.

### 2. Glossário (palavras que você vai usar)

| Termo | O que é, em simples |
|---|---|
| **BI** | Business Intelligence: transformar dados em respostas para decidir |
| **Telegram bot** | Um "usuário robô" do Telegram que recebe e envia mensagens por programa |
| **Backend** | O programa que roda num servidor e faz o trabalho; o usuário não o vê |
| **FastAPI** | Biblioteca Python para criar o backend (recebe pedidos pela internet) |
| **API** | "Tomada" pela qual um programa pede algo a outro (ex.: nosso backend pede ao Gemini) |
| **Webhook** | Endereço do nosso backend para onde o Telegram entrega as mensagens |
| **Polling** | Em vez de o Telegram entregar, um programa fica **perguntando** "há mensagem nova?" |
| **LLM** | *Large Language Model*: modelo de IA que entende e gera texto. O Gemini é um LLM |
| **Gemini** | O LLM do Google, usado por API (não treinamos nem alteramos ele) |
| **Prompt** | As instruções escritas que damos ao LLM para ele agir como queremos |
| **JSON** | Formato de texto para dados estruturados (ex.: `{"metrica": "faturamento"}`) |
| **Function calling** | O LLM pede para o sistema rodar uma "ferramenta" (ex.: consultar o banco) |
| **SQL** | Linguagem para consultar bancos de dados (`SELECT ... FROM ...`) |
| **PostgreSQL** | O banco de dados relacional que guarda as tabelas |
| **Schema** | A "planta" do banco: tabelas, colunas e relações |
| **Template** | Modelo fixo de SQL, montado pelo código (sem IA) |
| **CTE / WITH** | Um trecho de SQL que cria uma "tabela temporária" dentro da consulta |
| **Seed / seeder** | Gerador que cria os dados sintéticos de forma repetível |
| **Sintético** | Inventado por programa; não vem de pessoas ou empresas reais |
| **Role somente leitura** | Usuário do banco que **só pode ler**, nunca alterar |
| **Docker / container** | "Caixa" que empacota o programa com tudo que ele precisa para rodar igual em qualquer lugar |
| **Imagem** | A receita pronta da caixa (o container é a imagem rodando) |
| **VM** | Computador virtual na nuvem (aqui, na Oracle) onde o sistema roda |
| **CI** | Verificação automática que roda os testes a cada alteração (GitHub Actions) |
| **PR (Pull Request)** | Proposta de mudança no GitHub, revisada antes de entrar na versão principal |
| **TF-IDF** | Forma de transformar texto em números (palavras mais raras pesam mais) |
| **Regressão logística** | Algoritmo simples de classificação, usado no nosso classificador |
| **Fine-tuning** | Re-treinar um modelo grande. **Não fizemos isso com o Gemini** |
| **Acurácia / precisão / cobertura** | % de acertos / % de acertos entre o que foi aceito / % de casos em que o modelo se arriscou |

### 3. Arquitetura em camadas

| Camada | Arquivos principais | Função |
|---|---|---|
| 1. Mensageria | `app/telegram_bot.py`, `app/messaging.py` | Receber e enviar mensagens no Telegram |
| 2. Backend | `app/main.py`, `app/sessions.py`, `app/config.py` | Receber, filtrar, enfileirar e manter a conversa de cada gestor |
| 3. Agente | `app/bi_agent.py`, `app/prompts.py` | Orquestrar: entender, validar, consultar e responder |
| 4. Regras de período e plano | `app/relative_periods.py`, `app/analysis_contract.py`, `app/monthly_comparisons.py` | Calcular datas e validar o que o Gemini planejou |
| 5. SQL | `app/query_templates.py`, `app/managerial_queries.py`, `app/sql_policy.py` | Montar e proteger as consultas |
| 6. Banco | `app/database_tools.py`, `db/schema.sql`, `db/roles.sql` | Executar a consulta com segurança e devolver linhas |
| 7. Resposta | `app/rendering.py`, `app/managerial_rendering.py` | Montar o texto final a partir das células do banco |
| 8. Dados e testes | `scripts/`, `tests/`, `evaluation/`, `training/` | Gerar dados, provar que funciona, treinar o classificador |
| 9. Implantação | `Dockerfile`, `runtime_entrypoint.py`, `deploy/oracle/` | Colocar para rodar na VM |

### 4. O papel do Gemini (e o que ele NÃO faz)

**Faz duas coisas:**
1. **Planejador (em toda pergunta).** Lê a pergunta e devolve um **JSON** com o plano: qual métrica
   (faturamento, pedidos...), qual medida (valor, quantidade), o período e o tipo de análise. **Não escreve SQL.**
2. **Redator de SQL (só em filtros livres).** Se a pergunta tem um filtro que não há modelo pronto
   ("só Joinville"), o Gemini escreve o `SELECT` usando as ferramentas `get_schema` e `execute_sql`. O código valida antes de rodar.

**Não faz:** calcular datas relativas, validar o plano, autorizar SQL, executar a consulta, escrever a
resposta nem os números, nem aprender com as conversas.

| Não faz | Quem faz |
|---|---|
| Datas relativas ("ontem", "ano passado") | `app/relative_periods.py` (Python) |
| Validar o plano | `app/analysis_contract.py` |
| SQL de totais e análises padrão | `app/query_templates.py`, `app/managerial_queries.py` |
| Autorizar SQL livre | `app/sql_policy.py` |
| Executar a consulta | PostgreSQL, com usuário somente leitura |
| **Escrever a resposta e os números** | `app/rendering.py`, `app/managerial_rendering.py` |

**Quantas chamadas ao Gemini por pergunta:** uma (só o planejador) para totais, análises padrão,
esclarecimentos e recusas; duas ou mais (planejador + ciclo de SQL) para filtros livres.

**Modelo usado:** `gemini-3.5-flash-lite`, por API, plano gratuito do Google AI Studio. A proposta original
previa Claude (Anthropic) ou GPT-4o; a troca para Gemini foi decisão do responsável, para usar a cota gratuita.

**O que vai para o Gemini:** a pergunta, o histórico da conversa (incluindo respostas anteriores do bot),
o glossário do schema. **As linhas devolvidas pelo banco não vão ao Gemini** (padrão `SEND_ROWS_TO_MODEL=false`): no
caminho de SQL livre o modelo recebe só colunas, número de linhas e se houve truncamento, e o backend lê as células e
monta a resposta. Erros do banco só levam o detalhe quando são de esquema (SQLSTATE 42xxx), porque o de dados pode
citar valores. Ver [Privacidade e LGPD](../README.md#privacidade-e-lgpd).

### 5. O caminho completo de uma pergunta (exemplo real)

Pergunta do gestor: **"Top 3 clientes por faturamento em setembro de 2026"**.

#### Passo 1 — O Telegram entrega a mensagem
- `app/telegram_bot.py` (`run`, `forward_updates`) fica em **polling**: pergunta ao Telegram se há
  mensagens, e encaminha cada uma ao nosso backend por um POST em `/telegram/webhook`.
- Se o backend recusar o conteúdo de vez (erro 400, 413 ou 422), o update é **ignorado** e registrado, para um
  update ruim não travar o bot. Erros de rede, 5xx e de segredo (401/403) são tentados de novo.

#### Passo 2 — O backend recebe, confere e enfileira (`app/main.py`)
- `webhook()`: confere o **segredo** do cabeçalho (`hmac.compare_digest`), limita o corpo a 64 KiB,
  valida que é um update do Telegram, descarta repetições (guarda os últimos 10 mil `update_id` por 24 h)
  e coloca na **fila** (máx. 100; cheia = erro 503).
- 4 **trabalhadores** (`worker`) tiram da fila e chamam `TelegramService.process`.

#### Passo 3 — Quem pode falar? (`app/messaging.py`)
- `TelegramService.process` só aceita **chat privado** e **usuários autorizados** (`TELEGRAM_ALLOWED_USER_IDS`).
- Trata comandos: `/comecar`, `/ajuda`, `/limpar` (apaga o histórico). Outras mensagens vão ao agente.
- A conversa de cada gestor fica em `app/sessions.py` (`SessionStore`): guarda os últimos 8 turnos,
  expira em 1 hora e usa um **cadeado** para atender uma mensagem por vez por pessoa.

#### Passo 4 — O agente entende a pergunta (`app/bi_agent.py`, método `BIAgent._answer`)
1. **Classificador local (opcional, está ligado).** `app/intent_classifier.py` reconhece a intenção
   (aqui: *ranking*). Se estiver confiante, anexa **dois exemplos** ao prompt e escreve no log
   `intencao rotulo=ranking confianca=0.99 aceita=True` (sem o texto da pergunta).
2. **Planejador Gemini.** `_generate` envia a pergunta, o histórico, a data de hoje e o `PLANNER_PROMPT`
   (`app/prompts.py`), exigindo resposta em JSON no formato `PLANNER_SCHEMA`. Resposta típica:
   `{"metric":"faturamento","measure":"valor","operation":"analysis","period":{...},
   "analysis":{"kind":"ranking","group_by":"cliente","limit":3,...}}`.
3. **Normalização do plano** (código, não IA):
   - `normalize_monthly_comparison_plan` (`monthly_comparisons.py`): detecta "algum mês caiu?".
   - `normalize_relative_plan` (`relative_periods.py`): corrige "hoje", "ontem", "ano passado" etc. com a data real.
4. **Recusas.** Se o plano diz `unsupported_reason` (lucro, causa, previsão), responde a mensagem fixa de `UNSUPPORTED`, sem tocar no banco.
5. **Esclarecimento** (`clarify`, `clarify_query`): se falta métrica, medida ou período, ou o período não
   tem **trecho literal** da pergunta como prova, o bot **pergunta** em vez de adivinhar. Aqui o plano é válido.

#### Passo 5 — Montar a consulta (`_query`)
O agente escolhe um de três caminhos:
- **A. Modelo gerencial** (`managerial_query`, em `app/managerial_queries.py`): comparações, séries
  mensais, **rankings**, participação, desvios. O SQL é montado pelo código. *É o caso do nosso exemplo:*
  `kind=ranking`, `group_by=cliente`, `LIMIT 3`.
- **B. Total simples** (`total_query`, em `app/query_templates.py`): um número para uma métrica e período.
- **C. SQL livre pelo Gemini**: só quando há filtro personalizado (cidade, status, "somente"...). Um
  detector no agente força esse caminho (`CITY_FILTER` e uma lista de palavras como "somente", "apenas").

#### Passo 6 — Executar com segurança (`app/database_tools.py`, `app/sql_policy.py`)
- `execute_sql` chama `validate_select` (`sql_policy.py`), que lê o SQL como **árvore sintática** e só deixa
  passar: um único `SELECT`, nas 5 tabelas de negócio, com funções da lista permitida, sem escrita,
  sem CTE recursiva e sem consultar o catálogo do PostgreSQL.
- Conecta com o usuário **`readonly_agent`** (`DatabaseTools.connection`): transação somente leitura, limite de
  tempo (3 s), no máximo 100 linhas, e **recusa conectar** se esse usuário tiver qualquer permissão de escrita.

#### Passo 7 — Escrever a resposta (`app/managerial_rendering.py`)
- `render_managerial` recebe as células do banco e monta o texto: cabeçalho, período e uma linha por item:

```
📊 Ranking de faturamento emitido
Período: 01/09/2026 a 30/09/2026

1. Peças Floresta — R$ 23.439,00
2. Rota Norte Catarinense Transportes — R$ 19.065,35
3. Peças Santa Cruz — R$ 18.500,55
ℹ️ Mostrando apenas os principais itens.
```
- Se há duas medidas, `merge_groupable_answers` junta num bloco só. Se o grupo passar do limite de tamanho, devolve as respostas separadas.

#### Passo 8 — Enviar de volta
- `TelegramService.send` divide a resposta em pedaços de até 3.500 caracteres (`message_chunks`), tenta de
  novo em caso de limite do Telegram e, nos esclarecimentos, mostra **botões** (`clarification_keyboard`).
- O turno (pergunta + resposta) é guardado na sessão para as continuações ("E em agosto?").

### 6. Por que foi desenhado assim (as decisões que você pode defender)

| Decisão | Motivo |
|---|---|
| IA só interpreta; código calcula e escreve | Evita que o modelo invente números; tudo é rastreável ao banco |
| SQL padrão por modelos fixos | Mais rápido, barato e previsível que deixar a IA escrever SQL toda vez |
| Esclarecer em vez de adivinhar | Um número errado com cara de certo é pior que uma pergunta a mais |
| Datas calculadas por Python | O LLM erra contas de calendário; "ontem" tem que ser exato |
| Usuário do banco somente leitura + validação de SQL | Duas barreiras independentes: mesmo que uma falhe, a outra protege |
| Dados sintéticos | Sem dado pessoal (LGPD), base reproduzível e testável |
| Gemini no plano gratuito | Custo zero para um projeto acadêmico |

### 7. Mapa de arquivos — pasta `app/` (3.265 linhas em 21 arquivos)

| Arquivo | O que faz | Funções/classes principais |
|---|---|---|
| `main.py` | Cria o backend FastAPI; rotas `/health` e `/telegram/webhook`; fila e 4 trabalhadores | `create_app`, `webhook`, `health`, `lifespan` |
| `telegram_bot.py` | Programa de **polling** (ou registro do webhook) | `run`, `forward_update`, `forward_updates`, `main` |
| `messaging.py` | Regras de conversa no Telegram: autorização, comandos, envio e botões | `TelegramService`, `message_chunks`, `clarification_keyboard` |
| `sessions.py` | Histórico por gestor, com expiração e cadeado | `SessionStore`, `Session` |
| `config.py` | Todas as configurações (lidas do `.env`) | `Settings` |
| `bi_agent.py` | **O agente**: orquestra planejador, validação, consulta e resposta | `BIAgent` (`answer`, `_answer`, `_query`, `_generate`), `clarify`, `clarify_query`, `merge_groupable_answers` |
| `prompts.py` | As **instruções ao Gemini** (planejador e redator de SQL) e o formato JSON exigido | `PLANNER_PROMPT`, `SYSTEM_PROMPT`, `TOOLS`, `PLANNER_SCHEMA` |
| `analysis_contract.py` | Valida o plano: período com prova literal, tipos de análise | `validate_period`, `validate_analysis`, `UNSUPPORTED` |
| `relative_periods.py` | Calcula "hoje", "ontem", "ano passado", dia exato, mês fixado | `normalize_relative_plan`, `exact_day`, `is_single_day_expression`, `single_month` |
| `monthly_comparisons.py` | Entende "algum mês teve queda em relação ao ano passado?" | `monthly_decline_request`, `normalize_monthly_comparison_plan` |
| `query_templates.py` | SQL fixo para totais (12 combinações métrica×medida) | `TOTALS`, `total_query` |
| `managerial_queries.py` | SQL fixo para comparação, série, ranking, participação, desvio | `managerial_query` |
| `sql_policy.py` | **Filtro de segurança** do SQL (lista de tabelas, funções, nós permitidos) | `validate_select`, `validate_relations` |
| `database_tools.py` | Conecta ao banco, mostra o schema e executa com limites | `DatabaseTools`, `get_schema`, `execute_sql` |
| `rendering.py` | Formata números e período; resposta do caminho de SQL livre | `render_answer`, `cell_text`, `period_text`, `METRICS` |
| `managerial_rendering.py` | Resposta dos modelos gerenciais (total, lista, bloco) | `render_managerial`, `render_managerial_group` |
| `intent_classifier.py` | Classificador local de intenção (lê o JSON treinado) | `IntentClassifier`, `select_examples` |
| `domain.py` | Lista de cidades atendidas | `CITIES`, `CITY_NAMES` |
| `cli.py`, `cli_support.py` | Conversa pelo terminal (`bi-cli`), sem Telegram | `run` |

#### Detalhes que ajudam a explicar

- **Métricas** (`rendering.METRICS`): faturamento emitido, recebimentos, pedidos de venda, contratos de
  fornecimento, clientes, horas de atendimento, ocorrências de pós-venda. Os nomes internos
  (`pedidos`, `horas`, `chamados`) vieram da versão inicial (serviços de software) e foram mantidos; o
  **significado de negócio** é o de autopeças (veja a seção 9).
- **Regras de negócio** nos totais: faturamento = notas por **data de emissão**, sem canceladas;
  recebimentos = por **data de pagamento**, só pagas; pedidos = por data do pedido, sem cancelados.
- **Operações do plano:** `total` (um número) ou `analysis` (comparar, série, ranking, etc.).
- **Tipos de análise** (`KINDS`): comparação, tendência, ranking, segmentação, operacional.

### 8. Mapa de arquivos — outras pastas

#### `scripts/` — geração de dados e ferramentas (1.488 linhas)
| Arquivo | Função |
|---|---|
| `seed.py` | Gera os dados sintéticos; escolhe o **perfil** (`original`, `original-v2`, `comparativo`, `comparativo-v2`, `autopecas`) |
| `comparative_seed.py` | Perfil de 22 meses (jan/2025–out/2026) e a auditoria de cobertura mensal |
| `autopecas_seed.py` | **Perfil de autopeças** (o atual): clientes, peças, valores, notas, pós-venda |
| `manage_db.py` (comando `bi-db`) | `init` (cria schema e usuário somente leitura), `seed`, `validate`, `coverage` |
| `evaluate.py` | Avaliação com perguntas de referência (valida o SQL; com `--live` chama o Gemini) |
| `check_connections.py` | Diagnóstico das conexões (banco, Gemini, Telegram) sem enviar mensagens |
| `train_intents.py` | Treina e testa o classificador de intenções |

#### `db/` — o banco
- `schema.sql`: **5 tabelas** — `clientes`, `contratos`, `pedidos`, `faturamento`, `indicadores_operacionais`
  (com chaves, restrições e índices).
- `roles.sql`: cria o usuário `readonly_agent` com permissão **só de leitura**.

#### `evaluation/` — avaliação (352 linhas + casos)
- `dataset.py` (formato dos casos), `runner.py` (executa e guarda evidências), `scoring.py` (compara resultados).
- `cases.json`: **40 casos** (20 desenvolvimento + 20 reservados); `managerial-cases-v1.json`: **35 casos** gerenciais.

#### `training/` — classificador de intenções (534 linhas)
- `corpus.py` (valida o corpus), `fit.py` (treina), `build_corpus_v2.py` (gera as perguntas sintéticas).
- `questions-v1.json` / `questions-v2.json` (perguntas), `protocol*.json` (regras do experimento),
  `intent-model-v1.json` / `intent-model-v2.json` (modelos treinados).

#### Implantação
- `Dockerfile`, `runtime_entrypoint.py`: a imagem e o programa de entrada, com 3 modos: `backend`, `polling` e `manage-db`.
- `docker-compose.yml`: banco local para desenvolvimento. `deploy/oracle/compose.yaml`: o conjunto de
  produção (banco + backend + polling). `deploy/oracle/configure.py`: grava os segredos com permissão restrita.
- `.github/workflows/tests.yml`: o CI. `.env.example`: modelo das configurações (sem segredos).

#### `docs/` — documentação consolidada por tema
`README.md` (índice e entrega final), `projeto.md` (arquitetura, plano, dicionário de dados),
`avaliacao.md` (protocolos e treinamento de intenções), `experimentos.md` (resultados reais com o Gemini),
`verificacoes.md`, `deploy.md` (inclui a implantação de autopeças de 07/11/2026) e este guia
(`apresentacao.md`). Em subpastas: `entregaveis/` (relatórios, proposta e apresentação) e `dados/` (JSON e SQL).

### 9. O banco de dados e os dados sintéticos

**As 5 tabelas e o significado de negócio (autopeças):**

| Tabela | Significado | Campos principais |
|---|---|---|
| `clientes` | Oficinas, auto elétricas, funilarias, autocenters, frotas, retíficas e lojas | nome, segmento, cidade, uf, cadastrado_em |
| `contratos` | Contratos de fornecimento. `sustentacao` = reposição recorrente; `projeto` = fornecimento pontual | cliente_id, modalidade, início, fim, valor_contratado, status |
| `pedidos` | **Pedidos de venda** de peças | contrato_id, descrição, data, valor, status |
| `faturamento` | Notas fiscais | pedido_id, número, emissão, vencimento, pagamento, valor, status |
| `indicadores_operacionais` | Por contrato e mês: horas de atendimento e ocorrências de pós-venda (garantia, troca, devolução) | competência, horas_previstas/realizadas, chamados_abertos/resolvidos |

> Os nomes das colunas (`chamados_*`, `horas_*`) vêm da versão inicial; mudar o schema exigiria reescrever
> testes e SQL. Por isso mudamos o **vocabulário que o usuário e o Gemini veem**, não os nomes do banco.

**Perfil `autopecas`** (`scripts/autopecas_seed.py`), com semente 42 (mesmos dados toda vez):
- 100 clientes, 22 meses (jan/2025 a out/2026), cerca de 733 contratos, 7,7 mil pedidos, 8,1 mil notas.
- **Escala de empresa pequena-média:** em média R$ 350–410 mil e 320–360 pedidos por mês, ticket médio perto de R$ 1.100.
- Nomes como "Autocenter Atiradores", "Mecânica Camargo & Filhos"; peças como "Pastilhas e discos de freio".
- Notas com prazo de 15 a 45 dias por tipo de cliente, parcelamento ocasional e inadimplência pequena.
- Pós-venda com taxa de resolução em torno de 83%.

**Como o dado é verificado:** `bi-db validate` confere 6 regras de consistência (todo cliente tem contrato;
pedido dentro da vigência do contrato; nota depois do pedido; total faturado não passa do pedido; etc.).
`bi-db coverage` confere que **todo mês** tem dados.

### 10. Segurança (as camadas)

| Camada | O que garante | Onde |
|---|---|---|
| Autorização | Só IDs de gestores autorizados e só chat privado | `messaging.py` |
| Segredo do webhook | Só o nosso bot consegue entregar mensagens | `main.py` |
| Limites | Corpo ≤ 64 KiB, fila ≤ 100, 4 trabalhadores, sessão com expiração | `main.py`, `sessions.py` |
| Filtro de SQL | Um `SELECT`, 5 tabelas, funções permitidas, sem escrita nem catálogo | `sql_policy.py` |
| Usuário somente leitura | Mesmo se o filtro falhar, o banco não permite escrever | `db/roles.sql`, `database_tools.py` |
| Verificação ao conectar | Recusa conexão se o usuário tiver permissão de escrita | `database_tools.py` |
| Limites de consulta | 3 s, 100 linhas, resultado até ~60 mil caracteres | `database_tools.py` |
| Sem segredos no código | Chaves em arquivo privado com permissão restrita; fora do GitHub | `deploy/oracle/`, `.gitignore` |
| Logs sem conteúdo | Nenhum log guarda texto de perguntas ou respostas | `bi_agent.py`, `main.py` |

### 11. O classificador de intenções (o "treinamento")

**O que é.** Um modelo pequeno **treinado de verdade** (aprendizado supervisionado): TF-IDF + regressão
logística. Lê a pergunta e prevê uma de 7 intenções (total, comparação, tendência, ranking, segmentação,
operacional, genérica). **Não é o Gemini**, e **o Gemini não foi treinado**.

**Dados.** Perguntas **sintéticas** de autopeças geradas por moldes (`build_corpus_v2.py`): 24 formas de
perguntar por intenção, 1.112 para treino, 224 para validação e 224 para teste. As formas usadas na
validação e no teste **nunca aparecem no treino**.

**Protocolo.** O critério de sucesso foi gravado **antes** do treino (precisão das sugestões aceitas ≥ 0,90 e
cobertura ≥ 0,50 no teste). O modelo foi congelado num commit e o teste foi aberto **uma única vez**.

**Resultado:**

| | Validação | Teste |
|---|---:|---:|
| Acurácia | 84,8% | **87,9%** |
| Cobertura das sugestões aceitas | 76,8% | **80,8%** |
| Precisão das sugestões aceitas | 93,6% | **95,0%** |

**Como é usado.** Quando confiante (≥ 0,5) e a intenção não é genérica, o bot acrescenta até dois
exemplos de treino ao prompt do Gemini, marcados "sem autoridade sobre datas ou SQL". Ele **não decide**
métrica, período, SQL ou números. A prova de uso é uma linha no log do backend.

**Limites honestos.** O ganho nas respostas **não apareceu** numa medida pequena (16 respostas, com e sem o classificador, sem diferença além do ruído do Gemini); o teste é sintético; a classe
*operacional* é a mais fraca (F1 0,67); numa checagem informal com 22 perguntas reais, acertou 17 (77%).
A versão 1 (de software, 4 formas por cenário) teve 0 sugestões aceitas e ficou desligada.

Detalhes: `docs/avaliacao.md` e `docs/avaliacao.md`.

### 12. Testes e avaliação: o que prova o quê

#### 12.1 Testes automáticos (`tests/`, 29 arquivos, 3.646 linhas)
**296 testes aprovados com PostgreSQL real e 0 pulados** (rodados em 08/11/2026 contra um PostgreSQL
embutido, reproduzindo os passos do CI). Sem banco, 268 rodam e 28 são pulados. Em 10/11/2026, com
os testes novos da reavaliação e do estado durável, a suíte tem 337 testes: 285 passam sem banco de
teste e 52 o exigem (não foram rodados com o banco de teste completo nesta data).

| Grupo | Arquivos de teste | O que garantem |
|---|---|---|
| Agente | `test_agent`, `test_managerial_agent` | Fluxo completo com Gemini **simulado**: esclarecimentos, erros, várias métricas |
| Datas | `test_relative_periods`, `test_monthly_comparisons`, `test_analysis_contract` | "Ontem", intervalos, ano passado, mês fixado, comparações |
| SQL e segurança | `test_sql_policy`, `test_managerial_queries`, `test_database_integration`, `test_managerial_postgres` | Ataques recusados; SQL dos modelos confere com cálculo independente |
| Resposta | `test_rendering`, `test_managerial_rendering`, `test_telegram_presentation` | Formato do texto, números exatos, divisão em mensagens |
| Backend | `test_backend`, `test_sessions`, `test_telegram_transport`, `test_runtime_entrypoint`, `test_e2e_local` | Webhook, fila, autorização, polling, ponta a ponta com PostgreSQL |
| Dados | `test_seed`, `test_comparative_seed`, `test_autopecas_seed` | Dados reproduzíveis, consistentes, na escala certa, sem "Empresa Fictícia" |
| Treinamento | `test_intent_*` (4 arquivos), `test_intent_v2` | Corpus, modelo e uso do classificador |
| Avaliação e conexões | `test_evaluation`, `test_managerial_evaluation`, `test_check_connections`, `test_gemini_transport` | O próprio sistema de avaliação e as mensagens de erro do provedor |

**Prática usada:** primeiro um teste que **falha** reproduzindo o defeito, depois a correção. Nos PRs
desta semana, os testes novos foram confirmados como falhando sem a correção.

#### 12.2 Avaliação real com o Gemini (outubro de 2026, versão congelada `59c9eb8`)
| Conjunto | Resultado | Observação |
|---|---|---|
| 40 casos originais: 20 de desenvolvimento | **20/20** na 3ª rodada | Antes houve rodadas parciais e diagnósticos |
| 40 casos originais: 20 **reservados** (teste) | **20/20** (16/16 respostas, 4/4 esclarecimentos) | Aberto uma única vez; média de **1,649 s** por turno (agente + banco; não inclui o Telegram) |
| 35 casos gerenciais: 25 de desenvolvimento | **24/25** | Falha D38: esclarecimento indevido (planejador devolveu medida vazia) |

**Como ler esses números:** medem o sistema **híbrido** (Gemini + modelos + código) numa amostra
pequena; **não** provam generalização ampla e **não** são só "acurácia da IA". Foram obtidos com o
domínio e o código de outubro (software). Depois do domínio de autopeças e das correções de novembro, a
avaliação real com o Gemini **não foi repetida** (depende da cota); no lugar, usamos os testes automáticos, a
conferência dos valores do bot contra o gerador e os testes manuais no Telegram.

#### 12.3 Conferência no Telegram (07–08/11/2026)
Cada resposta foi comparada com o valor que o gerador de dados produz: totais, recebimentos, comparação
ago/2026 × ago/2025 (+6,20%), ranking, distribuição por segmento, dia exato, taxa de resolução (65%),
intervalos de datas e "compara com o ano passado". **Todos bateram, centavo por centavo.**

#### 12.4 Revisão independente do código inteiro (ultrareview)
Uma revisão automática do código completo apontou **10 achados**; **todos foram reproduzidos** antes
de corrigir (nenhum falso positivo). Seis foram corrigidos (intervalos reduzidos a um dia, "ano passado" sem mês,
taxa com 20 casas, limite de tamanho derrubando respostas, CTE lendo o catálogo, update ruim travando o
bot) e quatro menores ficaram de fora.

### 13. A história do desenvolvimento (linha do tempo)

79 commits entre 04/10/2026 e 08/11/2026.

| Data | Marco |
|---|---|
| 04/10 | Repositório criado; primeira versão com PostgreSQL real e CI; testes de integração |
| 10/10 | Alinhamento com a proposta; diagnóstico das conexões; revisão frente ao PDF aprovado |
| 11/10 | Várias métricas por pergunta; avaliação reproduzível (S7–S11); 40 casos; rodadas reais; teste reservado; base de 22 meses; relatório final e entrega |
| 12/10 | Treinamento de intenções v1; análises gerenciais (comparar, série, ranking, participação); comandos em português; anos relativos; correção da comparação mensal |
| 02/11 | Hospedagem na Oracle versionada; dia exato ("ontem") sem depender do Gemini; perfis de dados v2; mesclagem de medidas no mesmo bloco |
| 07/11 | **Domínio de autopeças**: respostas limpas, vocabulário, dataset novo (escala menor); deploy na Oracle; defeitos achados e corrigidos (taxa de resolução, formato) |
| 08/11 | Revisão do código inteiro; correções de datas, segurança e robustez; **classificador v2** treinado, avaliado e ligado; correção do entrypoint do container |

**Etapas formais do cronograma (PAC):** S1–S7 fundamentação, schema, dados, agente e integração;
S7–S8 casos de avaliação; S8–S11 experimentos e versão congelada; S11–S12 validação (aceite declarado
pelo responsável); S12–S14 relatório final; S14–S16 revisão e entrega.

**Mudanças de decisão que valem contar:** (1) provedor trocado de Anthropic para Gemini (cota gratuita);
(2) escopo ampliado até a entrega final; (3) em novembro, domínio de serviços de software trocado para
autopeças e dados reduzidos à escala de uma empresa pequena-média.

### 14. Como demonstrar ao vivo (roteiro de 8 a 10 minutos)

| # | O que fazer | O que mostrar |
|---|---|---|
| 1 | `/limpar` e `/comecar` | Bot em português, histórico limpo |
| 2 | "Qual o faturamento?" | Pergunta o período (não adivinha) |
| 3 | "setembro de 2026" | R$ 458.603,80 |
| 4 | "Pedidos de venda em setembro de 2026, valor e quantidade" | R$ 468.323,95 e 385 pedidos, uma linha por medida |
| 5 | "Top 3 clientes por faturamento em setembro de 2026" | Ranking compacto (Peças Floresta R$ 23.439,00) |
| 6 | "Compare o faturamento de agosto de 2026 com agosto de 2025" | +6,20%, com 📈 |
| 7 | "Contratos em agosto de 2026" → "compara com o ano passado" | Mês mantido na continuação |
| 8 | "Qual o lucro em setembro de 2026?" | Recusa honesta: sem dados de custo |
| 9 | Mostrar o **log** do backend | Linha `intencao rotulo=...` (classificador em uso) |
| 10 | Mostrar `docs/avaliacao.md` | Método, protocolo e limites |

### 15. Perguntas prováveis da banca (e respostas curtas)

**O Gemini foi treinado por vocês?** Não. É usado por API, sem alterar pesos. Treinamos um classificador
pequeno e local, com dados sintéticos, que só sugere exemplos ao Gemini.

**A IA pode inventar números?** Não os exibidos: todo número vem do banco; o texto final é montado pelo
nosso código, não pelo Gemini.

**E se a IA gerar um SQL perigoso?** Duas barreiras: o filtro lê o SQL como árvore e só aceita um `SELECT` nas
5 tabelas com funções permitidas; e o usuário do banco é somente leitura, e o sistema recusa conectar se ele tiver permissão de escrita.

**Os dados são reais? E a LGPD?** São 100% sintéticos, sem CNPJ, telefone ou e-mail. O sistema já nasce com minimização: as linhas do banco não
são enviadas ao provedor da IA. Restam a pergunta e o histórico da conversa (inclui respostas anteriores), por isso,
com dados reais, ainda seriam necessários contrato com o provedor, base legal e RIPD. Ver [Privacidade e LGPD](../README.md#privacidade-e-lgpd).

**Por que SQL por modelo fixo e não deixar a IA escrever tudo?** Previsibilidade, custo e segurança. A IA só escreve SQL para filtros livres.

**Como sabem que as respostas estão certas?** Testes automáticos com cálculo independente, 40 + 35 casos de
referência com o Gemini real, e conferência manual dos valores do bot contra o gerador de dados.

**Qual a acurácia do sistema?** Em outubro: 20/20 no teste reservado de 40 casos (amostra pequena), com 1,649 s
por turno. Não foi repetida após a mudança de domínio; os testes automáticos e a conferência manual cobrem essa lacuna.

**O que não funciona?** Lucro e margem (não há custos), previsão, causa de variações. Perguntas vagas geram esclarecimento.
Veja a seção 16.

**Por que o classificador está ligado se o ganho não apareceu na medida?** Porque atingiu o critério de qualidade
declarado antes do teste e seu papel é seguro (só sugere exemplos). A medida de 10/11/2026 (conjunto C, ligado e desligado) não mostrou diferença além do ruído; uma amostra maior seria necessária para concluir.

**Quem escreveu o código?** Seja direto: foi desenvolvido com assistentes de IA, sob sua direção e revisão. As
decisões de projeto, os testes, a avaliação e a validação são suas, e este guia mostra que você domina cada parte.

### 16. Limitações e honestidade (não esconda; mostre que você conhece)

- Os resultados de **outubro** (domínio de software) e os de **novembro** (autopeças: 12/16, 6/8 e 13/16) não são comparáveis: base, casos, classificador e código mudaram. Nenhum dos dois indica que o sistema melhorou ou piorou.
- A amostra de avaliação é **pequena** (40 e 35 casos) e sintética; não prova generalização.
- O **GitHub Actions está falhando na inicialização** desde 07/11 (causa externa ao código, a verificar na conta);
  por isso os testes com banco foram rodados localmente.
- O classificador: **sem efeito mensurável** nas respostas na medida pequena de 10/11/2026; teste sintético; classe *operacional* fraca.
- O formato de **SQL livre** mostra valores sem "R$" (o texto não afirma a moeda de uma consulta escrita pela IA).
- Os nomes das colunas do banco seguem o vocabulário de software; só o significado de negócio mudou.
- O PDF e o Word do **relatório final** e os experimentos antigos estão no vocabulário de software.
- O sistema depende de serviços externos (Gemini, Telegram) e de uma cota gratuita.
- Fila, deduplicação e histórico ficam em memória por padrão (um processo, reiniciar perde o que não foi processado). O **estado durável** em PostgreSQL (`STATE_DATABASE_URL`) corrige isso e permite vários workers, mas a entrega é *pelo menos uma vez*, não exatamente uma vez.
- A latência medida (1,649 s) **não inclui** o tempo do Telegram.

### 17. Comandos úteis (para rodar e mostrar)

```powershell
# Preparar o ambiente (uma vez)
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt ; python -m pip install -e . --no-deps
Copy-Item .env.example .env      # depois edite as chaves

# Banco local e dados de autopeças
docker compose up -d --wait
bi-db init
bi-db seed --profile autopecas --clients 100 --seed 42 --start-month 2025-01 --end-month 2026-10
bi-db validate ; bi-db coverage --profile autopecas

# Testes e lint
python -m pytest -q          # com TEST_DATABASE_URL definido, roda os testes com PostgreSQL
python -m ruff check app scripts tests evaluation training

# Conversar sem Telegram
bi-cli

# Avaliação (validate não chama o Gemini)
python -m scripts.evaluate validate
python -m scripts.evaluate validate --dataset evaluation/managerial-cases-v1.json
```

Na VM da Oracle (produção): ver `deploy/oracle/README.md` (envio por `scp`, `docker build --no-cache`,
`docker compose ... up -d`) e `docs/deploy.md` (o registro das oito rodadas).

### 18. Cola de números

| Item | Valor |
|---|---|
| Commits | 79 (04/10 a 08/11/2026) |
| Código do aplicativo (`app/`) | 21 arquivos, 3.265 linhas |
| Testes | 29 arquivos, 323 testes (todos aprovados com PostgreSQL) |
| Tabelas do banco | 5 |
| Dataset de autopeças | 100 clientes · 22 meses · ~733 contratos · ~7,7 mil pedidos · ~8,1 mil notas |
| Escala | ~R$ 350–410 mil e 320–360 pedidos por mês · ticket médio ~R$ 1.100 |
| Avaliação real (out/2026) | 40 casos: 20/20 desenvolvimento e 20/20 reservados · média 1,649 s/turno |
| Avaliação gerencial | 35 casos; 24/25 no desenvolvimento |
| Classificador v2 | 1.112 treino · 224 validação · 224 teste · acurácia 87,9% · precisão das aceitas 95,0% · cobertura 80,8% |
| Limites de segurança | consulta 3 s · 100 linhas · corpo 64 KiB · fila 100 · 4 trabalhadores · sessão 1 h / 8 turnos |
| Ultrareview | 10 achados reproduzidos · 6 corrigidos |

## Demonstração e reprodução da entrega

_Origem: `docs/apresentacao.md` (consolidado em 2026-11-09)._

Use somente a base sintética e um usuário autorizado. O roteiro é uma orientação de apresentação; não é registro de que uma nova demonstração foi executada. Credenciais ficam no `.env`, nunca nos slides, terminal gravado ou pacote.

### Preparação

1. Instale as dependências conforme o [README](../README.md) e prepare um banco PostgreSQL 16 isolado. Para a apresentação, carregue o perfil `autopecas` (`bi-db seed --profile autopecas --clients 100 --seed 42 --start-month 2025-01 --end-month 2026-10`). `bi-db init` e `bi-db seed` recusam recursos já existentes ou base preenchida; não use reset destrutivo.
2. Execute `bi-db validate` e `python -m scripts.evaluate validate`. Esta etapa não chama Gemini. As contagens e os valores dos relatórios de outubro referem-se aos perfis anteriores; não os atribua à base `autopecas` sem comparação.
3. Configure o modelo, a chave Gemini, o token Telegram, o segredo e os IDs permitidos no ambiente de demonstração. Respeite a configuração do bot em uso; não execute webhook e polling simultaneamente.
4. Confira saúde do backend e utilize apenas um processo FastAPI. Reiniciar perde sessões e fila em memória.

### Apresentação sugerida de cinco a oito minutos

| Momento | Ação | O que demonstrar |
|---|---|---|
| Contexto | Explicar serviço B2B e base sintética | Pergunta em português e indicadores sem dados reais |
| Arquitetura | Mostrar Telegram → FastAPI → Gemini → PostgreSQL | Quatro camadas e role somente leitura |
| Ambiguidade | Enviar `Qual o faturamento?` | Esclarecimento do período antes de SQL |
| Continuação | Responder `janeiro de 2025` | Resposta numérica com período e conferência SQL |
| Múltiplas métricas | Enviar `Qual o total de pedidos e o faturamento emitido em agosto de 2025?` | Resultados independentes por métrica |
| Contexto | Enviar `/limpar` e uma nova pergunta | Reinício explícito da conversa |
| Evidência | Mostrar relatório do teste reservado | 16/16 respostas, 4/4 esclarecimentos, limites da amostra |
| Encerramento | Explicar aceite e limitações | Aceite simples de 11/10/2026, sem feedback atribuído |

### Conferência independente

Use a role de leitura para conferir a resposta de faturamento, sem mostrar a URL ou senha de conexão:

```sql
SELECT SUM(valor) AS total
FROM faturamento
WHERE emissao >= DATE '2025-01-01'
  AND emissao < DATE '2025-02-01'
  AND status <> 'cancelada';
```

A apresentação copia o valor produzido na base atual, sem fixar um número a partir de memória. Os relatórios versionados referem-se à base cujo hash foi registrado; não atribua seus valores a uma base regenerada sem comparação.

### Falhas e medição

Em cota ou indisponibilidade, mostre a mensagem controlada e encerre a chamada; não habilite cobrança ou mude modelo para concluir a apresentação. As evidências congeladas continuam disponíveis offline. Nunca exponha corpos HTTP, assinaturas de ferramentas ou logs que possam conter conteúdo interno.

A latência ponta a ponta no Telegram **não foi medida**: o valor publicado (1,649 s) é de agente + banco. Uma medição futura deve registrar o envio no cliente Telegram e o recebimento da resposta com o mesmo relógio, versão, pergunta, base e condição de rede, sem incluir a espera humana por esclarecimento. Do mesmo modo, não se atribui comparação com dashboards sem um protocolo equivalente.

## Roteiro de entrega do PAC

_Origem: `docs/apresentacao.md` (consolidado em 2026-11-09)._

Registro do cronograma do PAC e da situação final de cada entrega. A meta de trabalho era **01/12/2026** (início de dezembro), antecipada a pedido do responsável. O [índice da entrega final](README.md#entrega-final--pac-extensionista-viii) lista os artefatos.

### Resultado entregue

Um gestor autorizado faz perguntas em português em chat privado no Telegram, recebe esclarecimento quando necessário e obtém indicadores rastreáveis à base sintética. A entrega inclui código reproduzível, avaliação com evidências, relatório acadêmico e demonstração. O sistema não pressupõe múltiplos processos nem persistência de filas e sessões.

### Cronograma e situação final

| Etapa planejada | Situação final | Evidência |
|---|---|---|
| Publicação, CI e teste real | Código publicado e suíte com PostgreSQL aprovada. Conversa real com Gemini/Telegram confirmada pelo responsável; não há registro detalhado versionado (data, resposta e valor conferido) | [Deploy](deploy.md), [verificações](verificacoes.md) |
| Conjunto de avaliação | 40 casos originais e 35 cenários gerenciais, com SQL de referência e separação entre desenvolvimento e teste reservado | [Avaliação](avaliacao.md) |
| Avaliação e correções | Rodadas reais com o Gemini; terceira rodada 20/20 e teste reservado 16/16 respostas e 4/4 esclarecimentos | [Experimentos](experimentos.md) |
| Versão candidata | Reprodução em Linux com Docker, 110 testes com PostgreSQL e 34 referências SQL; roteiro de demonstração; versão congelada | [Verificações](verificacoes.md#verificação-de-reprodução-para-entrega-final) |
| Relatório e validação qualitativa | Relatório final (Word/PDF) entregue. Aceite do gestor declarado pelo responsável; sem feedback estruturado | [Avaliação](avaliacao.md#registro-de-aceite-do-gestor) |
| Revisão e entrega | Normas institucionais, assinaturas e submissão ficam a cargo do responsável | [Índice da entrega](README.md#entrega-final--pac-extensionista-viii) |

### Critérios de aceitação do teste real

O roteiro passo a passo está no [README](../README.md#teste-manual-de-ponta-a-ponta). O teste é aceito quando:

- a ambiguidade não executa consulta de negócio;
- a continuação usa o período informado;
- o valor coincide com a consulta de referência;
- `/limpar` reinicia o contexto;
- um usuário não autorizado não obtém resposta com dados;
- falhas externas produzem mensagem controlada, sem credenciais nem diagnóstico interno.

### Avaliação acadêmica

Os testes automáticos não comprovam acerto semântico do LLM; por isso a avaliação usa um arquivo de casos com identificador, categoria, pergunta, contexto, comportamento esperado e SQL de referência, e um executor opt-in que não chama provedores por padrão. Cada rodada preserva o conjunto e o commit usados, e o critério de acerto foi definido antes das rodadas finais.

### Limites de escopo

Ficam fora desta entrega dashboard novo, novos canais de mensagens, múltiplos provedores simultâneos e infraestrutura distribuída. Reiniciar o processo pode perder fila e histórico; essa limitação consta no relatório e no roteiro de demonstração.
