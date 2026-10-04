# Assistente Conversacional de BI — PAC Extensionista VIII

MVP acadêmico em português do Brasil: **Telegram → FastAPI → Gemini → PostgreSQL 16**. Base B2B integralmente sintética, inspirada em serviços de desenvolvimento de software. Escopo implementado: Fases 0–3. Não inclui avaliação acadêmica, conjunto de perguntas ou experimentos da Fase 4.

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

## Teste manual real — pendente

O usuário autorizou seguir para o teste real com Gemini; a execução depende de configurar as credenciais locais. Nenhum teste simulado comprova acesso à API externa. Quando a chave e o token estiverem disponíveis:

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

Para usar Compose, prepare um `.env` coerente com o novo volume e use outra porta ou pare o cluster nativo. O Compose foi fornecido, mas não pôde ser executado nesta máquina sem Docker.

## Estrutura e continuidade

`app/`: agente, política SQL, tools, renderizador, sessões, FastAPI, Telegram e CLI. `db/`: schema e grants. `scripts/`: administração e Faker. `tests/`: testes de engenharia. `docs/`: anexos, desenho, dicionário e verificação.

Próxima etapa: concluir o teste real Gemini/Telegram; depois, em outra sessão, criar o conjunto de 30–50 perguntas com SQL/resultado de referência, medir acerto semântico e esclarecimentos, iterar prompts com erros observados, executar experimentos e validação qualitativa, e redigir o relatório final. As atividades de Fase 4 não foram iniciadas aqui.

Referências técnicas consultadas: [SDK Gemini](https://googleapis.github.io/python-genai/), [preços Gemini](https://ai.google.dev/gemini-api/docs/pricing), [webhook python-telegram-bot](https://docs.python-telegram-bot.org/en/stable/examples.customwebhookbot.html), [timeouts PostgreSQL 16](https://www.postgresql.org/docs/16/runtime-config-client.html).
