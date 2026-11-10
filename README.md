# Assistente Conversacional de BI — PAC Extensionista VIII

Assistente em português do Brasil que permite a gestores consultar indicadores de negócio por mensagens no Telegram, sem escrever SQL. A pergunta passa por quatro camadas: **Telegram → FastAPI → Gemini → PostgreSQL 16**. Toda a base é **sintética**. O domínio de apresentação é uma revenda de autopeças de porte pequeno a médio (perfil `autopecas`).

## Visão geral

O gestor escreve, por exemplo, `Qual o faturamento em janeiro de 2025?` ou `Compare os pedidos de agosto com o ano passado`. O assistente:

1. interpreta a pergunta e identifica métrica, medida e período;
2. pede esclarecimento, **antes de qualquer SQL**, quando algo está ambíguo (`Qual o faturamento?` gera uma pergunta sobre o período);
3. consulta o PostgreSQL por uma role somente leitura, com SQL validado por AST;
4. responde em texto, com números e datas copiados das células retornadas pelo banco.

Capacidades:

- totais por métrica, medida e período, com até quatro combinações na mesma pergunta (`Qual o total de pedidos e o faturamento emitido em agosto de 2025?`);
- comparações entre períodos, contribuição para variações, séries mensais, rankings, participação e desvio operacional;
- continuidade de conversa (`E do mês de agosto?` mantém métricas e ano do turno anterior), com histórico por usuário e `/limpar`;
- `hoje`, `ontem`, `anteontem` e datas de um único dia (`05/03/2025`, `dia 20 de janeiro de 2025`) resolvidos de forma determinística, fora do Gemini. `dia 20 de janeiro` sem ano exige `esse ano` ou `ano passado` no pedido; caso contrário o assistente pergunta o ano;
- formato único de resposta: cabeçalho, período uma vez e uma linha por medida (`Valor: R$ …`, `Quantidade: 295 pedidos`); rankings numerados sem identificador interno; dia único como `05/11/2026`;
- classificador local de intenções (TF-IDF + regressão logística) que sugere exemplos ao planejador (veja [Classificador de intenções](#classificador-de-intenções)).

Interfaces: bot do Telegram (polling ou webhook HTTPS) e CLI local (`bi-cli`).

## Instalação

Requisitos: Python 3.11+ e Docker com Compose. Comandos em PowerShell; no Linux/macOS use `.venv/bin/activate`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m pip install -e . --no-deps
Copy-Item .env.example .env
```

O lock foi verificado com Python 3.13. Para instalar pelas faixas de versões, use `python -m pip install -e ".[dev]"`. Se já existe `.env`, preserve-o e edite apenas as variáveis desejadas.

### Configuração (`.env`)

| Variável | Uso |
|---|---|
| POSTGRES_DB / POSTGRES_USER | Banco e proprietário administrativo do Compose |
| POSTGRES_PASSWORD | Senha administrativa própria; substituir o exemplo |
| READONLY_PASSWORD | Senha própria e diferente para `readonly_agent` |
| POSTGRES_PORT | Porta local, padrão 55432 |
| ADMIN_DATABASE_URL | URL do proprietário; apenas setup/carga |
| DATABASE_URL | URL **com usuário `readonly_agent`**; nunca usar administrador no agente |
| GEMINI_API_KEY | Chave criada no Google AI Studio |
| GEMINI_MODEL | Padrão `gemini-3.5-flash-lite` |
| INTENT_CLASSIFIER_ENABLED | Padrão `true`; `false` usa somente o planejador Gemini |
| INTENT_MODEL_PATH | Vazio usa o modelo empacotado (`training/intent-model-v2.json`) |
| TELEGRAM_BOT_TOKEN | Token obtido diretamente no @BotFather |
| TELEGRAM_WEBHOOK_SECRET | Segredo aleatório, 16 a 256 caracteres A–Z, a–z, 0–9, `_` e `-` |
| TELEGRAM_ALLOWED_USER_IDS | IDs numéricos dos gestores, separados por vírgula; vazio bloqueia todos |
| TELEGRAM_WEBHOOK_URL | URL pública HTTPS terminada em `/telegram/webhook`; dispensável no polling |
| QUERY_TIMEOUT_MS / MAX_QUERY_ROWS | Padrões: 3000 ms e 100 linhas |
| SESSION_TTL_SECONDS / MAX_SESSIONS / MAX_HISTORY_TURNS | Padrões: uma hora, 1000 sessões e oito turnos (`MAX_SESSIONS` vale só para o estado em memória) |
| STATE_DATABASE_URL | Opcional. URL da role `app_estado`; ativa o [estado durável](#estado-durável-e-vários-workers). Vazio mantém fila e sessões em memória |
| STATE_PASSWORD | Senha da role `app_estado`; usada somente por `bi-db init-state` |
| INBOX_MAX_PENDING | Padrão 100: updates pendentes aceitos antes de responder 503 |
| BACKEND_WORKERS | Padrão 1; valores maiores só são aceitos pelo container com `STATE_DATABASE_URL` |

Mantenha as senhas consistentes com as duas URLs e aplique percent-encoding se houver caracteres especiais. Não publique `.env`, logs do banco ou `.local/`. Para gerar um segredo: `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

### Chave Gemini e cota gratuita

1. Crie uma chave em [Google AI Studio — API Keys](https://aistudio.google.com/apikey) e confirme que o projeto está no **Free Tier**.
2. Salve-a apenas no `.env` (`GEMINI_API_KEY=...`) e reinicie o backend/polling.

O modelo padrão tem entrada e saída gratuitas no Free Tier segundo a [tabela oficial](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite); limites variam por projeto. Uma pergunta normalmente faz várias chamadas (planejamento, schema, SQL e resposta), e a cota pode terminar durante a conversa: o assistente informa o limite em português, sem trocar para modelo pago. **Usar o modelo com chave de projeto pago pode gerar cobrança**; o código não controla o plano do Google. No Free Tier o Google pode usar o conteúdo para melhorar seus produtos, por isso use somente a base sintética. Erros de chave/permissão, cota, modelo indisponível e serviço indisponível têm mensagens distintas.

## Banco de dados

```powershell
docker compose up -d --wait
bi-db init
bi-db seed --profile autopecas --clients 100 --seed 42 --start-month 2025-01 --end-month 2026-10
bi-db validate
bi-db coverage --profile autopecas
```

`init` cria o schema e a role de leitura em uma transação e recusa schema/role existentes, para não alterar outro projeto. `seed` é transacional e recusa banco preenchido. Não há comando de reset destrutivo. `docker compose down` preserva o volume, e alterar `POSTGRES_PASSWORD` depois da criação do volume não muda a senha já armazenada.

### Estado durável e vários workers

Por padrão, a fila de updates, a deduplicação e o histórico das conversas ficam em memória e o backend roda em **um único processo**: reiniciar perde o que ainda não foi processado. Para evitar isso, o estado pode ficar no próprio PostgreSQL (schema `estado`, sem nenhum acesso da role de leitura):

```powershell
# STATE_PASSWORD no .env; usa ADMIN_DATABASE_URL e não altera as tabelas de negócio
bi-db init-state
# STATE_DATABASE_URL=postgresql://app_estado:<STATE_PASSWORD>@localhost:55432/<POSTGRES_DB>
```

Com `STATE_DATABASE_URL` definida:

- o webhook grava o update no banco **antes** de responder 200 e deduplica por `update_id`; um update aceito sobrevive a reinícios e é processado quando o backend volta (o texto da pergunta só fica no banco até a conclusão);
- os consumidores reservam updates com `FOR UPDATE SKIP LOCKED` (reserva de 180 s, até 3 tentativas), de modo que vários processos dividem a fila sem processar o mesmo update duas vezes;
- o histórico das conversas é gravado no banco, com lock consultivo por conversa, e expira por `SESSION_TTL_SECONDS`;
- a role `app_estado` só acessa as duas tabelas do schema `estado`; `readonly_agent` continua sem acesso a elas.

A garantia é **pelo menos uma vez**: uma queda depois de enviar a resposta e antes de marcar o update como concluído pode repetir a resposta. Exatamente uma vez continua fora do alcance. `/health` informa `estado_duravel`.

### Perfis de dados

O schema é o mesmo em todos os perfis (cinco tabelas); muda apenas o conteúdo gerado, sempre de forma determinística por `--seed`.

| Perfil | Conteúdo | Uso |
|---|---|---|
| `autopecas` | 100 clientes de nicho (oficinas, auto elétricas, funilarias, autocenters, frotas, retíficas, lojas), 22 meses, em média R$ 350–410 mil e 320–360 pedidos por mês, ticket médio perto de R$ 1.100 | Apresentação e produção |
| `original` | 30 clientes, contratos e pedidos de 2024/2025 | Avaliação congelada de 40 casos |
| `original-v2` | Mesmos clientes e contratos, com pedidos em qualquer dia do mês, descrições variadas e valores com flutuação | Reavaliação sobre dados mais variados |
| `comparativo` | 100 clientes, 22 meses (jan/2025–out/2026): 681 contratos, 5.100 pedidos, 5.809 notas e 1.700 indicadores | Comparações entre períodos; hash SHA256 publicado em [`docs/projeto.md`](docs/projeto.md#base-sintética-para-comparações-de-bi) |
| `comparativo-v2` | Mesma cobertura do `comparativo`, com pedidos espalhados pelo mês e descrições variadas | Variante com dados mais realistas |

Os perfis `original` e `comparativo` não são alterados, porque alimentam a avaliação congelada e o hash publicado. As cargas `-v2` auditam a variedade (dias, descrições e valores distintos) antes de aceitar os dados. Para `comparativo`/`comparativo-v2` use `--clients 100 --start-month 2025-01 --end-month 2026-10`; para `original`/`original-v2`, `--clients 30`.

No perfil `autopecas`, pedidos são pedidos de venda, contratos são contratos de fornecimento, horas são horas de atendimento e chamados são ocorrências de pós-venda (garantias, trocas e devoluções); o planejador aceita "chamados" e "ocorrências". Veja o [dicionário de dados](docs/projeto.md#dicionário-de-dados), as [consultas SQL de comparação](docs/dados/consultas-base-comparativa.sql) e o [resumo mensal](docs/dados/base-comparativa-resumo.json).

## Uso

### CLI local

```powershell
bi-cli
```

Experimente `Qual o faturamento em janeiro de 2025?`. Comandos: `/limpar` e `/sair`. Sem `GEMINI_API_KEY`, o CLI informa em português que a IA não está configurada.

As respostas mostram o período e distinguem ausência de registros de campos não preenchidos. `Total de pedidos` significa quantidade; para dinheiro, peça `valor dos pedidos`. Totais simples usam consultas padronizadas; filtros adicionais e análises detalhadas usam o executor SQL restrito.

### Telegram com polling (sem HTTPS público)

Configure a chave Gemini, o token, o segredo e os IDs autorizados. Obtenha seu ID pela própria Bot API (`getUpdates`, com webhook e polling parados), sem compartilhar o token nem usar terceiros, e converse em chat privado com o bot.

```powershell
# Terminal 1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
# Terminal 2, com o mesmo .env e ambiente virtual
bi-telegram polling
```

O polling usa python-telegram-bot e encaminha cada update ao webhook FastAPI local, de modo que as perguntas passam pelas mesmas quatro camadas. O offset só avança depois que o backend aceita o update. O comando remove o webhook remoto do bot sem descartar updates; **não execute polling e webhook ao mesmo tempo**.

Comandos no Telegram: `/start`, `/help` e `/limpar`. Mensagens de grupos e de usuários fora da allowlist são ignoradas. `http://127.0.0.1:8000/health` confirma processo e configuração, não a conectividade com Gemini ou banco.

### Telegram com webhook público

Exponha o backend por HTTPS (proxy ou túnel), configure `TELEGRAM_WEBHOOK_URL` e registre:

```powershell
bi-telegram register-webhook
```

O endpoint exige o cabeçalho `X-Telegram-Bot-Api-Secret-Token`; mantenha o segredo apenas no backend e no registro do Telegram, nunca na URL. A fila tem capacidade limitada, deduplicação em memória e quatro consumidores, com serialização por sessão. **Sem `STATE_DATABASE_URL`, use um único worker/processo FastAPI**; com estado durável, vários processos podem dividir a carga.

### Diagnóstico de conexões

```powershell
# Apenas configuração; não faz chamadas de rede
python -m scripts.check_connections
# Verifica PostgreSQL, resposta do Gemini e autenticação do Telegram
python -m scripts.check_connections --testar-conexoes
```

`configurado` significa somente presença/formato; `confirmado`, que a conexão respondeu. `pendente` ou `falhou` produz código de saída diferente de zero e orientação em português. O comando não exibe credenciais, não envia mensagens, não consome updates e não altera o webhook. A opção de teste consome uma chamada da cota Gemini.

## Classificador de intenções

Um modelo local TF-IDF + regressão logística (versão 2) foi treinado com 1.112 perguntas sintéticas em vocabulário de autopeças e avaliado em 224 perguntas de teste escritas de formas que o treino nunca viu: **acurácia de 87,9% e, nas sugestões aceitas, cobertura de 80,8% e precisão de 95,0%**, atingindo o critério declarado antes do teste.

- Está **ligado por padrão** (`INTENT_CLASSIFIER_ENABLED=true`). Quando confiante, acrescenta até dois exemplos de treino ao prompt do planejador, sem autoridade sobre datas, SQL ou números, e registra `intencao rotulo=... confianca=... aceita=...` no log, sem o texto da pergunta.
- Baixa confiança, artefato ausente/inválido ou intenção genérica mantêm o caminho geral. O assistente funciona pelo planejador Gemini mesmo com o classificador desativado.
- O runtime usa inferência em JSON, sem scikit-learn, e não treina com conversas dos usuários.
- **Não é fine-tuning do Gemini**, e **o ganho nas respostas não foi medido**: acurácia de classificação não é acurácia de SQL. A classe mais frágil é a operacional (F1 de 0,67).
- Num servidor já configurado, o arquivo privado de configuração pode ter `INTENT_CLASSIFIER_ENABLED=false` e precisa ser ajustado (veja o [guia da Oracle](deploy/oracle/README.md)).

Método, limites e resultados: [treinamento v2](docs/avaliacao.md#treinamento-supervisionado-de-intenções--versão-2-revenda-de-autopeças). A [versão 1](docs/avaliacao.md#treinamento-supervisionado-de-intenções--versão-1) fica como histórico. Para reproduzir o treino (Python 3.12/3.13):

```powershell
python -m pip install -r requirements-training-lock.txt
python -m training.build_corpus_v2
python -m scripts.train_intents validate --corpus training/questions-v2.json
python -m scripts.train_intents train --corpus training/questions-v2.json --c-grid 0.5,1,2,5,10,20,50,100 --thresholds 0.3,0.4,0.5,0.6,0.7 --joint-selection --seed 42 --output .local/intent-training-nova
# Depois de congelar o artefato e concluir ajustes somente na validação:
python -m scripts.train_intents test --corpus training/questions-v2.json --model .local/intent-training-nova/model.json --output .local/intent-test-novo
```

Pastas de saída existentes são recusadas.

## Segurança e garantia dos números

- A AST do PostgreSQL aplica allowlist de SELECT, nós, funções, tabelas e tipos. DML/DDL, SELECT INTO, locks, funções arbitrárias e schemas externos são bloqueados.
- `readonly_agent` não é superusuário, não pertence a outras roles e recebe SELECT somente nas cinco tabelas. A aplicação verifica a role e recusa grants de escrita. Transações são read-only; timeout e limite de linhas valem para toda consulta de negócio, e os metadados também têm timeout e limite fixo.
- O planejamento sem tools exige métrica, medida e período com evidência literal do pedido ou do histórico antes de permitir SQL.
- Erros SQL voltam ao modelo como `tool_result` para autocorreção limitada. Detalhes do PostgreSQL ficam no contexto interno, não na resposta ao gestor.
- O modelo retorna somente uma referência ao resultado. O backend produz a introdução e os registros, sem prosa livre do modelo. Números e datas vêm das células; `Decimal` mantém todos os dígitos e o agente não arredonda (o SQL pode arredondar se o usuário pedir). Percentuais são exibidos com duas casas decimais, somente no texto.
- Agregados únicos com alias `total` recebem uma frase natural conforme a métrica e a medida. O renderizador não deduz soma, moeda ou percentual pelo alias. NULL nunca vira zero e resultados parciais são identificados.
- O estado durável usa uma role própria (`app_estado`), sem superusuário, dona de nada e com acesso apenas às tabelas do schema `estado`; ela não lê as tabelas de negócio.
- Acesso administrativo fica nos comandos de setup; não existe tool administrativa. Os logs da aplicação omitem textos, SQL e credenciais.

## Testes e avaliação

```powershell
python -m pytest -q
python -m ruff check app scripts tests evaluation training
```

A suíte tem 323 testes; os que dependem de PostgreSQL são marcados como skipped sem `TEST_DATABASE_URL` (negócio) e `TEST_STATE_ADMIN_URL` (estado durável: URL administrativa de um banco **de teste**, cujo schema `estado` e role `app_estado` são recriados). Para executá-la inteira contra a base sintética carregada, sem exibir a senha:

```powershell
python -c "import os,pytest; from app.config import Settings; os.environ['TEST_DATABASE_URL']=Settings().database_url.get_secret_value(); raise SystemExit(pytest.main(['-q']))"
```

Use somente a base sintética do projeto. A suíte verifica negação de DML/DDL, timeout real, limite de linhas, precisão decimal, autocorreção, ambiguidade, sessões, webhook, o protocolo nativo do SDK Gemini (assinaturas, chamadas paralelas, erros de cota/permissão), o classificador e o fluxo completo com PostgreSQL real e APIs Gemini/Telegram simuladas. Simulações não comprovam a interpretação do Gemini nem a entrega pelo Telegram.

### Avaliação com o Gemini

`evaluation/` contém 40 casos originais, SQL de referência e um executor reproduzível. Em outubro de 2026, na base original (30 clientes, domínio de software), a terceira rodada de desenvolvimento e o teste reservado concluíram 20/20 casos cada, na versão `59c9eb8`, sem falhas semânticas. Em 09/11/2026 a avaliação foi refeita com o perfil `autopecas` e o Gemini real, e o resultado foi menor: o desenvolvimento fechou em 16/16 depois de duas correções, mas os reservados deram **12/16** (conjunto A) e **6/8** (gerencial), ambos no limite do critério de 70%, em uma rodada cada. Depois disso corrigi as falhas de interpretação do conjunto A, que deixou de ser independente ([experimentos](docs/experimentos.md#correção-das-falhas-do-reservado-do-conjunto-a-09112026)). Protocolo e resultados: [avaliação](docs/avaliacao.md#reavaliação-no-perfil-autopecas-protocolo-declarado-antes-da-rodada) e [experimentos](docs/experimentos.md#reavaliação-no-perfil-autopecas--teste-reservado-do-conjunto-a-310-09112026). Em outubro, a versão, a base, o modelo e o conjunto foram congelados antes da avaliação reservada, que aprovou 16/16 respostas e 4/4 esclarecimentos. A latência média de 1,649 s mede agente e banco, sem o transporte do Telegram, e as taxas valem para esta amostra. Evidências e limitações: [experimentos](docs/experimentos.md) e [verificações](docs/verificacoes.md). O conjunto gerencial, com 35 cenários separados dos 40 originais, usa `--dataset evaluation/managerial-cases-v1.json`.

```bash
python -m scripts.evaluate validate
python -m scripts.evaluate run --live --split development --interval 60 --limit 20
```

Os resultados ficam em `.local/evaluation/`. Rode o conjunto reservado (`--split test`) somente depois de congelar os ajustes de desenvolvimento, e nunca para ajustar prompts. A avaliação não envia mensagens nem reinicia o Telegram. Rodadas reais exigem o ambiente conectado e consomem a cota do Gemini.

Para o perfil `autopecas`, use `--dataset evaluation/cases-autopecas.json` (versão 3.1.0: mesmos 40 casos adaptados às datas e ao vocabulário da revenda, com dois pedidos não suportados). Para reavaliar os mesmos 40 casos sobre uma base `original-v2`, use `--dataset evaluation/cases-original-v2.json`. O SQL de referência é idêntico ao do conjunto original (calculado ao vivo contra o banco carregado); só a versão declarada no arquivo muda, para não misturar evidências entre perfis.

### Teste manual de ponta a ponta

1. Execute setup, validação, backend e polling (ou webhook HTTPS).
2. Em chat privado, envie `/start` e `Qual o faturamento?`; confirme a pergunta sobre o período.
3. Responda `janeiro de 2025` e confira o resultado com a consulta abaixo, usando o login de leitura.
4. Envie `/limpar` e confirme que o histórico não influencia a próxima pergunta.

```sql
SELECT SUM(valor) AS total
FROM faturamento
WHERE emissao >= DATE '2025-01-01'
  AND emissao < DATE '2025-02-01'
  AND status <> 'cancelada';
```

## Implantação

A hospedagem em produção usa Docker Compose (PostgreSQL 16, backend e um processo de polling) em uma VM Oracle. Dockerfile, `runtime_entrypoint.py`, `deploy/oracle/compose.yaml` e o configurador de segredos estão no repositório. O [guia de implantação e atualização](deploy/oracle/README.md) cobre instalação, troca do banco pelo perfil `autopecas` e atualização do código; o histórico das implantações está em [`docs/deploy.md`](docs/deploy.md).

## Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| `app/` | Agente, política SQL, tools, renderização, sessões, FastAPI, Telegram e CLI |
| `db/` | Schema e grants |
| `scripts/` | Administração do banco, geradores de dados, avaliação, treino e diagnóstico |
| `training/` | Corpus, protocolo e modelos do classificador de intenções |
| `evaluation/` | Casos, SQL de referência, executor e pontuação |
| `tests/` | Testes de engenharia |
| `deploy/oracle/` | Compose e configurador da hospedagem |
| `docs/` | Documentação consolidada (índice em [`docs/README.md`](docs/README.md)) |

## Documentação

- [Projeto](docs/projeto.md): escopo, arquitetura, plano, dicionário de dados e base comparativa.
- [Avaliação](docs/avaliacao.md): protocolos, treinamento de intenções, aceite do gestor e comparação com a proposta.
- [Experimentos](docs/experimentos.md) e [verificações](docs/verificacoes.md): resultados e evidências.
- [Deploy](docs/deploy.md): publicação e implantações.
- [Apresentação](docs/apresentacao.md): guia de estudo e roteiros de demonstração.
- Relatório final: [Word](docs/entregaveis/Relatorio-Final-PAC-VIII-Arthur-Hassuma.docx), [PDF](docs/entregaveis/Relatorio-Final-PAC-VIII-Arthur-Hassuma.pdf) e [fonte textual](docs/relatorio-final-pac-viii.md).

## Limitações conhecidas

- Sem `STATE_DATABASE_URL`, fila, deduplicação e histórico ficam em memória: reiniciar o processo pode perder updates já aceitos ou permitir o reprocessamento de updates antigos, e só um worker é suportado. Com o [estado durável](#estado-durável-e-vários-workers) isso é resolvido, mas a entrega continua **pelo menos uma vez** (uma queda entre enviar a resposta e concluir o update pode repeti-la), nunca exatamente uma vez.
- A garantia de origem numérica não comprova a correção semântica do SQL: filtros ou joins errados continuam possíveis, e a taxa de acerto só vale para a amostra avaliada.
- A interpretação das perguntas depende do Gemini e da cota do projeto configurado. Na reavaliação de 09/11/2026 os reservados acertaram 12/16 (autopecas) e 6/8 (gerencial). As três falhas de interpretação do conjunto A (T04, T05 e T10) foram corrigidas depois, o que **contamina** esse reservado. A versão corrigida foi medida numa partição nova de 20 casos (conjunto C, escrita depois das correções): **13/16** respostas corretas, 3/3 esclarecimentos e 1/1 pedido não suportado, em uma execução; as falhas foram um ranking com formato diferente do gabarito e dois esclarecimentos de medida para perguntas ambíguas ([experimentos](docs/experimentos.md#reavaliação-no-perfil-autopecas--conjunto-c-partição-reservada-nova-100-09112026)). Com 20 casos, esse resultado não permite afirmar melhora em relação aos 12/16 anteriores.
- O aceite do gestor está registrado por declaração do responsável; não houve coleta qualitativa estruturada, medição de latência ponta a ponta no Telegram nem comparação com dashboards.
- Todos os dados são sintéticos; o assistente não foi avaliado com dados reais.

## Licença

Distribuído sob a licença MIT; veja [LICENSE](LICENSE). Os dados do projeto são sintéticos.

## Referências técnicas

[SDK Gemini](https://googleapis.github.io/python-genai/), [preços Gemini](https://ai.google.dev/gemini-api/docs/pricing), [webhook python-telegram-bot](https://docs.python-telegram-bot.org/en/stable/examples.customwebhookbot.html) e [timeouts PostgreSQL 16](https://www.postgresql.org/docs/16/runtime-config-client.html).
