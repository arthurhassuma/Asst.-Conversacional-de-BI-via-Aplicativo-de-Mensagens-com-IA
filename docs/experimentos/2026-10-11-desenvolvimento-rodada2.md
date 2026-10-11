# Desenvolvimento — rodada 2, 11/10/2026

Rodada interrompida, com 9 casos aprovados entre 10 registrados de 20 planejados. Motivo de parada: `provider_error_429`. Código de saída do executor: 2.

## Identidade e preservação

- Rodada: `20261011T153617Z-0a9bf9d9`; artefatos locais ignorados: `/workspace/pac_privado-desenvolvimento/.local/evaluation/20261011T153617Z-0a9bf9d9`.
- Fontes executados: `8b11f2d9767caa3329b893e069930163c1830dd0`. Checkout/manifesto: `b5b691d9528e38141f66e4a9da56e856db6c302b`, contendo apenas relatórios adicionais; os hashes de todos os fontes/conjunto coincidem com a versão original. Estado modificado no manifesto: `False`.
- Conjunto versão 1.0.0, SHA256 `6a42eeb54169b15751eec3ff2e7657f52cdab96dc674dbaa7be16bc5c620bc2c`.
- Fontes SHA256 agregado `ef99187e3b872919ff4600c2cc9c0a9d74b12c890e715efa22111b3f3fcacd20`.
- Base SHA256 agregado `d4f6623f1de2d8050ca3901b231ff00e05f1627bb09ecf8f7a7f0db86578cf6d`. Hashes agregados usam SHA256 de `evaluation.runner.dump` (UTF-8, chaves ordenadas, indentação 2).
- Modelo configurado/resolvido: `gemini-3.5-flash-lite`. O alias não identifica pesos imutáveis.
- Uma única nova rodada: `python -m scripts.evaluate run --live --split development --interval 12 --limit 20 --env-file /workspace/pac_privado/.env`.
- Mesmo Python/dependências, configuração e base. SDK com uma tentativa por requisição. Sem retry adicional, troca de modelo, ajuste de cobrança, prompts ou gabaritos.
- `database_after.unchanged=true`; hashes/contagens completos constam do JSON resumido e coincidem antes/depois e com a base original. `.env` e processos do bot preservados. Rodada anterior e diagnóstico D08 preservados.
- Nenhum teste reservado foi executado contra o agente. A validação automática das 34 referências SQL realizada pelo executor é somente leitura e não chama Gemini.

## Resultados

| Caso | Estado | Latência por turno (ms) | Requisições SDK |
|---|---|---:|---:|
| D01 | passed | 1173.415 | 1 |
| D02 | passed | 825.326 | 1 |
| D03 | passed | 2404.717 | 4 |
| D04 | passed | 2769.112 | 4 |
| D05 | passed | 838.410 | 1 |
| D06 | passed | 1025.185 | 1 |
| D07 | passed | 2520.475 | 4 |
| D08 | passed | 2514.039 | 4 |
| D09 | passed | 2338.598 | 4 |
| D10 | provider_error | 2022.553 | 4 |
| D11 | not_run | — | 0 |
| D12 | not_run | — | 0 |
| D13 | not_run | — | 0 |
| D14 | not_run | — | 0 |
| D15 | not_run | — | 0 |
| D16 | not_run | — | 0 |
| D17 | not_run | — | 0 |
| D18 | not_run | — | 0 |
| D19 | not_run | — | 0 |
| D20 | not_run | — | 0 |

- clarification_accuracy: 0/4 aprovados, 0 registrados; taxa: indisponível (rodada incompleta).
- execution_accuracy: 9/16 aprovados, 10 registrados; taxa: indisponível (rodada incompleta).

## Latência e consumo

10 turnos observados. Média 1.843 s, mediana 2.181 s, mínimo 0.825 s, máximo 2.769 s. Inclui agente, Gemini e banco; exclui intervalo entre turnos, Telegram, tempo humano e comparação da avaliação. Não demonstra SLA ponta a ponta.

28 requisições SDK registradas; 27 com uso informado e 1 sem uso. Tokens conhecidos: entrada 41307, saída 1354, total 42661. Uso ausente não é imputado como zero; tokens de raciocínio não informados separadamente e custo não estimado.

## Diagnóstico e limitações

Nenhuma falha semântica foi observada nos casos concluídos. D10 sofreu falha externa por HTTP429, sem resultado selecionado; D11–D20 permanecem desconhecidos. Não houve iteração de prompt ou correção de produto. O checkpoint preserva o código, sem mensagem detalhada de cota: não é possível distinguir limite por minuto de cota diária. A reprodução e esta rodada não esclarecem a causa do HTTP400 original.

### D10 — turno 1

Status `provider_error`, código do provedor `429`. Diagnóstico sintético selecionado/referência:

```json
{
  "case": "D10",
  "provider_code": 429,
  "question": "Qual o valor médio dos pedidos não cancelados de março de 2025, sem arredondar?",
  "reference_queries": [
    {
      "metric": "pedidos",
      "result": {
        "columns": [
          "total"
        ],
        "rows": [
          [
            "17282.416250000000"
          ]
        ],
        "truncated": false
      },
      "sql": "SELECT AVG(valor) AS total FROM pedidos WHERE data_pedido >= DATE '2025-03-01' AND data_pedido < DATE '2025-04-01' AND status <> 'cancelado'"
    }
  ],
  "selected_queries": [
    {
      "plan": {
        "measure": "valor",
        "metric": "pedidos",
        "operation": "analysis",
        "period": {
          "end": "2025-04-01",
          "evidence": "março de 2025",
          "start": "2025-03-01"
        }
      },
      "selected_id": null,
      "selected_result": null,
      "selected_sql": null
    }
  ],
  "status": "provider_error",
  "turn": 0
}
```


Amostra de desenvolvimento pequena e conhecida; não substitui teste reservado ou validação qualitativa. Somente resultados selecionados e renderizados contam para aprovação, conforme o scorer congelado. Não foram publicados artefatos brutos, corpos HTTP, assinaturas ou credenciais.
