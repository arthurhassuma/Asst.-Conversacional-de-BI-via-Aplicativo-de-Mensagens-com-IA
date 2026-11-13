# Documentação do projeto

Índice da pasta `docs/`. A documentação foi consolidada por tema em 2026-11-09; cada seção preserva o texto original e indica o arquivo de origem (o histórico completo continua no git).

## Documentos

- [projeto.md](projeto.md): escopo, arquitetura, plano, dicionário de dados e base comparativa.
- [avaliacao.md](avaliacao.md): protocolos, treinamento de intenções (v1/v2), aceite do gestor e comparação com a proposta.
- [experimentos.md](experimentos.md): rodadas de desenvolvimento, teste reservado e correções.
- [verificacoes.md](verificacoes.md): registros de verificação por etapa.
- [proposta.md](proposta.md): texto da proposta original (anterior à implementação).
- [reproducao.md](reproducao.md): guia passo a passo para reproduzir testes, base, referências e avaliação.
- [deploy.md](deploy.md): publicação no GitHub e implantação na Oracle.
- [apresentacao.md](apresentacao.md): guia de estudo, roteiro de demonstração e de entrega.
- [relatorio-final-pac-viii.md](relatorio-final-pac-viii.md): fonte textual do relatório final.
- `entregaveis/`: relatórios (DOCX/PDF), proposta e apresentação (PPTX/PDF).
- `dados/`: resultados em JSON, consultas SQL e corpora de treinamento.

## Entrega final — PAC Extensionista VIII

_Origem: `docs/README.md` (consolidado em 2026-11-09)._

Preparada em **11/10/2026**, conforme ampliação de escopo autorizada pelo responsável, e **atualizada em 10/11/2026** com o [adendo do relatório](relatorio-final-pac-viii.md#10-adendo-de-10-de-novembro-de-2026) (mudanças posteriores, reavaliação com autopeças e limitações), a apresentação revisada e o registro das implantações. Este índice reúne os artefatos até S16; a submissão à instituição e a aprovação docente são atos posteriores. As seções 1 a 9 do relatório são o retrato de outubro; onde divergem do adendo, vale o adendo.

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

Em outubro, os fontes ficaram congelados em `59c9eb8fa0b73444e770effd3e3e80724049164b`; a reprodução Docker daquela versão aprovou **110 testes**, sem skips, e **34 referências SQL**, com base idêntica à dos experimentos. Depois disso o código mudou (domínio de autopeças, estado durável, classificador, correções da reavaliação). A versão de entrega atualizada é a da tag `v1.0.0`, com **285 testes passando** e 52 que exigem um PostgreSQL de teste; a reprodução Docker completa não foi refeita para ela.

Em 10/11/2026 o DOCX recebeu o adendo (seção 10, com sumário atualizado) e o PDF foi reexportado pelo Microsoft Word, com 16 páginas. Nesta atualização foram conferidas visualmente as páginas do adendo, a página de aceite e a formatação dos subtítulos; as páginas 1 a 14 não foram reinspecionadas além do sumário. A apresentação (PPTX e PDF) passou de 20 para 23 slides: dois de conversa simulada no estilo Telegram ("Uma conversa de verdade" e "Perguntas diretas, com o número do banco", com textos e valores gerados pelo próprio bot sobre a base sintética) e um da reavaliação de novembro; os slides de testes, produção, limitações e resumo tiveram os números atualizados. O slide da avaliação de outubro e o gráfico de testes por assunto seguem como retrato de outubro e estão rotulados assim. O relatório PAC VII original não foi alterado.

O teste reservado de outubro, na base original, atingiu 16/16 respostas e 4/4 esclarecimentos, com média de **1,649 s** para agente e banco. **Esses números não são comparáveis com os da reavaliação com autopeças** (novembro), que usa outra base, outros casos e um sistema diferente, e não indicam melhora nem piora: 12/16 e 6/8 nos reservados da versão antiga, e 13/16 num conjunto novo para a versão corrigida, todos no limite do critério ([experimentos](experimentos.md#reavaliação-no-perfil-autopecas--conjunto-c-partição-reservada-nova-100-09112026)). A latência não mede o transporte Telegram, e os resultados valem para amostras pequenas, sem comprovação de generalização ampla ou comparação com dashboards.

### Pacote e rastreabilidade

O ZIP de entrega reúne os arquivos versionados desta branch, incluindo `.env.example`, código, conjunto de avaliação e documentação. Seu `manifesto-entrega.json` registra o commit documental, o commit dos fontes congelados e SHA256 de cada arquivo. A geração verifica os hashes e a integridade do ZIP.

O pacote exclui `.git/`, `.local/`, ambientes virtuais, `.env`, credenciais, logs e bancos locais. Os dados sintéticos são reproduzidos pelo seeder; artefatos brutos das chamadas ficam no ambiente de origem e não são distribuídos. O pacote não altera a visibilidade do repositório. O código é distribuído sob a licença MIT (arquivo `LICENSE`).

### Providências do responsável

Conferir as normas institucionais, preencher eventuais assinaturas e submeter os artefatos. A aprovação docente não é presumida. A licença MIT prevista na proposta foi adicionada ao repositório (`LICENSE`); a decisão de tornar o repositório público continua do responsável. Medir latência Telegram ponta a ponta, comparar com dashboards e coletar feedback estruturado são trabalhos adicionais, não resultados inventados nesta entrega.
