# Desenvolvimento — rodada 3, 11/10/2026

Rodada completa, com 20 casos aprovados entre 20 registrados de 20 planejados. Motivo de parada: `null` (conclusão normal). Código de saída do executor: 0.

## Identidade e preservação

- Rodada: `20261011T161317Z-1c15b47d`; artefatos locais ignorados: `/workspace/pac_privado-desenvolvimento-rodada3/.local/evaluation/20261011T161317Z-1c15b47d`.
- Fontes executados: `59c9eb8fa0b73444e770effd3e3e80724049164b`. Checkout/manifesto: `59c9eb8fa0b73444e770effd3e3e80724049164b`, checkout isolado limpo na versão indicada. Conjunto, base e modelo coincidem com as rodadas anteriores; a mudança de fontes limita-se à melhoria diagnóstica autorizada, sem alterar prompts/gabaritos. Estado modificado no manifesto: `False`.
- Conjunto versão 1.0.0, SHA256 `6a42eeb54169b15751eec3ff2e7657f52cdab96dc674dbaa7be16bc5c620bc2c`.
- Fontes SHA256 agregado `d46a1a6fbb6c79507704cc03ff8aa6fe5db48c1788fb588e7f1d2442d7b0d860`.
- Base SHA256 agregado `d4f6623f1de2d8050ca3901b231ff00e05f1627bb09ecf8f7a7f0db86578cf6d`. Hashes agregados usam SHA256 de `evaluation.runner.dump` (UTF-8, chaves ordenadas, indentação 2).
- Modelo configurado/resolvido: `gemini-3.5-flash-lite`. O alias não identifica pesos imutáveis.
- Uma única nova rodada: `python -m scripts.evaluate run --live --split development --interval 60 --limit 20 --env-file /workspace/pac_privado/.env`.
- Mesmo Python/dependências, configuração e base. SDK com uma tentativa por requisição. Sem retry adicional, troca de modelo, ajuste de cobrança, prompts ou gabaritos.
- `database_after.unchanged=true`; hashes/contagens completos constam do JSON resumido e coincidem antes/depois e com a base original. `.env` e processos do bot preservados. Rodada anterior e diagnóstico D08 preservados.
- Nenhum teste reservado foi executado contra o agente. A validação automática das 34 referências SQL realizada pelo executor é somente leitura e não chama Gemini.

110 testes passaram com PostgreSQL real, sem skips; lint `ruff check app scripts tests evaluation` passou; `scripts.evaluate validate` validou 34 referências SQL antes da API. Nenhuma configuração precisou ser reconstruída.

## Resultados

| Caso | Estado | Latência por turno (ms) | Requisições SDK |
|---|---|---:|---:|
| D01 | passed | 974.561 | 1 |
| D02 | passed | 951.553 | 1 |
| D03 | passed | 3468.223 | 4 |
| D04 | passed | 3834.029 | 4 |
| D05 | passed | 964.286 | 1 |
| D06 | passed | 1517.974 | 1 |
| D07 | passed | 2705.670 | 4 |
| D08 | passed | 2939.034 | 4 |
| D09 | passed | 2867.110 | 4 |
| D10 | passed | 2274.411 | 4 |
| D11 | passed | 2666.320 | 4 |
| D12 | passed | 2893.172 | 4 |
| D13 | passed | 796.175 | 1 |
| D14 | passed | 967.397 | 1 |
| D15 | passed | 1131.485 | 1 |
| D16 | passed | 883.015, 1276.397 | 2 |
| D17 | passed | 694.469 | 1 |
| D18 | passed | 906.249 | 1 |
| D19 | passed | 842.283 | 1 |
| D20 | passed | 831.960 | 1 |

- clarification_accuracy: 4/4 aprovados, 4 registrados; taxa: **100%**.
- execution_accuracy: 16/16 aprovados, 16 registrados; taxa: **100%**.

A taxa de execução mede o sistema híbrido completo: planejamento pelo modelo, templates para totais e SQL gerado para análises. Não é uma taxa exclusiva de geração livre de SQL.

## Latência e consumo

21 turnos observados. Média 1.733 s, mediana 1.131 s, mínimo 0.694 s, máximo 3.834 s. Inclui agente, Gemini e banco; exclui intervalo entre turnos, Telegram, tempo humano e comparação da avaliação. Não demonstra SLA ponta a ponta.

45 requisições SDK registradas; 45 com uso informado e 0 sem uso. Tokens conhecidos: entrada 67329, saída 2366, total 69695. Uso ausente não é imputado como zero; tokens de raciocínio não informados separadamente e custo não estimado.

## Diagnóstico e limitações

Nenhuma falha semântica observada nesta rodada. Não houve iteração de prompt ou correção de produto. O sucesso desta rodada não apaga o HTTP400 anterior nem estabelece sua causa.

Nenhum erro de API ocorreu nesta rodada. O intervalo maior e o sucesso atual não permitem determinar se o HTTP429 anterior representava limite diário ou por minuto; não há prazo de reset inferido.

Amostra de desenvolvimento pequena e conhecida; não substitui teste reservado ou validação qualitativa. Somente resultados selecionados e renderizados contam para aprovação, conforme o scorer congelado. Não foram publicados artefatos brutos, corpos HTTP, assinaturas ou credenciais.
