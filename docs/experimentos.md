# Experimentos e correções

Registros das rodadas de desenvolvimento, do teste reservado e da correção da comparação mensal. Os resultados brutos (JSON) estão em `dados/experimentos/`.

## Conteúdo

- [Desenvolvimento — 11/10/2026](#desenvolvimento--11102026)
- [Desenvolvimento — rodada 2, 11/10/2026](#desenvolvimento--rodada-2-11102026)
- [Desenvolvimento — rodada 3, 11/10/2026](#desenvolvimento--rodada-3-11102026)
- [Diagnóstico direcionado de D08 — 11/10/2026](#diagnóstico-direcionado-de-d08--11102026)
- [Teste reservado — 11/10/2026](#teste-reservado--11102026)
- [Desenvolvimento gerencial real — 12/10/2026](#desenvolvimento-gerencial-real--12102026)
- [Comparação mensal com o ano anterior — 12/10/2026](#comparação-mensal-com-o-ano-anterior--12102026)

## Desenvolvimento — 11/10/2026

_Origem: `docs/experimentos.md` (consolidado em 2026-11-09)._

Rodada real **interrompida em D08 por HTTP 400 do Gemini**, sem repetição automática.
D01–D07 tiveram respostas corretas; D08 não concluiu uma resposta; D09–D20 não foram
executados. Não há taxa oficial de execution accuracy ou clarification accuracy.
O teste reservado não foi executado com Gemini. Não houve mudança de produto,
prompts, conjunto, gabaritos, modelo, plano de cobrança ou processos do bot.

### Identificação e execução

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

### Cobertura e resultados por caso

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

### Latência e consumo observado

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

### Diagnóstico de D08

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

### Integridade e limitações

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

## Desenvolvimento — rodada 2, 11/10/2026

_Origem: `docs/experimentos.md` (consolidado em 2026-11-09)._

Rodada interrompida, com 9 casos aprovados entre 10 registrados de 20 planejados. Motivo de parada: `provider_error_429`. Código de saída do executor: 2.

### Identidade e preservação

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

### Resultados

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

### Latência e consumo

10 turnos observados. Média 1.843 s, mediana 2.181 s, mínimo 0.825 s, máximo 2.769 s. Inclui agente, Gemini e banco; exclui intervalo entre turnos, Telegram, tempo humano e comparação da avaliação. Não demonstra SLA ponta a ponta.

28 requisições SDK registradas; 27 com uso informado e 1 sem uso. Tokens conhecidos: entrada 41307, saída 1354, total 42661. Uso ausente não é imputado como zero; tokens de raciocínio não informados separadamente e custo não estimado.

### Diagnóstico e limitações

Nenhuma falha semântica foi observada nos casos concluídos. D10 sofreu falha externa por HTTP429, sem resultado selecionado; D11–D20 permanecem desconhecidos. Não houve iteração de prompt ou correção de produto. O checkpoint preserva o código, sem mensagem detalhada de cota: não é possível distinguir limite por minuto de cota diária. A reprodução e esta rodada não esclarecem a causa do HTTP400 original.

#### D10 — turno 1

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

## Desenvolvimento — rodada 3, 11/10/2026

_Origem: `docs/experimentos.md` (consolidado em 2026-11-09)._

Rodada completa, com 20 casos aprovados entre 20 registrados de 20 planejados. Motivo de parada: `null` (conclusão normal). Código de saída do executor: 0.

### Identidade e preservação

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

### Resultados

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

### Latência e consumo

21 turnos observados. Média 1.733 s, mediana 1.131 s, mínimo 0.694 s, máximo 3.834 s. Inclui agente, Gemini e banco; exclui intervalo entre turnos, Telegram, tempo humano e comparação da avaliação. Não demonstra SLA ponta a ponta.

45 requisições SDK registradas; 45 com uso informado e 0 sem uso. Tokens conhecidos: entrada 67329, saída 2366, total 69695. Uso ausente não é imputado como zero; tokens de raciocínio não informados separadamente e custo não estimado.

### Diagnóstico e limitações

Nenhuma falha semântica observada nesta rodada. Não houve iteração de prompt ou correção de produto. O sucesso desta rodada não apaga o HTTP400 anterior nem estabelece sua causa.

Nenhum erro de API ocorreu nesta rodada. O intervalo maior e o sucesso atual não permitem determinar se o HTTP429 anterior representava limite diário ou por minuto; não há prazo de reset inferido.

Amostra de desenvolvimento pequena e conhecida; não substitui teste reservado ou validação qualitativa. Somente resultados selecionados e renderizados contam para aprovação, conforme o scorer congelado. Não foram publicados artefatos brutos, corpos HTTP, assinaturas ou credenciais.

## Diagnóstico direcionado de D08 — 11/10/2026

_Origem: `docs/experimentos.md` (consolidado em 2026-11-09)._

A única reprodução autorizada **passou**. O HTTP 400 da rodada original não reapareceu; sua causa detalhada permanece indeterminada. Não há evidência suficiente para propor uma correção de produto. A reprodução bem-sucedida não altera o resultado nem as taxas nulas da rodada interrompida.

### Escopo e identidade

- Fontes executados: `8b11f2d9767caa3329b893e069930163c1830dd0`. Todos os hashes de fontes, conjunto e referências foram conferidos contra o manifesto original antes da reprodução; HEAD contém somente documentação adicional.
- Conjunto SHA256: `6a42eeb54169b15751eec3ff2e7657f52cdab96dc674dbaa7be16bc5c620bc2c`. Somente D08 foi executado, com histórico vazio conforme o caso original; nenhum caso reservado ou rodada completa foi executado.
- Modelo configurado e resolvido: `gemini-3.5-flash-lite`, sem troca de modelo ou alteração de cobrança.
- SDK `google-genai` 1.75.0, API `v1beta`, timeout 30 s e `HttpRetryOptions(attempts=1)`.
- Reprodução concluída em 11/10/2026 às 12:33:13 (America/Sao_Paulo).
- Artefatos locais ignorados: `/workspace/pac_privado-desenvolvimento/.local/diagnostic-d08/` (`reproduce.py`, `calls.json`, `result.json`, `database_after.json`). Não são publicados.

### Resultado e limite de requisições

- Status final: `answer`; comparação do **resultado selecionado e renderizado** com a referência: correta (`passed=true`). Houve uma tentativa SQL e seleção `q1`.
- Código de erro nesta reprodução: `null`; mensagem de erro sanitizada: ausente, porque nenhuma chamada falhou.
- Quatro requisições SDK, uma tentativa por requisição, zero retries extras; teto local de segurança: sete requisições. Não houve 429 ou outra indicação de cota, nem nova reprodução após o sucesso.
- Sequência: planejamento → `get_schema` → `execute_sql` → resposta final. Uma consulta intermediária correta não foi usada isoladamente como critério de sucesso.
- Latência agente/banco: 2.846 s; exclui Telegram e comparação/identificação da base.
- Tokens informados nas quatro respostas: entrada 6517, saída 276, total 6793. Sem estimativa de custo ou generalização de acurácia.

### Estrutura observada

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

### Interpretação e preservação

A evidência original continua sendo `provider_error_400`, `provider_code=400`, sem resultado selecionado em D08. O checkpoint original não preservou a mensagem detalhada do provedor ou a estrutura completa das mensagens. A reprodução atual percorreu o mesmo fluxo de quatro chamadas e concluiu corretamente; não é possível recuperar retroativamente a causa do erro anterior, nem afirmar que foi cota, credencial, assinatura inválida ou falha transitória.

O wrapper local registra somente estrutura, metadados e mensagem sanitizada se houver erro; remove valores secretos configurados e URLs da mensagem. Ele repropaga o objeto original da exceção sem alterar código/identidade. Como não houve erro nesta execução, não há mensagem original capturada. Não armazena corpos HTTP ou valores binários de assinaturas.

`database_after.unchanged=true`; os fingerprints completos antes/depois coincidem com a base da rodada original. O hash do `.env` original também foi conferido e permanece igual, sem publicação do hash ou conteúdo. Fontes, prompts, gabaritos, serviços e bot não foram alterados ou reiniciados. Apenas este relatório é publicado; a próxima investigação que dependa de outra chamada ao provedor exige novo escopo autorizado.

## Teste reservado — 11/10/2026

_Origem: `docs/experimentos.md` (consolidado em 2026-11-09)._

Rodada completa, com 20 casos aprovados entre 20 registrados de 20 planejados. Motivo de parada: `null` (conclusão normal). Código de saída do executor: 0.

### Identidade e preservação

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

### Resultados

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

### Latência e consumo

21 turnos observados. Média 1.649 s, mediana 1.073 s, mínimo 0.761 s, máximo 3.070 s. Inclui agente, Gemini e banco; exclui intervalo entre turnos, Telegram, tempo humano e comparação da avaliação. Não demonstra SLA ponta a ponta.

48 requisições SDK registradas; 48 com uso informado e 0 sem uso. Tokens conhecidos: entrada 72205, saída 2508, total 74713. Uso ausente não é imputado como zero; tokens de raciocínio não informados separadamente e custo não estimado.

### Diagnóstico e limitações

Nenhuma falha semântica observada nesta rodada. Não houve iteração de prompt ou correção de produto. O resultado desta avaliação não apaga as interrupções anteriores nem estabelece suas causas.

Nenhum erro de API ocorreu nesta avaliação; não há inferência de prazo de reset ou tipo de cota anterior.

As taxas medem o sistema híbrido completo (planejamento pelo modelo, templates de totais e geração SQL para análises), não somente geração livre de SQL. Nenhuma fase posterior ou nova chamada API foi iniciada após este teste.

Amostra reservada pequena; não substitui validação qualitativa nem sustenta generalização ampla. Caso qualquer falha reservada oriente ajustes futuros, declarar contaminação e preparar um novo conjunto reservado para uma avaliação independente. Somente resultados selecionados e renderizados contam para aprovação, conforme o scorer congelado. Não foram publicados artefatos brutos, corpos HTTP, assinaturas ou credenciais.

## Desenvolvimento gerencial real — 12/10/2026

_Origem: `docs/experimentos.md` (consolidado em 2026-11-09)._

Rodada completa, 24/25 casos registrados aprovados; 25 planejados. Exit code `0`, stop_reason `null`. Nenhuma repetição de rodada ou caso, correção de produto, teste gerencial reservado, treinamento ou teste de classificação foi executado.

### Identificação

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

### Resultados por caso

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

### Latência e consumo

25 turnos; média agente+banco 1.432 s, mediana 1.391 s, mínimo 0.979 s, máximo 3.193 s. Inclui provedor, compilação, renderização e banco; exclui intervalo e transporte Telegram. Não comprova SLA ponta a ponta.

28 requisições SDK registradas; 28 com consumo informado, 0 sem consumo. Tokens conhecidos: entrada 55967, saída 3741, total 59708. Uso ausente não imputado como zero; sem estimativa de custo.

### Falhas e resultados selecionados

D38 é falha de planejamento/esclarecimento indevido: o plano retornou measure=null e foi recusado antes de consultar SQL. Não decorre de zeros monetários escalados ou do formato do gabarito, pois nenhum resultado foi produzido para comparar.

#### D38, turno 1

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

### Preservação e limites

`database_after.unchanged=true`; hashes/contagens iguais ao snapshot inicial. Bot comparativo manteve os mesmos processos/configuração, sem restart ou mensagem proativa. Base e fontes `59c9eb8`, `.env` original e evidências acadêmicas preservados. Nenhum teste gerencial reservado foi executado; aguardará revisão/congelamento separado. A autorização condicional posterior exigia 25/25 aprovados para reservado/deploy; D38 impede essa continuação. A revisão `85ac8eb` mencionada pelo coordenador não foi aplicada durante esta rodada, e o bot não foi atualizado. Nenhum ganho é atribuído ao classificador. Os resultados desta base/versão não se misturam às métricas acadêmicas antigas. Outubro completo é cenário futuro sintético, status 31/10/2026. Revisão automática técnica não equivale a feedback de gestor.

Hashes dos artefatos brutos locais, mantidos ignorados:

| Arquivo | SHA256 |
|---|---|
| manifest.json | `c1d591f07d8cd8c7ac094a5c06906b94799b93e6f0495ddf05f9546da927fb4f` |
| cases.jsonl | `208ee758e8c7c0e7dc9575475d04b9e4938786ad15c25c4ba3796c2117ced107` |
| summary.json | `5bb82f22d949c36d440e41e35b81edad24837b755be4eae38034abba35806953` |
| summary.md | `a05e51dfda7d1933e6fb1e1a32991e50ec6445ea684c63636a11bc191eaf0d0d` |
| database_after.json | `3a6af8014dee48218bacb5499f3c3f7df69e5bcb88bb158e38bae20683950dca` |

## Comparação mensal com o ano anterior — 12/10/2026

_Origem: `docs/experimentos.md` (consolidado em 2026-11-09)._

### Problema e correção

O pedido “Nesse ano, teve algum mês que teve faturamento menor que o do ano
passado?” já especifica comparação por mês. A validação antiga rejeitava planos
`tendencia` com `comparison_period`, perguntando desnecessariamente se o usuário
queria comparar períodos. Mesmo com um plano `comparacao/mes`, não havia template
mensal: o executor dependia de SQL gerado e a resposta livre de campos não
distinguia com clareza ausência de quedas de ausência de dados.

A correção preserva uma intenção mensal de queda explicitamente presente no
pedido, inclusive ao responder ao esclarecimento pendente. Conserva a validação
de datas/evidências e os filtros. O planejador passa a explicar esse caso e a
substituição de setembro/pedidos por ano/faturamento na nova pergunta.

O SQL controlado agrega cada período separadamente, alinha os mesmos meses e
calcula diferença, percentual e direção no PostgreSQL. Aceita somente intervalos
com cortes de calendário compatíveis, dentro de um ano cada; outras situações e
filtros personalizados continuam no executor habitual. Não altera a allowlist.
Meses sem linhas de uma das partes usam zero somente com contagem que comprova
ausência; valores NULL existentes e taxas sem denominador continuam indefinidos.

O renderer apresenta somente os meses com queda quando solicitados; sem queda,
informa isso expressamente. Distingue base sem registros, valores indefinidos e
resultado truncado. Comparações mensais gerais conservam todos os meses. Os
percentuais permanecem com duas casas na apresentação; células SQL não são
arredondadas. O último mês parcial recebe aviso.

### Evidências e limites

- Base de código anterior: `583080dc98e95c8c1096671cb482ac244a6253bb`.
- Diagnóstico anterior com a pergunta isolada: plano `comparacao/mes` válido,
  seis requisições Gemini e resposta com detalhamento de campos sem conclusão.
  O esclarecimento do print é compatível com a barreira de validação identificada;
  não se afirma que o plano original do chat foi capturado.
- Verificação final usa planejador simulado e PostgreSQL readonly real. Planos
  incorretamente classificados como `tendencia` são normalizados antes do SQL.
  As somas de cada mês são verificadas contra SELECTs independentes sem joins.
- No cenário Jan–12/Out de 2026 versus Jan–12/Out de 2025: dez meses com registros,
  nenhum com queda. Resposta local informa ausência de queda; outubro é parcial.
- Cobertura adicional: queda real, aumento, entrada/saída, base zero, NULL,
  esclarecimento pendente, troca de assunto, filtros, corte incompatível,
  anos bissextos e truncamento.
- Suíte final: 209 testes aprovados em 3,60s, com PostgreSQL real. Ruff,
  formatação e `pip check` aprovados. Treinamento/teste do classificador e
  conjuntos reservados não foram reexecutados, nem alterados.
- Fingerprints das bases comparativa e original iguais aos manifests anteriores.
  Modelo, chaves, role readonly e flags do bot são preservados.
- O teste adicional online com contexto do print foi recusado pela revisão
  automática por envolver envio de contexto conversacional ao Gemini. Não foi
  executado por outro caminho, nem se atribui esse bloqueio à cota Gemini.
  A entrega corrigida foi validada depois pelo teste humano descrito abaixo.

Artefatos de diagnóstico e configuração permanecem locais/ignorados em `.local/`;
não se publicam credenciais, logs brutos ou histórico pessoal. A alteração de
produto não modifica resultados de experimentos congelados anteriores.

### Implantação e confirmação humana

Código implantado: `686b21cd7d1e6da32d234edc832488c0efb0d54b`, publicado na
branch `codex/comparacao-mensal`. O checkout ativo continua em
`/workspace/pac_privado-periodos`, atualizado por fast-forward; o runtime anterior
foi encerrado antes do novo início. Main não recebeu merge.

- Backend `/health`: HTTP 200 e configuração Telegram/IA/banco presente.
- Exatamente um processo de polling; supervisor registra o commit implantado.
- Mesma base `bi_comparativo`, modelo, chave, token, IDs, role e classificador
  desabilitado. Nenhuma mensagem Telegram proativa foi enviada.
- Fingerprints original/comparativo conferidos novamente após implantação e
  iguais aos manifests anteriores.
- Rollback privado preserva commit `583080dc98e95c8c1096671cb482ac244a6253bb`
  e supervisor anterior, sem copiar credenciais.
- Arthur enviou `/comecar` e repetiu a pergunta no Telegram; confirmou neste chat
  “Respondeu corretamente”. Essa é a evidência humana de entrega; não se afirma
  que health sozinho a comprova, nem se atribuem tokens/latência a esse teste.
- Instruções de retomada atualizadas no rascunho do ambiente. Exigem publicação
  pelas configurações do ambiente para uso em retomadas futuras.

## Reavaliação no perfil autopecas — desenvolvimento do conjunto A (3.0.0, 09/11/2026)

Primeira rodada real da reavaliação definida em [avaliação](avaliacao.md#reavaliação-no-perfil-autopecas-protocolo-declarado-antes-da-rodada), executada antes de qualquer correção.

**Configuração (do manifesto).** Código no commit `8635ce7` (`git_dirty: false`), conjunto 3.0.0 (SHA256 `4fca7b2e…`), modelo `gemini-3.5-flash-lite`, classificador de intenções ligado, intervalo de 60 s, perfil `autopecas` (seed 42, 100 clientes, jan/2025–out/2026). A verificação final da base confirmou que ela não mudou (`database_after.unchanged: true`).

**Resultado.** Rodada completa (20 de 20 casos, sem parada): *execution accuracy* **14/16 (87,5%)**, esclarecimentos 3/3, pedido não suportado 1/1, latência média de agente e banco de 2.467 ms (sem Telegram). O critério declarado (pelo menos 12 de 16) foi atendido. Falhas: D04 e D08.

| Caso | Classificação | O que ocorreu |
|---|---|---|
| D08 | Gabarito (formato de saída) | Resposta numericamente correta (R$ 194.143,65 na primeira posição, os cinco clientes iguais ao gabarito), mas o gabarito esperava as colunas `cliente`, `total` e o produto devolve `item`, `valor`, `posicao`. Reavaliado offline com o gabarito 3.1.0, o mesmo rastro passa. |
| D04 | Interpretação (planejador) | Para "valor contratado dos contratos iniciados em 2025, excluindo os cancelados", o planejador gerou `analysis.kind = ranking`, `group_by = nenhum`, sem limite; o contrato recusou e o bot respondeu "Informe um ranking de um a cem itens…". O classificador rotulou a pergunta como `ranking` (confiança 0,76). |

**Diagnóstico do D04 (6 chamadas extras, fora da rodada).** Com o classificador ligado, 3 de 3 repetições falharam do mesmo modo. Com ele desligado, 2 de 3 falharam e 1 respondeu certo (R$ 7.558.967,33, igual à referência). Com tão poucas repetições, isso **não permite concluir que o classificador causa o erro**: o planejador falha mesmo sem ele; fica apenas o indício de que o rótulo `ranking` não ajudou. Reforça que o ganho do classificador nas respostas continua não medido.

**Tratamento.** Ver a Emenda 1 do protocolo: gabarito 3.1.0 para D08 e T08 e `normalize_unranked_plan` no agente. A rodada de desenvolvimento seguinte, com a 3.1.0 e o agente corrigido, está registrada abaixo.

## Reavaliação no perfil autopecas — desenvolvimento do conjunto A (3.1.0, 09/11/2026)

Segunda rodada de desenvolvimento, depois das correções da Emenda 1.

**Configuração (do manifesto).** Código no commit `14287a3` (`git_dirty: false`), conjunto 3.1.0 (SHA256 `e4c8b430…`), modelo `gemini-3.5-flash-lite`, classificador de intenções ligado, intervalo de 60 s, mesma base da rodada 1 (`database_after.unchanged: true`).

**Resultado.** Rodada completa (20 de 20 casos): *execution accuracy* **16/16 (100%)**, esclarecimentos 3/3, pedido não suportado 1/1, latência média de agente e banco de 2.934 ms (rodada 1: 2.467 ms), nenhuma falha. D04 respondeu R$ 7.558.967,33, igual à referência; D08 passou com o gabarito 3.1.0.

| | Rodada 1 (3.0.0) | Rodada 2 (3.1.0) |
|---|---|---|
| Execution accuracy | 14/16 | 16/16 |
| Esclarecimentos | 3/3 | 3/3 |
| Não suportado | 1/1 | 1/1 |
| Falhas | D04, D08 | nenhuma |

**Como ler.** Este resultado **não é uma estimativa independente**: o agente e o gabarito foram corrigidos a partir das falhas deste mesmo conjunto de desenvolvimento. Cada caso rodou uma vez e o Gemini não é determinístico (o D04 variou nas repetições do diagnóstico). Mostra apenas que as falhas encontradas foram resolvidas. A medida sem viés vem dos testes reservados, que seguem intocados nesta data e serão rodados uma única vez com o código congelado em `14287a3`.

## Reavaliação no perfil autopecas — teste reservado do conjunto A (3.1.0, 09/11/2026)

Uma única rodada, executada depois do congelamento e sem nenhuma correção posterior.

**Configuração (do manifesto).** Commit `0cbe39d` (`git_dirty: false`; difere do `14287a3` apenas por este registro em `docs/`, sem mudança no agente), conjunto 3.1.0 (SHA256 `e4c8b430…`), partição `test`, modelo `gemini-3.5-flash-lite`, classificador ligado, intervalo de 60 s, base inalterada ao final.

**Resultado.** Rodada completa (20 de 20): *execution accuracy* **12/16 (75%)**, esclarecimentos 2/3, pedido não suportado 1/1, latência média de agente e banco de 2.551 ms. O critério (pelo menos 12 de 16) foi atendido no limite. Falhas: T04, T05, T08, T10 e T18.

| Caso | Natureza | O que ocorreu |
|---|---|---|
| T04 | Agente (valor do filtro) | O planejador filtrou `modalidade = 'sustentação'` (com acento); no dado o valor é `sustentacao`. Resultado 0, esperado 87. |
| T05 | Agente (agrupamento) | "Clientes cadastrados em cada UF" virou ranking por `cidade` sem limite; o bot pediu o tamanho de um ranking. Mesma família do D04. |
| T08 | Formato de saída | Os três clientes e os valores estão corretos, mas o agente devolveu `cliente, valor, registros` e o gabarito exige `item, valor, posicao`. |
| T10 | Agente (escopo) | "Média de horas realizadas por registro operacional" foi tratada como fora do escopo. |
| T18 | Status | Esperava esclarecimento de métrica; o status foi `unsupported_request`, com texto de ajuda praticamente igual. |

Pelo protocolo, as cinco contam como falha; T08 e T18 não foram reclassificadas.

## Reavaliação no perfil autopecas — teste reservado do conjunto B (managerial-v1, T21–T30, 09/11/2026)

Uma única rodada, logo depois da anterior, no mesmo commit `0cbe39d` e sem correção posterior. Conjunto `managerial-v1` (SHA256 `cdb71fa8…`), base inalterada.

**Resultado.** 10 de 10 casos: *execution accuracy* **6/8 (75%)**, esclarecimento 1/1, pedido não suportado 1/1, latência média de 2.379 ms. O critério (pelo menos 6 de 8) foi atendido no limite. Falhas: T26 e T28.

| Caso | O que ocorreu |
|---|---|
| T26 | Participação por segmento. O agente montou duas consultas para a métrica `pedidos` (total e distribuição). A distribuição é idêntica ao gabarito, mas o corretor exige uma consulta por métrica e o gabarito esperava uma. |
| T28 | Faturamento emitido, recebido e diferença. O agente fez duas consultas; R$ 346.184,72, R$ 303.361,91 e R$ 42.822,81 estão corretos, mas o gabarito esperava uma consulta só. |

**Leitura conjunta.** Os dois reservados atenderam ao critério declarado, mas no limite exato (18/24 no total, uma rodada cada). O desenvolvimento de 16/16 não se repetiu nos reservados, o que dá a dimensão do ajuste feito sobre ele. T08, T26 e T28 acertam o número e erram só a forma; T04, T05 e T10 são falhas reais do agente e ficam como limitações conhecidas, sem correção. Corrigi-las exigiria declarar estes reservados contaminados e preparar um novo conjunto independente. O ganho do classificador de intenções continua não medido.

## Correção das falhas do reservado do conjunto A (09/11/2026)

Feita depois de registrar os reservados, por decisão do responsável. **Contamina o reservado do conjunto A** (ver a Emenda 2 do [protocolo](avaliacao.md)); nada foi corrigido a partir das falhas T08, T18, T26 e T28, que não são falhas de interpretação.

**Causas e correções.**

| Caso | Causa (evidência) | Correção |
|---|---|---|
| T05 | Falha estável (4 de 4 execuções): o contrato de análise não tem agrupamento por UF, o planejador escolheu `cidade` com `kind = ranking` e sem limite, e o contrato pediu o tamanho de um ranking. | `normalize_unranked_plan` passa a tratar qualquer ranking sem limite como consulta comum quando a pergunta não pede ranking, top, maiores, menores, lista, "principais", "mais" etc. Testes de regressão nos dois sentidos. |
| T04 | Intermitente: o modelo copiou a grafia da pergunta (`sustentação`) e o dado guarda `sustentacao`. O `get_schema` só citava o valor numa frase. | `get_schema` devolve `valores`, os valores distintos reais das colunas `modalidade`, `status`, `segmento` e `uf`, com a instrução de usar a grafia exata do dado. Teste de integração. |
| T10 | Variação do planejador (1 recusa em 4 execuções): a mesma pergunta ora era respondida, ora marcada `fora_escopo`. | Regra curta no prompt do planejador: média, mínimo, máximo e mediana de métricas existentes são suportados, e `fora_escopo` é só para assunto sem relação com os dados. Sem teste automatizado (depende do modelo). |

**Verificação (chamadas reais, fora dos conjuntos, mesmas perguntas).** Depois das correções: T05 2/2 agrupando por `uf`; T10 8/8 com o valor de referência (11,8971…); T04 6/6 respondidas sem acento. Uma primeira versão do prompt do T10, mais longa e com exemplo em JSON, deu T10 10/10, mas fez o T04 pedir esclarecimento indevido ("valor ou quantidade?") em 3 de 6 execuções, contra 0 de 6 com o prompt anterior; foi descartada em favor da versão curta.

**Limites desta verificação.** Repetições da mesma pergunta que originou a correção não são medida independente; as amostras são pequenas (2 a 8 execuções) e o Gemini não é determinístico. A mudança no `get_schema` e no prompt afeta todas as perguntas, e não foi medida num conjunto novo. Os 280 testes automatizados passam (um teste de integração, `test_percent_operator_and_like_patterns`, depende dos dados do banco sintético e falha no banco local `autopecas`, com ou sem estas mudanças).

## Reavaliação no perfil autopecas — conjunto C, partição reservada nova (1.0.0, 09/11/2026)

Medida da versão **corrigida** do agente, em casos escritos depois das correções. Uma única execução, sem nenhuma alteração posterior.

**Configuração (do manifesto).** Commit `f4ab7e6` (`git_dirty: false`), conjunto `cases-autopecas-reservado-2.json` 1.0.0 (SHA256 `45d5b120…`), partição `test` (T41–T60), modelo `gemini-3.5-flash-lite`, classificador ligado, intervalo de 60 s, base inalterada ao final.

**Resultado.** 20 de 20 casos: *execution accuracy* **13/16 (81%)**, esclarecimentos 3/3, pedido não suportado 1/1, latência média de agente e banco de 2.813 ms. O critério declarado (pelo menos 12 de 16) foi atendido. Falhas: T48, T52 e T53.

| Caso | Natureza | O que ocorreu |
|---|---|---|
| T48 | Formato de saída | Os quatro clientes e os valores estão corretos, mas o agente devolveu `cliente, total, registros` e o gabarito exige o formato canônico `item, valor, posicao`. Mesma falha de forma do T08. |
| T52 | Pergunta ambígua | "Qual o **total de pedidos** não cancelados em 2026 para clientes de São Paulo?" gerou "valor ou quantidade?". "Total de pedidos" admite as duas leituras e o gabarito assumiu valor. |
| T53 | Pergunta ambígua | "Qual a **soma dos pedidos** em fevereiro de 2033?" gerou o mesmo esclarecimento. |

Pelo protocolo as três contam como falha; T52 e T53 não foram reclassificadas, embora a redação seja do autor dos casos e o esclarecimento seja defensável.

**Leitura.**
- Nenhuma falha tem número errado. As categorias das três correções (T44 filtro por modalidade com acento, T45 agrupamento por modalidade, T50 média) passaram, o que indica que as correções generalizam além das perguntas que as originaram.
- Os 20 casos não distinguem 13/16 de 12/16 (o reservado da versão antiga, no conjunto A) com segurança; não se deve afirmar melhora.
- Quem escreveu os casos conhecia as falhas anteriores, o que favorece a versão corrigida em T44, T45 e T50.
- Os esclarecimentos de T52 e T53 lembram os que apareceram numa versão descartada do prompt. Esta rodada não permite dizer se a regra atual do prompt ou o `get_schema` aumentou esse tipo de esclarecimento, porque a redação dos dois casos já é ambígua.
- Pendências: o formato do ranking (T08 e T48) acerta o número e erra só a forma, e depende de o gabarito exigir o formato canônico; o ganho do classificador de intenções foi medido depois, sem efeito mensurável (ver a seção seguinte).

## Medida do classificador de intenções no conjunto C (10/11/2026)

Segue o protocolo declarado antes das rodadas em [avaliação](avaliacao.md). Conjunto C (T41–T60, SHA256 `45d5b120…`), mesmo intervalo (60 s), modelo e base; agente do commit `f4ab7e6` na rodada 1 e do `ce44f07` nas demais (diferem só por um rótulo de renderização, fora da pontuação). Base inalterada ao final de todas.

**Rodadas válidas.**

| Rodada | Classificador | Execução | Respostas corretas |
|---|---|---|---|
| 1 (`f4ab7e6`) | ligado | completa, 20/20 | 13/16 |
| 2 (`ce44f07`) | **desligado** | **interrompida** por `provider_error_503` no T58 (18/20; T59 e T60 não rodaram) | 13/16 nos 16 casos de resposta, que rodaram todos; sem taxa oficial |
| 3 (`ce44f07`) | ligado (repetição) | completa, 20/20 | 14/16 |

**Tentativas interrompidas, registradas por completude.** Antes das rodadas 2 e 3, duas tentativas pararam por `provider_error_503` do Gemini (desligado: 8 casos; ligado: 4 casos) e a rodada 2 acima também parou. Nenhum resultado das interrompidas entra nas contas; os casos afetados pelo 503 (T48 na primeira tentativa desligada, T44 na ligada, T58 na rodada 2) não foram contados como falha do agente. Depois de uma chamada de teste ao Gemini, as rodadas foram refeitas do zero.

**Caso a caso (só os que variaram ou falharam).**

| Caso | Rodada 1 (ligado) | Rodada 2 (desligado) | Rodada 3 (ligado) |
|---|---|---|---|
| T48 (formato do ranking) | falha | falha | falha |
| T52 ("total de pedidos") | falha | falha | falha |
| T53 ("soma dos pedidos") | falha | falha | **correto** |
| T58 | correto | 503 | correto |
| T59, T60 | corretos | não rodaram | corretos |

**Leitura pela regra fixada antes.** Diferença entre desligado e ligado nas respostas: 0 caso contra a rodada 1 e 1 caso (T53) contra a rodada 3. Diferença entre as duas rodadas com o classificador ligado: 1 caso (o mesmo T53). A regra exigia pelo menos 3 casos e mais que a variação entre as rodadas ligadas; nenhuma condição foi atendida. Conclusão: **sem efeito mensurável nesta amostra**. Isso não prova que o classificador não ajude: 16 respostas e uma ou duas execuções por configuração só detectariam um efeito grande. O T53 mudou de resultado entre duas execuções idênticas, o que mostra a variação do próprio Gemini.

**Latência.** A média de agente e banco foi 2.813 ms (rodada 1), 5.564 ms (rodada 2, parcial) e 4.303 ms (rodada 3). A diferença não é atribuível ao classificador: as rodadas 2 e 3 coincidiram com instabilidade do provedor (503), e a rodada 1 foi feita antes.

**Sem ajustes.** Nenhum código ou conjunto foi alterado por causa dessas rodadas; o conjunto C segue sem contaminação.

