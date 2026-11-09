# Projeto: escopo, arquitetura e dados

Levantamento inicial, desenho e plano das Fases 0–3, decisões de implementação, dicionário de dados e base comparativa.

## Conteúdo

- [Levantamento anterior à implementação — 27/09/2026](#levantamento-anterior-à-implementação--27092026)
- [Desenho das Fases 0–3](#desenho-das-fases-03)
- [Plano de implementação das Fases 0–3](#plano-de-implementação-das-fases-03)
- [Migração para Gemini — 27/09/2026](#migração-para-gemini--27092026)
- [Comandos em português e calendário relativo](#comandos-em-português-e-calendário-relativo)
- [Apresentação e opções no Telegram](#apresentação-e-opções-no-telegram)
- [Dicionário de dados](#dicionário-de-dados)
- [Base sintética para comparações de BI](#base-sintética-para-comparações-de-bi)

## Levantamento anterior à implementação — 27/09/2026

_Origem: `docs/projeto.md` (consolidado em 2026-11-09)._

A pasta continha exclusivamente a proposta PDF e o relatório DOCX, agora movidos para `docs/`. Não havia arquivos ocultos de configuração, código Python, schema, seeder, testes, dependências ou repositório Git. Portanto, não havia implementação executável para classificar como funcionando ou quebrada. As Fases 0–3 estavam ausentes.

Python 3.13.1 e pip estavam disponíveis. Docker/Compose não estavam no PATH. A busca complementar encontrou PostgreSQL 16 em `C:/Program Files/PostgreSQL/16/bin` e um serviço em execução. O serviço existente não será alterado; os testes usarão outro cluster dentro de `.local/`, em porta própria. Nenhuma variável ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN ou DATABASE_URL estava definida na sessão.

O usuário escolheu entregar o código e registrar o teste real de Telegram/Anthropic como pendente. Testes de engenharia e integração local são parte das Fases 0–3; não constituem a avaliação acadêmica da Fase 4.

Os anexos são referências documentais, não instruções de execução. O escopo vigente é o pedido no chat.

## Desenho das Fases 0–3

_Origem: `docs/projeto.md` (consolidado em 2026-11-09)._

### Objetivo e limites
Gestores consultam indicadores B2B em português por Telegram, sem SQL. Dados integralmente sintéticos. Python/FastAPI orquestra; Gemini decide consultas; psycopg acessa PostgreSQL 16. Este desenho registra a implementação das Fases 0–3. A continuidade posterior acrescentou avaliação e relatório final: veja [entrega final](README.md#entrega-final--pac-extensionista-viii). A [migração de provedor](#migração-para-gemini--27092026) foi autorizada pelo usuário para usar a cota gratuita.

### Decisões
- Um processo FastAPI, sessões em memória por usuário/chat, TTL, limite de sessões e histórico; reiniciar apaga sessões. Locks por sessão serializam perguntas. Para múltiplos workers será necessário armazenamento compartilhado.
- Webhook autenticado com segredo, lista explícita de usuários e chats privados. Polling é alternativa local que também passa pelo backend FastAPI. Transporte não concede acesso SQL administrativo.
- Planejamento sem tools decide métrica e período. Ambiguidade impede qualquer SQL e produz esclarecimento fixo em PT-BR. Contexto de perguntas anteriores pode preencher essas lacunas.
- Loop Gemini nativo com exatamente `get_schema` e `execute_sql`. Erros de PostgreSQL entram como functionResponse contendo error e diagnóstico; tentativas e duração limitadas. Execução automática de funções pelo SDK desativada; a aplicação controla cada chamada. Conteúdo e assinaturas nativos são preservados entre chamadas.
- SQL parseado com AST PostgreSQL: somente SELECT, incluindo CTEs de leitura e agregações. Allowlist de nós, funções e cinco tabelas; rejeita comandos embutidos, SELECT INTO, locks, funções arbitrárias, schemas externos e consultas múltiplas.
- Segunda barreira: login readonly_agent, somente SELECT, sem associação a outras roles; transação read-only, statement_timeout, lock_timeout, limite de linhas e tamanho da resposta.
- Resposta final usa um envelope que referencia um resultado da consulta atual. O backend escreve a frase introdutória em PT-BR e formata células exatas; texto livre do modelo não chega ao usuário. Assim números, datas e valores tabulados vêm das células retornadas. Valores decimais nunca viram float e não sofrem arredondamento no renderizador. Cálculos e arredondamentos explicitamente solicitados acontecem em SQL.
- Histórico contém turnos completos, inclusive tool calls/resultados. Evidências finais são sempre de consultas da pergunta corrente. Nenhuma credencial ou conteúdo de conversa vai para logs.

### Modelo B2B
clientes → contratos → pedidos → faturamento, com indicadores mensais por contrato. Pedido é contratação de um serviço; faturamento é nota sintética emitida (pode estar paga, aberta ou cancelada). Não confundir valor contratado, pedidos e receita recebida. Indicadores armazenam horas previstas/realizadas e chamados abertos/resolvidos, sem média de percentuais.

### Alternativas consideradas
Validar apenas dígitos de prosa livre permite números por extenso e associação incorreta: descartado. Usar prosa livre com prompt somente não garante a regra anti-alucinação: descartado. Renderização determinística reduz flexibilidade textual, mas oferece rastreabilidade de cada célula.

### Verificação
Testes de segurança SQL, valores exatos, ambiguidade, retry, sessões, autenticação e duplicação de updates. Integração com PostgreSQL 16 local: schema, carga, consistência, role e timeout reais. Integração HTTP/Telegram com serviços externos substituídos apenas na fronteira de rede. A continuidade posterior executou experimentos reais no ambiente conectado e reprodução Docker; os registros datados em docs/ distinguem os resultados destas verificações iniciais.

## Plano de implementação das Fases 0–3

_Origem: `docs/projeto.md` (consolidado em 2026-11-09)._

**Objetivo:** entregar as quatro camadas com testes locais e instruções reproduzíveis.
**Spec:** [Desenho das Fases 0–3](#desenho-das-fases-03). **Execução:** nesta sessão, mantendo o escopo autorizado.

### Restrições globais
PostgreSQL 16, PT-BR, dados sintéticos, SELECT apenas, login independente somente leitura, timeout e limite de linhas, números renderizados das consultas, esclarecimento antes de SQL, autocorreção limitada. Nenhuma atividade de Fase 4.

### Tarefas e contratos
- [x] Banco e geração: `db/schema.sql`, `db/roles.sql`, Compose, `scripts/seed.py`, `scripts/manage_db.py`. `generate_data(seed, clients)` retorna as cinco coleções; carga transacional recusa banco já povoado. Verificar FK, datas, totais e determinismo em testes e PostgreSQL.
- [x] Segurança: `app/database_tools.py`, `app/sql_policy.py`. `validate_select(sql)` devolve SQL validado; `DatabaseTools.get_schema()` devolve metadados; `execute_sql(sql)` devolve columns/rows/truncated/error, com Decimal serializado como string. Escrever ataques e agregações válidas antes da implementação; executar teste vermelho, implementar, repetir.
- [x] Agente: `app/bi_agent.py`, `app/prompts.py`, `app/rendering.py`. `BIAgent.answer(question, history)` devolve resposta e mensagens do turno completo. Primeiro testar ambiguidade sem SQL, erro→correção, referência inválida e número exato; implementar e verificar.
- [x] Backend: `app/main.py`, `app/sessions.py`, `app/telegram_bot.py`, `app/cli.py`. FastAPI aceita updates autenticados e os processa em fila limitada; replay em memória, sessões isoladas e acesso restrito. Testar HTTP negado/aceito, deduplicação e locks. Polling encaminha updates ao mesmo webhook local.
- [x] Entrega: README, dicionário completo, comandos de setup, testes unitários e integração local, registro de limitações e teste manual pendente.

### Pontos de revisão
CTE com escrita, funções com efeitos colaterais, números em prosa ou cabeçalhos, mensagem ambígua com histórico, duplicação/concor­rência no webhook. Acrescentar casos à tarefa responsável e revisar a integração inteira ao final.

### Registro final
58 testes aprovados com PostgreSQL real. Teste externo Anthropic/Telegram e execução do Compose pendentes, conforme docs/verificacoes.md.

## Migração para Gemini — 27/09/2026

_Origem: `docs/projeto.md` (consolidado em 2026-11-09)._

### Decisão e escopo

O usuário autorizou substituir a Anthropic pelo Gemini para viabilizar o teste com cota gratuita. A proposta acadêmica original permanece intacta em PDF/DOCX; esta nota registra a mudança de implementação e sua justificativa de custo. As quatro camadas e as regras de segurança permanecem: Telegram, FastAPI, agente com duas tools e PostgreSQL 16.

Modelo padrão: `gemini-3.5-flash-lite`, configurável em GEMINI_MODEL. A documentação oficial lista entrada e saída gratuitas no Free Tier e recomenda essa família para projetos novos. A família 2.5 está restrita a usuários que já a utilizavam. A disponibilidade concreta e a cota dependem do projeto/chave; não foram presumidas nem verificadas sem credencial.

### Integração

- SDK oficial `google-genai`, cliente assíncrono `aio.models.generate_content`, API Gemini Developer (não Vertex AI).
- Planejador sem tools, saída JSON com schema explícito. Evidência do período e compatibilidade da métrica continuam validadas na aplicação antes de SQL.
- Executor declara exatamente `get_schema` e `execute_sql`. Automatic function calling do SDK desativado: a execução passa obrigatoriamente pelos validadores existentes.
- Respostas das tools usam `functionResponse` com nome e ID original quando fornecido. Chamadas paralelas recebem respostas correspondentes na mesma ordem.
- O conteúdo nativo do modelo, inclusive `thought_signature`, é preservado para as próximas chamadas; pensamentos não são exibidos ao gestor.
- As tentativas de autocorreção SQL, o timeout do turno e os limites de rounds continuam aplicados. O SDK faz uma tentativa por requisição, sem retries ocultos de cota e sem trocar o modelo automaticamente.
- Erros de chave/permissão, configuração, modelo indisponível, cota e indisponibilidade recebem mensagens PT-BR sem expor a resposta interna do provedor.
- A resposta final continua um identificador de resultado, renderizado com as células exatas pelo backend.

### Configuração e custo

Use GEMINI_API_KEY e GEMINI_MODEL; as antigas variáveis ANTHROPIC não são mais utilizadas. Chaves locais já existentes foram preservadas, mas não são enviadas ao novo provedor. O SDK Anthropic saiu das dependências do projeto.

Crie um projeto/chave no Google AI Studio e mantenha o projeto no **Free Tier**, sem ativar faturamento para este teste. O código não altera faturamento; se a chave pertencer a um projeto pago, as mesmas chamadas podem ser cobradas. Na cota gratuita, atingir limites produz erro e interrompe a consulta. A cota não é ilimitada e pode variar.

O Google informa que conteúdo no Free Tier pode ser usado para melhorar seus produtos. Envie apenas as perguntas e dados sintéticos deste projeto, sem informações reais de clientes ou credenciais em mensagens ao bot.

### Verificação

Testes usam o SDK oficial com transporte HTTP simulado. Cobrem declarações de tools, schema JSON do planejador, assinaturas opacas, chamadas paralelas, erros SQL, bloqueio de segurança e códigos HTTP de erro. A integração com Telegram também usa o SDK real com transporte simulado; PostgreSQL é real nos testes de integração.

O teste com a API Gemini e o Telegram reais ainda depende de configurar GEMINI_API_KEY, TELEGRAM_BOT_TOKEN e o usuário autorizado. Esta migração não inicia as avaliações acadêmicas da Fase 4.

### Fontes

- [SDK Python oficial](https://googleapis.github.io/python-genai/)
- [Preços e Free Tier](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite)
- [Disponibilidade e substituição de modelos](https://ai.google.dev/gemini-api/docs/deprecations)
- [Criação da chave](https://ai.google.dev/gemini-api/docs/get-started)
- [Function calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [Saídas estruturadas](https://ai.google.dev/gemini-api/docs/structured-output)

## Comandos em português e calendário relativo

_Origem: `docs/projeto.md` (consolidado em 2026-11-09)._

Alteração solicitada em 12/10/2026, posterior às versões de avaliação e apresentação já publicadas. Não altera gabaritos, dados, modelo de intenções ou resultados históricos.

### Comandos

`/comecar` e `/começar` digitados iniciam a mesma conversa de `/start`, com opções de métrica. `/ajuda` é alternativa de `/help`. O menu nativo Telegram usa nomes ASCII (`/comecar`, `/ajuda`, `/limpar`), pois nomes de BotCommand não admitem acento. O handler também aceita o texto digitado `/começar`.

### Datas relativas

A referência é a data atual em America/Sao_Paulo. O planejador continua escolhendo métrica, medida e tipo de análise; o backend resolve expressões relativas com evidência literal do usuário antes de consultar o banco e valida esses intervalos.

- “Esse/este ano”, “ano atual”, “neste ano”: 01/janeiro até hoje inclusive.
- “Ano passado/anterior”, “último ano”, sozinho: ano anterior completo.
- Mês nomeado com ano relativo, por exemplo “fevereiro desse ano”: mês inteiro do ano atual.
- “Fevereiro desse ano, compare com o ano passado”: fevereiro completo em ambos os anos, ano anterior como base.
- “Compare ano atual com ano anterior”: 01/janeiro até o mesmo mês/dia atual inclusive em ambos os anos; o ano anterior é a base. A resposta mostra os dois intervalos efetivos. Uma base explicitamente indicada é respeitada.

Inícios inclusivos e fins exclusivos; 29/fevereiro é ajustado para 28/fevereiro no ano não bissexto. Datas explícitas não são substituídas. Perguntas sem período/evidência continuam pedindo esclarecimento; não foi criado período padrão. Intervalos com vários meses permanecem tratados pelo contrato existente do plano, sem substituir por um mês arbitrário.

Na data da implementação, 12/10/2026: ano atual é 01/01/2026–12/10/2026; a comparação equivalente anterior é 01/01/2025–12/10/2025. A base comparativa continua sintética e pode conter períodos futuros; expressões anuais atuais não estendem a consulta até datas futuras.

### Verificação

68 checks selecionados passaram: calendário, dia bissexto/virada de ano, evidência inventada, datas explícitas, integração do planejador, comandos, contexto e apresentação. 26 checks PostgreSQL/e2e com APIs simuladas passaram; Ruff aprovado. Não foram repetidos treinamento, teste de classificação ou conjuntos reservados. Dois exemplos diretos de faturamento relativo foram usados para verificação do Gemini, com uma tentativa por requisição; evidências locais privadas não incluem envio proativo Telegram.

## Apresentação e opções no Telegram

_Origem: `docs/projeto.md` (consolidado em 2026-11-09)._

Alteração posterior ao congelamento `ed38382`, solicitada em 12/10/2026 após teste humano no bot.

Percentuais são exibidos com exatamente duas casas decimais e arredondamento decimal HALF_UP, incluindo variação, participação e taxa de resolução. Exemplo: 187,8237825408560075% → 187,82%. O arredondamento afeta somente texto, nunca células SQL, cálculos, referências, traces ou dados armazenados. NULL continua “não informado”; percentuais próximos de zero não exibem zero negativo.

Mensagens de resultado, ausência de registros, boas-vindas e limite de previsão não incluem mais o aviso sobre dados sintéticos. Essa natureza continua registrada nas definições e documentação da base; avisos sobre resultado parcial ou base não comparável foram preservados.

Esclarecimentos de métrica/medida oferecem teclado de opções Telegram (`ReplyKeyboardMarkup`), como Valor/Quantidade/Ambos, Horas previstas/Horas realizadas/Ambas e as medidas de chamados. O botão envia texto normal no mesmo chat, usando o histórico existente. O teclado é removido após resposta/limpeza. Perguntas de datas/períodos explícitos continuam com entrada de texto. Não usa enquete de votação, callback ou processamento de votos; mantém a validação existente de chat privado e IDs autorizados.

Verificação: 66 checks selecionados de apresentação, backend, agente/renderização e transporte simulado passaram; 26 checks de PostgreSQL/e2e com APIs simuladas passaram; Ruff aprovado. Nenhum teste de classificação, treinamento, reservado antigo ou gerencial real foi reexecutado. As métricas publicadas das versões congeladas permanecem atribuídas a essas versões.

## Dicionário de dados

_Origem: `docs/projeto.md` (consolidado em 2026-11-09)._

PostgreSQL 16, schema `public`. DDL e constraints: [schema.sql](../db/schema.sql).
**Domínio:** revenda de autopeças de porte pequeno a médio, que vende a oficinas, frotas e lojas. Os nomes de tabelas e colunas vêm da versão inicial (serviços de software) e foram mantidos por compatibilidade com o SQL, os testes e a avaliação; o significado de negócio é o da tabela abaixo.

| Nome no banco | Significado no negócio |
|---|---|
| `contratos` | Contratos de fornecimento. `sustentacao` = reposição recorrente de peças; `projeto` = fornecimento pontual por demanda |
| `pedidos` | Pedidos de venda de peças |
| `faturamento` | Notas fiscais |
| `indicadores_operacionais.horas_*` | Horas de atendimento (balcão e televendas) |
| `indicadores_operacionais.chamados_*` | Ocorrências de pós-venda: garantias, trocas e devoluções |

Todos os registros são fictícios. Não se gera CNPJ, telefone ou e-mail. Valores monetários são BRL, armazenados como `numeric`, sem ponto flutuante. Datas não têm horário. IDs inteiros são gerados pelo seeder, sem sequências.

### clientes
Um cliente (oficina, auto elétrica, funilaria, autocenter, frota, retífica ou loja) pode ter vários contratos.

| Campo | Tipo | Significado / restrição |
|---|---|---|
| id | integer | PK |
| nome | varchar(160) | Nome comercial fictício (ex.: Auto Mecânica Santa Cruz). Os perfis antigos usam o prefixo Empresa Fictícia |
| segmento | varchar(80) | Tipo de cliente: Oficina mecânica, Auto elétrica, Funilaria e pintura, Autocenter, Frota e transportadora, Loja de autopeças ou Retífica de motores (perfil autopecas) |
| cidade | varchar(100) | Município sintético |
| uf | char(2) | UF, duas letras maiúsculas |
| cadastrado_em | date | Data de cadastro; referência temporal de novos clientes |

### contratos
Contrato de fornecimento (reposição recorrente ou fornecimento pontual), pertencente a um cliente.

| Campo | Tipo | Significado / restrição |
|---|---|---|
| id | integer | PK |
| cliente_id | integer | FK clientes.id |
| descricao | varchar(200) | Objeto do fornecimento |
| modalidade | varchar(30) | projeto ou sustentacao |
| inicio | date | Início da vigência |
| fim | date | Fim inclusivo da vigência; não anterior ao início |
| valor_contratado | numeric(14,2) | Total previsto do contrato, estritamente positivo |
| status | varchar(20) | ativo, concluido ou cancelado |

### pedidos
Pedidos de venda gerados ao longo da vigência do contrato. No perfil original há um pedido por mês de cada contrato; no perfil autopecas a quantidade varia por cliente e mês.

| Campo | Tipo | Significado / restrição |
|---|---|---|
| id | integer | PK |
| contrato_id | integer | FK contratos.id |
| descricao | varchar(200) | Peças vendidas (ex.: Pastilhas e discos de freio) |
| data_pedido | date | Data da venda/aprovação do pedido |
| valor | numeric(14,2) | Valor do pedido, positivo |
| status | varchar(20) | aprovado, entregue ou cancelado |

### faturamento
Um pedido pode gerar vários documentos. A base padrão gera um documento por pedido não cancelado. Não há FK redundante para cliente/contrato: derivar pelo pedido evita vínculos contraditórios.

| Campo | Tipo | Significado / restrição |
|---|---|---|
| id | integer | PK |
| pedido_id | integer | FK pedidos.id |
| numero_documento | varchar(40) | Identificador único da nota (prefixo SINT, COMP ou NF, conforme o perfil) |
| emissao | date | Data de emissão, referência de faturamento |
| vencimento | date | Vencimento, não anterior à emissão |
| pagamento | date, nullable | Data efetiva do pagamento; não anterior à emissão |
| valor | numeric(14,2) | Valor faturado positivo |
| status | varchar(20) | aberta, paga ou cancelada; pagamento existe se e somente se paga |

### indicadores_operacionais
Uma medição por contrato/competência. Ocorrências de pós-venda (colunas `chamados_*`) são uma coorte aberta no mês: resolvidos se refere à mesma coorte, não ao estoque anterior.

| Campo | Tipo | Significado / restrição |
|---|---|---|
| id | integer | PK |
| contrato_id | integer | FK contratos.id |
| competencia | date | Primeiro dia do mês; UNIQUE com contrato_id |
| horas_previstas | numeric(10,2) | Horas de atendimento planejadas, positivas |
| horas_realizadas | numeric(10,2) | Horas de atendimento realizadas, não negativas; podem exceder a previsão |
| chamados_abertos | integer | Coorte de ocorrências de pós-venda abertas no mês, não negativa |
| chamados_resolvidos | integer | Entre zero e chamados_abertos |

Todos os campos são NOT NULL, exceto pagamento. PKs, FKs, checks locais e UNIQUE são garantidos pelo banco. Regras entre tabelas (pedido dentro da vigência, faturamento após pedido e totais até o contratado) são garantidas pelo gerador e verificadas pelo comando `bi-db validate`; não há triggers para essas regras. O agente não pode escrever dados.

### Definições de consulta

| Métrica | Data / filtro | Cálculo |
|---|---|---|
| Faturamento emitido | emissao; excluir cancelada | SUM(faturamento.valor) |
| Recebimentos | pagamento; status paga | SUM(faturamento.valor) |
| Valor de pedidos | data_pedido; excluir cancelado | SUM(pedidos.valor) |
| Quantidade de pedidos | data_pedido; excluir cancelado | COUNT(*) |
| Novos contratos | inicio | COUNT(*) ou SUM(valor_contratado), conforme pedido |
| Contratos vigentes | sobreposição da vigência com período | Solicitar intenção explícita; não confundir com novos contratos |
| Novos clientes | cadastrado_em | COUNT(*) |
| Horas | competencia | SUM(horas_previstas) ou SUM(horas_realizadas) |
| Taxa de resolução | competencia | SUM(chamados_resolvidos)::numeric / NULLIF(SUM(chamados_abertos),0) |

Intervalos de consulta são início inclusivo e fim exclusivo. A taxa é fração; multiplicar por cem em SQL se o usuário solicitar porcentagem. Arredondar em SQL somente quando solicitado. SUM sem registros resulta NULL; COUNT resulta zero. Não somar contratos depois de joins que multipliquem suas linhas. Agregar cada fato antes de combinar fatos diferentes.

### Base padrão e índices
**Perfil `autopecas` (recomendado para a apresentação):** `bi-db seed --profile autopecas --clients 100 --seed 42 --start-month 2025-01 --end-month 2026-10`. Cobre 22 meses com 100 clientes, cerca de 730 contratos, 7,7 mil pedidos e 8,1 mil notas. Escala de revenda pequena-média: em média R$ 350–410 mil e 320–360 pedidos por mês, ticket médio perto de R$ 1.100 (de R$ 60 a R$ 40 mil por pedido). Pedidos têm quantidade e valor variáveis por cliente e dia útil; notas têm prazo por segmento (15 a 45 dias), parcelamento ocasional, inadimplência pequena e pedidos `aprovado` só nos últimos dias do cenário. Em janeiro de 2025 os recebimentos são baixos porque o cenário não traz notas de dezembro de 2024. Nenhum nome de cliente contém "Empresa Fictícia".

Perfis anteriores (`original`, `original-v2`, `comparativo`, `comparativo-v2`) permanecem para reproduzir a avaliação congelada e o hash de `docs/projeto.md`. Neles: seed padrão 42, 30 clientes, contratos nos anos 2024/2025, cadastros em 2023; pagamentos podem avançar para 2026. Quantidades dependem de seed e versão do Faker; `requirements-lock.txt` registra o ambiente verificado. No perfil original, os pedidos mensais ficam entre cinco e trinta mil reais. A carga recusa tabelas previamente preenchidas, preservando dados existentes.

Índices: FKs de contratos/pedidos/faturamento; data_pedido, emissao, pagamento não nulo; vigência dos contratos; competencia e chave única (contrato_id, competencia).

## Base sintética para comparações de BI

_Origem: `docs/projeto.md` (consolidado em 2026-11-09)._

Perfil `comparativo-v1`, seed 42, **janeiro de 2025 a outubro de 2026**: 22 meses. Preparado em 11/10/2026 por solicitação do responsável. Outubro contém o mês inteiro como cenário sintético, inclusive datas posteriores à preparação. Não são dados observados nem projeções estimadas de uma empresa real. Status representam uma fotografia em **31/10/2026**.

### Conteúdo

| Entidade | Registros |
|---|---:|
| Clientes | 100 |
| Contratos | 681 |
| Pedidos | 5.100 |
| Documentos de faturamento | 5.809 |
| Indicadores operacionais | 1.700 |

Os 12 clientes da carteira inicial têm cadastro anterior ao período; os outros 88 se distribuem pelos 22 meses, com quatro novos clientes por mês. Há quatro segmentos e seis cidades, com UFs coerentes. A carteira combina sustentação recorrente e projetos. Contratos ativos têm término posterior à fotografia. Contratos concluídos e cancelados mantêm seus movimentos históricos.

Cada mês tem novos contratos nos três status, pedidos aprovados/entregues/cancelados, notas pagas/abertas/canceladas, recebimentos, horas e chamados. Cancelamento de um pedido não gera nota. Algumas notas parcelam o pedido, permitindo testar joins sem duplicar os valores. Notas canceladas não integram faturamento emitido ou recebimentos. O total faturado válido não supera o pedido, e pedidos válidos não superam o contrato.

Os valores variam por cliente, mês e entrega. Fatores explícitos de sazonalidade e um fator anual de cenário de 12% alteram os valores-base, junto de variação aleatória determinística. Crescimento de carteira também altera os totais. Essas regras criam um cenário para demonstração, sem sustentar conclusões econômicas sobre a Galvitech. Indicadores incluem situações com zero chamados, horas abaixo/acima do planejado e taxas diferentes entre meses.

[Resumo mensal](dados/base-comparativa-resumo.json) contém contagens, status, valores exatos e hash do conteúdo gerado. SHA256 do JSON canônico dos registros (UTF-8, `ensure_ascii=False`, `sort_keys=True`, `default=str`): `bbef709101afee9888a6232c2d5a5736b241384a9fed9a9eb468d1190a9ab30a`. Identidade depende também das versões das bibliotecas.

### Preparação em banco separado

O perfil `original` continua sendo o padrão e preserva a base usada na avaliação acadêmica. Não substitua o banco dos experimentos. A carga recusa bases preenchidas e não oferece reset automático.

Para Compose, prepare `.env.comparativo` a partir de `.env.example`, com senhas novas e URLs coerentes, `POSTGRES_DB=bi_comparativo` e porta livre, por exemplo `55440`. Não copie valores secretos para o Git ou chat. Use um projeto Compose separado:

```powershell
docker compose --env-file .env.comparativo -p pac-comparativo up -d --wait
python -m scripts.manage_db init --env-file .env.comparativo
python -m scripts.manage_db seed --profile comparativo --clients 100 --seed 42 --start-month 2025-01 --end-month 2026-10 --env-file .env.comparativo
python -m scripts.manage_db validate --env-file .env.comparativo
python -m scripts.manage_db coverage --env-file .env.comparativo
```

`coverage` acessa o banco em transação de leitura, confere as invariantes e exige todas as entidades/status e recebimentos em cada competência. Falta de mês ou status produz erro, sem publicar um resumo parcial como se fosse completo. O perfil exige pelo menos 34 clientes para esse período; 100 é o padrão do CLI quando `--profile comparativo` é informado. O intervalo configurável aceita de um a 24 meses.

Para consultar esta base no agente, a configuração do processo deve apontar `DATABASE_URL` para o novo banco com o login `readonly_agent`. As ferramentas do agente nunca usam a URL administrativa. Preserve a configuração anterior e os tokens existentes. Reinicie o backend com a nova configuração após conferir a carga; não execute dois pollings do mesmo bot. A geração não altera tokens, webhook ou processo Telegram automaticamente.

### Comparações úteis

- “Mostre o faturamento emitido por mês de janeiro de 2025 a outubro de 2026.”
- “Compare o faturamento de janeiro a outubro de 2025 com janeiro a outubro de 2026.”
- “Compare os recebimentos de agosto de 2025 e agosto de 2026.”
- “Mostre as horas previstas e realizadas por mês de janeiro de 2025 a outubro de 2026.”
- “Compare a taxa de resolução de chamados de janeiro a outubro de 2025 e de 2026.”
- “Qual o faturamento por segmento em setembro de 2026?”

Compare períodos equivalentes: 2025 tem 12 meses, 2026 somente dez. Perguntas anuais sem esse cuidado misturam coberturas. A taxa de resolução usa somas dos chamados, sem média simples dos percentuais de cada contrato.

### Separação das evidências

Os experimentos de 40 casos e suas taxas pertencem à base original de 2024/2025 e aos fontes congelados. Não são resultados desta nova base. A ampliação é uma versão posterior para exploração e apresentação. Uma nova avaliação semântica precisaria de novas perguntas reservadas, sem reutilizar a amostra anterior para ajustar o agente.
