# Entrega final — PAC Extensionista VIII

Preparada em **11/10/2026**, conforme ampliação de escopo autorizada pelo responsável. Este índice reúne os artefatos até S16; a submissão à instituição e a aprovação docente são atos posteriores.

## Artefatos

- [Relatório editável](Relatorio-Final-PAC-VIII-Arthur-Hassuma.docx), [PDF](Relatorio-Final-PAC-VIII-Arthur-Hassuma.pdf) e [fonte textual](relatorio-final-pac-viii.md).
- [Aceite declarado do gestor](validacao-gestor.md), registrado em 11/10/2026, sem síntese de feedback nem atribuição de resultados qualitativos.
- [Roteiro de demonstração](roteiro-demonstracao.md), preparado para apresentação; sua elaboração não comprova um novo ensaio executado.
- [Setup e operação](../README.md), [schema](../db/schema.sql), [dicionário](dicionario-de-dados.md) e [protocolo de avaliação](protocolo-avaliacao.md).
- [Desenvolvimento concluído](experimentos/2026-10-11-desenvolvimento-rodada3.md), [teste reservado](experimentos/2026-10-11-teste-reservado.md) e [reprodução com Docker](verificacao-entrega-final.md).
- [Comparação com o cronograma original](comparacao-proposta.md). Proposta e relatório PAC VII permanecem preservados em `docs/`.

## Fechamento do cronograma

| Etapa | Entrega e evidência |
|---|---|
| S1–S7 | Fundamentação retomada, schema, base sintética, agente Gemini e integração Telegram/FastAPI |
| S7–S8 | 40 casos: 20 de desenvolvimento e 20 reservados; referências SQL e protocolo |
| S8–S11 | Experimentos, diagnóstico, regressões e versão congelada; 20/20 casos aprovados em cada partição |
| S11–S12 | Validação e aceite declarados pelo responsável em 11/10/2026; não há instrumento qualitativo ou feedback documentado |
| S12–S14 | Relatório final com metodologia, resultados, limitações e referências |
| S14–S16 | Revisão dos artefatos, reprodução Docker, roteiro e pacote de entrega preparados; submissão institucional ainda a cargo do responsável |

Os fontes permanecem congelados em `59c9eb8fa0b73444e770effd3e3e80724049164b`. A reprodução Docker aprovou **110 testes**, sem skips, e **34 referências SQL**, com base idêntica à dos experimentos. Não foram feitas novas chamadas ao modelo na preparação final.

O PDF foi exportado pelo Microsoft Word e suas 14 páginas foram revisadas visualmente. Conteúdo, resultados, data, geometria, imagens e conteúdo XML auxiliar do DOCX foram conferidos; o relatório PAC VII original manteve seu SHA256. O DOCX recebeu posteriormente ajustes cosméticos na fonte do sumário e nos rodapés. A reexportação desses ajustes foi interrompida; o PDF mantém a versão de formatação já revisada, com o mesmo conteúdo. O bloqueio automático do encerramento de processos Word foi respeitado.

O teste reservado atingiu 16/16 respostas e 4/4 esclarecimentos. A média de **1,649 s** cobre agente e banco; não mede transporte Telegram. Os resultados são do sistema híbrido nesta amostra pequena, sem comprovação de generalização ampla ou comparação com dashboards.

## Pacote e rastreabilidade

O ZIP de entrega reúne os arquivos versionados desta branch, incluindo `.env.example`, código, conjunto de avaliação e documentação. Seu `manifesto-entrega.json` registra o commit documental, o commit dos fontes congelados e SHA256 de cada arquivo. A geração verifica os hashes e a integridade do ZIP.

O pacote exclui `.git/`, `.local/`, ambientes virtuais, `.env`, credenciais, logs e bancos locais. Os dados sintéticos são reproduzidos pelo seeder; artefatos brutos das chamadas ficam no ambiente de origem e não são distribuídos. O pacote é uma entrega privada: não altera visibilidade do repositório nem concede licença.

## Providências do responsável

Conferir as normas institucionais, preencher eventuais assinaturas e submeter os artefatos. A aprovação docente não é presumida. A publicação pública sob MIT prevista na proposta permanece pendente de decisão explícita sobre visibilidade e licença. Medir latência Telegram ponta a ponta, comparar com dashboards e coletar feedback estruturado são trabalhos adicionais, não resultados inventados nesta entrega.
