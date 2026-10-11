# Desenvolvimento — 11/10/2026

Rodada real **interrompida em D08 por HTTP 400 do Gemini**, sem repetição automática.
D01–D07 tiveram respostas corretas; D08 não concluiu uma resposta; D09–D20 não foram
executados. Não há taxa oficial de execution accuracy ou clarification accuracy.
O teste reservado não foi executado com Gemini. Não houve mudança de produto,
prompts, conjunto, gabaritos, modelo, plano de cobrança ou processos do bot.

## Identificação e execução

- Commit executado: `8b11f2d9767caa3329b893e069930163c1830dd0`, sem alterações locais durante a rodada.
- Branch de evidências: `codex/experimento-desenvolvimento`; o commit de publicação
  do relatório é posterior à execução e não substitui o commit executado acima.
- Worktree isolado: `/workspace/pac_privado-desenvolvimento`.
- Rodada: `20261011T151909Z-5411e2fc`.
- Artefatos locais: `/workspace/pac_privado-desenvolvimento/.local/evaluation/20261011T151909Z-5411e2fc`. Manifesto, checkpoints, resumo e
  `database_after.json` foram preservados; seus hashes estão no JSON resumido.
- Manifesto criado em 2026-10-11T12:19:09.950842-03:00 (America/Sao_Paulo).
- Conjunto v1.0.0, SHA-256: `6a42eeb54169b15751eec3ff2e7657f52cdab96dc674dbaa7be16bc5c620bc2c`.
- Hash agregado da base: `d4f6623f1de2d8050ca3901b231ff00e05f1627bb09ecf8f7a7f0db86578cf6d`.
- Hash agregado dos fontes: `ef99187e3b872919ff4600c2cc9c0a9d74b12c890e715efa22111b3f3fcacd20`.
- Modelo configurado e resolvido informado pelo SDK: `gemini-3.5-flash-lite`.
  A resposta retorna esse identificador, sem uma versão imutável dos pesos.
- Python 3.12 e dependências reutilizados do ambiente original, sem reinstalação.
  Pacotes: google-genai 1.75.0, psycopg 3.3.6,
  pglast 7.18, Faker 39.1.0.
- Configuração original referenciada por `--env-file`, sem cópia nem exposição de valores.

Validação anterior: **107 testes passaram com PostgreSQL real, sem skips**, lint
`ruff check app scripts tests evaluation` aprovado; **34 referências SQL validadas**
sem chamadas ao Gemini. A validação técnica inclui referências de ambas as partições,
conforme o comando solicitado; isso não executa o teste reservado contra o agente real.

Comando da única rodada: `python -m scripts.evaluate run --live --split development
--interval 12 --limit 20`, com `--env-file` apontando à configuração original.
Limites: 100 linhas, 3000 ms por SQL,
6 rodadas de tools e 3 erros SQL por consulta.
Código de saída: **2**, motivo registrado: `provider_error_400`.

Os hashes agregados de base/fontes são SHA-256 do objeto correspondente do manifesto,
serializado com `evaluation.runner.dump` (JSON UTF-8, chaves ordenadas, indentação 2).
O hash do conjunto é calculado sobre os bytes integrais do arquivo congelado.

## Cobertura e resultados por caso

Há 20 casos planejados: 16 de resposta e quatro exclusivos de esclarecimento.
Foram registrados oito casos (40% de cobertura por checkpoints), com sete respostas
concluídas e uma falha de provedor. Nenhum caso exclusivo de esclarecimento foi
alcançado. A coluna de latência lista o tempo do agente por turno, em milissegundos.

| Caso | Resultado | Latência do agente (ms) | Chamadas ao SDK |
|---|---|---:|---:|
| D01 | Correto | 955.042 | 1 |
| D02 | Correto | 965.730 | 1 |
| D03 | Correto | 2653.805 | 4 |
| D04 | Correto | 2707.158 | 4 |
| D05 | Correto | 805.279 | 1 |
| D06 | Correto | 924.197 | 1 |
| D07 | Correto | 2699.869 | 4 |
| D08 | Falha de API (HTTP 400) | 6263.911 | 4 |
| D09 | Não executado | — | 0 |
| D10 | Não executado | — | 0 |
| D11 | Não executado | — | 0 |
| D12 | Não executado | — | 0 |
| D13 | Não executado | — | 0 |
| D14 | Não executado | — | 0 |
| D15 | Não executado | — | 0 |
| D16 | Não executado | — | 0 |
| D17 | Não executado | — | 0 |
| D18 | Não executado | — | 0 |
| D19 | Não executado | — | 0 |
| D20 | Não executado | — | 0 |

Execution accuracy: 16 planejados, oito registrados, sete aprovados; **taxa indisponível**.
Clarification accuracy: quatro planejados, zero executados; **taxa indisponível**.
Não calcular 7/8 como taxa oficial nem interpretar os não executados como respostas erradas.
A meta estritamente superior a 70% não pode ser avaliada nesta rodada incompleta.

## Latência e consumo observado

- Oito turnos observados, incluindo o turno interrompido por erro de API.
- Média: **2.247 s**; mediana: **1.810 s**.
- Mínimo: 0.805 s; máximo: 6.264 s.
- Média dos sete turnos aprovados: 1.673 s.
- **20 chamadas registradas ao SDK**, 19 com metadados de uso,
  uma interrompida por HTTP 400 sem metadados.
- Tokens reportados nas respostas disponíveis: **28169 de entrada**,
  **1009 de saída** e **29178 no total**.
  Uso da chamada rejeitada e tokens de raciocínio separados não foram informados;
  não imputar zero. Estes valores não demonstram custo ou faturamento.

A latência inclui agente, comunicação com Gemini e banco; exclui intervalo de 12 s,
transporte Telegram e tempo humano. Não comprova a meta ponta a ponta abaixo de 10 s.

## Diagnóstico de D08

Pergunta de desenvolvimento: Quais os cinco clientes com maior faturamento emitido em 2025? Mostre nome e valor, em ordem decrescente de valor; desempate pelo nome.

O planejamento identificou faturamento, medida valor, operação analysis e período
de 01/01/2025 até 01/01/2026 exclusivo. O agente executou a consulta abaixo e recebeu
o ranking correto. A quarta chamada do caso, posterior ao retorno do SQL, foi
rejeitada com HTTP 400. **Não há SQL nem resultado selecionado para renderização**.
O caso permanece reprovado: uma tentativa correta descartada não conta como resposta.

SQL da tentativa executada (não selecionada):

```sql
SELECT c.nome AS cliente, SUM(f.valor) AS total, COUNT(*) AS registros FROM faturamento f JOIN pedidos p ON f.pedido_id = p.id JOIN contratos co ON p.contrato_id = co.id JOIN clientes c ON co.cliente_id = c.id WHERE f.emissao >= DATE '2025-01-01' AND f.emissao < DATE '2026-01-01' AND f.status <> 'cancelada' GROUP BY c.id, c.nome ORDER BY total DESC, cliente ASC LIMIT 5
```

SQL de referência congelado, sem alteração:

```sql
SELECT c.nome AS cliente, SUM(f.valor) AS total FROM clientes c JOIN contratos ct ON ct.cliente_id=c.id JOIN pedidos p ON p.contrato_id=ct.id JOIN faturamento f ON f.pedido_id=p.id WHERE f.emissao >= DATE '2025-01-01' AND f.emissao < DATE '2026-01-01' AND f.status <> 'cancelada' GROUP BY c.id,c.nome ORDER BY total DESC, c.nome ASC LIMIT 5
```

Após validar/remover somente a coluna auxiliar `registros`, os resultados da tentativa
e da referência coincidem exatamente, inclusive ordem e valores. Os cinco resultados
abaixo são integralmente sintéticos; nomes e decimais foram copiados das células.

| Cliente sintético | Total (decimal sem arredondamento) |
|---|---:|
| Empresa Fictícia Oliveira | 801844.96 |
| Empresa Fictícia Sampaio Lima Ltda. | 513866.08 |
| Empresa Fictícia Carvalho Sousa S/A | 387629.16 |
| Empresa Fictícia Ferreira | 340894.20 |
| Empresa Fictícia Aparecida | 327730.92 |

A tentativa traz contagens auxiliares 35, 23, 22, 12 e 12. Não foi observada
divergência semântica entre resposta selecionada e gabarito em D01–D07. D08 é
classificado como erro de integração/provedor, não como SQL semanticamente incorreto.
O rastreamento conserva o código 400, mas não o corpo HTTP do erro; a causa detalhada
não pode ser afirmada. **Não é evidência de HTTP 429/cota, chave inválida ou indisponibilidade**.
Não houve nova tentativa, mudança de modelo ou correção de produto nesta rodada.

## Integridade e limitações

`database_after.json` registra `unchanged: true`, com hashes/contagens idênticos aos
do manifesto. Comparação adicional contra o baseline anterior à execução confirmou
a base completa inalterada. `.env` teve integridade conferida sem exibir seu hash ou
conteúdo; backend e polling mantiveram os mesmos processos e backend HTTP 200.

| Tabela | Registros | SHA-256 canônico |
|---|---:|---|
| clientes | 30 | `6ee90bee748166b6225042efcf5956992911a3b1d217d7050daf16f9017b476f` |
| contratos | 56 | `ae24e5d8a8a5318ec80334d10f7821a4b8b47b3a87a8fb33418e2a9ad4957989` |
| faturamento | 628 | `252c1257f6d83385527d1a78d45ab570665f8a71fbe952a9ba1443b125f8d9ec` |
| indicadores_operacionais | 672 | `ce385c40f8abec95d7e91d09af648e42d1079e9c3c9ec49d5c83090e2c5bf255` |
| pedidos | 672 | `c2dcec531aedb5cd685d8df5b5c3b78fabd7fe25d7b08aaae0f5bbf42af984da` |

Somente este relatório e o JSON resumido são publicados. Credenciais, logs HTTP,
checkpoints brutos, arquivos locais, banco e processos permanecem no ambiente de
origem. Prompts/gabaritos/fontes da versão executada permanecem congelados.

A rodada incompleta não valida a hipótese acadêmica, a meta de acurácia, os casos
não alcançados, a partição reservada ou generalização a dados reais. O diagnóstico
de D08 deve orientar uma revisão posterior da integração; uma nova rodada só deve
ser iniciada por autorização, com versão identificada e a rodada original preservada.
