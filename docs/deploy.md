# Publicação e implantação

Publicação no GitHub e implantação na Oracle (entrega histórica, recuperação e rodadas com perfil de autopeças).

## Conteúdo

- [Publicação e nova verificação — 04/10/2026](#publicação-e-nova-verificação--04102026)
- [Hospedagem Oracle: entrega histórica e recuperação dos arquivos](#hospedagem-oracle-entrega-histórica-e-recuperação-dos-arquivos)
- [Implantação na Oracle: respostas limpas e perfil autopecas (07/11/2026)](#implantação-na-oracle-respostas-limpas-e-perfil-autopecas-07112026)

## Publicação e nova verificação — 04/10/2026

_Origem: `docs/deploy.md` (consolidado em 2026-11-09)._

### Origem e preservação

O projeto foi encontrado em `C:/Users/arthu/PAC - TCC`, com Git inicializado,
sem commits e sem remote. O destino `arthurhassuma/pac_privado` estava privado,
sem branches e sem conteúdo. Não havia trabalho remoto a sobrescrever.

Foram copiados 43 arquivos elegíveis pelo ignore original, incluindo código,
testes, documentação, proposta PDF e relatório DOCX. A cópia foi conferida por
SHA-256. Os 43 arquivos originais permaneceram inalterados. O ambiente virtual,
o `.env` e o banco original ficaram na pasta de origem.

O `.gitignore` foi ampliado para credenciais, variantes de `.env`, chaves privadas,
logs, bancos locais, backups e artefatos gerados. `.env.example` continua versionado.
Uma inspeção local procurou padrões de tokens/chaves e os segredos conhecidos do
`.env` original no material selecionado, incluindo XML do DOCX e streams
descompactáveis do PDF; não houve achados. Essa inspeção não substitui revisão
de novos arquivos antes de cada publicação.

### Evidências atuais

- 65 testes aprovados, sem skips, em Windows com Python 3.13.1 e PostgreSQL 16.
- Banco novo e isolado, seed 42, 30 clientes; o banco original não foi utilizado.
- Carga: 30 clientes, 56 contratos, 672 pedidos, 628 registros de faturamento,
  672 indicadores operacionais.
- As seis verificações de consistência retornaram zero problemas.
- `ruff check app scripts tests` passou; `pip check` não encontrou conflitos.
- O PostgreSQL temporário foi encerrado após os testes; arquivos locais ignorados
  foram preservados para retomada.
- A árvore publicada no commit de importação `68d55baf67729448aba1912742c7927b06662d35`
  coincide com a árvore local: `05f3617031142b61cecd6043ca73b71f1244e4e1`.

O registro em [Verificação da entrega — Fases 0–3](verificacoes.md#verificação-da-entrega--fases-03) descreve a primeira entrega, anterior à migração
Gemini. Não deve ser interpretado como a contagem atual nem como prova de API real.

### Integração contínua

O workflow `.github/workflows/tests.yml` prepara PostgreSQL 16 descartável,
instala as dependências fixadas, verifica consistência, executa lint e a suíte
completa. Usa APIs Gemini/Telegram simuladas e não necessita de chaves externas.
Senhas `ci_only_*` pertencem somente ao serviço efêmero de testes.

O resultado local acima não comprova execução do workflow no GitHub: consulte a
execução vinculada ao commit em [Actions](https://github.com/arthurhassuma/pac_privado/actions).
O workflow segue os exemplos oficiais de [serviços PostgreSQL](https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers),
[checkout](https://github.com/actions/checkout) e [setup-python](https://github.com/actions/setup-python).

### Limitações e próxima validação

Gemini e Telegram reais ainda não foram testados. A origem possui chave Gemini,
token Telegram e lista de usuários vazios. Configure esses valores apenas no
`.env` do checkout usado para executar o projeto. Não os envie em commits, issues
ou mensagens. Confirme o modelo disponível na conta antes do teste.

A execução do Docker Compose também permanece pendente. Os testes de integração
locais usaram PostgreSQL nativo. A avaliação semântica e a entrega acadêmica estão
organizadas no [roteiro até dezembro](apresentacao.md#roteiro-de-entrega-do-pac).

## Hospedagem Oracle: entrega histórica e recuperação dos arquivos

_Origem: `docs/deploy.md` (consolidado em 2026-11-09)._

### Conferência anterior à publicação, realizada em 02/11/2026

A consulta Git read-only ao origin confirmou main em
`a971546f25adbf996bfc1279637042125b6a4882`. Os cinco arquivos de runtime/Compose/
configuração não existem nessa árvore. Não há commit remoto desses arquivos
nessa main no momento da consulta. O commit a971546 é datado de 12/10 no Git;
13/10 é a data da preparação e implantação do pacote, não a data desse commit.

O ZIP enviado pelo usuário tem 123813 bytes e SHA256
`26e8b1987386c7d727f9e70ead7a67da5f89af1683b66bda74816537be08bd17`, idêntico ao
registro original. As 53 entradas do seu manifesto foram conferidas e os 43
arquivos já rastreados no repositório coincidem byte a byte com a main. Portanto
o pacote não contém uma versão diferente dos fontes do agente para substituir
os ajustes de 12/10; contém esses fontes e os complementos de hospedagem.

A recuperação inicial preservou e preparou os arquivos fora do checkout. Após
autorização do usuário, os nove arquivos desta entrega são versionados, sem
executar comandos na VM. Compose/configurador foram reorganizados em deploy/oracle,
com .gitignore para private/ e guia atualizado. Hashes dos cinco originais estão
em deploy/oracle/origem-recuperacao.json.

### Distinção entre as etapas

- 12/10: evolução gerencial, correção D38, UX, percentuais, comandos em português,
  opções de esclarecimento, datas relativas e comparação mensal. São fontes já
  incorporados à main mencionada; resultados congelados mantêm suas versões.
- 13/10: empacotamento, imagem Docker, Compose, configuração privada, preparação
  da VM e da base, transferência para um receptor e validação humana.

### Evidência histórica de implantação

Conforme capturas e confirmações nesta conversa: VM Oracle Ubuntu 24.04,
VM.Standard.E2.1.Micro indicada Always Free elegível, 1 OCPU/1 GB RAM, região
Vinhedo; Docker e Compose instalados. O usuário executou SSH/SCP e os comandos;
o agente não estabeleceu SSH direto na VM.

Imagem pac-bi-runtime:local construída com pip check. Projeto pac-bi-24h, banco
bi_comparativo separado e carga com seed 42, 100 clientes e 22 meses. Contagens observadas:
100/681/5100/5809/1700; seis critérios de validate com resultado zero.
Backend/banco saudáveis e autenticação Telegram observados. Após encerrar o
supervisor/polling antigos e bloquear reativação local, o novo polling foi ligado.
O usuário demonstrou /comecar, /limpar e consulta de faturamento e confirmou
continuidade depois de fechar o terminal, Docker enabled e restart unless-stopped.

Essas são evidências históricas, não verificação de saúde atual da VM em novembro.
Não houve medição de uptime de 24 h, reboot da VM, fatura, backup/restore ou SLA. Health
não testa cada dependência por consulta. Não foi observado coverage/fingerprint
completo pós-carga na VM; verificações isoladas anteriores não substituem isso.

### Pacote original e manifesto

O ZIP completo também contém README-INSTALACAO.md, verify-package.py,
source-manifest.json, SOURCE_COMMIT.txt e guias em .local/hospedagem. Eles descrevem
o layout e os hashes do release original. Não se devem colar esses hashes como
manifesto do novo layout GitHub: os caminhos foram reorganizados e a documentação
é nova. O ZIP original pode ser preservado como release histórico separado.

Não foram incluídos configurações privadas, valores secretos, IP, chave SSH,
dump de banco ou logs. Não houve nova chamada Gemini/Telegram, treinamento,
avaliação reservada ou alteração do servidor durante esta recuperação.

## Implantação na Oracle: respostas limpas e perfil autopecas (07/11/2026)

_Origem: `docs/deploy.md` (consolidado em 2026-11-09)._

Registro da atualização da VM Oracle com o formato de respostas revisado, o vocabulário
de revenda de autopeças e o perfil de dados `autopecas`, em cinco rodadas entre a noite de
07/11/2026 e a madrugada de 08/11/2026. Distingue o que foi observado do que foi apenas informado ou inferido, no
mesmo critério dos registros anteriores. Horários do Telegram são de Brasília (UTC-3);
os da VM estão em UTC, por isso o nome dos backups já marca 08/11.

### Origem do código

| Rodada | PR | Commit | Merge na `main` | Conteúdo |
|---|---|---|---|---|
| 1 | #8 | `6125efe` | `2ac4127` | Formato de respostas, vocabulário de autopeças, perfil `autopecas` |
| 2 e 3 | #11 | `35fe6d9` | `f193e94` | Taxa de resolução da pós-venda, resposta de valor único, total filtrado |
| 2 e 3 | #12 | `496fc7e` | `2974dad` | Substantivo repetido nos totais de ocorrências |
| 4 | #15 | `fb1f611` | `4a482ca` | Intervalos de datas e mês fixado na conversa |
| 4 | #16 | `46bfb7b` | `640f847` | Taxa de resolução em porcentagem; respostas agrupadas sem falha |
| 4 | #17 | `471b57a` | `0db3a33` | Escopo de CTE no filtro de SQL; polling que não trava |
| 5 | #19 | `f6df14a` | `ca2e83e` | Classificador de intenções v2 (autopeças), avaliado e ligado por padrão |
| 5 | #20 | `4292e39` | `8146065` | Entrypoint do container passa a respeitar `INTENT_CLASSIFIER_ENABLED` |

Mudanças documentadas no [README](../README.md) (seção do perfil `autopecas`), no
[dicionário de dados](projeto.md#dicionário-de-dados) e no [guia da Oracle](../deploy/oracle/README.md).

Verificação local antes de cada envio: 230, 232 e 234 testes aprovados nas rodadas 1 a 3
e 257 na `main` após os PRs #15 a #17 (241, 243 e 255 em cada PR), 265 após o #19 e 268 após o #20, com 28 ignorados (dependem de PostgreSQL, indisponível na máquina de desenvolvimento) e
`ruff check` limpo. A carga do perfil em PostgreSQL real só foi executada na VM.

### Rodada 1: respostas, vocabulário e perfil `autopecas`

A VM não é um clone git; a atualização seguiu o fluxo por `scp` do guia da Oracle.

1. `scp` de 13 arquivos: `app/` (8: `analysis_contract`, `bi_agent`, `database_tools`,
   `domain`, `managerial_rendering`, `messaging`, `prompts`, `rendering`), `scripts/` (4:
   `autopecas_seed`, `comparative_seed`, `manage_db`, `seed`) e `db/schema.sql`.
2. Reconstrução da imagem `pac-bi-runtime:local` com `--no-cache`: 17 de 17 etapas, 242 s,
   com `pip check` (observado).
3. Backup, parada de backend/polling, remoção do volume `pgdata`, `manage-db init` e
   `seed --profile autopecas --clients 100 --seed 42 --start-month 2025-01
   --end-month 2026-10`, validação e religação.

Os testes no Telegram desta rodada (23:17 a 23:26) deram, em todos os casos, exatamente o
valor que o gerador produz com a semente 42:

| Pergunta | Resposta observada |
|---|---|
| Pedidos de venda, "Ambos", setembro/2026 | `Valor: R$ 468.323,95` e `Quantidade: 385 pedidos` |
| Faturamento / recebimentos, setembro/2026 | R$ 458.603,80 / R$ 354.864,67 |
| Faturamento emitido versus recebimentos | diferença de R$ 103.739,13 e a nota sobre inadimplência |
| Faturamento ago/2026 versus ago/2025 | R$ 370.523,06 contra R$ 348.892,28: +R$ 21.630,78, 6,20% |
| Horas de atendimento, setembro/2026 | 1.457,00 h previstas, 1.511,41 h realizadas, desvio de 3,73% |
| Faturamento em 15/09/2026; pedidos em 16/09/2026 | R$ 19.417,00; 17 pedidos e R$ 19.005,40 |
| Faturamento de ontem (06/11/2026) | `Não encontrei registros para esses filtros.` |
| Pedidos de 08.12.2025 até 10.01.2026 | 342 pedidos, R$ 353.107,75 |
| Top 3 e distribuição por segmento, setembro/2026 | Peças Floresta R$ 23.439,00; Frota e transportadora 27,04% |
| Vendas em outubro (vaga), lucro, previsão | Esclarecimento, "sem dados de custos" e "sem modelo de previsão" |
| "Chamados" e "ocorrências" | Mesma resposta nas duas formas |

O total de outubro, R$ 483.850,40, coincide com o do gerador: o código antigo teria mostrado
`pedidos de serviços` e a base antiga tinha cerca de R$ 2,4 milhões no mês.

#### Defeito encontrado nesta rodada

Em setembro/2026 a base tinha 20 ocorrências abertas e 2 resolvidas (taxa de 10,00%).
Causa: `chamados_resolvidos = abertas × taxa // 100` arredondava para baixo e zerava quase
todas. O teste de ocorrências acima confirmou o valor errado no bot, o que provou que o
dataset era o do gerador. Dois outros desvios apareceram nos mesmos testes: "Faturamento
em Joinville" foi tratado como ranking e pediu um limite de itens, e "clientes novos"
saiu no formato antigo (`Medida: quantidade` e `• Quantidade: 1`).

### Rodada 2: reseed intermediário (sem efeito)

Foi feito um novo reseed esperando incluir a correção da taxa. Observado: a primeira
tentativa foi executada em `~`, fora de `~/pac_privado`, e falhou sem alterar nada
(`compose.yaml: no such file`, `volume is in use`). A segunda, dentro de `~/pac_privado`,
concluiu: backup `-2` de 1,2 MB, volume recriado, `init`, `seed`, `validate` com todos os
contadores em zero, `coverage`, `/health` e polling no ar.

Porém a imagem ainda tinha o código da rodada 1: a saída do `coverage` mostrava
`chamados_resolvidos: 2` em setembro/2026, e o Telegram (23:37 a 23:39) ainda perguntava
o ranking de Joinville e mostrava `Medida: quantidade`. A base ficou idêntica à anterior.
Lição registrada: o `manage-db` roda de dentro da imagem, então o `scp` e o `docker build`
precisam vir **antes** do reseed, e vale conferir com
`docker run --rm --entrypoint grep pac-bi-runtime:local -c "resolver = Random" scripts/autopecas_seed.py`.

### Rodada 3: correções no ar

Arquivos enviados conforme as instruções: `app/prompts.py`, `app/rendering.py`,
`app/managerial_rendering.py` e `scripts/autopecas_seed.py`, seguidos de reconstrução da
imagem e novo reseed. A saída do terminal desta rodada não foi vista pelo agente; a
evidência é o Telegram (23:50 e 23:51):

| Pergunta | Antes | Depois (observado) |
|---|---|---|
| Faturamento em Joinville, setembro/2026 | Pergunta de ranking | `Valor: 147.135,20`, direto |
| Quantos clientes novos em outubro/2026? | `Medida: quantidade` e `• Quantidade: 1` | `Quantidade: 1` |
| "Chamados" abertos, resolvidos, saldo e taxa, setembro/2026 | 20, 2, 18, 10,00% | 20, 13, 7, 65,00% |

O que ficou sem confirmação visual: a remoção do substantivo repetido (`Ocorrências
abertas: 20` em vez de `20 ocorrências`), validada apenas por teste automatizado, e o
`/health` desta rodada.

### Rodada 4: correções do ultrareview do repositório inteiro

Um ultrareview do código-fonte completo (PR descartável #14, fechado sem mesclar; 50
arquivos, sem `tests/`) apontou 10 achados. Todos foram reproduzidos antes de corrigir; nenhum
era falso positivo, e um era defeito introduzido nesta mesma sessão (o limite de 12 mil
caracteres no agrupamento de medidas). Seis foram corrigidos nos PRs #15 a #17:

| Achado | Correção |
|---|---|
| Intervalo com `hoje`, `ontem` ou data numérica virava um dia só, sem aviso | Só uma expressão de dia isolada é resolvida; intervalos mantêm o período |
| "Compara com o ano passado" depois de fixar um mês comparava o ano inteiro | O mês vem do outro período da comparação, validado contra o que o gestor digitou |
| Taxa de resolução em total saía com 20 casas decimais | Consulta em pontos percentuais e unidade `percentual`: `85,71%` |
| Pergunta com várias medidas falhava se o texto junto passasse de 12 mil caracteres | Cai para as respostas separadas |
| CTE podia ler `pg_roles` e outras relações do catálogo pelo próprio nome | Cada corpo enxerga só o escopo externo e os CTEs anteriores |
| Um update recusado (400, 413, 422) travava o polling para todos | Ignorado com log; 401/403, 429, 5xx e rede continuam em nova tentativa |

Ficaram de fora, por serem menores: `EXTRACT` na lista permitida mas nunca aceito, fila de
sessões (4 mensagens seguidas de um gestor ocupam os 4 trabalhadores), `get_schema` chamado só
para checar erro e o seed `comparativo-v2` legado (6 de 5.892 notas com pagamento antes da
emissão; o `autopecas` tem 0).

Arquivos enviados por `scp` (6, todos em `app/`): `analysis_contract`, `bi_agent`,
`query_templates`, `relative_periods`, `sql_policy`, `telegram_bot`, seguidos de reconstrução da
imagem e recriação de backend e polling, sem reseed. A saída do terminal desta rodada não foi
vista pelo agente. Evidência no Telegram (00:37 a 00:39), conferida com o gerador de dados:

| Pergunta | Resposta observada |
|---|---|
| Faturamento de 01/09/2026 a 15/09/2026 | Período `01/09/2026 a 15/09/2026` (antes: um dia só); `Valor: 240.102,20` |
| Contratos em agosto de 2026, "ambos" | `Valor: R$ 85.830,45` e `Quantidade: 27 contratos` |
| "Compara com o ano passado" na sequência | Base `01/08/2025 a 31/08/2025` contra `01/08/2026 a 31/08/2026`; valor R$ 121.032,03 contra R$ 85.830,45 (-29,08%), quantidade 29 contra 27 (-6,90%) |
| Taxa de resolução das ocorrências, setembro/2026 | `Taxa de resolução: 65,00%` (antes: razão bruta) |
| Pedidos de venda em setembro/2026, valor e quantidade | `R$ 468.323,95` e `385 pedidos`, sem regressão |
| Faturamento de janeiro até hoje | Período `01/01/2026 a 08/11/2026`, `R$ 4.010.237,73` |

A previsão de que "janeiro até hoje" passaria a pedir o período não se confirmou: o Gemini
devolveu uma evidência que o validador aceitou e a resposta veio correta, com o intervalo
inteiro. O caso vago continua protegido por teste automatizado.

Sem confirmação visual (não aparecem pelo Telegram, só por teste automatizado): o bloqueio do
CTE sobre o catálogo e o descarte de update recusado no polling.

### Rodada 5: classificador de intenções v2 em uso

O treinamento supervisionado v2, em vocabulário de autopeças, está descrito em
[treinamento de intenções v2](avaliacao.md#treinamento-supervisionado-de-intenções--versão-2-revenda-de-autopeças): teste reservado com acurácia de 87,9%,
cobertura de 80,8% e precisão de 95,0% nas sugestões aceitas, critério declarado antes do treino e
atingido. Ele só sugere até dois exemplos ao planejador do Gemini; o ganho nas respostas **não foi
medido**.

Primeira tentativa (PR #19). Arquivos enviados por `scp`: `app/bi_agent.py`, `app/config.py`,
`app/main.py`, `training/` (modelo, corpus, protocolo, gerador e `fit.py`), `scripts/train_intents.py` e
`pyproject.toml`. Observado: os `grep` de conferência retornaram 1, os dois arquivos do modelo estavam
dentro da imagem (build de 17 etapas, 225 s) e o `sed` gravou `INTENT_CLASSIFIER_ENABLED=true` no
arquivo privado (`grep -c` igual a 1). O `/health` respondeu. **Mas a linha de log `intencao` não
apareceu**, ou seja, o classificador não estava em uso. Uma segunda causa de confusão: o comando de
conferência foi colado no chat do Telegram, e o bot o tratou como pergunta.

Causa: o `runtime_entrypoint.py` original forçava `intent_classifier_enabled=False` em todos os modos
de aplicação e exportava o valor, ignorando o arquivo privado. A instrução com `sed` nunca poderia ter
efeito, falha de quem a escreveu sem ler esse arquivo. Correção no PR #20: a linha foi removida (as
credenciais administrativas continuam removidas), a mudança foi registrada em
`deploy/oracle/origem-recuperacao.json` com o hash do original e há testes que falham sem a correção.

Segunda tentativa. Enviado `runtime_entrypoint.py`, imagem reconstruída com `--no-cache` e backend e
polling recriados. Evidência observada no terminal, depois da pergunta "Top 3 clientes por
faturamento em setembro de 2026" enviada no Telegram às 01:31:

```
backend-1  | INFO:app.bi_agent:intencao rotulo=ranking confianca=0.99 aceita=True
```

A resposta do bot foi a de antes (Peças Floresta, R$ 23.439,00), como esperado: o classificador não
escolhe métrica, período, SQL nem números. Sem confirmação visual: a saída de
`printenv INTENT_CLASSIFIER_ENABLED` e a linha com abstenção para uma pergunta vaga
(`aceita=False`); só uma pergunta foi verificada no log.

Para desligar sem rebuild: trocar `true` por `false` no arquivo privado e recriar o backend (agora tem
efeito, depois da correção do entrypoint).

### Rodada 6: estado durável (09/11/2026)

Objetivo: eliminar a perda de updates aceitos e a repetição de respostas após reinício, e permitir
mais de um worker. O código está no commit `7298341` (PR desta rodada); a descrição técnica está em
[projeto.md](projeto.md#estado-durável-da-execução-09112026).

**Execução (conferida por capturas de tela do responsável, por volta das 18:14 de 09/11/2026):**

1. Envio por `scp` de `app/config.py`, `app/main.py`, `app/state.py`, `scripts/manage_db.py`,
   `db/estado.sql` e `runtime_entrypoint.py`, e reconstrução da imagem com `--no-cache`.
2. `STATE_PASSWORD` gravada em `setup.env` e `STATE_DATABASE_URL` em `application.env`, uma linha em
   cada arquivo (contagem com `grep -c`, sem exibir os valores).
3. `manage-db init-state`: `{"status": "Estado durável (schema estado e role app_estado) pronto."}`.
4. Recriação de `backend` e `polling`: containers saudáveis e `/health` com `"estado_duravel":true`.

**Verificação na VM (observada):**

- Conversa real no Telegram: esclarecimento de período, `setembro de 2026` (R$ 458.603,80),
  `/limpar`, pedidos com esclarecimento de medida e continuação (`e de setembro`: R$ 468.323,95 e
  385 pedidos).
- `SELECT status, count(*) FROM estado.updates GROUP BY 1`: 7 linhas `concluido` e nenhuma
  `pendente` ou `processando`, uma por mensagem enviada.
- `docker compose restart backend` com o log mostrando encerramento e início limpos; um update
  recebido logo depois foi processado normalmente.
- Após o reinício, a pergunta de continuação `e de outubro` foi respondida pelo bot (relato do
  responsável, sem captura de tela), compatível com o histórico da conversa ter sobrevivido ao
  reinício.

**Não verificado nesta rodada:** mais de um worker (`BACKEND_WORKERS` ficou em 1); a perda real de um
update durante uma queda não foi provocada na VM (coberta apenas pelos testes com PostgreSQL local);
o backup do passo 1 do guia deve ser conferido com `ls ~/backup-estado-*.sql`, e esta documentação
não o verificou. A entrega continua *pelo menos uma vez*: uma queda entre enviar a resposta e concluir
o update pode repetir a resposta.

**Reversão:** remover a linha `STATE_DATABASE_URL` de `application.env` e recriar `backend polling`
volta ao modo em memória; as tabelas do schema `estado` ficam inertes. Para o código anterior,
`git show bc9dab7:<arquivo>` e reconstruir com `--no-cache`.

### Antes e depois (mesmas perguntas do teste de 05/11)

| Item | Antes | Depois |
|---|---|---|
| Pedidos em outubro | 295, R$ 2.401.621,96 | 386, R$ 483.850,40 |
| Ticket médio | cerca de R$ 8.100 | cerca de R$ 1.250 |
| Ranking (10 primeiros) | todos os clientes com 6 pedidos | de 7 a 15 pedidos |
| Nome do cliente | `11 — Empresa Fictícia 011 Sampaio Lima Ltda.` | `Centro Automotivo Itaum` |
| Duas medidas | cabeçalho e rótulo repetidos | `Valor:` e `Quantidade:` em linhas únicas |
| Taxa de resolução de setembro | 10,00% (defeito da rodada 1) | 65,00% (83% no período inteiro) |

### Limitações conhecidas

- Janeiro de 2025 tem recebimentos baixos: o cenário não traz notas de dezembro de 2024.
- Pedidos `aprovado` (ainda não entregues) existem só nos últimos dias de outubro de 2026.
- Consultas de SQL livre (por exemplo, filtro por cidade) mostram o valor sem `R$`: o texto
  não afirma a moeda de uma consulta que o modelo escreveu. A mesma pergunta pode seguir o
  caminho livre ou o controlado conforme o planejador: "Faturamento de 01/09/2026 a
  15/09/2026" saiu como `Valor: 240.102,20`, enquanto "até hoje" saiu com `R$`. Os números
  estão corretos nos dois; só o formato difere.
- O classificador v2 não teve o efeito nas respostas medido; o teste que o aprovou é sintético, e a
  checagem informal com 22 perguntas reais deu 77% de acerto. A classe operacional é a mais frágil.
- Perfis anteriores, avaliação congelada, relatório entregue (PDF e Word), experimentos antigos e o
  classificador v1 continuam no vocabulário de software.

### Reversão

- Dados, na VM (`ls ~/backup-pgdata-*.sql` para conferir):
  - `backup-pgdata-20261108.sql` (819 KB, 01:53 UTC): estado anterior à primeira carga
    `autopecas`, isto é, a base antiga de serviços de software (conteúdo inferido pela
    ordem das operações e pelo tamanho menor).
  - `backup-pgdata-20261108-2.sql` (1,2 MB, 02:34 UTC): base `autopecas` com a taxa de
    resolução defeituosa.
  - `backup-pgdata-20261108-0246.sql` (1,2 MB, 02:47 UTC): base `autopecas` ainda com a
    taxa de resolução defeituosa, feito imediatamente antes do reseed da rodada 3. É o
    ponto de retorno mais recente.
  - Os três nomes, tamanhos e horários foram conferidos com `ls -lh` na VM (observado).
  - Restaurar num banco novo, conforme o guia da Oracle.
- Código: reenviar os arquivos de um commit anterior (`git show 3e43545:<arquivo>` para antes
  do PR #8; `git show 6125efe:<arquivo>` para o estado da rodada 1; `git show 2974dad:<arquivo>`
  para o estado anterior à rodada 4; `git show 778b45d:<arquivo>` para o anterior à rodada 5),
  reconstruir com `--no-cache` e recriar backend/polling.
- Guardar os backups até a apresentação.
- Para a rodada 6 (estado durável) valem as instruções de reversão da própria seção.
