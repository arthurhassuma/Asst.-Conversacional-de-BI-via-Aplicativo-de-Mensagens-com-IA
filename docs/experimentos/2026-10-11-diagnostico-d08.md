# Diagnóstico direcionado de D08 — 11/10/2026

A única reprodução autorizada **passou**. O HTTP 400 da rodada original não reapareceu; sua causa detalhada permanece indeterminada. Não há evidência suficiente para propor uma correção de produto. A reprodução bem-sucedida não altera o resultado nem as taxas nulas da rodada interrompida.

## Escopo e identidade

- Fontes executados: `8b11f2d9767caa3329b893e069930163c1830dd0`. Todos os hashes de fontes, conjunto e referências foram conferidos contra o manifesto original antes da reprodução; HEAD contém somente documentação adicional.
- Conjunto SHA256: `6a42eeb54169b15751eec3ff2e7657f52cdab96dc674dbaa7be16bc5c620bc2c`. Somente D08 foi executado, com histórico vazio conforme o caso original; nenhum caso reservado ou rodada completa foi executado.
- Modelo configurado e resolvido: `gemini-3.5-flash-lite`, sem troca de modelo ou alteração de cobrança.
- SDK `google-genai` 1.75.0, API `v1beta`, timeout 30 s e `HttpRetryOptions(attempts=1)`.
- Reprodução concluída em 11/10/2026 às 12:33:13 (America/Sao_Paulo).
- Artefatos locais ignorados: `/workspace/pac_privado-desenvolvimento/.local/diagnostic-d08/` (`reproduce.py`, `calls.json`, `result.json`, `database_after.json`). Não são publicados.

## Resultado e limite de requisições

- Status final: `answer`; comparação do **resultado selecionado e renderizado** com a referência: correta (`passed=true`). Houve uma tentativa SQL e seleção `q1`.
- Código de erro nesta reprodução: `null`; mensagem de erro sanitizada: ausente, porque nenhuma chamada falhou.
- Quatro requisições SDK, uma tentativa por requisição, zero retries extras; teto local de segurança: sete requisições. Não houve 429 ou outra indicação de cota, nem nova reprodução após o sucesso.
- Sequência: planejamento → `get_schema` → `execute_sql` → resposta final. Uma consulta intermediária correta não foi usada isoladamente como critério de sucesso.
- Latência agente/banco: 2.846 s; exclui Telegram e comparação/identificação da base.
- Tokens informados nas quatro respostas: entrada 6517, saída 276, total 6793. Sem estimativa de custo ou generalização de acurácia.

## Estrutura observada

IDs são representados por rótulos locais, sem seus valores originais. `id1` e `id2` abaixo pertencem à mesma requisição final; rótulos em respostas isoladas não são comparáveis entre capturas.

| Etapa | Roles/partes enviados | Resposta do modelo |
|---|---|---|
| 1 | `user:text` | `model:text` (plano) |
| 2 | `user:text` | `model:functionCall(get_schema)` |
| 3 | `user:text`, `model:functionCall(get_schema)`, `user:functionResponse(get_schema)` | `model:functionCall(execute_sql)` |
| 4 | `user:text`, `model:functionCall(get_schema)`, `user:functionResponse(get_schema)`, `model:functionCall(execute_sql)`, `user:functionResponse(execute_sql)` | `model:text` (resposta final) |

Na requisição 4:

| Role/tipo | Nome | ID presente/rótulo | Correspondência | thought_signature |
|---|---|---|---|---|
| user/text | — | — | — | ausente, NoneType, comprimento 0 |
| model/functionCall | get_schema | sim/id1 | — | presente, bytes, comprimento 98 |
| user/functionResponse | get_schema | sim/id1 | nome e ID iguais à chamada anterior | ausente, NoneType, comprimento 0 |
| model/functionCall | execute_sql | sim/id2 | — | presente, bytes, comprimento 98 |
| user/functionResponse | execute_sql | sim/id2 | nome e ID iguais à chamada anterior | ausente, NoneType, comprimento 0 |

Todas as quatro respostas do modelo continham uma única parte com assinatura presente, tipo `bytes`, comprimento 98. As assinaturas dos dois functionCall mantiveram presença/tipo/comprimento no reenvio. Nenhum valor de assinatura foi exibido ou publicado; essa observação estrutural não constitui uma comparação byte a byte.

## Interpretação e preservação

A evidência original continua sendo `provider_error_400`, `provider_code=400`, sem resultado selecionado em D08. O checkpoint original não preservou a mensagem detalhada do provedor ou a estrutura completa das mensagens. A reprodução atual percorreu o mesmo fluxo de quatro chamadas e concluiu corretamente; não é possível recuperar retroativamente a causa do erro anterior, nem afirmar que foi cota, credencial, assinatura inválida ou falha transitória.

O wrapper local registra somente estrutura, metadados e mensagem sanitizada se houver erro; remove valores secretos configurados e URLs da mensagem. Ele repropaga o objeto original da exceção sem alterar código/identidade. Como não houve erro nesta execução, não há mensagem original capturada. Não armazena corpos HTTP ou valores binários de assinaturas.

`database_after.unchanged=true`; os fingerprints completos antes/depois coincidem com a base da rodada original. O hash do `.env` original também foi conferido e permanece igual, sem publicação do hash ou conteúdo. Fontes, prompts, gabaritos, serviços e bot não foram alterados ou reiniciados. Apenas este relatório é publicado; a próxima investigação que dependa de outra chamada ao provedor exige novo escopo autorizado.
