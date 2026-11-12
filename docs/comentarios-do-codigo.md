# Comentários e docstrings do código, por função

Este documento reúne, **função por função**, os comentários (`#`) e as docstrings que existiam no código-fonte
até a versão **v1.0.1** (commit `81778f8`). Eles foram removidos do código; o raciocínio que registravam
está aqui, ao lado do nome e da assinatura de cada função ou classe.

## Como ler

- **Escopo.** Foram retirados os comentários `#` e as docstrings dos arquivos Python e os comentários `--` dos
  arquivos SQL em `db/`. Foram mantidos os marcadores que têm efeito sobre ferramentas (`# fmt: skip`) e os comentários
  de arquivos de configuração (`.env.example`, `.github/workflows/tests.yml`, `.gitignore`), que fazem parte
  da configuração e não do código.
- **Números de linha** referem-se aos arquivos **antes** da remoção (commit `81778f8`). Para ver o texto original no
  contexto, use `git show 81778f8:caminho/do/arquivo.py`.
- **Cada entrada** mostra o tipo (*Docstring* ou *Comentário*), a linha, o texto original e, nos comentários, o trecho de código
  que ele explica (**Trecho comentado**).
- **Efeito sobre o comportamento.** A remoção não altera a lógica: a comparação das árvores sintáticas (AST) antes e depois
  difere somente nas docstrings e em duas chamadas que usavam `description=__doc__` (`scripts/evaluate.py` e
  `scripts/train_intents.py`), que passaram a receber o mesmo texto como literal. A suíte de testes continua com 337 testes passando.
- **Recorrência.** Vários comentários registram decisões de segurança (nada de texto do provedor, SQL, credencial ou pergunta do
  usuário em logs e respostas) e de correção do comportamento do agente. As seções por arquivo abaixo permitem localizá-las.

## Índice

- [`app/__init__.py`](#app__init__py)
- [`app/analysis_contract.py`](#appanalysis_contractpy)
- [`app/bi_agent.py`](#appbi_agentpy)
- [`app/cli.py`](#appclipy)
- [`app/cli_support.py`](#appcli_supportpy)
- [`app/database_tools.py`](#appdatabase_toolspy)
- [`app/domain.py`](#appdomainpy)
- [`app/intent_classifier.py`](#appintent_classifierpy)
- [`app/main.py`](#appmainpy)
- [`app/managerial_queries.py`](#appmanagerial_queriespy)
- [`app/managerial_rendering.py`](#appmanagerial_renderingpy)
- [`app/messaging.py`](#appmessagingpy)
- [`app/monthly_comparisons.py`](#appmonthly_comparisonspy)
- [`app/prompts.py`](#apppromptspy)
- [`app/query_templates.py`](#appquery_templatespy)
- [`app/relative_periods.py`](#apprelative_periodspy)
- [`app/rendering.py`](#apprenderingpy)
- [`app/sessions.py`](#appsessionspy)
- [`app/sql_policy.py`](#appsql_policypy)
- [`app/state.py`](#appstatepy)
- [`app/telegram_bot.py`](#apptelegram_botpy)
- [`deploy/oracle/configure.py`](#deployoracleconfigurepy)
- [`evaluation/__init__.py`](#evaluation__init__py)
- [`evaluation/dataset.py`](#evaluationdatasetpy)
- [`evaluation/runner.py`](#evaluationrunnerpy)
- [`evaluation/scoring.py`](#evaluationscoringpy)
- [`runtime_entrypoint.py`](#runtime_entrypointpy)
- [`scripts/__init__.py`](#scripts__init__py)
- [`scripts/autopecas_seed.py`](#scriptsautopecas_seedpy)
- [`scripts/check_connections.py`](#scriptscheck_connectionspy)
- [`scripts/comparative_seed.py`](#scriptscomparative_seedpy)
- [`scripts/evaluate.py`](#scriptsevaluatepy)
- [`scripts/manage_db.py`](#scriptsmanage_dbpy)
- [`scripts/seed.py`](#scriptsseedpy)
- [`scripts/train_intents.py`](#scriptstrain_intentspy)
- [`tests/test_agent.py`](#teststest_agentpy)
- [`tests/test_analysis_contract.py`](#teststest_analysis_contractpy)
- [`tests/test_autopecas_seed.py`](#teststest_autopecas_seedpy)
- [`tests/test_check_connections.py`](#teststest_check_connectionspy)
- [`tests/test_comparative_seed.py`](#teststest_comparative_seedpy)
- [`tests/test_database_integration.py`](#teststest_database_integrationpy)
- [`tests/test_durable_state.py`](#teststest_durable_statepy)
- [`tests/test_e2e_local.py`](#teststest_e2e_localpy)
- [`tests/test_evaluation.py`](#teststest_evaluationpy)
- [`tests/test_gemini_transport.py`](#teststest_gemini_transportpy)
- [`tests/test_intent_v2.py`](#teststest_intent_v2py)
- [`tests/test_managerial_agent.py`](#teststest_managerial_agentpy)
- [`tests/test_managerial_rendering.py`](#teststest_managerial_renderingpy)
- [`tests/test_relative_periods.py`](#teststest_relative_periodspy)
- [`tests/test_rendering.py`](#teststest_renderingpy)
- [`tests/test_runtime_entrypoint.py`](#teststest_runtime_entrypointpy)
- [`tests/test_seed.py`](#teststest_seedpy)
- [`tests/test_sql_policy.py`](#teststest_sql_policypy)
- [`tests/test_telegram_transport.py`](#teststest_telegram_transportpy)
- [`training/__init__.py`](#training__init__py)
- [`training/build_corpus_v2.py`](#trainingbuild_corpus_v2py)
- [`training/corpus.py`](#trainingcorpuspy)
- [`training/fit.py`](#trainingfitpy)
- [Arquivos SQL (`db/`)](#arquivos-sql-db)

## Comentários por arquivo

### `app/__init__.py`

**Nível do módulo**

- *Docstring* (linha 1): Assistente conversacional de BI — PAC Extensionista VIII.

### `app/analysis_contract.py`

**Nível do módulo**

- *Docstring* (linha 1): Contratos gerenciais: sem inferir período, filtros ou unidade monetária.

**Função `validate_period`** (linha 49) — `def validate_period(period: dict, messages: list[dict], *, today=None) -> dict`

- *Comentário* (linhas 124–125): Mês fixado antes na conversa ("agosto de 2026") e reaproveitado no ano relativo: aceito só se o próprio gestor nomeou esse mês.
  - Trecho comentado: `carried = single_month(period) named = set().union(`

**Função `normalize_unranked_plan`** (linha 154) — `def normalize_unranked_plan(plan: dict, question: str) -> dict`

- *Docstring* (linhas 155–163): Ranking sem limite que o gestor não pediu é uma consulta comum, não um ranking.

  Dois casos reais: "contratos iniciados em 2025, excluindo os cancelados" (total com filtro,
  marcado como ranking sem agrupamento) e "clientes cadastrados em cada UF" (o contrato não tem
  agrupamento por UF e o modelo escolheu cidade). Em ambos o prompt manda usar analysis=null e
  deixar o SQL personalizado agrupar e ordenar como foi pedido. Só reinterpreta quando a
  pergunta não pede ranking, top, maiores, menores, lista nem algo equivalente ("principais",
  "mais"); nesses casos o esclarecimento sobre o tamanho do ranking continua valendo.

### `app/bi_agent.py`

**Nível do módulo**

- *Docstring* (linha 1): Planejamento sem SQL, loop de tools e saída final com proveniência das células.
- *Comentário* (linha 35): Pedido restrito a uma cidade exige SQL personalizado, nunca o total padrão.
  - Trecho comentado: `CITY_FILTER = r"\b(?:em|de|na)\s+(?:" + "|".join(map(re.escape, CITY_NAMES)) + r")\b"`

**Função `gemini_contents`** (linha 64) — `def gemini_contents(messages)`

- *Docstring* (linha 65): Preserva partes e thought_signature originais nos turnos de function calling.

**Função `provider_error_category`** (linha 95) — `def provider_error_category(error)`

- *Docstring* (linha 96): Classificação indicativa: retorna apenas rótulos fixos, nunca texto do provedor.

**Função `merge_groupable_answers`** (linha 108) — `def merge_groupable_answers(answers: list[str], evidences: list[dict]) -> list[str]`

- *Docstring* (linhas 109–110): Funde respostas consecutivas com cabeçalho idêntico (mesma métrica, período e
  tipo), variando só a medida, para não repetir o cabeçalho a cada medida pedida.
- *Comentário* (linhas 139–140): O grupo junto passa do limite, mas cada resposta já foi montada sozinha: entregue-as separadas em vez de falhar a pergunta inteira.
  - Trecho comentado: `merged.extend(answers[index:end]) index = end return merged`

**Função `clarify_query`** (linha 161) — `def clarify_query(plan: dict, messages: list, *, today=None) -> str | None`

- *Comentário* (linha 193): Só aceita evidência literal de mensagem do gestor, não de tool ou modelo.
  - Trecho comentado: `if ( not isinstance(evidence, str) or not evidence.strip()`

**Função `BIAgent.__init__`** (linha 216) — `def __init__(self, settings: Settings, client=None, database=None)`

- *Comentário* (linha 233): O classificador é apoio opcional; sua falha nunca bloqueia o planejador.
  - Trecho comentado: `self.intent_model = None async def close(self):`

**Função `BIAgent.answer`** (linha 243) — `async def answer(self, question: str, history: list, *, trace: dict | None=None) -> tuple[str, list]`

- *Comentário* (linha 246): Evidência opcional pertence à chamada, nunca ao estado compartilhado do bot.
  - Trecho comentado: `trace = trace if trace is not None else {} trace.clear()`
- *Comentário* (linha 279): Nenhuma exceção externa, credencial ou SQL chega ao Telegram.
  - Trecho comentado: `return FAILURE, turn + [{"role": "assistant", "content": FAILURE}]`

**Função `BIAgent._answer`** (linha 297) — `async def _answer(self, question, history, turn, trace)`

- *Comentário* (linhas 299–300): O planejador não declara tools: não envie blocos tool_use/tool_result históricos à API sem as respectivas definições. Mantém pedido e resposta.
  - Trecho comentado: `planning_messages = [m for m in messages if isinstance(m["content"], str)]`
- *Comentário* (linha 311): Só rótulo e confiança: o texto da pergunta nunca vai para o log.
  - Trecho comentado: `logger.info( "intencao rotulo=%s confianca=%.2f aceita=%s",`
- *Comentário* (linha 376): Barreira conservadora contra omissão de filtros explícitos em templates.
  - Trecho comentado: `if ( re.search( r"\b(somente|apenas|só|pag[oa]s?|cancelad[oa]s?|entregues?|ativos?|média|médio|mediana|perc...`
- *Comentário* (linhas 401–402): Cada métrica tem resultados próprios: q1 de pedidos não pode ser reutilizado como faturamento. Mantém só o contexto textual entre consultas.
  - Trecho comentado: `evidence = {"plan": copy.deepcopy(query), "attempts": []}`
- *Comentário* (linhas 411–412): Guarda só o pedido real e a resposta visível. Tools/assinaturas permanecem no loop que as originou, sem contaminar esclarecimentos ou outras métricas.
  - Trecho comentado: `return text, turn + [{"role": "assistant", "content": text}]`

**Função `BIAgent._query`** (linha 415) — `async def _query(self, plan, messages, trace, evidence)`

- *Comentário* (linha 569): Uma pergunta composta só é concluída quando todas as métricas são válidas.
  - Trecho comentado: `raise ValueError("Não foi possível concluir uma das consultas planejadas.")`

### `app/cli.py`

**Nível do módulo**

- *Docstring* (linha 1): CLI local com as mesmas regras e histórico do agente Telegram.

### `app/cli_support.py`

**Nível do módulo**

- *Docstring* (linha 1): Erros de argumentos também seguem o idioma do produto.

### `app/database_tools.py`

**Nível do módulo**

- *Docstring* (linha 1): Conexões descartáveis, role de leitura e consultas limitadas no servidor.

**Função `scalar`** (linha 22) — `def scalar(value)`

- *Comentário* (linha 24): Preserva dígitos e escala, inclusive zero; nunca float.
  - Trecho comentado: `return format(value, "f")`

**Função `DatabaseTools.connection`** (linha 37) — `def connection(self)`

- *Comentário* (linha 61): Também recusa grants de escrita introduzidos acidentalmente depois do setup.
  - Trecho comentado: `bad = conn.execute("""SELECT EXISTS (SELECT 1 FROM pg_class c`

**Função `DatabaseTools._categorical_values`** (linha 73) — `def _categorical_values(conn, columns) -> dict`

- *Docstring* (linhas 74–78): Valores distintos das colunas de categoria, para o modelo filtrar com a grafia do dado.

  Só colunas de texto com nome de categoria e poucos valores distintos; nomes, descrições e
  outros textos livres não entram.

**Função `DatabaseTools.execute_sql`** (linha 137) — `def execute_sql(self, sql: str) -> dict`

- *Comentário* (linha 142): LIMIT fora da consulta também limita SELECTs sem LIMIT ou com LIMIT maior.
  - Trecho comentado: `with conn.cursor() as cur: cur.execute( f"SELECT * FROM ({query}) AS resultado LIMIT {self.settings.max_que...`
- *Comentário* (linhas 144–145): O único valor interpolado além da AST normalizada é um inteiro validado. Sem bind parameters, '%' do SQL não vira placeholder.
  - Trecho comentado: `cur.execute( f"SELECT * FROM ({query}) AS resultado LIMIT {self.settings.max_query_rows + 1}"`
- *Comentário* (linha 171): Diagnóstico do servidor é dado interno para autocorreção, nunca resposta ao gestor.
  - Trecho comentado: `detail = (exc.diag.message_primary or "")[:500]`

### `app/domain.py`

**Nível do módulo**

- *Docstring* (linha 1): Vocabulário do negócio compartilhado entre o agente e a geração de dados.
- *Comentário* (linha 3): Praças atendidas pela revenda: (cidade, UF). A ordem não tem significado.
  - Trecho comentado: `CITIES = ( ("Joinville", "SC"), ("Blumenau", "SC"),`

### `app/intent_classifier.py`

**Nível do módulo**

- *Docstring* (linha 1): Inferência TF-IDF/logística do artefato aprendido; não consulta banco ou IA.

### `app/main.py`

**Nível do módulo**

- *Docstring* (linhas 1–5): Backend FastAPI.

  Sem STATE_DATABASE_URL, sessões e fila ficam em memória: use um único processo. Com ele, caixa de
  entrada e sessões são duráveis (PostgreSQL) e vários processos podem compartilhar a carga.

**Função `create_app.lifespan`** (linha 46) — `async def lifespan(app)`

- *Comentário* (linha 50): Sem isto o INFO dos módulos do projeto não chega ao log do container.
  - Trecho comentado: `handler = logging.StreamHandler() handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)...`
- *Comentário* (linha 55): httpx INFO registra URLs que contêm o token do Telegram.
  - Trecho comentado: `for name in ("httpx", "httpcore", "telegram", "google.genai"):`

**Função `create_app.lifespan.settle`** (linha 71) — `async def settle(action, update_id)`

- *Comentário* (linha 75): A reserva expira e outro consumidor reprocessa; nunca derruba o consumidor.
  - Trecho comentado: `logger.error("falha_estado_duravel") async def worker():`

### `app/managerial_queries.py`

**Nível do módulo**

- *Docstring* (linha 1): SQL gerencial compilado de registros fixos; números calculados no PostgreSQL.

**Função `_aligned_months`** (linha 74) — `def _aligned_months(plan)`

- *Docstring* (linha 75): Somente intervalos de um ano calendário com os mesmos cortes mês/dia.

**Função `managerial_query`** (linha 99) — `def managerial_query(plan: dict) -> dict | None`

- *Comentário* (linha 115): Outros alinhamentos temporais continuam no executor de SQL.
  - Trecho comentado: `return None`
- *Comentário* (linha 128): Taxas não são aditivas: preservar numeradores/denominadores no SQL livre.
  - Trecho comentado: `return None`
- *Comentário* (linha 200): Para horas, uma relação fixa própria conserva ambas as medidas do mesmo registro.
  - Trecho comentado: `planned_plan = {**plan, "measure": "horas_previstas"}`

### `app/managerial_rendering.py`

**Nível do módulo**

- *Docstring* (linhas 1–7): Texto gerencial controlado: cálculos e direção exclusivamente das células SQL.

  Três formas de apresentação, todas com um único cabeçalho e sem rótulos repetidos:
  - total: uma linha ``Rótulo: valor`` por medida;
  - lista (ranking, evolução, distribuição): uma linha por item;
  - bloco (comparações e análises com várias colunas): item e marcadores.
- *Comentário* (linha 48): Colunas de uma consulta total/lista que carregam a medida pedida.
  - Trecho comentado: `MEASURE_COLUMNS = {"total", "valor", "quantidade", "horas", "taxa"}`

**Função `_amount`** (linha 85) — `def _amount(column, value, context, *, noun=True)`

- *Docstring* (linha 86): Valor de uma linha isolada; contagens ganham o substantivo ("6 pedidos").

**Função `grouping_key`** (linha 124) — `def grouping_key(context: dict)`

- *Docstring* (linha 125): Identifica contextos com cabeçalho idêntico, variando só a medida.

**Função `display_item`** (linha 147) — `def display_item(item, context, monthly: bool) -> str`

- *Docstring* (linha 148): Nome do item sem o identificador interno que o SQL usa para desempatar.

**Função `_total_lines`** (linha 175) — `def _total_lines(record, context)`

- *Comentário* (linha 182): "Ocorrências abertas: 20" já nomeia o item; só "Quantidade" pede o substantivo.
  - Trecho comentado: `noun = context.get("measure") in (None, "quantidade")`

**Função `_render_parts`** (linha 199) — `def _render_parts(result: dict, context: dict) -> tuple[list[str], list[str], bool]`

- *Docstring* (linha 200): Cabeçalho, corpo e se o resultado está vazio (para fundir medidas).

**Função `render_managerial_group`** (linha 298) — `def render_managerial_group(items: list[tuple[dict, dict]]) -> str`

- *Docstring* (linhas 299–300): Mescla resultados com cabeçalho idêntico (mesma métrica, período e tipo),
  variando só a medida, num único bloco em vez de repetir o cabeçalho.
- *Comentário* (linha 309): Totais já trazem o rótulo da medida em cada linha.
  - Trecho comentado: `lines.extend([f"{measure_subtitle(context)}: sem registros"] if empty else body)`

### `app/messaging.py`

**Nível do módulo**

- *Docstring* (linha 1): Regras de mensageria compartilhadas pelo webhook e pelo polling local.

**Função `clarification_keyboard`** (linha 16) — `def clarification_keyboard(text)`

- *Docstring* (linha 17): Opções controladas enviam texto normal e mantêm o contexto/autorização do chat.
- *Comentário* (linha 29): O prefixo vem de METRICS: é o mesmo texto que o agente usa ao pedir a medida.
  - Trecho comentado: `choices = { "pedidos": [["Valor", "Quantidade", "Ambos"]],`

**Função `message_chunks`** (linha 50) — `def message_chunks(text: str)`

- *Comentário* (linha 51): Margem para limite UTF-16 do Telegram; separa linhas, preservando cada célula.
  - Trecho comentado: `chunks, current = [], "" for line in text.splitlines():`

**Função `TelegramService.process`** (linha 95) — `async def process(self, payload)`

- *Comentário* (linha 133): Não revelar traceback, perguntas, respostas ou token nos logs.
  - Trecho comentado: `await self.send(msg.chat_id, FAILURE)`

### `app/monthly_comparisons.py`

**Nível do módulo**

- *Docstring* (linha 1): Conserva a intenção literal de encontrar quedas na comparação mês a mês.

**Função `monthly_decline_request`** (linha 9) — `def monthly_decline_request(messages)`

- *Comentário* (linhas 14–15): Uma resposta ao esclarecimento mantém a pergunta pendente, não uma pergunta antiga já respondida. Não usa conteúdo do assistente como evidência temporal.
  - Trecho comentado: `if plain(text).strip().rstrip(".!?") == "comparar periodos":`

**Função `normalize_monthly_comparison_plan`** (linha 37) — `def normalize_monthly_comparison_plan(plan, messages)`

- *Comentário* (linha 59): Datas, evidências, medidas e filtros continuam exigindo a validação normal.
  - Trecho comentado: `return result`

### `app/prompts.py`

**Nível do módulo**

- *Comentário* (linha 170): Extensões opcionais preservam o contrato dos planos existentes.
  - Trecho comentado: `PERIOD_SCHEMA = deepcopy(PLANNER_SCHEMA["properties"]["queries"]["items"]["properties"]["period"])`

### `app/query_templates.py`

**Nível do módulo**

- *Docstring* (linha 1): Totais simples definidos pelo plano, sem SQL livre gerado pelo modelo.
- *Comentário* (linha 5): Identificadores e expressões são fixos; só entram datas ISO validadas.
  - Trecho comentado: `TOTALS = { ("faturamento", "valor"): ( "faturamento",`
- *Comentário* (linha 69): Em pontos percentuais, como o template gerencial: o texto mostra "85,71%".
  - Trecho comentado: `"SUM(chamados_resolvidos)::numeric * 100 / NULLIF(SUM(chamados_abertos), 0)",`

### `app/relative_periods.py`

**Nível do módulo**

- *Docstring* (linha 1): Resolve calendário apenas quando há evidência relativa literal do usuário.

**Função `is_single_day_expression`** (linha 53) — `def is_single_day_expression(evidence)`

- *Docstring* (linhas 54–58): Só uma expressão de dia, sem outro limite, mês ou palavra de intervalo.

  "ontem até hoje", "de janeiro até hoje" e "01/02/2026 a 15/02/2026" são intervalos:
  reduzi-los a um dia devolveria um total errado sem avisar o gestor.
- *Comentário* (linha 68): O mês de "dia 20 de janeiro" pertence à própria expressão; qualquer outro, não.
  - Trecho comentado: `return len(month_numbers(text)) <= (1 if named else 0)`

**Função `exact_day`** (linha 72) — `def exact_day(evidence, today)`

- *Docstring* (linha 73): Resolve hoje/ontem/anteontem e datas de um único dia, explícitas ou nomeadas.

**Função `relative_info`** (linha 109) — `def relative_info(period, messages, today)`

- *Comentário* (linha 137): Intervalos explícitos com vários meses permanecem a cargo do plano validado.
  - Trecho comentado: `return None return {"offset": 0 if current else -1, "month": next(iter(months), None)}`

**Função `single_month`** (linha 142) — `def single_month(period)`

- *Docstring* (linha 143): Mês de um período que cobre exatamente um mês de calendário, senão None.

**Função `normalize_relative_plan`** (linha 177) — `def normalize_relative_plan(plan, messages, today=None)`

- *Comentário* (linhas 192–193): "Compara com o ano passado" depois de fixar um mês: o mês está no outro período do plano ("agosto de 2026"), não na evidência relativa.
  - Trecho comentado: `for field, other in (("period", "comparison_period"), ("comparison_period", "period")):`
- *Comentário* (linhas 209–210): Comparações naturais usam o ano anterior como base. Uma base explicitamente indicada pelo gestor permanece na ordem que ele pediu.
  - Trecho comentado: `explicit_base = any( m.get("role") == "user" and isinstance(m.get("content"), str)`

### `app/rendering.py`

**Nível do módulo**

- *Docstring* (linha 1): A resposta não incorpora prosa nem números livres produzidos pelo modelo.
- *Comentário* (linhas 17–18): Rótulos fixos por coluna canônica: cabeçalhos livres poderiam esconder números gerados pelo modelo. Usados pelo renderizador de SQL livre e pelo gerencial.
  - Trecho comentado: `COLUMN_LABELS = { "total": "Total", "nome": "Nome",`
- *Comentário* (linha 53): Singular e plural da contagem de cada métrica ("6 pedidos", "1 pedido").
  - Trecho comentado: `COUNT_NOUNS = { "pedidos": ("pedido", "pedidos"),`

**Função `percent_text`** (linha 66) — `def percent_text(value) -> str`

- *Docstring* (linha 67): Arredonda apenas a apresentação; preserva a célula original da consulta.

**Função `period_text`** (linha 97) — `def period_text(period: dict) -> str`

- *Docstring* (linha 98): Período legível; o fim da consulta é exclusivo, o texto é inclusivo.

**Função `render_answer`** (linha 106) — `def render_answer(payload: dict, results: dict, metric: str, period: dict | None=None, measure: str | None=None) -> str`

- *Comentário* (linhas 135–136): SUM sem linhas produz uma linha NULL. Só afirmar ausência quando a consulta traz a contagem de registros; NULL sozinho pode ser dado ausente.
  - Trecho comentado: `columns, rows = result["columns"], result["rows"]`
- *Comentário* (linhas 146–147): Frases controladas para um único agregado. O modelo não escreve nem arredonda o valor; detalhes, NULLs e resultados parciais continuam no formato de registros.
  - Trecho comentado: `subjects = { ("faturamento", "valor"): "faturamento emitido",`
- *Comentário* (linhas 171–172): O alias total também pode vir de AVG ou de uma variação. Não inferir soma, moeda ou porcentagem somente pelo alias ou pelo plano do LLM.
  - Trecho comentado: `text = f"📊 Resultado para {subject}: {cell_text(value)}."`
- *Comentário* (linhas 180–181): Uma única célula: uma linha rotulada pela medida pedida, sem marcador nem linha "Medida" repetindo o mesmo dado. O alias não prova moeda: sem "R$".
  - Trecho comentado: `column = visible[0] value = rows[0][columns.index(column)]`
- *Comentário* (linha 212): Não corte um número no meio para caber no Telegram.
  - Trecho comentado: `if len(text) > 12000: raise InvalidAnswer("Resultado extenso. Solicite um resumo ou refine os filtros.")`

### `app/sessions.py`

**Nível do módulo**

- *Docstring* (linha 1): Sessões locais com turnos completos, TTL e exclusão mútua por gestor/chat.

**Função `SessionStore.acquire`** (linha 32) — `async def acquire(self, key)`

- *Comentário* (linha 45): Conta também os que aguardam lock, para impedir remoção durante uma fila.
  - Trecho comentado: `session.borrowers += 1 try: async with session.lock:`

### `app/sql_policy.py`

**Nível do módulo**

- *Docstring* (linha 1): Allowlist sobre a AST real de PostgreSQL; falha fechada para sintaxe desconhecida.

**Função `validate_relations`** (linha 108) — `def validate_relations(value, visible_ctes=frozenset())`

- *Docstring* (linhas 109–114): CTE autoriza referências só dentro do seu escopo lexical, nunca em irmãos.

  Num WITH não recursivo, o corpo de cada CTE enxerga apenas os CTEs anteriores e os do
  escopo externo: o próprio nome e os seguintes caem na relação real do search_path
  (pg_catalog primeiro). Só a consulta principal enxerga todos eles.

### `app/state.py`

**Nível do módulo**

- *Docstring* (linhas 1–9): Estado de execução do backend: caixa de entrada de updates e sessões de conversa.

  Duas implementações com o mesmo contrato:

  * em memória (padrão, um único processo): `MemoryInbox` e `sessions.SessionStore`;
  * durável em PostgreSQL (`STATE_DATABASE_URL`): `PostgresInbox` e `PostgresSessionStore`.
    Sobrevive a reinícios e permite vários processos, com entrega "pelo menos uma vez" e
    deduplicação por `update_id`.

**Classe `MemoryInbox`** (linha 28) — `class MemoryInbox`

- *Docstring* (linha 29): Fila e deduplicação em memória; reiniciar o processo perde os dois.

**Função `MemoryInbox.retry`** (linha 63) — `async def retry(self, update_id)`

- *Comentário* (linha 64): permite que o Telegram reenvie o update
  - Trecho comentado: `self.seen.pop(update_id, None)`

**Classe `_Db`** (linha 71) — `class _Db`

- *Docstring* (linhas 72–76): Conexão síncrona compartilhada, serializada e recriada quando cai.

  O psycopg assíncrono não funciona com o loop padrão do Windows; `to_thread` mantém o mesmo
  código em qualquer sistema.

**Classe `PostgresInbox`** (linha 110) — `class PostgresInbox`

- *Docstring* (linha 111): Caixa de entrada durável: o update é gravado antes de o webhook responder 200.

**Função `PostgresInbox.purge`** (linha 210) — `async def purge(self)`

- *Docstring* (linha 211): Encerra updates que esgotaram as tentativas e apaga registros antigos.

**Classe `PostgresSessionStore`** (linha 234) — `class PostgresSessionStore`

- *Docstring* (linha 235): Sessões em PostgreSQL com lock consultivo por conversa, válido entre processos.

**Função `PostgresSessionStore.acquire`** (linha 282) — `async def acquire(self, key)`

- *Comentário* (linha 294): libera o lock consultivo
  - Trecho comentado: `await asyncio.to_thread(conn.close)`

### `app/telegram_bot.py`

**Nível do módulo**

- *Docstring* (linha 1): Polling encaminha ao FastAPI; register-webhook configura a entrega HTTPS.
- *Comentário* (linhas 14–15): O backend recusou o conteúdo do update; reenviá-lo nunca terá outro resultado. Já 401/403 (segredo errado) e 5xx são problemas de configuração ou temporários: seguem em nova tentativa.
  - Trecho comentado: `PERMANENT_REJECTIONS = frozenset({400, 413, 422})`

**Função `forward_update`** (linha 19) — `async def forward_update(client, update, backend_url, secret)`

- *Docstring* (linha 20): Encaminha ao backend; devolve o status se ele recusou o update de forma permanente.

**Função `forward_updates`** (linha 32) — `async def forward_updates(client, updates, backend_url, secret)`

- *Docstring* (linhas 33–38): Encaminha o lote em ordem e devolve o próximo offset a cada update tratado.

  Falha temporária propaga sem avançar o offset daquele update; os anteriores já foram
  entregues. Recusa permanente é registrada e o update é descartado, senão um único
  update ruim travaria o bot para todos os gestores.

**Função `run`** (linha 46) — `async def run(command, backend_url)`

- *Comentário* (linha 70): Valide o backend antes de desativar o webhook remoto.
  - Trecho comentado: `async with httpx.AsyncClient(timeout=15) as client:`

### `deploy/oracle/configure.py`

**Nível do módulo**

- *Docstring* (linha 1): Executar no servidor novo: entrada oculta, arquivos privados, sem segredos no terminal.

### `evaluation/__init__.py`

**Nível do módulo**

- *Docstring* (linha 1): Avaliação acadêmica opt-in; não participa do atendimento Telegram.

### `evaluation/dataset.py`

**Nível do módulo**

- *Docstring* (linha 1): Contrato do conjunto congelado e validação das consultas de referência.

### `evaluation/runner.py`

**Nível do módulo**

- *Docstring* (linha 1): Experimentos sequenciais: referências SQL, checkpoints e evidência reproduzível.

**Função `database_fingerprint`** (linha 42) — `def database_fingerprint(database)`

- *Docstring* (linha 43): Somente leitura, timeout da conexão e limite explícito por tabela.

**Função `score_turn`** (linha 61) — `def score_turn(turn, trace, references)`

- *Comentário* (linhas 78–79): O prompt e o renderer reservam registros como metadado de ausência. Outras colunas extras continuam reprovando; contagens precisam ser inteiras.
  - Trecho comentado: `if "registros" in selected["columns"]: if selected["columns"].count("registros") != 1:`
- *Comentário* (linha 87): O renderer oculta todos os valores quando afirma ausência de registros.
  - Trecho comentado: `if len(rows) == 1 and selected["rows"][0][index] == 0:`

### `evaluation/scoring.py`

**Nível do módulo**

- *Docstring* (linha 1): Comparação independente de aliases, sem arredondamento ou tolerância oculta.

### `runtime_entrypoint.py`

**Nível do módulo**

- *Docstring* (linha 1): Carrega configuração privada montada; nunca grava credenciais na imagem.

**Função `main`** (linha 33) — `def main()`

- *Comentário* (linha 38): Fila, deduplicação e histórico em memória não são compartilhados entre processos.
  - Trecho comentado: `raise SystemExit("BACKEND_WORKERS maior que 1 exige STATE_DATABASE_URL.")`

### `scripts/__init__.py`

**Nível do módulo**

- *Docstring* (linha 1): Comandos administrativos; nunca expostos ao agente.

### `scripts/autopecas_seed.py`

**Nível do módulo**

- *Docstring* (linhas 1–16): Perfil ``autopecas``: revenda sintética de porte pequeno a médio.

  A empresa vende peças a oficinas, auto elétricas, funilarias, autocenters, frotas,
  retíficas e lojas menores no Sul/Sudeste. O schema é o mesmo dos demais perfis:

  - ``contratos`` são contratos de fornecimento: ``sustentacao`` é a reposição
    recorrente (um por cliente) e ``projeto`` é o fornecimento pontual por demanda;
  - ``pedidos`` são pedidos de venda de peças, em reais e centavos inteiros;
  - ``faturamento`` são notas fiscais, com prazo de pagamento por segmento;
  - ``indicadores_operacionais`` guardam horas de atendimento (balcão e televendas)
    e ocorrências de pós-venda (garantias, trocas e devoluções), nas colunas
    ``horas_*`` e ``chamados_*``.

  Tudo é determinístico para a mesma semente. Fatores de sazonalidade, tickets e
  taxas são hipóteses declaradas de cenário, não estimativas de uma empresa real.
- *Comentário* (linha 30): clientes já cadastrados antes do primeiro mês do cenário
  - Trecho comentado: `INITIAL_PORTFOLIO = 70`
- *Comentário* (linha 31): carteira que pede fornecimento pontual todo mês
  - Trecho comentado: `MONTHLY_SUPPLY_CLIENTS = 12`
- *Comentário* (linhas 41–42): ticket: mediana do pedido em reais; orders: pedidos por mês (mín., máx.) antes do porte do cliente; terms: prazos de pagamento em dias.
  - Trecho comentado: `SEGMENTS = { "Oficina mecânica": { "weight": 34,`
- *Comentário* (linhas 181–182): Status exigidos em todo mês. "aprovado" (pedido ainda não entregue) só aparece nos últimos dias do cenário; contratos não têm exigência de status por mês.
  - Trecho comentado: `REQUIRED_STATUSES = { "contratos": set(), "pedidos": {"entregue", "cancelado"},`

**Função `generate_autopecas_data.add_activity`** (linha 261) — `def add_activity(contract, active_months, segment, size, *, project=False)`

- *Comentário* (linhas 309–312): Cada ocorrência é sorteada à parte, num gerador próprio: com poucas por mês, opened * rate // 100 zerava quase todas as resolvidas (taxa perto de 10%). Manter a ordem dos sorteios acima e usar outro gerador aqui preserva todo o resto da base, que já está implantada.
  - Trecho comentado: `resolver = Random(f"{seed}-{contract['id']}-{month:%Y%m}")`
- *Comentário* (linha 326): O valor contratado é o previsto: sempre cobre o que foi pedido.
  - Trecho comentado: `contract["valor_contratado"] = _cents_to_decimal(max(total_cents, 1) * 105 // 100)`

**Função `generate_autopecas_data`** (linha 206) — `def generate_autopecas_data(seed: int, clients: int, start: str, end: str) -> dict`

- *Comentário* (linha 370): Fornecimentos pontuais: um grupo fixo pede todo mês; os demais, de vez em quando.
  - Trecho comentado: `project_months = ( months if client_id <= MONTHLY_SUPPLY_CLIENTS else eligible[1 + client_id % 4 :: 4]`

**Função `sales_summary`** (linha 391) — `def sales_summary(data: dict) -> dict`

- *Docstring* (linha 392): Totais por ano e médias mensais, para conferir a escala do cenário.

### `scripts/check_connections.py`

**Nível do módulo**

- *Docstring* (linha 1): Diagnóstico opt-in das conexões, sem alterar webhook ou enviar mensagens.

**Função `check_telegram`** (linha 58) — `async def check_telegram(settings)`

- *Comentário* (linhas 59–60): A inicialização do SDK chama getMe. Não chamar getUpdates, sendMessage, setWebhook ou deleteWebhook: diagnóstico não interfere no bot em uso.
  - Trecho comentado: `async with Bot(settings.telegram_bot_token.get_secret_value()):`

**Função `diagnose`** (linha 65) — `async def diagnose(settings: Settings, *, test_connections=False)`

- *Comentário* (linha 113): URLs do Telegram e exceções de SDK podem conter segredos.
  - Trecho comentado: `report[name] = {"status": "falhou", "detalhe": failure}`

### `scripts/comparative_seed.py`

**Nível do módulo**

- *Docstring* (linhas 1–5): Cenário sintético para comparação mensal, separado da base experimental original.

  Valores em centavos inteiros. A cobertura mínima é determinística, não depende
  de sorteios. Status representam a fotografia no último dia do cenário.

**Função `generate_comparative_data`** (linha 75) — `def generate_comparative_data(seed: int, clients: int, start: str, end: str, *, version: str='v1') -> dict`

- *Comentário* (linha 99): Fatores declarados de cenário, não estimativas de desempenho de uma empresa.
  - Trecho comentado: `seasonality = [90, 94, 100, 103, 98, 106, 101, 110, 108, 114, 120, 92]`
- *Comentário* (linha 213): A carteira inicial garante novos projetos e todos os status em cada mês.
  - Trecho comentado: `project_months = months if client_id <= 12 else eligible[::3]`

**Função `generate_comparative_data.add_activity`** (linha 102) — `def add_activity(contract, active_months, base_cents, project=False)`

- *Comentário* (linha 108): Entregas de tamanhos diferentes ao longo do mês, sem perder centavos.
  - Trecho comentado: `parts = [total_cents * 40 // 100, total_cents * 35 // 100]`
- *Comentário* (linha 136): Parte da carteira tem faturamento parcelado para exercitar joins.
  - Trecho comentado: `amounts = [amount] if order_id % 4 else [amount // 2, amount - amount // 2]`

**Função `coverage_report`** (linha 237) — `def coverage_report(data: dict, start: str='2025-01', end: str='2026-10', *, required: dict[str, set[str]] | None=None, profile: str='comparativo-v1') -> dict`

- *Docstring* (linha 245): Confere presença mensal e os status exigidos em cada mês antes de publicar os totais.

**Função `coverage_report.total`** (linha 273) — `def total(rows, field)`

- *Comentário* (linha 274): O schema usa escala 2; normaliza a representação sem alterar o valor.
  - Trecho comentado: `return format(sum((r[field] for r in rows), Decimal("0")), ".2f")`

### `scripts/evaluate.py`

**Nível do módulo**

- *Docstring* (linha 1): Validação offline e avaliação real opt-in; nunca imprime credenciais.

**Função `execute`** (linha 44) — `async def execute(args)`

- *Comentário* (linha 60): Mantém o denominador completo; limite é um teto de chamadas, não troca de amostra.
  - Trecho comentado: `output = create_output(root) evidence = manifest(root, path, dataset, settings, database, args.split)`

### `scripts/manage_db.py`

**Nível do módulo**

- *Docstring* (linha 1): Setup explícito com credencial administrativa; nunca chamado por tools do agente.

**Função `initialize_state`** (linha 40) — `def initialize_state(conn, password: str)`

- *Docstring* (linhas 41–44): Cria (ou atualiza, de forma idempotente) o schema `estado` e a role app_estado.

  Não toca nas tabelas de negócio nem na role de leitura; pode rodar em base já populada.

**Função `database_coverage`** (linha 94) — `def database_coverage(conn, start: str='2025-01', end: str='2026-10', profile: str='')`

- *Docstring* (linha 95): Auditoria administrativa da base comparativa, sem usar a API de IA.

**Função `main`** (linha 134) — `def main()`

- *Comentário* (linha 188): Mensagens psycopg podem conter dados de conexão; não exibir DSN/segredos.
  - Trecho comentado: `message = ( str(exc) if isinstance(exc, ValueError)`

### `scripts/seed.py`

**Nível do módulo**

- *Docstring* (linha 1): Geração determinística: centavos inteiros, datas fixas e Faker com seed local.

**Função `generate_data_v2`** (linha 37) — `def generate_data_v2(seed: int=42, clients: int=30) -> dict[str, list[dict]]`

- *Docstring* (linhas 38–41): Mesma estrutura relacional do perfil original, com cobertura diária real e
  sem repetir descrição, valor ou cidade/segmento de forma constante entre registros.
  Perfil novo e opcional: não substitui o perfil original já usado pela avaliação congelada.
- *Comentário* (linha 126): Todos os pedidos do ano foram cancelados; preserva o CHECK > 0 do contrato.
  - Trecho comentado: `contract["valor_contratado"] = base return data`

**Função `day_coverage_report`** (linha 131) — `def day_coverage_report(data: dict) -> dict`

- *Docstring* (linhas 132–133): Confere que pedidos não ficam presos a um único dia do mês, nem a uma
  descrição ou valor fixos repetidos — evidência direta da correção do perfil v2.

**Função `generate_data`** (linha 152) — `def generate_data(seed: int=42, clients: int=30, *, profile: str='original', start_month: str='2025-01', end_month: str='2026-10') -> dict[str, list[dict]]`

- *Comentário* (linha 195): Mantém UF coerente com a cidade sintética.
  - Trecho comentado: `if data["clientes"][-1]["cidade"] == "Curitiba":`

### `scripts/train_intents.py`

**Nível do módulo**

- *Docstring* (linha 1): CLI de treino local, sem chamadas externas e sem utilizar dados de sessões.

### `tests/test_agent.py`

**Função `test_same_metric_and_period_measures_are_merged_without_repeating_header`** (linha 332) — `async def test_same_metric_and_period_measures_are_merged_without_repeating_header()`

- *Comentário* (linha 347): Cada medida aparece uma única vez, como linha rotulada (sem subtítulo repetido).
  - Trecho comentado: `assert text.count("Valor:") == 1 and text.count("Quantidade:") == 1`

### `tests/test_analysis_contract.py`

**Função `test_filtered_total_without_ranking_needs_no_analysis_block`** (linha 82) — `def test_filtered_total_without_ranking_needs_no_analysis_block()`

- *Comentário* (linha 83): "Faturamento em Joinville em setembro de 2026": um número só, SQL personalizado.
  - Trecho comentado: `from app.bi_agent import clarify from app.prompts import PLANNER_PROMPT`

### `tests/test_autopecas_seed.py`

**Função `test_monthly_coverage_with_realistic_statuses`** (linha 75) — `def test_monthly_coverage_with_realistic_statuses(data)`

- *Comentário* (linha 80): Pedido aprovado (ainda não entregue) só existe nos dias finais do cenário.
  - Trecho comentado: `approved = [o for o in data["pedidos"] if o["status"] == "aprovado"]`

**Função `test_after_sales_resolution_rate_is_realistic`** (linha 131) — `def test_after_sales_resolution_rate_is_realistic(data)`

- *Comentário* (linha 132): Regressão: o arredondamento para baixo deixava a taxa de resolução perto de 10%.
  - Trecho comentado: `rows = data["indicadores_operacionais"] opened = sum(r["chamados_abertos"] for r in rows)`

### `tests/test_check_connections.py`

**Nível do módulo**

- *Docstring* (linha 1): Diagnóstico operacional: configuração não deve ser confundida com acesso real.

**Função `test_invalid_and_missing_configuration_never_calls_providers`** (linha 49) — `async def test_invalid_and_missing_configuration_never_calls_providers(monkeypatch)`

- *Comentário* (linha 55): _env_file=None desativa apenas dotenv, não as variáveis do processo/CI.
  - Trecho comentado: `monkeypatch.setenv("DATABASE_URL", "postgresql://configuracao-ambiente/bi")`

### `tests/test_comparative_seed.py`

**Função `test_comparative_v1_still_matches_frozen_day_window_and_descriptions`** (linha 107) — `def test_comparative_v1_still_matches_frozen_day_window_and_descriptions()`

- *Docstring* (linhas 108–109): Trava de regressão: comparativo (v1) alimenta docs/projeto.md com
  hash publicado; não pode mudar, mesmo ao corrigir a variedade no v2.

### `tests/test_database_integration.py`

**Função `test_schema_lists_the_stored_spelling_of_categorical_values`** (linha 40) — `def test_schema_lists_the_stored_spelling_of_categorical_values(settings)`

- *Comentário* (linhas 41–43): Reservado do perfil autopecas (T04): a pergunta dizia "sustentação" e o dado guarda "sustentacao"; sem ver a grafia real, o modelo copiou a da pergunta e contou zero contratos. Os valores esperados vêm do próprio banco, porque cada perfil guarda um subconjunto diferente.
  - Trecho comentado: `db = DatabaseTools(settings) valores = db.get_schema()["valores"]`

**Função `test_simple_total_business_rules_against_independent_rows`** (linha 122) — `def test_simple_total_business_rules_against_independent_rows(settings, metric, measure)`

- *Comentário* (linha 143): O total devolve pontos percentuais (85,71), não a razão (0,8571).
  - Trecho comentado: `expected = ( Decimal(sum(row[3] for row in selected)) * 100 / sum(row[2] for row in selected)`

### `tests/test_durable_state.py`

**Nível do módulo**

- *Docstring* (linhas 1–5): Estado durável (caixa de entrada e sessões) com PostgreSQL real.

  Exige TEST_STATE_ADMIN_URL: URL administrativa de um banco de TESTE. O schema `estado` e a role
  `app_estado` desse banco são recriados pela fixture.
- *Comentário* (linha 66): --- caixa de entrada ---------------------------------------------------------------------
  - Trecho comentado: `async def test_register_is_idempotent_across_restarts(state_url, clean):`
- *Comentário* (linha 186): --- sessões -------------------------------------------------------------------------------
  - Trecho comentado: `def turn(text): return [{"role": "user", "content": text}, {"role": "assistant", "content": "ok"}]`
- *Comentário* (linha 251): --- permissões da role de estado -----------------------------------------------------------
  - Trecho comentado: `def test_state_role_is_restricted_to_state_tables(admin_url, state_url, clean):`
- *Comentário* (linha 283): --- backend com estado durável -------------------------------------------------------------
  - Trecho comentado: `class Agent: def __init__(self): self.histories = []`

**Função `state_url`** (linha 35) — `def state_url(admin_url)`

- *Comentário* (linha 39): A role é do cluster e pode ter privilégios em outros bancos: só alinha a senha.
  - Trecho comentado: `conn.execute(f"ALTER ROLE app_estado PASSWORD '{STATE_PASSWORD}'")`

**Função `test_register_is_idempotent_across_restarts`** (linha 69) — `async def test_register_is_idempotent_across_restarts(state_url, clean)`

- *Comentário* (linha 74): processo novo: nada em memória
  - Trecho comentado: `restarted = inbox(state_url)`

**Função `test_accepted_update_survives_restart_and_is_claimed_once`** (linha 80) — `async def test_accepted_update_survives_restart_and_is_claimed_once(state_url, clean)`

- *Comentário* (linha 83): "queda" antes de processar
  - Trecho comentado: `await before.close()`

**Função `test_concurrent_consumers_never_claim_the_same_update`** (linha 90) — `async def test_concurrent_consumers_never_claim_the_same_update(state_url, clean)`

- *Comentário* (linha 102): todos, e cada um exatamente uma vez
  - Trecho comentado: `assert sorted(claimed) == list(range(1, 41))`

**Função `test_claim_skips_rows_locked_by_another_consumer`** (linha 107) — `async def test_claim_skips_rows_locked_by_another_consumer(state_url, clean)`

- *Comentário* (linha 111): outro consumidor segura a linha 1 numa transação
  - Trecho comentado: `with psycopg.connect(clean) as other:`

**Função `test_stale_lease_is_reclaimed_after_worker_crash`** (linha 128) — `async def test_stale_lease_is_reclaimed_after_worker_crash(state_url, clean)`

- *Comentário* (linha 131): processando, sem concluir
  - Trecho comentado: `assert await crashed.claim() is not None`
- *Comentário* (linha 134): lease ainda vigente
  - Trecho comentado: `assert await survivor.claim() is None`

**Função `test_backpressure_when_too_many_pending`** (linha 153) — `async def test_backpressure_when_too_many_pending(state_url, clean)`

- *Comentário* (linha 159): libera espaço
  - Trecho comentado: `await box.done(1)`

**Função `test_history_survives_restart_and_respects_limit`** (linha 193) — `async def test_history_survives_restart_and_respects_limit(state_url, clean)`

- *Comentário* (linha 201): outro usuário: isolado
  - Trecho comentado: `async with restarted.acquire((10, 43)) as session:`

**Função `test_two_processes_serialize_the_same_conversation`** (linha 224) — `async def test_two_processes_serialize_the_same_conversation(state_url, clean)`

- *Comentário* (linha 236): b espera o lock de a
  - Trecho comentado: `assert order == []`
- *Comentário* (linha 239): b enxerga o que a gravou
  - Trecho comentado: `assert order == [("b", 1)]`

**Função `test_initialize_state_is_idempotent_and_requires_a_real_password`** (linha 276) — `def test_initialize_state_is_idempotent_and_requires_a_real_password(admin_url, state_url)`

- *Comentário* (linha 278): segunda execução não falha
  - Trecho comentado: `initialize_state(conn, STATE_PASSWORD)`

**Função `test_duplicate_after_restart_is_not_answered_twice`** (linha 339) — `async def test_duplicate_after_restart_is_not_answered_twice(state_url, clean)`

- *Comentário* (linha 347): reinício do processo
  - Trecho comentado: `app2 = make_app(state_url, agent, sender)`

**Função `test_update_accepted_before_a_crash_is_answered_after_restart`** (linha 354) — `async def test_update_accepted_before_a_crash_is_answered_after_restart(state_url, clean)`

- *Comentário* (linha 356): aceito (200 enviado) e o processo caiu
  - Trecho comentado: `await crashed.register(1, update(1))`

**Função `test_two_backend_processes_share_the_inbox_without_double_answer`** (linha 379) — `async def test_two_backend_processes_share_the_inbox_without_double_answer(state_url, clean)`

- *Comentário* (linhas 388–389): O lock por conversa serializa os dois processos: cada pergunta enxerga exatamente os turnos gravados pelas anteriores, sem perder nem repetir nenhum.
  - Trecho comentado: `assert sorted(len(h) for h in agent.histories) == [0, 2, 4, 6, 8, 10]`

### `tests/test_e2e_local.py`

**Nível do módulo**

- *Docstring* (linha 1): Integração de engenharia, não avaliação acadêmica nem prova de Telegram real.

### `tests/test_evaluation.py`

**Função `test_autopecas_dataset_adapts_the_original_inside_the_profile_data_range`** (linha 51) — `def test_autopecas_dataset_adapts_the_original_inside_the_profile_data_range()`

- *Comentário* (linha 65): Só D17 e T20 mudam de categoria: os demais casos mantêm o desenho do conjunto original.
  - Trecho comentado: `changed = {c.id for c, o in zip(dataset.cases, original.cases, strict=True) if c.category != o.category}`
- *Comentário* (linhas 68–69): As datas de referência ficam na faixa carregada (jan/2025 a out/2026). Exceções: cadastro de clientes (desde 2022) e os casos de ausência/zero, que usam anos propositalmente vazios.
  - Trecho comentado: `for case in dataset.cases: if case.category in {"sem_dados", "zero_explicito"}:`

**Função `test_autopecas_second_reserved_partition_mirrors_the_categories_inside_the_data_range`** (linha 81) — `def test_autopecas_second_reserved_partition_mirrors_the_categories_inside_the_data_range()`

- *Comentário* (linha 93): Mesmas categorias do reservado original do conjunto A, em instâncias novas.
  - Trecho comentado: `reserved = [c for c in original.cases if c.split == "test"]`
- *Comentário* (linha 96): Nenhuma pergunta repete as do conjunto A.
  - Trecho comentado: `seen = {t.question for c in original.cases for t in c.turns}`

### `tests/test_gemini_transport.py`

**Nível do módulo**

- *Docstring* (linha 1): Exercita o SDK oficial na fronteira HTTP, sem gastar cota ou enviar dados.

### `tests/test_intent_v2.py`

**Nível do módulo**

- *Docstring* (linha 1): Corpus, modelo congelado e uso do classificador de intenções v2 (revenda de autopeças).
- *Comentário* (linha 20): Sem período o agente pede esclarecimento depois do planejador, sem consultar o banco.
  - Trecho comentado: `NO_PERIOD = {**PLAN, "period": None} def test_corpus_v2_is_balanced_domain_specific_and_phrasings_never_cro...`

**Função `test_corpus_v2_is_balanced_domain_specific_and_phrasings_never_cross_partitions`** (linha 24) — `def test_corpus_v2_is_balanced_domain_specific_and_phrasings_never_cross_partitions()`

- *Comentário* (linhas 34–35): Cada molde (group_id) pertence a uma única partição, e os de validação e teste são moldes que o treino nunca viu.
  - Trecho comentado: `partitions = {} for row in rows: partitions.setdefault(row["group_id"], set()).add(row["split"])`

### `tests/test_managerial_agent.py`

**Função `ungrouped_ranking_plan`** (linha 170) — `def ungrouped_ranking_plan()`

- *Comentário* (linhas 171–172): Plano real observado na reavaliação do perfil autopecas (caso D04): o planejador marcou "ranking" sem agrupamento nem limite para um total com filtro de status.
  - Trecho comentado: `return { "metric": "contratos", "measure": "valor",`

**Função `grouped_ranking_plan_without_limit`** (linha 219) — `def grouped_ranking_plan_without_limit(group_by)`

- *Comentário* (linhas 220–221): Plano real observado no reservado do perfil autopecas (caso T05): "clientes por UF" saiu como ranking por cidade sem limite, porque o contrato não tem agrupamento por UF.
  - Trecho comentado: `plan = ungrouped_ranking_plan() plan.update(metric="clientes", measure="quantidade")`

### `tests/test_managerial_rendering.py`

**Função `test_ranking_is_compact_numbered_and_hides_internal_ids`** (linha 143) — `def test_ranking_is_compact_numbered_and_hides_internal_ids()`

- *Comentário* (linha 156): sem linhas em branco entre os itens
  - Trecho comentado: `assert "" not in lines[3:-1]`

### `tests/test_relative_periods.py`

**Função `test_numeric_date_range_is_accepted_but_a_vague_range_asks_for_the_period`** (linha 225) — `def test_numeric_date_range_is_accepted_but_a_vague_range_asks_for_the_period()`

- *Comentário* (linha 231): vira pergunta de esclarecimento, nunca um dia só
  - Trecho comentado: `with pytest.raises(ValueError):`

**Função `test_compare_with_last_year_still_means_the_whole_year_when_no_month_is_involved`** (linha 266) — `def test_compare_with_last_year_still_means_the_whole_year_when_no_month_is_involved()`

- *Comentário* (linha 274): mesmo corte do ano atual
  - Trecho comentado: `assert result["period"]["end"] == "2025-10-13"`

### `tests/test_rendering.py`

**Função `test_alias_total_does_not_prove_sum_or_currency`** (linha 99) — `def test_alias_total_does_not_prove_sum_or_currency(metric, measure, value)`

- *Comentário* (linhas 100–101): AVG(horas_realizadas) AS total e variação percentual AS total são resultados possíveis: o alias não certifica a operação nem a unidade.
  - Trecho comentado: `text = render_answer( {"kind": "answer", "result_id": "q1"},`

**Função `test_category_columns_have_fixed_labels_instead_of_the_generic_one`** (linha 124) — `def test_category_columns_have_fixed_labels_instead_of_the_generic_one()`

- *Comentário* (linha 125): Reavaliação no perfil autopecas: "clientes por UF" saía como "Campo: SC · Quantidade: 18".
  - Trecho comentado: `text = render_answer( {"kind": "answer", "result_id": "q1"},`

### `tests/test_runtime_entrypoint.py`

**Nível do módulo**

- *Docstring* (linha 1): O entrypoint do container deve respeitar a configuração privada do classificador.

**Função `test_backend_honours_the_classifier_flag_from_the_private_file`** (linha 12) — `def test_backend_honours_the_classifier_flag_from_the_private_file(tmp_path, monkeypatch, value, expected)`

- *Comentário* (linhas 15–16): Regressão: o entrypoint forçava False em todos os modos, e o valor do arquivo privado nunca chegava ao backend, mesmo com o classificador v2 empacotado.
  - Trecho comentado: `config = tmp_path / "application.env" config.write_text(`
- *Comentário* (linha 24): configured() exporta variáveis
  - Trecho comentado: `monkeypatch.setattr(os, "environ", dict(os.environ))`
- *Comentário* (linha 29): As credenciais administrativas continuam removidas dos modos de aplicação.
  - Trecho comentado: `assert settings.admin_database_url.get_secret_value() == ""`

**Função `test_several_workers_without_durable_state_are_refused`** (linha 69) — `def test_several_workers_without_durable_state_are_refused(tmp_path, monkeypatch)`

- *Comentário* (linha 70): Com estado em memória, cada worker teria fila, deduplicação e histórico próprios.
  - Trecho comentado: `with pytest.raises(SystemExit): _backend_args(tmp_path, monkeypatch, "BACKEND_WORKERS=2\n")`

**Função `test_state_password_is_removed_outside_manage_db`** (linha 75) — `def test_state_password_is_removed_outside_manage_db(tmp_path, monkeypatch)`

- *Comentário* (linha 83): configured() exportou o valor já limpo
  - Trecho comentado: `os.environ.pop("STATE_PASSWORD", None)`

### `tests/test_seed.py`

**Função `test_original_profile_still_matches_frozen_single_day_and_description`** (linha 32) — `def test_original_profile_still_matches_frozen_single_day_and_description()`

- *Docstring* (linhas 33–34): Trava de regressão: o perfil original não pode mudar, pois alimenta a
  avaliação congelada de 40 casos com SQL de referência já publicados.

### `tests/test_sql_policy.py`

**Nível do módulo**

- *Comentário* (linha 61): O corpo do CTE não enxerga o próprio nome: cai em pg_catalog.pg_roles.
  - Trecho comentado: `"WITH pg_roles AS (SELECT * FROM pg_roles) SELECT * FROM pg_roles",`
- *Comentário* (linha 63): Nem os irmãos seguintes: "pg_settings" ainda não existe quando x é resolvido.
  - Trecho comentado: `"WITH x AS (SELECT * FROM pg_settings), pg_settings AS (SELECT 1) SELECT * FROM x",`

### `tests/test_telegram_transport.py`

**Função `run_batch`** (linha 43) — `async def run_batch(statuses, ids=(1, 2, 3))`

- *Docstring* (linha 44): Encaminha um lote; `statuses` mapeia update_id -> status HTTP do backend.

**Função `test_an_update_the_backend_permanently_rejects_is_skipped_not_retried_forever`** (linha 67) — `async def test_an_update_the_backend_permanently_rejects_is_skipped_not_retried_forever(status)`

- *Comentário* (linha 70): o update seguinte ainda é entregue
  - Trecho comentado: `assert received == [1, 2, 3]`
- *Comentário* (linha 71): o offset passa do update recusado
  - Trecho comentado: `assert offsets == [2, 3, 4]`

**Função `test_temporary_or_configuration_errors_keep_the_update_for_a_retry`** (linha 75) — `async def test_temporary_or_configuration_errors_keep_the_update_for_a_retry(status)`

- *Comentário* (linha 79): o update 2 não avançou o offset: será reenviado
  - Trecho comentado: `assert offsets == [2]`

### `training/__init__.py`

**Nível do módulo**

- *Docstring* (linha 1): Dados sintéticos e treinamento supervisionado do classificador local.

### `training/build_corpus_v2.py`

**Nível do módulo**

- *Docstring* (linhas 1–10): Gera o corpus sintético v2 de intenções, no domínio de revenda de autopeças.

  Cada classe tem 24 formas de perguntar ("moldes"). Os moldes são sorteados, por classe,
  para treino (16), validação (4) e teste (4) e **nunca se repetem entre partições**: a
  validação e o teste medem perguntas escritas de um jeito que o modelo não viu, não só
  outro mês ou outra métrica no mesmo molde. Dentro de cada molde, métricas e períodos
  variam. Tudo é determinístico e sintético; nenhuma mensagem de gestor foi usada.

  Uso: python -m training.build_corpus_v2 (grava training/questions-v2.json).
- *Comentário* (linha 21): (forma sem artigo, forma com artigo)
  - Trecho comentado: `METRICS = [ ("faturamento emitido", "o faturamento emitido"),`
- *Comentário* (linhas 54–56): Cada molde usa: {m} métrica sem artigo, {a} com artigo, {p} período ("em ..."), {p1}/{p2} meses para comparar, {r} intervalo mensal, {n} tamanho do ranking, {g}/{gs} cliente(s)/contrato(s), {s}/{ss} segmento(s)/cidade(s).
  - Trecho comentado: `FRAMES = { "total": [ "Qual o total de {m} {p}?",`
- *Comentário* (linha 241): Moldes de cada classe por partição: 16 treino, 4 validação, 4 teste.
  - Trecho comentado: `SPLIT_SIZES = (("train", 16, 10), ("validation", 4, 8), ("test", 4, 8))  # (partição, moldes, perguntas)`
- *Comentário* (linha 242): (partição, moldes, perguntas)
  - Trecho comentado: `SPLIT_SIZES = (("train", 16, 10), ("validation", 4, 8), ("test", 4, 8))`

### `training/corpus.py`

**Nível do módulo**

- *Docstring* (linha 1): Corpus com separação por cenário, nunca por paráfrase individual.

### `training/fit.py`

**Nível do módulo**

- *Docstring* (linha 1): Treino e seleção em validação; teste reservado é uma operação separada.

**Função `metrics`** (linha 17) — `def metrics(actual, predicted, *, accepted=None)`

- *Comentário* (linha 30): Das sugestões aceitas, quantas acertaram a classe: o que decide se vale usar.
  - Trecho comentado: `"accepted_precision": ( sum(a == p for a, p, ok in zip(actual, predicted, accepted, strict=True) if ok)`

**Função `threshold_report`** (linha 44) — `def threshold_report(model, vx, vy, labels, threshold)`

- *Docstring* (linha 45): Desempenho na validação quando só se aceita sugestão com confiança >= limiar.

**Função `fit_model`** (linha 57) — `def fit_model(records: list[dict], seed: int=42, c_grid: tuple[float, ...]=DEFAULT_C_GRID, thresholds: tuple[float, ...]=DEFAULT_THRESHOLDS, joint: bool=False) -> tuple[dict, dict]`

- *Docstring* (linhas 64–69): Treina na partição de treino e escolhe hiperparâmetros só pela validação.

  Por padrão escolhe C pelo macro-F1 puro e depois o limiar (protocolo v1). Com
  ``joint`` escolhe C e limiar juntos pelo macro-F1 com abstenção, que já pune
  cobertura baixa; é o que importa quando as sugestões só são usadas acima do limiar.

### Arquivos SQL (`db/`)

**`db/schema.sql`** (linhas 1–2)

- Dados inteiramente sintéticos. Execute com o proprietário administrativo.
- Domínio: revenda de autopeças. Nomes de tabelas e colunas são mantidos por compatibilidade.

**`db/roles.sql`** (linhas 1 e 13)

- A criação do login e senha parametrizada ocorre em `scripts/manage_db.py`.
- Sem grants automáticos: novas tabelas precisam de revisão explícita.

**`db/estado.sql`** (linhas 1–3 e 8–9)

- Estado de execução do backend (caixa de entrada de updates e sessões de conversa). Fica em schema próprio, sem nenhum grant para `readonly_agent`; a role `app_estado` é criada por `scripts/manage_db.py` (`init-state`) e só enxerga estas duas tabelas. Idempotente.
- Na coluna `payload` de `estado.updates`: o texto do usuário só existe enquanto o update está pendente; vira NULL ao concluir ou falhar, mantendo apenas o identificador para deduplicação.

**`db/migrations/2026-11-autopecas-comentarios.sql`** (linhas 1–2)

- Atualiza apenas os comentários do schema (`COMMENT ON`) para o vocabulário de autopeças. Seguro em base existente: não altera dados, tabelas ou colunas. Execute com o proprietário.
