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

## Cronograma e limites

S7–S8: conjunto e executor entregues, com revisão técnica do gabarito; revisão por professor/especialista permanece recomendada. S8–S10: experimento real iniciado, cobertura incompleta. S10–S11: mecanismos de diagnóstico e regressões entregues; ajustes semânticos e comparação antes/depois dependem do relatório e de uma rodada de desenvolvimento válida. O teste reservado depende do congelamento desses ajustes.

Validação qualitativa com gestor, comparação com dashboards e redação final pertencem às etapas posteriores. A latência do executor mede agente+banco e não equivale a transporte Telegram ponta a ponta.
