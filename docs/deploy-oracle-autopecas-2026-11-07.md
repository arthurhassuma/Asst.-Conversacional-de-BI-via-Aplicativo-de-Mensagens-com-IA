# Implantação na Oracle: respostas limpas e perfil autopecas (07/11/2026)

Registro da atualização da VM Oracle com o formato de respostas revisado, o vocabulário
de revenda de autopeças e o perfil de dados `autopecas`. Distingue o que foi observado
do que foi apenas informado, no mesmo critério dos registros anteriores.

## Origem

- Código: PR #8 (`feat/autopecas-e-respostas-limpas`), commit `6125efe`, mesclado na `main`
  como `2ac4127` em 08/11/2026 01:05 UTC (07/11 à noite no horário de Brasília).
- Mudanças: [README](../README.md) (seção do perfil `autopecas`), [dicionário de
  dados](dicionario-de-dados.md) e [guia da Oracle](../deploy/oracle/README.md).
- Verificação local antes do envio: 230 testes aprovados e 28 ignorados (dependem de
  PostgreSQL, indisponível na máquina de desenvolvimento) e `ruff check` limpo. A carga
  do perfil em PostgreSQL real e os testes `skipped` não foram executados localmente.

## O que foi feito na VM

A VM não é um clone git; a atualização seguiu o fluxo por `scp` do guia da Oracle.

1. Envio por `scp` de 13 arquivos: `app/` (8: `analysis_contract`, `bi_agent`,
   `database_tools`, `domain`, `managerial_rendering`, `messaging`, `prompts`,
   `rendering`), `scripts/` (4: `autopecas_seed`, `comparative_seed`, `manage_db`, `seed`)
   e `db/schema.sql`. `app/domain.py` e `scripts/autopecas_seed.py` são novos.
2. Reconstrução da imagem com `--no-cache`.
3. Troca da base: backup, parada de backend/polling, remoção do volume `pgdata`,
   `manage-db init` e `seed --profile autopecas --clients 100 --seed 42
   --start-month 2025-01 --end-month 2026-10`, validação e religação.

## Evidência

Observado em capturas de tela desta conversa:

- Build da imagem `pac-bi-runtime:local` concluído, 17 de 17 etapas, 242 s, com
  `pip check` e `COPY` de `app`, `scripts` e `db`.
- No Telegram, `/limpar` e `/comecar` responderam e as perguntas abaixo foram respondidas
  com o formato novo:

| Pergunta (período: mês passado inteiro, 01/10/2026 a 31/10/2026) | Resposta |
|---|---|
| Clientes | `Quantidade: 1 cliente` |
| Quantos pedidos cada um gerou? | Ranking numerado, líder com 15 pedidos, 10 itens |
| Qual o valor dos pedidos? | `Valor: R$ 483.850,40` |
| Separados por cliente | Ranking por valor, líder R$ 32.335,35 |

- O total de R$ 483.850,40 é idêntico ao que o gerador produz para outubro de 2026 com
  a semente 42. Isso confirma, de forma indireta, que o código novo **e** a base nova
  estão em uso: o código antigo mostraria `Resumo de pedidos de serviços` e a base antiga
  tinha cerca de R$ 2,4 milhões no mês.

Não vistos pelo agente, apenas informados ou inferidos pela resposta do bot: saída dos
`scp`, tamanho do backup, resultados de `validate` e `coverage --profile autopecas`,
`/health` e início do polling. O número de linhas carregadas não foi lido da VM. O
gerador produz 100 clientes, 733 contratos, 7.754 pedidos, 8.151 notas e 2.451
indicadores com esses parâmetros.

## Antes e depois (mesmas perguntas do teste de 05/11)

| Item | Antes | Depois |
|---|---|---|
| Pedidos no mês | 295, R$ 2.401.621,96 | 386 (valor do gerador), R$ 483.850,40 (observado) |
| Ticket médio | cerca de R$ 8.100 | cerca de R$ 1.250 |
| Ranking (10 primeiros) | todos os clientes com 6 pedidos | de 7 a 15 pedidos |
| Nome do cliente | `11 — Empresa Fictícia 011 Sampaio Lima Ltda.` | `Centro Automotivo Itaum` |
| Duas medidas | cabeçalho e rótulo repetidos | `Valor:` e `Quantidade:` em linhas únicas |

## Pendências de teste real

Casos ainda não conferidos no Telegram com o Gemini e o prompt novo; registrar o
resultado aqui quando executados:

- "Ambos" em pedidos (linhas `Valor:` e `Quantidade:` sem repetição).
- Ocorrências de pós-venda (abertas, resolvidas, taxa), também com a palavra "chamados".
- Horas de atendimento previstas e realizadas por contrato.
- Comparação de períodos e dia exato (ontem, data por extenso).
- Pergunta vaga ("como foram as vendas?") deve pedir esclarecimento.

## Limitações conhecidas do perfil

- Janeiro de 2025 tem recebimentos baixos: o cenário não traz notas de dezembro de 2024.
- Pedidos `aprovado` (ainda não entregues) existem só nos últimos dias de outubro de 2026.
- Perfis anteriores, avaliação congelada, relatório entregue (PDF e Word) e experimentos
  antigos continuam no vocabulário de software.

## Reversão

- Dados: restaurar o backup gerado na troca, de 07/11/2026, `~/backup-pgdata-20261107.sql`,
  num banco novo, conforme o guia da Oracle. O nome usa o `date` da VM, que está em UTC e
  já marcava 08/11 no início da sessão (01:43); se `20261107` não existir, o arquivo é
  `~/backup-pgdata-20261108.sql`. Confirme com `ls ~/backup-pgdata-*.sql`.
- Código: reenviar os arquivos da `main` anterior (`git show 3e43545:<arquivo>`),
  reconstruir com `--no-cache` e recriar backend/polling.
- Guardar o backup até concluir os testes pendentes.
