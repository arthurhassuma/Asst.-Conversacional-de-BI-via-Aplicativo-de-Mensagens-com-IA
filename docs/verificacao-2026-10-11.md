# Verificação de engenharia e continuidade até S10–S11

Data: 11/10/2026. O usuário autorizou continuar além do escopo original, até as semanas S10–S11, usando o ambiente do chat “Configurar pac_privado”. A configuração secreta permaneceu nesse ambiente.

## Versão integrada

O commit `8b11f2d9767caa3329b893e069930163c1830dd0`, branch `codex/avaliacao-s7-s11`, integra a versão funcional em nuvem `72469bb` com as proteções da revisão anterior `383de6b`. O PR de rascunho [#2](https://github.com/arthurhassuma/pac_privado/pull/2) reúne as alterações; nenhum merge em main foi feito.

Foi implementado o conjunto de 40 casos (20 desenvolvimento, 20 teste reservado), com 34 consultas SQL de referência e comparação exata dos resultados. O agente registra plano, tentativas, resultado selecionado, modelo resolvido e tokens por chamada, sem estado de rastreio compartilhado entre usuários. O executor preserva checkpoints, interrompe em falhas externas e invalida taxas quando a base muda ou sua verificação final falha.

## Evidências de engenharia

- PostgreSQL 16 local: as 34 consultas de referência executaram sem erro e sem truncamento. O comando `python -m scripts.evaluate validate --env-file ../.env` confirmou o mesmo.
- Suíte local completa antes da última proteção: 106 testes passaram, incluindo PostgreSQL real. Depois da proteção final, os 12 testes do módulo de avaliação passaram.
- [GitHub Actions, execução 38150606149](https://github.com/arthurhassuma/pac_privado/actions/runs/38150606149): **107 testes passaram**, lint aprovado, preparação e validação da base PostgreSQL 16 aprovadas. Commit executado: `8b11f2d`.
- Revisão independente identificou e orientou correções para a coluna auxiliar `registros`, o rótulo genérico de valores médios, a classificação de falhas de transporte e a invalidação da rodada quando a confirmação final do banco falha.

Esses testes comprovam propriedades de engenharia. Não comprovam a meta acadêmica de acurácia, a latência Telegram ou aceitação por um gestor.

## Experimento real

Uma rodada de desenvolvimento foi iniciada no checkout isolado `/workspace/pac_privado-desenvolvimento`, com o commit publicado e configuração original. A versão passou nos 107 testes e no lint também nesse ambiente; as 34 referências foram validadas.

A execução `20261011T151909Z-5411e2fc` registrou D01–D07 como corretos e foi interrompida em D08, com código de saída 2 e `provider_error_400`. O modelo resolvido observado foi `gemini-3.5-flash-lite`. A tentativa SQL de D08 correspondeu ao gabarito, mas nenhum resultado foi selecionado antes do erro externo. A base permaneceu inalterada. Não há taxa oficial disponível para essa rodada parcial. O teste reservado ainda não foi executado.

Os artefatos brutos permanecem em `.local/evaluation/` no ambiente em nuvem. O [relatório revisado](experimentos/2026-10-11-desenvolvimento.md) e seu JSON resumido foram incorporados do commit remoto `8b6fcc5`. O HTTP 400 não constitui evidência de cota (HTTP 429); o rastreamento original não conservou sua causa detalhada. Uma reprodução direcionada de D08 foi autorizada para diagnóstico de integração, preservando esta rodada.

Os arquivos JSON passam a usar LF explicitamente em `.gitattributes`, para conservar o hash de bytes entre checkouts Windows/Linux. O conteúdo congelado do conjunto v1.0.0 permanece idêntico ao blob Git executado na nuvem.

A [reprodução direcionada de D08](experimentos/2026-10-11-diagnostico-d08.md) passou na mesma versão, sem reproduzir o HTTP 400. Não foi aplicada correção de causa presumida. A [segunda rodada](experimentos/2026-10-11-desenvolvimento-rodada2.md), `20261011T153617Z-0a9bf9d9`, passou em D01–D09 e interrompeu D10 por HTTP 429. D11–D20 e o teste reservado permanecem não executados. A base continuou inalterada, e as taxas oficiais continuam nulas. Os nove casos concluídos não apresentaram divergência semântica; não orientaram alteração de prompt. A mensagem detalhada de cota não foi preservada, portanto seu período de recuperação é desconhecido.

Com base na lacuna de evidência observada, foi acrescentada classificação segura de erros API no trace, restrita a rótulos fixos; mensagens brutas não são guardadas. Os três testes de regressão falharam antes da implementação e passaram depois. Os 37 testes de SDK, agente e avaliação passaram com o aprimoramento. Essa alteração de diagnóstico é posterior às rodadas e não deve ser atribuída às versões experimentadas.

## Cronograma e limites

### Desenvolvimento concluído e congelamento

A [terceira rodada de desenvolvimento](experimentos/2026-10-11-desenvolvimento-rodada3.md), `20261011T161317Z-1c15b47d`, concluiu 20/20 casos na versão `59c9eb8fa0b73444e770effd3e3e80724049164b`, com intervalo de 60 segundos. Foram aprovadas 16/16 respostas (execution accuracy de 100%) e 4/4 perguntas de esclarecimento (clarification accuracy de 100%). Não houve erro externo ou semântico; não foi necessário alterar prompts. As rodadas incompletas anteriores continuam preservadas e sem taxas oficiais.

O JSON publicado foi conferido contra seus 20 registros: 21 turnos, 45 requisições e média de 1,733 s para agente e banco. O hash do conjunto coincide com o arquivo local; os fontes de aplicação, avaliação, scripts e banco permanecem idênticos à versão executada. O ambiente de origem validou os hashes dos artefatos brutos, a base inalterada, 110 testes de engenharia, lint e 34 referências SQL antes da rodada. Esses resultados de desenvolvimento não substituem teste reservado.

Em continuidade autorizada pelo usuário, foram congelados os fontes `59c9eb8`, o conjunto v1.0.0 (SHA256 `6a42eeb54169b15751eec3ff2e7657f52cdab96dc674dbaa7be16bc5c620bc2c`), o modelo `gemini-3.5-flash-lite`, os limites e a base da terceira rodada. Uma única execução de T01–T20 foi realizada no ambiente configurado, mantendo o intervalo de 60 segundos e parada em qualquer erro externo. Nenhuma correção será orientada pelo teste reservado sem declarar contaminação e preparar outra amostra independente.

### Teste reservado concluído

O [teste reservado](experimentos/2026-10-11-teste-reservado.md), rodada `20261011T163747Z-5fe3b066`, concluiu T01–T20 com saída 0 e 20/20 casos aprovados: execution accuracy de 16/16 (100%) e clarification accuracy de 4/4 (100%). Não houve erro externo ou semântico, ajuste de código/prompt, repetição ou consulta adicional após a conclusão.

O ambiente de origem recalculou a aprovação dos casos e as taxas dos checkpoints usando o scorer congelado, verificou seus 21 turnos e os hashes dos artefatos brutos. A revisão local confirmou identidade de fontes/conjunto/modelo/limites/bibliotecas/base com a rodada de desenvolvimento, IDs e totais do relatório, soma das 48 requisições e latência média de 1,649 s. Todas as chamadas tiveram uso informado: 74.713 tokens. Base, configuração secreta e bot foram preservados.

A meta de execution accuracy estritamente superior a 70% foi atingida nesta amostra reservada. O resultado mede o sistema híbrido completo, com templates para totais e SQL gerado para análises; não demonstra acurácia exclusiva de geração livre de SQL ou generalização ampla. A latência continua restrita a agente e banco. Os 110 testes são evidência de engenharia da mesma versão executados antes do desenvolvimento, não 110 perguntas reais nem testes repetidos nesta avaliação.

S7–S8: conjunto e executor entregues, com revisão técnica do gabarito; revisão por professor/especialista permanece recomendada. S8–S10: desenvolvimento e teste reservado completos, preservando as rodadas interrompidas. S10–S11: diagnóstico, rastreamento, regressões, análise de desenvolvimento, congelamento e avaliação reservada entregues. Nenhuma falha semântica justificou nova iteração de prompt. As evidências estão no PR #2, sem merge em main ou atualização automática do bot.

Validação qualitativa com gestor, comparação com dashboards e redação final pertencem às etapas posteriores. A latência do executor mede agente+banco e não equivale a transporte Telegram ponta a ponta.


## Ampliação até a entrega final

Posteriormente, o responsável autorizou desenvolver até o final e confirmou aceite do gestor em 11/10/2026, sem síntese de feedback. O [registro declaratório](validacao-gestor.md) documenta essa origem; não constitui estudo qualitativo ou aprovação institucional. O [relatório final](relatorio-final-pac-viii.md), o [roteiro de demonstração](roteiro-demonstracao.md) e o [índice da entrega](entrega-final.md) foram preparados.

A [reprodução Docker isolada](verificacao-entrega-final.md) aprovou 110 testes, sem skips, lint e 34 referências SQL. A base recém-gerada teve o mesmo fingerprint dos experimentos. Fontes congelados preservados; nenhuma nova chamada Gemini/Telegram ou ajuste guiado pelo teste reservado. O parágrafo anterior sobre etapas posteriores é histórico e foi superado por esta ampliação. Comparação com dashboards e latência Telegram ponta a ponta continuam não medidas.
