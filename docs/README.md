# Documentação do projeto

Índice da pasta `docs/`. A documentação foi consolidada por tema em 2026-11-09; cada seção preserva o texto original e indica o arquivo de origem (o histórico completo continua no git).

## Documentos

- [projeto.md](projeto.md): escopo, arquitetura, plano, dicionário de dados e base comparativa.
- [avaliacao.md](avaliacao.md): protocolos, treinamento de intenções (v1/v2), aceite do gestor e comparação com a proposta.
- [experimentos.md](experimentos.md): rodadas de desenvolvimento, teste reservado e correções.
- [verificacoes.md](verificacoes.md): registros de verificação por etapa.
- [deploy.md](deploy.md): publicação no GitHub e implantação na Oracle.
- [apresentacao.md](apresentacao.md): guia de estudo, roteiro de demonstração e de entrega.
- [relatorio-final-pac-viii.md](relatorio-final-pac-viii.md): fonte textual do relatório final.
- `entregaveis/`: relatórios (DOCX/PDF), proposta e apresentação (PPTX/PDF).
- `dados/`: resultados em JSON, consultas SQL e corpora de treinamento.
- `superpowers/`: planos e especificações de processo.

## Entrega final — PAC Extensionista VIII

_Origem: `docs/README.md` (consolidado em 2026-11-09)._

Preparada em **11/10/2026**, conforme ampliação de escopo autorizada pelo responsável. Este índice reúne os artefatos até S16; a submissão à instituição e a aprovação docente são atos posteriores.

### Artefatos

- [Relatório editável](entregaveis/Relatorio-Final-PAC-VIII-Arthur-Hassuma.docx), [PDF](entregaveis/Relatorio-Final-PAC-VIII-Arthur-Hassuma.pdf) e [fonte textual](relatorio-final-pac-viii.md).
- [Aceite declarado do gestor](avaliacao.md#registro-de-aceite-do-gestor), registrado em 11/10/2026, sem síntese de feedback nem atribuição de resultados qualitativos.
- [Roteiro de demonstração](apresentacao.md#demonstração-e-reprodução-da-entrega), preparado para apresentação; sua elaboração não comprova um novo ensaio executado.
- [Setup e operação](../README.md), [schema](../db/schema.sql), [dicionário](projeto.md#dicionário-de-dados) e [protocolo de avaliação](avaliacao.md#protocolo-de-avaliação--s7-a-s11).
- [Desenvolvimento concluído](experimentos.md#desenvolvimento--rodada-3-11102026), [teste reservado](experimentos.md#teste-reservado--11102026) e [reprodução com Docker](verificacoes.md#verificação-de-reprodução-para-entrega-final).
- [Comparação com o cronograma original](avaliacao.md#comparação-da-proposta-com-a-implementação). Proposta e relatório PAC VII permanecem preservados em `docs/`.

### Fechamento do cronograma

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

### Pacote e rastreabilidade

O ZIP de entrega reúne os arquivos versionados desta branch, incluindo `.env.example`, código, conjunto de avaliação e documentação. Seu `manifesto-entrega.json` registra o commit documental, o commit dos fontes congelados e SHA256 de cada arquivo. A geração verifica os hashes e a integridade do ZIP.

O pacote exclui `.git/`, `.local/`, ambientes virtuais, `.env`, credenciais, logs e bancos locais. Os dados sintéticos são reproduzidos pelo seeder; artefatos brutos das chamadas ficam no ambiente de origem e não são distribuídos. O pacote é uma entrega privada: não altera visibilidade do repositório nem concede licença.

### Providências do responsável

Conferir as normas institucionais, preencher eventuais assinaturas e submeter os artefatos. A aprovação docente não é presumida. A publicação pública sob MIT prevista na proposta permanece pendente de decisão explícita sobre visibilidade e licença. Medir latência Telegram ponta a ponta, comparar com dashboards e coletar feedback estruturado são trabalhos adicionais, não resultados inventados nesta entrega.
