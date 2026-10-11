# Teste reservado — 11/10/2026

Rodada completa, com 20 casos aprovados entre 20 registrados de 20 planejados. Motivo de parada: `null` (conclusão normal). Código de saída do executor: 0.

## Identidade e preservação

- Rodada: `20261011T163747Z-5fe3b066`; artefatos locais ignorados: `/workspace/pac_privado-desenvolvimento-rodada3/.local/evaluation/20261011T163747Z-5fe3b066`.
- Fontes executados: `59c9eb8fa0b73444e770effd3e3e80724049164b`. Checkout/manifesto: `59c9eb8fa0b73444e770effd3e3e80724049164b`, checkout isolado limpo na versão indicada. Conjunto, base e modelo coincidem com as rodadas anteriores; fontes e limites são exatamente os congelados após desenvolvimento, sem alterar prompts/gabaritos. Estado modificado no manifesto: `False`.
- Conjunto versão 1.0.0, SHA256 `6a42eeb54169b15751eec3ff2e7657f52cdab96dc674dbaa7be16bc5c620bc2c`.
- Fontes SHA256 agregado `d46a1a6fbb6c79507704cc03ff8aa6fe5db48c1788fb588e7f1d2442d7b0d860`.
- Base SHA256 agregado `d4f6623f1de2d8050ca3901b231ff00e05f1627bb09ecf8f7a7f0db86578cf6d`. Hashes agregados usam SHA256 de `evaluation.runner.dump` (UTF-8, chaves ordenadas, indentação 2).
- Modelo configurado/resolvido: `gemini-3.5-flash-lite`. O alias não identifica pesos imutáveis.
- Uma única nova rodada: `python -m scripts.evaluate run --live --split test --interval 60 --limit 20 --env-file /workspace/pac_privado/.env`.
- Mesmo Python/dependências, configuração e base. SDK com uma tentativa por requisição. Sem retry adicional, troca de modelo, ajuste de cobrança, prompts ou gabaritos.
- `database_after.unchanged=true`; hashes/contagens completos constam do JSON resumido e coincidem antes/depois e com a base original. `.env` e processos do bot preservados. Rodada anterior e diagnóstico D08 preservados.
- Uma única avaliação reservada T01–T20 foi autorizada após a revisão do desenvolvimento. Nenhuma correção ou repetição foi feita com base neste teste. A validação automática das 34 referências SQL realizada pelo executor é somente leitura e não chama Gemini.

Na mesma versão, antes da rodada3, 110 testes passaram com PostgreSQL real, sem skips; lint `ruff check app scripts tests evaluation` passou; `scripts.evaluate validate` validou 34 referências SQL antes da API de desenvolvimento; o executor reservado também validou as referências antes das suas chamadas. Nenhuma configuração precisou ser reconstruída.

## Resultados

| Caso | Estado | Latência por turno (ms) | Requisições SDK |
|---|---|---:|---:|
| T01 | passed | 1010.875 | 1 |
| T02 | passed | 892.283 | 1 |
| T03 | passed | 2764.612 | 4 |
| T04 | passed | 2843.386 | 4 |
| T05 | passed | 2457.834 | 4 |
| T06 | passed | 880.007 | 1 |
| T07 | passed | 1053.588 | 1 |
| T08 | passed | 2432.498 | 4 |
| T09 | passed | 2552.881 | 4 |
| T10 | passed | 3070.094 | 4 |
| T11 | passed | 2635.339 | 4 |
| T12 | passed | 2366.212 | 4 |
| T13 | passed | 1073.266 | 1 |
| T14 | passed | 2445.340 | 4 |
| T15 | passed | 1123.260 | 1 |
| T16 | passed | 891.960, 909.456 | 2 |
| T17 | passed | 774.075 | 1 |
| T18 | passed | 876.828 | 1 |
| T19 | passed | 819.871 | 1 |
| T20 | passed | 761.283 | 1 |

- clarification_accuracy: 4/4 aprovados, 4 registrados; taxa: **100%**.
- execution_accuracy: 16/16 aprovados, 16 registrados; taxa: **100%**.

Os 20 registros têm IDs únicos, ordem esperada e todos os 21 turnos completos. A aprovação de cada turno/caso, o resumo e ambas as taxas foram recalculados dos checkpoints usando o scorer congelado. Os hashes dos cinco artefatos brutos foram confirmados e estão no JSON; os artefatos permanecem locais/ignorados. A configuração efetiva manteve seu fingerprint local entre pré-verificação e conclusão; nenhum fingerprint de segredo é publicado.

## Latência e consumo

21 turnos observados. Média 1.649 s, mediana 1.073 s, mínimo 0.761 s, máximo 3.070 s. Inclui agente, Gemini e banco; exclui intervalo entre turnos, Telegram, tempo humano e comparação da avaliação. Não demonstra SLA ponta a ponta.

48 requisições SDK registradas; 48 com uso informado e 0 sem uso. Tokens conhecidos: entrada 72205, saída 2508, total 74713. Uso ausente não é imputado como zero; tokens de raciocínio não informados separadamente e custo não estimado.

## Diagnóstico e limitações

Nenhuma falha semântica observada nesta rodada. Não houve iteração de prompt ou correção de produto. O resultado desta avaliação não apaga as interrupções anteriores nem estabelece suas causas.

Nenhum erro de API ocorreu nesta avaliação; não há inferência de prazo de reset ou tipo de cota anterior.

As taxas medem o sistema híbrido completo (planejamento pelo modelo, templates de totais e geração SQL para análises), não somente geração livre de SQL. Nenhuma fase posterior ou nova chamada API foi iniciada após este teste.

Amostra reservada pequena; não substitui validação qualitativa nem sustenta generalização ampla. Caso qualquer falha reservada oriente ajustes futuros, declarar contaminação e preparar um novo conjunto reservado para uma avaliação independente. Somente resultados selecionados e renderizados contam para aprovação, conforme o scorer congelado. Não foram publicados artefatos brutos, corpos HTTP, assinaturas ou credenciais.
