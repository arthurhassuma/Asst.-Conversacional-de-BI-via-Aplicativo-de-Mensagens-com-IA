# Desenvolvimento gerencial real — 12/10/2026

Rodada completa, 24/25 casos registrados aprovados; 25 planejados. Exit code `0`, stop_reason `null`. Nenhuma repetição de rodada ou caso, correção de produto, teste gerencial reservado, treinamento ou teste de classificação foi executado.

## Identificação

- Fontes: `1cc91970c242267c4c1e88db72ece3a7ed844c11`, checkout isolado `/workspace/pac_privado-gerencial`, branch `codex/gerencial-verificacao`. Checkout limpo no início; somente este relatório é publicado.
- Rodada `20261012T193635Z-d9656c6a`, artefatos locais ignorados `/workspace/pac_privado-gerencial/.local/evaluation/20261012T193635Z-d9656c6a`. Início 2026-10-12T16:36:35.542381-03:00.
- Conjunto `managerial-v1`, `evaluation/managerial-cases-v1.json`, SHA256 `cdb71fa885cd2f66e1251dbe5717b133a8079afa132592f2a5c5b7765c9da863`.
- Hash agregado dos fontes `225d69d316a15ed84fae9dd188f628cb9b5e819865ae33ca4e8f1b95892fcdf5`; base comparativa `dfdc635ddc05e8fbda1cbe2b132c3b505bb5fb29dfd50b95106e086a29e03725`. Agregados são SHA256 de `evaluation.runner.dump` UTF-8.
- Banco `bi_comparativo`, role `readonly_agent`; 100 clientes, seed 42, 22 meses janeiro/2025 a outubro/2026. Snapshot conferido contra a preparação comparativa; não foi usada a base acadêmica antiga.
- Modelo configurado `gemini-3.5-flash-lite`; resolvidos pelo SDK `gemini-3.5-flash-lite`. Alias sem identificação imutável de pesos.
- `INTENT_CLASSIFIER_ENABLED=false`. Artefatos/corpus JSON fazem parte dos hashes de fontes no manifesto. Nenhuma alegação de benefício causal do classificador; nenhuma rodada on/off duplicada.
- Limites: 100 linhas, timeout SQL 3000 ms, 6 rodadas de tools, 3 erros SQL; intervalo entre turnos 60 s e limite 25 casos. Uma tentativa SDK por requisição, sem fallback/modelo/cobrança alterados.

Comando executado uma vez em processo background, com log privado `.local/gerencial-development.log` e estado `.local/gerencial-job.json`:

```sh
python -m scripts.evaluate run --live --dataset evaluation/managerial-cases-v1.json --split development --interval 60 --limit 25 --env-file .local/gerencial.env
```

Configuração `.local/gerencial.env` privada (0600), combinando chave/modelo existentes e DSN readonly comparativo, sem token Telegram. Antes da API: 23 checks gerenciais selecionados passaram em 1,89 s com PostgreSQL; lint de app/scripts/tests/evaluation/training aprovado; `evaluate validate` executou 28 referências SQL sem Gemini. Não foi rodada a suíte completa, nem instalado/reexecutado treinamento ou avaliação da classificação. A validação SQL inclui referências do novo reservado, conforme o comando autorizado, mas não executa esses casos contra o agente.

## Resultados por caso

| Caso | Resultado | Agente por turno (ms) | Requisições SDK |
|---|---|---:|---:|
| D21 | correto | 1526.897 | 1 |
| D22 | correto | 1356.552 | 1 |
| D23 | correto | 1467.054 | 1 |
| D24 | correto | 1502.837 | 1 |
| D25 | correto | 1398.146 | 1 |
| D26 | correto | 1609.499 | 1 |
| D27 | correto | 1234.948 | 1 |
| D28 | correto | 1468.027 | 1 |
| D29 | correto | 1563.656 | 1 |
| D30 | correto | 1394.380 | 1 |
| D31 | correto | 1221.288 | 1 |
| D32 | correto | 1284.631 | 1 |
| D33 | correto | 1433.787 | 1 |
| D34 | correto | 1359.512 | 1 |
| D35 | correto | 1368.699 | 1 |
| D36 | correto | 1391.470 | 1 |
| D37 | correto | 1275.692 | 1 |
| D38 | clarification_measure | 1190.563 | 1 |
| D39 | correto | 1611.969 | 1 |
| D40 | correto | 3192.750 | 4 |
| D41 | correto | 1234.440 | 1 |
| D42 | correto | 1077.837 | 1 |
| D43 | correto | 978.870 | 1 |
| D44 | correto | 1590.158 | 1 |
| D45 | correto | 1075.810 | 1 |

- clarification_accuracy: 2 aprovados / 2 planejados, 2 registrados; taxa 100.00%.
- execution_accuracy: 19 aprovados / 20 planejados, 20 registrados; taxa 95.00%.
- unsupported_accuracy: 3 aprovados / 3 planejados, 3 registrados; taxa 100.00%.

Os resultados e taxas foram recalculados dos checkpoints com o scorer desta versão. Contrato exige formas explícitas, identificadores, ranking e direção quando definidos; decimal exato e ordem estável. A taxa é do sistema híbrido completo, não apenas SQL livre ou classificador.

## Latência e consumo

25 turnos; média agente+banco 1.432 s, mediana 1.391 s, mínimo 0.979 s, máximo 3.193 s. Inclui provedor, compilação, renderização e banco; exclui intervalo e transporte Telegram. Não comprova SLA ponta a ponta.

28 requisições SDK registradas; 28 com consumo informado, 0 sem consumo. Tokens conhecidos: entrada 55967, saída 3741, total 59708. Uso ausente não imputado como zero; sem estimativa de custo.

## Falhas e resultados selecionados

D38 é falha de planejamento/esclarecimento indevido: o plano retornou measure=null e foi recusado antes de consultar SQL. Não decorre de zeros monetários escalados ou do formato do gabarito, pois nenhum resultado foi produzido para comparar.

### D38, turno 1

Pergunta: Mostre chamados abertos, resolvidos, saldo e taxa de resolução em maio de 2026.

Status `clarification_measure`, código `null`, categoria segura `null`.

Esperado `answer`; resposta visível observada: 💬 Para chamados operacionais, deseja chamados abertos, resolvidos ou a taxa de resolução?

Plano global observado:

```json
{
  "queries": [
    {
      "analysis": {
        "custom_filters": false,
        "detail": "chamados",
        "group_by": "nenhum",
        "kind": "operacional",
        "limit": null
      },
      "measure": null,
      "metric": "chamados",
      "operation": "analysis",
      "period": {
        "end": "2026-06-01",
        "evidence": "maio de 2026",
        "start": "2026-05-01"
      }
    }
  ],
  "unsupported_reason": null
}
```

Nenhuma consulta ou resultado selecionado; não houve SQL executado neste turno.

Referência congelada (chamados):

```sql
SELECT 'Total'::text,SUM(chamados_abertos),SUM(chamados_resolvidos),SUM(chamados_abertos)-SUM(chamados_resolvidos),SUM(chamados_resolvidos)::numeric*100/NULLIF(SUM(chamados_abertos),0) FROM indicadores_operacionais WHERE competencia >= DATE '2026-05-01' AND competencia < DATE '2026-06-01'
```

Resultado esperado sintético:

```json
{
  "columns": [
    "text",
    "sum",
    "sum",
    "?column?",
    "?column?"
  ],
  "rows": [
    [
      "Total",
      3334,
      2883,
      451,
      "86.4727054589082184"
    ]
  ],
  "truncated": false
}
```

## Preservação e limites

`database_after.unchanged=true`; hashes/contagens iguais ao snapshot inicial. Bot comparativo manteve os mesmos processos/configuração, sem restart ou mensagem proativa. Base e fontes `59c9eb8`, `.env` original e evidências acadêmicas preservados. Nenhum teste gerencial reservado foi executado; aguardará revisão/congelamento separado. A autorização condicional posterior exigia 25/25 aprovados para reservado/deploy; D38 impede essa continuação. A revisão `85ac8eb` mencionada pelo coordenador não foi aplicada durante esta rodada, e o bot não foi atualizado. Nenhum ganho é atribuído ao classificador. Os resultados desta base/versão não se misturam às métricas acadêmicas antigas. Outubro completo é cenário futuro sintético, status 31/10/2026. Revisão automática técnica não equivale a feedback de gestor.

Hashes dos artefatos brutos locais, mantidos ignorados:

| Arquivo | SHA256 |
|---|---|
| manifest.json | `c1d591f07d8cd8c7ac094a5c06906b94799b93e6f0495ddf05f9546da927fb4f` |
| cases.jsonl | `208ee758e8c7c0e7dc9575475d04b9e4938786ad15c25c4ba3796c2117ced107` |
| summary.json | `5bb82f22d949c36d440e41e35b81edad24837b755be4eae38034abba35806953` |
| summary.md | `a05e51dfda7d1933e6fb1e1a32991e50ec6445ea684c63636a11bc191eaf0d0d` |
| database_after.json | `3a6af8014dee48218bacb5499f3c3f7df69e5bcb88bb158e38bae20683950dca` |
