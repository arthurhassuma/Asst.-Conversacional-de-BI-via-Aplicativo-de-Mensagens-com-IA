# Implantação na Oracle: respostas limpas e perfil autopecas (07/11/2026)

Registro da atualização da VM Oracle com o formato de respostas revisado, o vocabulário
de revenda de autopeças e o perfil de dados `autopecas`, em três rodadas na noite de
07/11/2026. Distingue o que foi observado do que foi apenas informado ou inferido, no
mesmo critério dos registros anteriores. Horários do Telegram são de Brasília (UTC-3);
os da VM estão em UTC, por isso o nome dos backups já marca 08/11.

## Origem do código

| Rodada | PR | Commit | Merge na `main` | Conteúdo |
|---|---|---|---|---|
| 1 | #8 | `6125efe` | `2ac4127` | Formato de respostas, vocabulário de autopeças, perfil `autopecas` |
| 2 | #11 | `35fe6d9` | `f193e94` | Taxa de resolução da pós-venda, resposta de valor único, total filtrado |
| 3 | #12 | `496fc7e` | `2974dad` | Substantivo repetido nos totais de ocorrências |

Mudanças documentadas no [README](../README.md) (seção do perfil `autopecas`), no
[dicionário de dados](dicionario-de-dados.md) e no [guia da Oracle](../deploy/oracle/README.md).

Verificação local antes de cada envio: 230, 232 e 234 testes aprovados, respectivamente,
com 28 ignorados (dependem de PostgreSQL, indisponível na máquina de desenvolvimento) e
`ruff check` limpo. A carga do perfil em PostgreSQL real só foi executada na VM.

## Rodada 1: respostas, vocabulário e perfil `autopecas`

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

### Defeito encontrado nesta rodada

Em setembro/2026 a base tinha 20 ocorrências abertas e 2 resolvidas (taxa de 10,00%).
Causa: `chamados_resolvidos = abertas × taxa // 100` arredondava para baixo e zerava quase
todas. O teste de ocorrências acima confirmou o valor errado no bot, o que provou que o
dataset era o do gerador. Dois outros desvios apareceram nos mesmos testes: "Faturamento
em Joinville" foi tratado como ranking e pediu um limite de itens, e "clientes novos"
saiu no formato antigo (`Medida: quantidade` e `• Quantidade: 1`).

## Rodada 2: reseed intermediário (sem efeito)

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

## Rodada 3: correções no ar

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

## Antes e depois (mesmas perguntas do teste de 05/11)

| Item | Antes | Depois |
|---|---|---|
| Pedidos em outubro | 295, R$ 2.401.621,96 | 386, R$ 483.850,40 |
| Ticket médio | cerca de R$ 8.100 | cerca de R$ 1.250 |
| Ranking (10 primeiros) | todos os clientes com 6 pedidos | de 7 a 15 pedidos |
| Nome do cliente | `11 — Empresa Fictícia 011 Sampaio Lima Ltda.` | `Centro Automotivo Itaum` |
| Duas medidas | cabeçalho e rótulo repetidos | `Valor:` e `Quantidade:` em linhas únicas |
| Taxa de resolução de setembro | 10,00% (defeito da rodada 1) | 65,00% (83% no período inteiro) |

## Limitações conhecidas

- Janeiro de 2025 tem recebimentos baixos: o cenário não traz notas de dezembro de 2024.
- Pedidos `aprovado` (ainda não entregues) existem só nos últimos dias de outubro de 2026.
- Consultas de SQL livre (por exemplo, filtro por cidade) mostram o valor sem `R$`: o texto
  não afirma a moeda de uma consulta que o modelo escreveu.
- Perfis anteriores, avaliação congelada, relatório entregue (PDF e Word) e experimentos
  antigos continuam no vocabulário de software.

## Reversão

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
  do PR #8; `git show 6125efe:<arquivo>` para o estado da rodada 1), reconstruir com
  `--no-cache` e recriar backend/polling.
- Guardar os backups até a apresentação.
