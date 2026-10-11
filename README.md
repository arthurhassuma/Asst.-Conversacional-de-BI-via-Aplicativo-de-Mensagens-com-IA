# Assistente Conversacional de BI — PAC Extensionista VIII

Entrega final preparada em **11/10/2026**: [índice dos artefatos e fechamento do cronograma](docs/entrega-final.md), [relatório Word](docs/Relatorio-Final-PAC-VIII-Arthur-Hassuma.docx), [PDF](docs/Relatorio-Final-PAC-VIII-Arthur-Hassuma.pdf) e [roteiro de demonstração](docs/roteiro-demonstracao.md). O aceite do gestor está registrado conforme declaração do responsável, sem feedback documentado. A [reprodução Docker](docs/verificacao-entrega-final.md) aprovou 110 testes com PostgreSQL e 34 referências SQL. Submissão e aprovação institucional permanecem a cargo do responsável.

Repositório de continuidade: [arthurhassuma/pac_privado](https://github.com/arthurhassuma/pac_privado).
Em 04/10/2026, a importação foi validada com **65 testes aprovados**, incluindo PostgreSQL real.
Veja [publicação e verificação atual](docs/publicacao-github.md), [testes automáticos](https://github.com/arthurhassuma/pac_privado/actions) e [roteiro de entrega até dezembro](docs/roteiro-entrega-dezembro.md).

Revisão de 10/10/2026: [comparação com a proposta aprovada](docs/comparacao-proposta.md) e [verificação da continuidade](docs/verificacao-2026-10-10.md). Foram aprovados 77 testes com PostgreSQL real e APIs externas simuladas. A conexão Gemini/Telegram em outro ambiente foi informada pelo usuário; não foi reproduzida com credenciais externas nesta revisão.

MVP acadêmico em português do Brasil: **Telegram → FastAPI → Gemini → PostgreSQL 16**. Base B2B integralmente sintética, inspirada em serviços de desenvolvimento de software. A continuidade autorizada até a entrega final inclui 40 casos de avaliação, experimentos reais com Gemini, aceite declarado do gestor e relatório final. As limitações medidas e as providências institucionais estão no índice da entrega.

O provedor foi alterado de Anthropic para Gemini por decisão do usuário para usar a cota gratuita. A proposta original permanece preservada. Veja a [justificativa e detalhes da migração](docs/migracao-gemini.md).

O levantamento encontrou somente os dois documentos, agora em [docs/](docs/). Não havia esqueleto de código. Veja [levantamento inicial](docs/levantamento-inicial.md), [arquitetura](docs/arquitetura.md) e [dicionário](docs/dicionario-de-dados.md).

## Setup reproduzível

Requisitos: Python 3.11+ e Docker com Compose. Execute na raiz do projeto. Exemplos PowerShell; no Linux/macOS use `.venv/bin/activate`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m pip install -e . --no-deps
Copy-Item .env.example .env
```

Se já existe `.env`, preserve-o e edite apenas as variáveis desejadas. Para instalar pelas faixas de versões, em vez do lock, use `python -m pip install -e ".[dev]"`. O lock foi verificado com Python 3.13 no Windows.

Edite `.env` localmente:

| Variável | Uso |
|---|---|
| POSTGRES_DB / POSTGRES_USER | Banco e proprietário administrativo do Compose |
| POSTGRES_PASSWORD | Senha administrativa própria; substituir exemplo |
| READONLY_PASSWORD | Senha própria e diferente para readonly_agent |
| POSTGRES_PORT | Porta local, padrão 55432 |
| ADMIN_DATABASE_URL | URL do proprietário; apenas setup/carga |
| DATABASE_URL | URL **com usuário readonly_agent**; nunca usar administrador no agente |
| GEMINI_API_KEY | Chave Gemini criada no Google AI Studio |
| GEMINI_MODEL | Padrão gemini-3.5-flash-lite; pode ser alterado explicitamente |
| TELEGRAM_BOT_TOKEN | Token obtido diretamente no @BotFather |
| TELEGRAM_WEBHOOK_SECRET | Segredo aleatório, entre 16 e 256 caracteres A–Z, a–z, 0–9, `_` e `-` |
| TELEGRAM_ALLOWED_USER_IDS | IDs numéricos dos gestores, separados por vírgula; vazio bloqueia todos |
| TELEGRAM_WEBHOOK_URL | URL pública HTTPS completa, terminada em /telegram/webhook; dispensável no polling |
| QUERY_TIMEOUT_MS / MAX_QUERY_ROWS | Padrões: 3000 ms e 100 linhas |
| SESSION_TTL_SECONDS / MAX_HISTORY_TURNS | Padrões: uma hora e oito turnos |

Mantenha as senhas consistentes com as duas URLs. Se houver caracteres especiais, aplique percent-encoding na URL. Não publique `.env`, logs do banco ou `.local/`. Um segredo pode ser gerado com `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

```powershell
docker compose up -d --wait
bi-db init
bi-db seed --seed 42 --clients 30
bi-db validate
```

`init` cria o schema e a role de leitura em uma transação. Recusa schema/role existentes para não alterar outro projeto. `seed` é transacional e recusa banco preenchido. Não existe comando automático de reset destrutivo. `docker compose down` preserva o volume. Mudanças em POSTGRES_PASSWORD após a primeira criação do volume não alteram a senha já armazenada no PostgreSQL.

## CLI local

```powershell
bi-cli
```

Experimente `Qual o faturamento em janeiro de 2025?`. `Qual o faturamento?` deve gerar esclarecimento antes de SQL. Comandos `/limpar` e `/sair`. Sem GEMINI_API_KEY, o CLI informa em português que a IA não está configurada.

É possível consultar até quatro combinações de métricas, medidas e períodos na mesma
pergunta, por exemplo: `Qual o total de pedidos e o faturamento emitido em agosto de 2025?`.
`Total de pedidos` significa quantidade; para dinheiro, peça `valor dos pedidos`.
`E do mês de agosto?` mantém as métricas e o ano do período anterior. Quando falta uma
medida, o esclarecimento indica a métrica pendente e mantém o restante do pedido.
As respostas mostram o período e distinguem ausência de registros de campos não
preenchidos. A base sintética tem pedidos e faturamento emitido em 2024/2025: em
09/10/2026, `mês passado` corresponde a setembro de 2026 e não encontra registros.
Totais simples usam consultas padronizadas; filtros adicionais e análises detalhadas
continuam usando o executor SQL restrito. Veja os [testes reais de outubro](docs/verificacao.md).

## Chave Gemini e cota gratuita

1. Acesse [Google AI Studio — API Keys](https://aistudio.google.com/apikey) com sua conta Google.
2. Crie uma chave/projeto e confira que o projeto está no **Free Tier**. Para este teste, não ative faturamento pago.
3. Salve a chave apenas no `.env`, na linha `GEMINI_API_KEY=...`, e mantenha `GEMINI_MODEL=gemini-3.5-flash-lite`.
4. Preserve as configurações do banco, segredo e token do Telegram. Reinicie o backend/polling após editar `.env`.

O modelo padrão tem entrada/saída gratuitas no Free Tier segundo a [tabela oficial](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite). A disponibilidade e os limites variam por projeto. Uma pergunta normalmente faz várias chamadas (planejamento, schema, SQL e resposta); a cota pode terminar durante uma conversa. O assistente informa o limite em português, sem mudar automaticamente para um modelo pago. **Usar esse modelo com chave de projeto pago pode gerar cobrança**; o código não controla o plano do Google.

No Free Tier o Google pode usar o conteúdo para melhorar seus produtos: utilize somente esta base sintética. Erros de chave/permissão, cota, modelo indisponível e serviço indisponível têm mensagens distintas. Os nomes antigos ANTHROPIC_API_KEY e ANTHROPIC_MODEL não são utilizados.

## Backend e Telegram local, sem HTTPS público

Configure a chave Gemini, token, segredo e IDs autorizados. Obtenha seu ID pela própria Bot API (`getUpdates`, com webhook/polling parados), sem compartilhar o token ou usar terceiros. Converse em chat privado com o bot.

Terminal principal:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Outro terminal, com o mesmo `.env` e ambiente virtual:

```powershell
bi-telegram polling
```

O polling usa python-telegram-bot e encaminha cada update ao webhook FastAPI local. As perguntas passam pelas mesmas quatro camadas. O offset avança somente após aceitação do backend. Esse comando remove o webhook remoto do bot, sem descartar updates; não execute polling e webhook remoto simultaneamente.

Saúde de processo/configuração: `http://127.0.0.1:8000/health`. Esse endpoint não confirma conectividade Gemini/banco. `/start`, `/help` e `/limpar` funcionam no Telegram. Mensagens de grupos e usuários fora da allowlist são ignoradas.

### Diagnóstico no ambiente conectado

Execute na raiz do checkout que contém o `.env` usado pelo bot:

```powershell
# Apenas configuração; não faz chamadas de rede
python -m scripts.check_connections
# Verifica PostgreSQL, resposta do Gemini e autenticação Telegram
python -m scripts.check_connections --testar-conexoes
```

`configurado` significa somente presença/formato; `confirmado` significa que a conexão indicada respondeu. `pendente` ou `falhou` produz código de saída diferente de zero e orientação em português. O comando não exibe credenciais, não envia mensagens, não consome updates e não altera o webhook. A opção de teste consome uma chamada da cota Gemini e respeita o projeto configurado; não verifica nem muda seu plano de cobrança. Ainda é necessário realizar o teste funcional abaixo para comprovar SQL e entrega das respostas.

## Webhook público

Disponibilize o backend por HTTPS com proxy/túnel de sua escolha e configure TELEGRAM_WEBHOOK_URL. Mantenha o segredo apenas no backend e no registro do Telegram; não o coloque na URL.

```powershell
bi-telegram register-webhook
```

O endpoint exige `X-Telegram-Bot-Api-Secret-Token`. A fila tem capacidade limitada, deduplicação em memória e quatro consumidores, com serialização por sessão. **Use apenas um worker/processo FastAPI.** Fila, deduplicação e histórico são voláteis: reiniciar pode perder updates já aceitos ou permitir reprocessamento de updates antigos. O MVP não garante entrega exatamente uma vez. Persistência durável e execução distribuída exigem evolução posterior.

## Segurança e números

- A AST PostgreSQL tem allowlist de SELECT, nós, funções, tabelas e tipos. DML/DDL, SELECT INTO, locks, funções arbitrárias e schemas externos são bloqueados.
- readonly_agent não é superusuário, não pertence a outras roles e recebe SELECT somente nas cinco tabelas. A aplicação verifica a role e recusa grants de escrita. Transações são read-only; timeout e limite externo de linhas são aplicados a toda consulta de negócio. Metadados também têm timeout e limite fixo.
- Planejamento sem tools exige métrica, medida e período com evidência literal do pedido/histórico antes de permitir SQL. Reconhecer a intenção continua dependendo do modelo; interpretação semântica exige a avaliação futura.
- Erros SQL voltam ao modelo como tool_result para autocorreção limitada. Detalhes do PostgreSQL ficam no contexto interno, não na resposta ao gestor.
- O modelo retorna somente referência ao resultado. O backend produz a introdução e os registros, sem incorporar prosa livre do modelo. Números e datas vêm das células; Decimal mantém todos os dígitos. O agente não arredonda na resposta. SQL pode arredondar se o usuário pedir.
- Agregados únicos com alias `total` recebem uma frase natural conforme a métrica e a medida, por exemplo faturamento ou quantidade de clientes. O valor é copiado integralmente da célula; o renderizador não deduz soma, moeda ou percentual pelo alias. Detalhamentos, NULL e resultados parciais mantêm o formato de registros e seus avisos.
- Essa garantia de origem numérica **não comprova a correção semântica do SQL**: escolher filtros ou joins errados continua possível e deverá ser medido na Fase 4. Resultados parciais são identificados; NULL não é convertido em zero.
- Acesso administrativo fica nos comandos de setup; não há tool administrativa. Logs da aplicação omitem textos, SQL e credenciais. O PostgreSQL pode registrar SQL com erro; os logs locais estão em `.local/` ignorado.

## Testes de engenharia

```powershell
python -m pytest -q
python -m ruff check app scripts tests
```

Sem TEST_DATABASE_URL, testes que precisam do PostgreSQL são marcados como skipped. Para rodar a suíte inteira contra a base sintética já carregada, sem exibir a senha:

```powershell
python -c "import os,pytest; from app.config import Settings; os.environ['TEST_DATABASE_URL']=Settings().database_url.get_secret_value(); raise SystemExit(pytest.main(['-q']))"
```

Use somente a base sintética deste projeto. A suíte verifica negação de DML/DDL, timeout real, limite de linhas, precisão decimal, autocorreção, ambiguidade, sessões, webhook e o fluxo completo com PostgreSQL real e APIs Gemini/Telegram simuladas na rede. Também verifica o protocolo nativo do SDK Gemini, preservação de assinaturas, chamadas paralelas e erros de cota/permissão. Isso não substitui o teste manual real.

## Teste manual real — registro de evidência

O usuário informou conexão Gemini/Telegram em outro ambiente. Nesta revisão não foram usadas credenciais externas, e o GitHub não contém a configuração do processo em execução. Nenhum teste simulado comprova acesso à API externa. No ambiente já conectado, conclua e registre o roteiro:

1. Execute setup, validação, backend e polling (ou webhook HTTPS).
2. Em chat privado, envie `/start` e `Qual o faturamento?`; confirme a pergunta sobre período.
3. Responda `janeiro de 2025`; confira o resultado com a consulta abaixo usando o login de leitura.
4. Envie `/limpar`; confirme que o histórico não influencia a próxima pergunta.
5. Registre data, modelo, versão do código, SQL de referência e valor recebido em `docs/verificacao.md`, sem tokens nem dados pessoais.

```sql
SELECT SUM(valor) AS total
FROM faturamento
WHERE emissao >= DATE '2025-01-01'
  AND emissao < DATE '2025-02-01'
  AND status <> 'cancelada';
```

## Ambiente local desta entrega

Docker não estava instalado. A carga e os testes usaram PostgreSQL **16.14** já disponível em `C:/Program Files/PostgreSQL/16/bin`, em cluster isolado `.local/pgdata`, porta **55439**. O serviço preexistente não foi alterado. `.env` local contém senhas aleatórias desse cluster e credenciais externas vazias; esse arquivo não integra a distribuição.

Para iniciar/parar esse cluster existente no Windows, a partir da raiz (sem recriá-lo):

```powershell
& 'C:/Program Files/PostgreSQL/16/bin/pg_ctl.exe' -D "$PWD/.local/pgdata" -l "$PWD/.local/postgres.log" -o '-p 55439 -h 127.0.0.1' -w start
# Ao terminar:
& 'C:/Program Files/PostgreSQL/16/bin/pg_ctl.exe' -D "$PWD/.local/pgdata" -m fast -w stop
```

Para usar Compose, prepare um `.env` coerente com o novo volume e use outra porta ou pare o cluster nativo. O Compose não foi executado nesta máquina Windows sem Docker. Posteriormente, a reprodução em ambiente Linux com Docker foi concluída em 11/10/2026; veja docs/verificacao-entrega-final.md.

## Estrutura e continuidade

`app/`: agente, política SQL, tools, renderizador, sessões, FastAPI, Telegram e CLI. `db/`: schema e grants. `scripts/`: administração e Faker. `tests/`: testes de engenharia. `docs/`: anexos, desenho, dicionário e verificação.

A continuidade inclui o conjunto de avaliação e as rodadas com Gemini descritas abaixo. A conexão real Gemini/Telegram foi validada no ambiente em nuvem. O relatório final e o aceite declarado do gestor estão disponíveis em docs/; não houve coleta qualitativa estruturada. Consulte os relatórios datados em `docs/` para distinguir implementação de resultados medidos.

Referências técnicas consultadas: [SDK Gemini](https://googleapis.github.io/python-genai/), [preços Gemini](https://ai.google.dev/gemini-api/docs/pricing), [webhook python-telegram-bot](https://docs.python-telegram-bot.org/en/stable/examples.customwebhookbot.html), [timeouts PostgreSQL 16](https://www.postgresql.org/docs/16/runtime-config-client.html).

## Avaliação S7–S11

Conjunto de 40 casos, SQL de referência e executor reproduzível em `evaluation/`. Consulte [o protocolo](docs/protocolo-avaliacao.md) antes de executar.

A [terceira rodada de desenvolvimento](docs/experimentos/2026-10-11-desenvolvimento-rodada3.md) e o [teste reservado](docs/experimentos/2026-10-11-teste-reservado.md) concluíram 20/20 casos cada na versão `59c9eb8`, sem falhas semânticas. A versão, base, modelo e conjunto foram congelados antes da avaliação reservada, que aprovou 16/16 respostas e 4/4 esclarecimentos. A média de 1,649 s mede agente e banco, sem transporte Telegram; as taxas medem o sistema híbrido nesta amostra. Consulte a [verificação atual](docs/verificacao-2026-10-11.md) para as evidências e limitações.

```bash
python -m scripts.evaluate validate
python -m scripts.evaluate run --live --split development --interval 60 --limit 20
```

Resultados ficam em `.local/evaluation/`. Teste reservado somente após congelar ajustes de desenvolvimento. A avaliação não envia mensagens nem reinicia o Telegram.
