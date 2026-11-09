# Verificações

Registros de verificação de cada etapa, em ordem cronológica aproximada.

## Conteúdo

- [Verificação da entrega — Fases 0–3](#verificação-da-entrega--fases-03)
- [Verificação da continuidade — 10/10/2026](#verificação-da-continuidade--10102026)
- [Verificação de engenharia e continuidade até S10–S11](#verificação-de-engenharia-e-continuidade-até-s10s11)
- [Verificação da base comparativa — 11/10/2026](#verificação-da-base-comparativa--11102026)
- [Verificação e ativação da base comparativa](#verificação-e-ativação-da-base-comparativa)
- [Verificação de reprodução para entrega final](#verificação-de-reprodução-para-entrega-final)
- [Verificação do treinamento e das análises gerenciais — 12/10/2026](#verificação-do-treinamento-e-das-análises-gerenciais--12102026)

## Verificação da entrega — Fases 0–3

_Origem: `docs/verificacoes.md` (consolidado em 2026-11-09)._

Executada em 27/09/2026, Windows, Python 3.13.1, PostgreSQL 16.14. Dependências exatas em `requirements-lock.txt`.

### Resultado observado

- **58 testes passaram**, sem skips na execução completa com TEST_DATABASE_URL apontando à base isolada.
- `ruff check app scripts tests`: sem erros após ajustes; formatação aplicada.
- `pip check`: sem conflitos de dependências; `compileall` de app/scripts sem erros.
- `bi-db validate`: zero ocorrências em todas as seis verificações de consistência.
- Comandos CLI instalados e executados; saída sem chave de IA é controlada em português. Erros de argumentos são traduzidos.
- `.env`, `.local/` e `.venv/` confirmados como ignorados pelo Git. Repositório Git inicializado localmente, sem remote configurado.

### Carga real

Cluster próprio em `.local/pgdata`, porta 55439, escuta apenas 127.0.0.1. Senhas aleatórias, autenticação SCRAM. O serviço PostgreSQL já existente no computador não foi alterado.

| Tabela | Linhas |
|---|---:|
| clientes | 30 |
| contratos | 56 |
| pedidos | 672 |
| faturamento | 628 |
| indicadores_operacionais | 672 |

Seed 42 e 30 clientes. O servidor temporário foi encerrado após os testes; a carga ficou persistida para retomada. Consulte README para iniciar/parar esse cluster ou recriar o ambiente via Docker em volume próprio.

### O que os testes provaram

- SELECTs analíticos válidos, rejeição de múltiplos comandos, DML em CTE, SELECT INTO, locks, funções fora da allowlist, schemas externos, tipos perigosos e CTE fora do escopo lexical.
- Negação de INSERT, UPDATE, DELETE, CREATE TABLE e CREATE TEMP TABLE pelo PostgreSQL, **sem passar pelo validador da aplicação e mesmo após solicitar transação de escrita**.
- statement_timeout real, recuperação após timeout, limite de linhas externo e precisão decimal exata.
- Serialização de intervalos/durações e consultas com `%`/LIKE; foram escritos testes que reproduziram as falhas antes das correções.
- Esclarecimento antes de SQL, validação de evidência do período, contexto de continuação, erro SQL retornado ao modelo, correção e limite de tentativas, usando respostas de API simuladas.
- Sessões isoladas e limitadas, TTL, serialização por usuário, autenticação do webhook, recusa de usuários/grupos, deduplicação e datas de updates.
- Teste de fluxo completo: HTTP do webhook → SDK Anthropic com transporte simulado → get_schema/execute_sql → **PostgreSQL real** → renderização → SDK Telegram com transporte simulado. Resultado conferido contra consulta independente ao banco.

### Revisão e correções

Revisão independente somente leitura realizada ao final. Identificou o tratamento ausente de `timedelta`, corrigido com regressão real no PostgreSQL. O histórico enviado ao planejador foi reduzido a mensagens textuais, enquanto o executor mantém os blocos de tools e suas definições. O caso de escopo de CTE foi identificado na revisão local e corrigido com teste que antes falhava.

### Pendências explícitas

- **Não foi feito teste real Anthropic/Telegram**, por decisão do usuário. Nenhum token externo foi fornecido ou mensagem real enviada. Simulações não confirmam acesso ao modelo, validade do token, entrega remota, qualidade de interpretação ou autocorreção pelo LLM real.
- **Docker Compose não foi executado**, pois Docker não está disponível nesta máquina. O SQL e o seeder foram executados no PostgreSQL 16 nativo; o arquivo Compose permanece a verificar em ambiente com Docker.
- O system prompt tem exemplos e tratamento dos erros de engenharia observados, mas sua iteração empírica com Claude real depende da configuração externa.
- Histórico/fila/deduplicação são locais e voláteis. Reinícios podem perder mensagens aceitas ou reprocessar entregas antigas; não há garantia de exatamente uma vez. Um único worker FastAPI é obrigatório.
- Origem dos números é garantida pelo renderizador; correção de métrica, filtros, joins e interpretação pelo modelo ainda precisa ser avaliada.

As Fases 0–2 e o código da Fase 3 foram implementados e testados localmente. A aceitação manual externa da Fase 3 está pendente. Nenhum conjunto de avaliação acadêmica, rodada de experimentos, validação qualitativa ou redação final foi iniciado.

### Atualização — 09/10/2026, ambiente na nuvem

Esta seção registra validações posteriores; as pendências acima descrevem a execução
histórica de setembro. Python 3.12, dependências do lockfile e PostgreSQL 16 via
Compose, com base sintética seed 42 e 30 clientes. Nenhuma credencial está neste documento.

O planejamento agora aceita até quatro combinações de métrica/medida/período,
executadas com resultados separados. `Total de pedidos` implica quantidade;
`valor dos pedidos` implica valor monetário. Esclarecimentos preservam as demais
métricas e o período. Totais gerais usam templates de SELECT com datas ISO validadas,
definições de status e COUNT de registros. Filtros extras, rankings e detalhamentos
continuam no executor SQL restrito. A classificação pelo modelo ainda exige
avaliação semântica; esses testes não constituem a Fase 4.

- **80 testes passaram**, incluindo PostgreSQL real, sem skips; lint sem erros.
- Regressões: resultados de métricas diferentes não se confundem; uma medida ou
  período pendente impede SQL; falha em uma métrica não apresenta a outra como
  resposta completa; NULL, zero e ausência de linhas permanecem distintos.
- Totais de recebimentos, horas e taxa de resolução conferidos contra registros
  independentes, com cálculo em Python/Decimal nas referências de teste.
- Gemini real: `Gostaria de consultar o total de pedidos e o faturamento emitido
  do mês passado` foi interpretado como setembro de 2026 para ambas as métricas;
  informou ausência de registros e mostrou as datas.
- Continuação real: `E do mês de agosto?` preservou ambas as métricas e o ano
  2026, também sem registros.
- Gemini real: a mesma pergunta para agosto de 2025 retornou **23 pedidos** e
  **404704,29** de faturamento emitido, conferidos contra o PostgreSQL.
- Gemini real: `Pedidos e faturamento emitido em agosto de 2025` pediu a medida
  de pedidos; a resposta `Valor` preservou faturamento e o período e retornou
  **404704,29** para cada métrica, em blocos separados.
- Em uma primeira versão, o executor livre não respeitou bem a separação das
  métricas e ocorreu limite de requisições. Após usar templates para totais simples
  (uma chamada ao planejador por pergunta), os casos reais acima passaram com o
  mesmo modelo, sem troca automática de provedor ou plano de cobrança.

Telegram real autenticado e conversa funcional confirmada pelo usuário antes desta
evolução. O backend deve ser reiniciado para carregar o código; polling e sessões
continuam dependentes desta máquina ativa. Um teste local com Gemini não substitui
a confirmação da nova resposta no chat do usuário.

## Verificação da continuidade — 10/10/2026

_Origem: `docs/verificacoes.md` (consolidado em 2026-11-09)._

### Código e ambiente

Fonte: `arthurhassuma/pac_privado`, base `31ad3a4`, branch `codex/alinhamento-proposta`. Clone em `C:/Users/arthu/PAC - TCC/pac_privado`; arquivos da cópia anterior preservados. Proposta PDF e relatório DOCX já estão versionados em `docs/`.

Usado o ambiente Python 3.13.1 existente na pasta superior e o cluster PostgreSQL 16.14 dedicado do projeto, porta 55439. O login de teste foi `readonly_agent`; a URL foi carregada em memória, sem impressão de credenciais. Não foi preciso instalar dependências nem copiar `.env` para o clone.

O cluster estava parado antes da revisão, foi iniciado para as verificações e encerrado ao final, preservando os dados. Nenhum serviço do ambiente conectado informado pelo usuário foi alterado.

### Evidência de engenharia

- Antes das mudanças: 52 testes aprovados e 13 testes de integração ignorados por ausência de `TEST_DATABASE_URL`.
- Depois das mudanças e revisão, com PostgreSQL: **77 testes aprovados, sem skips** (17,75 segundos nesta execução). Essa duração é da suíte, não latência média do assistente.
- Novos casos verificam frases controladas com precisão decimal, zero vindo de célula, NULL sem inventar zero, aviso de truncamento, diagnóstico sem rede por padrão, credenciais ausentes, autenticação pelos SDKs, schema incompleto e erro de cota sem revelar segredos.
- O fluxo completo testa webhook FastAPI, protocolo Gemini, PostgreSQL real e envio pelo SDK Telegram com transporte externo simulado. O valor renderizado é conferido com consulta independente.
- Os testes de PostgreSQL verificam também a negação de escrita, timeout, limite de linhas e consistência da base sintética.
- Diagnóstico executado contra o banco real: conexão somente leitura e metadados confirmados. As seis verificações de consistência retornaram zero ocorrências.
- `ruff check app scripts tests`, `compileall` e `git diff --check` passaram; `pip check` não encontrou conflitos de dependências.
- Revisão independente identificou que o alias `total` não comprova soma ou moeda. A apresentação foi corrigida para frase neutra, com regressões para média de horas e variação percentual; não acrescenta `R$`, percentuais ou afirmações de soma pelo alias.
- A primeira execução no GitHub passou em 76 testes e falhou no caso de configuração ausente: o teste herdava `DATABASE_URL` do processo CI, pois `_env_file=None` só desativa dotenv. A falha foi reproduzida localmente e a fixture passou a definir credenciais vazias explicitamente. O teste também injeta uma variável ambiente para cobrir essa situação. O resultado da execução remota atual deve ser conferido nos checks da proposta de mudança.

### Limites da verificação

O usuário confirmou conexão Gemini/Telegram em outro ambiente. Não recebemos credenciais e não realizamos chamadas reais a esses dois serviços nesta sessão. Nenhuma mensagem foi enviada pelo assistente ao Telegram e nenhum webhook foi registrado ou removido.

`--testar-conexoes` faz uma chamada pequena de geração ao Gemini, consumindo a cota do projeto configurado. A verificação Telegram usa apenas `getMe`. São testes de conectividade, não testes de interpretação, function calling real ou entrega ponta a ponta. O diagnóstico não verifica plano de cobrança.

Docker Compose e avaliação acadêmica não foram executados. Permanecem fora desta evidência: accuracy, latência média real, feedback da Galvitech e hipótese científica.

### Registro a preencher no ambiente conectado

| Campo | Valor |
|---|---|
| Data e commit usados no teste manual | Não registrado nesta revisão |
| Modelo configurado e versão resolvida | Não registrado nesta revisão |
| `/start` e pergunta `Qual o faturamento?` | Confirmar pergunta de esclarecimento |
| Continuação `janeiro de 2025` | Conferir valor contra SQL do README |
| SQL de referência / valor esperado / valor recebido | Registrar sem credenciais nem identificação pessoal |
| `/limpar` seguido de pergunta sem período | Confirmar novo esclarecimento |
| Observações e falhas externas | Registrar fielmente, sem considerar simulações como acesso real |

A seção [Verificação da entrega — Fases 0–3](#verificação-da-entrega--fases-03) conserva a primeira entrega de 27/09, anterior à migração. A seção [Publicação e nova verificação](deploy.md#publicação-e-nova-verificação--04102026) conserva a importação de 04/10. Este registro complementa esses históricos; não altera seus resultados retroativamente.

## Verificação de engenharia e continuidade até S10–S11

_Origem: `docs/verificacoes.md` (consolidado em 2026-11-09)._

Data: 11/10/2026. O usuário autorizou continuar além do escopo original, até as semanas S10–S11, usando o ambiente do chat “Configurar pac_privado”. A configuração secreta permaneceu nesse ambiente.

### Versão integrada

O commit `8b11f2d9767caa3329b893e069930163c1830dd0`, branch `codex/avaliacao-s7-s11`, integra a versão funcional em nuvem `72469bb` com as proteções da revisão anterior `383de6b`. O PR de rascunho [#2](https://github.com/arthurhassuma/pac_privado/pull/2) reúne as alterações; nenhum merge em main foi feito.

Foi implementado o conjunto de 40 casos (20 desenvolvimento, 20 teste reservado), com 34 consultas SQL de referência e comparação exata dos resultados. O agente registra plano, tentativas, resultado selecionado, modelo resolvido e tokens por chamada, sem estado de rastreio compartilhado entre usuários. O executor preserva checkpoints, interrompe em falhas externas e invalida taxas quando a base muda ou sua verificação final falha.

### Evidências de engenharia

- PostgreSQL 16 local: as 34 consultas de referência executaram sem erro e sem truncamento. O comando `python -m scripts.evaluate validate --env-file ../.env` confirmou o mesmo.
- Suíte local completa antes da última proteção: 106 testes passaram, incluindo PostgreSQL real. Depois da proteção final, os 12 testes do módulo de avaliação passaram.
- [GitHub Actions, execução 38150606149](https://github.com/arthurhassuma/pac_privado/actions/runs/38150606149): **107 testes passaram**, lint aprovado, preparação e validação da base PostgreSQL 16 aprovadas. Commit executado: `8b11f2d`.
- Revisão independente identificou e orientou correções para a coluna auxiliar `registros`, o rótulo genérico de valores médios, a classificação de falhas de transporte e a invalidação da rodada quando a confirmação final do banco falha.

Esses testes comprovam propriedades de engenharia. Não comprovam a meta acadêmica de acurácia, a latência Telegram ou aceitação por um gestor.

### Experimento real

Uma rodada de desenvolvimento foi iniciada no checkout isolado `/workspace/pac_privado-desenvolvimento`, com o commit publicado e configuração original. A versão passou nos 107 testes e no lint também nesse ambiente; as 34 referências foram validadas.

A execução `20261011T151909Z-5411e2fc` registrou D01–D07 como corretos e foi interrompida em D08, com código de saída 2 e `provider_error_400`. O modelo resolvido observado foi `gemini-3.5-flash-lite`. A tentativa SQL de D08 correspondeu ao gabarito, mas nenhum resultado foi selecionado antes do erro externo. A base permaneceu inalterada. Não há taxa oficial disponível para essa rodada parcial. O teste reservado ainda não foi executado.

Os artefatos brutos permanecem em `.local/evaluation/` no ambiente em nuvem. O [relatório revisado](experimentos.md#desenvolvimento--11102026) e seu JSON resumido foram incorporados do commit remoto `8b6fcc5`. O HTTP 400 não constitui evidência de cota (HTTP 429); o rastreamento original não conservou sua causa detalhada. Uma reprodução direcionada de D08 foi autorizada para diagnóstico de integração, preservando esta rodada.

Os arquivos JSON passam a usar LF explicitamente em `.gitattributes`, para conservar o hash de bytes entre checkouts Windows/Linux. O conteúdo congelado do conjunto v1.0.0 permanece idêntico ao blob Git executado na nuvem.

A [reprodução direcionada de D08](experimentos.md#diagnóstico-direcionado-de-d08--11102026) passou na mesma versão, sem reproduzir o HTTP 400. Não foi aplicada correção de causa presumida. A [segunda rodada](experimentos.md#desenvolvimento--rodada-2-11102026), `20261011T153617Z-0a9bf9d9`, passou em D01–D09 e interrompeu D10 por HTTP 429. D11–D20 e o teste reservado permanecem não executados. A base continuou inalterada, e as taxas oficiais continuam nulas. Os nove casos concluídos não apresentaram divergência semântica; não orientaram alteração de prompt. A mensagem detalhada de cota não foi preservada, portanto seu período de recuperação é desconhecido.

Com base na lacuna de evidência observada, foi acrescentada classificação segura de erros API no trace, restrita a rótulos fixos; mensagens brutas não são guardadas. Os três testes de regressão falharam antes da implementação e passaram depois. Os 37 testes de SDK, agente e avaliação passaram com o aprimoramento. Essa alteração de diagnóstico é posterior às rodadas e não deve ser atribuída às versões experimentadas.

### Cronograma e limites

#### Desenvolvimento concluído e congelamento

A [terceira rodada de desenvolvimento](experimentos.md#desenvolvimento--rodada-3-11102026), `20261011T161317Z-1c15b47d`, concluiu 20/20 casos na versão `59c9eb8fa0b73444e770effd3e3e80724049164b`, com intervalo de 60 segundos. Foram aprovadas 16/16 respostas (execution accuracy de 100%) e 4/4 perguntas de esclarecimento (clarification accuracy de 100%). Não houve erro externo ou semântico; não foi necessário alterar prompts. As rodadas incompletas anteriores continuam preservadas e sem taxas oficiais.

O JSON publicado foi conferido contra seus 20 registros: 21 turnos, 45 requisições e média de 1,733 s para agente e banco. O hash do conjunto coincide com o arquivo local; os fontes de aplicação, avaliação, scripts e banco permanecem idênticos à versão executada. O ambiente de origem validou os hashes dos artefatos brutos, a base inalterada, 110 testes de engenharia, lint e 34 referências SQL antes da rodada. Esses resultados de desenvolvimento não substituem teste reservado.

Em continuidade autorizada pelo usuário, foram congelados os fontes `59c9eb8`, o conjunto v1.0.0 (SHA256 `6a42eeb54169b15751eec3ff2e7657f52cdab96dc674dbaa7be16bc5c620bc2c`), o modelo `gemini-3.5-flash-lite`, os limites e a base da terceira rodada. Uma única execução de T01–T20 foi realizada no ambiente configurado, mantendo o intervalo de 60 segundos e parada em qualquer erro externo. Nenhuma correção será orientada pelo teste reservado sem declarar contaminação e preparar outra amostra independente.

#### Teste reservado concluído

O [teste reservado](experimentos.md#teste-reservado--11102026), rodada `20261011T163747Z-5fe3b066`, concluiu T01–T20 com saída 0 e 20/20 casos aprovados: execution accuracy de 16/16 (100%) e clarification accuracy de 4/4 (100%). Não houve erro externo ou semântico, ajuste de código/prompt, repetição ou consulta adicional após a conclusão.

O ambiente de origem recalculou a aprovação dos casos e as taxas dos checkpoints usando o scorer congelado, verificou seus 21 turnos e os hashes dos artefatos brutos. A revisão local confirmou identidade de fontes/conjunto/modelo/limites/bibliotecas/base com a rodada de desenvolvimento, IDs e totais do relatório, soma das 48 requisições e latência média de 1,649 s. Todas as chamadas tiveram uso informado: 74.713 tokens. Base, configuração secreta e bot foram preservados.

A meta de execution accuracy estritamente superior a 70% foi atingida nesta amostra reservada. O resultado mede o sistema híbrido completo, com templates para totais e SQL gerado para análises; não demonstra acurácia exclusiva de geração livre de SQL ou generalização ampla. A latência continua restrita a agente e banco. Os 110 testes são evidência de engenharia da mesma versão executados antes do desenvolvimento, não 110 perguntas reais nem testes repetidos nesta avaliação.

S7–S8: conjunto e executor entregues, com revisão técnica do gabarito; revisão por professor/especialista permanece recomendada. S8–S10: desenvolvimento e teste reservado completos, preservando as rodadas interrompidas. S10–S11: diagnóstico, rastreamento, regressões, análise de desenvolvimento, congelamento e avaliação reservada entregues. Nenhuma falha semântica justificou nova iteração de prompt. As evidências estão no PR #2, sem merge em main ou atualização automática do bot.

Validação qualitativa com gestor, comparação com dashboards e redação final pertencem às etapas posteriores. A latência do executor mede agente+banco e não equivale a transporte Telegram ponta a ponta.


### Ampliação até a entrega final

Posteriormente, o responsável autorizou desenvolver até o final e confirmou aceite do gestor em 11/10/2026, sem síntese de feedback. O [registro declaratório](avaliacao.md#registro-de-aceite-do-gestor) documenta essa origem; não constitui estudo qualitativo ou aprovação institucional. O [relatório final](relatorio-final-pac-viii.md), o [roteiro de demonstração](apresentacao.md#demonstração-e-reprodução-da-entrega) e o [índice da entrega](README.md#entrega-final--pac-extensionista-viii) foram preparados.

A [reprodução Docker isolada](#verificação-de-reprodução-para-entrega-final) aprovou 110 testes, sem skips, lint e 34 referências SQL. A base recém-gerada teve o mesmo fingerprint dos experimentos. Fontes congelados preservados; nenhuma nova chamada Gemini/Telegram ou ajuste guiado pelo teste reservado. O parágrafo anterior sobre etapas posteriores é histórico e foi superado por esta ampliação. Comparação com dashboards e latência Telegram ponta a ponta continuam não medidas.

## Verificação da base comparativa — 11/10/2026

_Origem: `docs/verificacoes.md` (consolidado em 2026-11-09)._

Escopo: cenário sintético de janeiro de 2025 a outubro de 2026, seed 42, 100 clientes. Não altera os resultados acadêmicos congelados na versão `59c9eb8`.

### PostgreSQL local

Carga executada em PostgreSQL 16.14, cluster separado `.local/comparativo/pgdata`, banco `bi_comparativo`, porta 55440. Configuração privada em `.local/comparativo/.env`. O cluster anterior na porta 55439 foi preservado.

- 100 clientes; 681 contratos; 5.100 pedidos; 5.809 notas; 1.700 indicadores.
- 22 meses completos e todos os status previstos em cada mês.
- Seis verificações de integridade aprovadas: clientes com contratos; pedidos e competências dentro do contrato; emissão após pedido e ausência de faturamento de pedido cancelado; limites financeiros por pedido e contrato.
- Faturamento, quantidade de pedidos válidos e recebimentos mensais consultados por `readonly_agent`, com timeout e limite do executor. As 22 linhas de cada resultado coincidem com o resumo mensal do gerador.
- As seis referências SQL também passaram pelo executor de leitura: 22, 2, 22, 22, 22 e 4 linhas. A comparação de janeiro a outubro retornou BRL 8904430,85 em 2025 e 18433975,14 em 2026. A referência usa `date_part`, compatível com a allowlist atual, sem ampliar permissões.
- **117 testes de engenharia aprovados** com PostgreSQL real e APIs externas simuladas, em 15,65 s. Ruff aprovado. A cobertura adicional verifica geração determinística, relações temporais/financeiras e ausência de status. A integração não pressupõe mais que 2026 esteja vazio; agosto de 2027 mantém o caso sem registros.

O hash canônico do perfil original, seed 42 e 30 clientes, permaneceu `194ee30b0d09be6fc3c49647c7c849a6246103b07620eae14960949156d12476` antes/depois da alteração. Bibliotecas e seed iguais são necessárias para reprodução. O hash comparativo consta no resumo JSON.

### Exemplos conferidos no banco

| Métrica | Agosto/2025 | Agosto/2026 |
|---|---:|---:|
| Pedidos válidos | 185 | 289 |
| Faturamento emitido válido (BRL) | 1239387,25 | 2060162,05 |
| Recebimentos (BRL) | 897881,27 | 1372786,38 |

Números extraídos de consultas SQL. Não são uma nova rodada de avaliação com Gemini e não demonstram por si só transporte Telegram. A verificação no ambiente conectado deve ser registrada separadamente. Outubro inteiro contém cenário futuro sintético em relação a 11/10/2026.

### Apresentação

Foi criada uma revisão de 14 slides em `apresentacao/Apresentacao-PAC-VIII-Arthur-Hassuma-Base-Comparativa.pptx`, na pasta de trabalho do responsável (fora deste repositório), com PDF de visualização e roteiro correspondente. A revisão mostra as novas contagens e comparação de agosto, e identifica que as taxas dos experimentos pertencem à base original. Os exemplos novos estão identificados como resultados esperados conferidos por SQL. A versão anterior foi preservada. Validação estrutural e geométrica aprovada; cinco tabelas editáveis, fonte Arial e revisão visual dos 14 slides. O PDF foi montado das prévias renderizadas; o PowerPoint mantém textos e tabelas editáveis.

### Ambiente conectado

A [verificação em Docker, Gemini e Telegram](#verificação-e-ativação-da-base-comparativa) foi concluída no ambiente conectado em 11/10/2026, com fonte documental publicada no commit `00b9c8428f22820b1b44b1b209c5faae41d7be1d`. A nova base foi ligada ao bot, com um único polling e rollback preservado. Os dois exemplos Gemini conferiram 185 pedidos / 1239387,25 em agosto de 2025 e 289 pedidos / 2060162,05 em agosto de 2026. A entrega de resposta no chat ainda depende da mensagem humana no Telegram. São exemplos pontuais; não alteram as métricas dos experimentos anteriores.

## Verificação e ativação da base comparativa

_Origem: `docs/verificacoes.md` (consolidado em 2026-11-09)._

11/10/2026 (America/Sao_Paulo). Fonte preparada: `11f8ecf19b241bdece42dd04e3195b9405d1e9b4`, em checkout separado `/workspace/pac_privado-comparativo`. Evidências publicadas somente na branch `codex/base-comparativa-verificacao`, criada a partir dessa versão; o branch de apresentação não foi alterado.

### Carga e identidade

PostgreSQL 16 em projeto Compose `codex-pac-comparativo-3cb7b9ef`, volume exclusivo e porta local `127.0.0.1:58917`, banco **bi_comparativo**. Senhas de teste novas e configuração privada em `.local/comparativo.env`, permissão 0600 e ignorada pelo Git. Compose validado com `config --quiet`, sem imprimir valores interpolados; imagem existente usada com `--pull never`.

Comandos executados com `--env-file .local/comparativo.env`:

```sh
python -m scripts.manage_db init --env-file .local/comparativo.env
python -m scripts.manage_db seed --profile comparativo --clients 100 --seed 42 --start-month 2025-01 --end-month 2026-10 --env-file .local/comparativo.env
python -m scripts.manage_db validate --env-file .local/comparativo.env
python -m scripts.manage_db coverage --env-file .local/comparativo.env
```

Todos concluíram com saída 0. Contagens verificadas:

| Entidade | Registros |
|---|---:|
| Clientes | 100 |
| Contratos | 681 |
| Pedidos | 5.100 |
| Faturamento | 5.809 |
| Indicadores operacionais | 1.700 |

Cobertura completa dos 22 meses, de janeiro/2025 a outubro/2026, incluindo entidades, status e recebimentos mensais. Os seis critérios de consistência retornaram zero inconsistências.

Hash canônico dos dados **gerados**: `bbef709101afee9888a6232c2d5a5736b241384a9fed9a9eb468d1190a9ab30a`, conforme `json.dumps(..., ensure_ascii=False, sort_keys=True, default=str)`. Todos os registros carregados foram lidos pela role restrita e comparados em valor com o gerador: iguais. A serialização bruta do PostgreSQL pode incluir zeros adicionais pela escala `numeric` do schema; não confundir esse JSON com a serialização do gerador. Fingerprints separados das tabelas ficaram nas evidências locais.

### Engenharia e consultas

Python 3.12.14 e dependências existentes reutilizados, sem reinstalação. Com `TEST_DATABASE_URL` da nova base:

- `python -m pytest -q --strict-markers`: **117 passed in 3.17s**, incluindo PostgreSQL real, sem skips.
- `python -m ruff check app scripts tests evaluation`: aprovado.
- As seis referências de `docs/dados/consultas-base-comparativa.sql` executaram pela role `readonly_agent`, em transações de leitura. Linhas retornadas por consulta: **22, 2, 22, 22, 22, 4**, sem truncamento.
- A consulta anual original com `extract` foi recusada pela allowlist do agente. Conforme correção documental autorizada, foram feitas apenas as substituições para `date_part('year', emissao)` e `date_part('month', emissao)`. Depois disso, as seis referências também passaram pela ferramenta SQL do agente. Não foi relaxada a política nem alterado código de produto.

Não foi reexecutado o conjunto reservado e nenhuma taxa acadêmica anterior é atribuída a esta base.

### Dois exemplos reais com Gemini

Foram executados **exatamente dois exemplos**, sem histórico anterior, perguntando a quantidade total de pedidos e o faturamento emitido de agosto de cada ano. O modelo planejou duas métricas; totais vieram dos templates do agente. Cada exemplo usou uma requisição SDK, com uma tentativa por requisição. Modelo resolvido: `gemini-3.5-flash-lite`; sem troca de modelo ou plano de cobrança.

| Período | Pedidos selecionados | Faturamento emitido selecionado | Resultado |
|---|---:|---:|---|
| Agosto/2025 | 185 | R$ 1.239.387,25 | Resposta final correta |
| Agosto/2026 | 289 | R$ 2.060.162,05 | Resposta final correta |

Gemini respondeu aos dois exemplos; nenhum erro externo ou bloqueio de cota ocorreu. São verificações manuais pontuais, não uma nova avaliação de acurácia. Não houve repetição de exemplos.

### Bot ligado à nova base

Os processos originais identificados estavam ativos e o backend respondeu à verificação de saúde antes da troca. Foi preservado rollback privado com comandos, diretórios e ambiente originais, sem modificar `/workspace/pac_privado/.env`.

O supervisor antigo foi encerrado primeiro, para impedir o reinício concorrente do polling. Só depois de confirmar seu encerramento e o do filho foi encerrado o backend antigo. O novo gerenciador usa o mesmo lock de polling; inicializa o backend com um worker e apenas um polling.

Verificações após a troca:

- Backend com checkout novo e `DATABASE_URL` da role `readonly_agent` em **bi_comparativo**, conferidos privadamente no processo; URL administrativa vazia no ambiente do bot.
- `/health`: HTTP200, Telegram autenticado, IA e banco configurados.
- Autenticação Telegram ocorreu na inicialização (`getMe`); o log sanitizado registrou “Polling ativo”. Isso comprova autenticação/recebimento iniciado, **não entrega de uma resposta no chat**.
- Varredura dos processos confirmou exatamente **um polling**. Processos novos: gerenciador 826287, backend 826288, polling 826291, no momento da verificação.
- Chave Gemini, token Telegram e IDs autorizados existentes foram reutilizados somente privadamente. Não houve envio proativo de mensagens.
- O restart criou sessões de conversa novas em memória. Um teste humano no chat privado ainda deve confirmar pergunta, resposta e continuidade, por exemplo com os dois períodos acima.

Runtime local: `.local/runtime-manager.py`; estado `.local/runtime-state.json`; log sanitizado `.local/runtime.log`. Rollback: executar `/workspace/pac_privado/.venv/bin/python /workspace/pac_privado-comparativo/.local/rollback-original.py`. Esse helper encerra o gerenciador novo antes de restaurar backend e supervisor originais. A configuração privada de rollback é 0600 e ignorada; o rollback foi preparado e inspecionado, mas não executado, para manter o bot na base nova. O volume comparativo permanece ativo porque agora serve o bot.

### Preservação e limites

A base dos experimentos manteve exatamente o fingerprint anterior; o checkout congelado `59c9eb8` e seus hashes de fontes continuam intactos. O `.env` original permaneceu byte a byte igual. As rodadas acadêmicas e seus artefatos não foram alterados. Apenas os processos desse bot foram substituídos pela configuração comparativa autorizada.

Outubro/2026 contém o mês inteiro como **cenário futuro sintético** em relação a 11/10/2026; status representam uma fotografia em **31/10/2026**. Não são fatos observados de uma empresa real.

Evidências locais ignoradas: `.local/preparation.json`, `.local/coverage.json`, `.local/reference-queries.json`, `.local/manual-examples.json` e `.local/switch-result.json`. Não foram publicados credenciais, valores de assinaturas, bancos ou logs HTTP brutos. `main` permanece sem merge.

## Verificação de reprodução para entrega final

_Origem: `docs/verificacoes.md` (consolidado em 2026-11-09)._

Data: 11/10/2026 (America/Sao_Paulo). Verificações executadas no ambiente em nuvem Linux x86_64, com Python 3.12.14 e dependências existentes em `/workspace/pac_privado/.venv`. Nenhuma chamada Gemini/Telegram foi feita, nenhum resultado reservado orientou ajustes e nenhuma feature ou fonte congelado foi alterado.

### Identidade conferida

- Checkout de execução isolado: `/workspace/pac_privado-desenvolvimento-rodada3`, HEAD destacado em `59c9eb8fa0b73444e770effd3e3e80724049164b`.
- Todos os hashes de aplicação, avaliação, scripts e SQL coincidem com o manifesto da rodada3 `20261011T161317Z-1c15b47d`; os fontes continuam idênticos após os checks. Relatórios locais não rastreados são apenas evidências previamente publicadas, não mudanças de produto.
- Conjunto v1.0.0: SHA256 `6a42eeb54169b15751eec3ff2e7657f52cdab96dc674dbaa7be16bc5c620bc2c`.
- Fontes, hash agregado: `d46a1a6fbb6c79507704cc03ff8aa6fe5db48c1788fb588e7f1d2442d7b0d860`.
- Base congelada, hash agregado: `d4f6623f1de2d8050ca3901b231ff00e05f1627bb09ecf8f7a7f0db86578cf6d`. Agregados usam SHA256 de `evaluation.runner.dump` (UTF-8, chaves ordenadas, indentação 2).
- A versão documental `13ff665a49f7cf0b0143e034f7ee4f1be8d37cfd` foi obtida e inspecionada sem mudar HEAD: seus fontes congelados e workflow são idênticos aos de `59c9eb8`. Seu commit imediato altera apenas documentação; a diferença acumulada inclui relatórios de evidências.

### Docker/Compose e isolamento

Docker CLI e daemon 28.4.0 e Compose v2.40.3 disponíveis. A imagem `postgres:16` já existia; não houve instalação de Docker nem download de imagem (`--pull never`).

A reprodução usou o `docker-compose.yml` original com projeto exclusivo `codex-pac-final-429b23fb50`, volume próprio do projeto e porta `127.0.0.1:53581`. A configuração foi validada com `config --quiet`, sem imprimir configuração interpolada. `--env-file /dev/null` impediu carregar configuração secreta original no Compose. Senhas administrativas e de leitura novas foram geradas apenas em memória e passadas no ambiente dos subprocessos; não são salvas ou publicadas. As configurações Gemini e Telegram desses subprocessos ficaram vazias.

Comandos Docker executados, todos com saída 0:

```sh
docker --version
docker compose version
docker info --format '{{.ServerVersion}}'
docker compose --env-file /dev/null -f docker-compose.yml -p codex-pac-final-429b23fb50 config --quiet
docker compose --env-file /dev/null -f docker-compose.yml -p codex-pac-final-429b23fb50 up -d --pull never
docker compose --env-file /dev/null -f docker-compose.yml -p codex-pac-final-429b23fb50 exec -T db pg_isready -U bi_owner -d bi_sintetico
docker compose --env-file /dev/null -f docker-compose.yml -p codex-pac-final-429b23fb50 down --volumes --remove-orphans
```

As variáveis de banco desses comandos apontavam exclusivamente ao banco descartável; os valores não aparecem no documento. Após a limpeza, consultas filtradas pelo rótulo desse projeto confirmaram ausência de containers e volumes remanescentes. Nenhum recurso de outro projeto foi removido.

### Reprodução da preparação e checks

No checkout congelado, com Python existente e ambiente apontando ao banco isolado:

| Comando | Evidência | Saída |
|---|---|---:|
| `python -m scripts.manage_db init` | Schema e role somente leitura criados em cluster novo | 0 |
| `python -m scripts.manage_db seed --seed 42 --clients 30` | 30 clientes, 56 contratos, 672 pedidos, 628 registros de faturamento, 672 indicadores | 0 |
| `python -m scripts.manage_db validate` | Zero inconsistências nos seis critérios | 0 |
| `python -m pytest -q --strict-markers` | **110 passed in 2.97s**, com PostgreSQL real e sem skips | 0 |
| `python -m ruff check app scripts tests evaluation` | Todos os checks aprovados | 0 |
| `python -m scripts.evaluate validate --env-file /dev/null` | **34 referências SQL validadas**, nenhuma chamada Gemini | 0 |
| `python -m pip check` | Nenhuma dependência incompatível | 0 |

O fingerprint completo da base isolada recém-gerada coincidiu exatamente com o manifesto congelado, inclusive hashes e contagens das cinco tabelas. A validação das referências é um check SQL somente leitura, não uma nova avaliação de modelo nem uma repetição do teste reservado.

O `pip check` também passou antes da reprodução. O aviso de cache não gravável do pip não afetou o resultado; nenhuma dependência foi instalada ou atualizada.

### Workflow da versão documental

O workflow `.github/workflows/tests.yml` de `13ff665` foi comparado byte a byte com o da versão congelada: idêntico. SHA256 `05f301e538abf692f0cabe55a84d3b6fbe1b5300e1d061db2ed79bc5ed259f0d`.

Foi conferido que ele prepara PostgreSQL 16 descartável, usa Python 3.13, instala `requirements-lock.txt`, executa `pip check`, lint, init/seed/validate e `pytest -q --strict-markers`. A sequência de checks de banco, lint e testes foi reproduzida localmente nesta verificação, além das 34 referências SQL.

A consulta read-only `gh run list --repo arthurhassuma/pac_privado --commit 13ff665a49f7cf0b0143e034f7ee4f1be8d37cfd --json databaseId,headSha,status,conclusion,url --limit 10` retornou **Forbidden** no acesso à API GitHub. Portanto, a aprovação remota informada pelo coordenador não foi confirmada independentemente aqui; nenhum workflow foi disparado. O acesso Git para obter código funcionou. Não se deve apresentar a reprodução local como execução GitHub Actions observada.

### Preservação e limitações

- A base original foi acessada somente para fingerprint antes/depois: conteúdo inalterado e igual ao manifesto congelado.
- O hash do `.env` original permaneceu igual, sem publicar conteúdo ou hash secreto. Os mesmos processos originais do backend, supervisor e bot permaneceram ativos; não houve reinício ou envio de mensagens.
- Evidências locais sanitizadas: `.local/final-delivery/verification.json`, ignorado pelo Git. Apenas este documento é publicado na branch `codex/experimento-desenvolvimento`; não há merge em main.
- Foi verificada a reprodução com dependências existentes e Python 3.12.14. Não se verificou instalação limpa do lock nem execução Python 3.13/GitHub Actions nesta rodada.
- Estes são checks de engenharia/reprodução, não novo experimento de acurácia ou medida Telegram ponta a ponta.
- O usuário informou validação e aceite do gestor em 11/10/2026, sem síntese de feedback. Isso é informação recebida, não observação ou validação realizada por este executor. Nenhuma síntese de feedback foi inventada.

## Verificação do treinamento e das análises gerenciais — 12/10/2026

_Origem: `docs/verificacoes.md` (consolidado em 2026-11-09)._

### Entrega e resultados locais

Plano aprovado pelo usuário, executado pelo próprio agente em checkout isolado. Branch `codex/treinamento-intencoes-implementacao`, [PR privada draft 4](https://github.com/arthurhassuma/pac_privado/pull/4), base `codex/base-comparativa`. Não houve merge em `main`, publicação pública ou mudança de licença. O PDF final anteriormente modificado pelo usuário foi preservado fora desta alteração.

Implementados: corpus supervisionado por grupos, treino TF-IDF/regressão logística, exportação JSON, inferência sem bibliotecas de treino, sugestão opcional de exemplos de treino, contrato gerencial, comparação/contribuição/séries/rankings/participação/desvios/fluxos, renderer PT-BR com emojis, conjunto gerencial independente, documentação e CI. As quatro camadas, duas tools, allowlist SELECT, role readonly, timeout, limite e autocorreção permanecem.

Treinamento real: 280 formulações sintéticas em 70 cenários, divididos por grupo em 196/28/56 textos (49/7/14 grupos). Artefato congelado em `935aa4b` antes de executar o teste uma única vez. Validação bruta 12/28; teste bruto 48/56, macro F1 0,8. Classe operacional 0/8 no teste. Limiar 0,7 teve cobertura aceita zero em validação e teste. Por essa evidência da validação, o classificador fica desligado por padrão. Não há benefício demonstrado para o agente. [Resultados completos](dados/treinamento-intencoes-resultados-v1.json).

Verificação local mais recente: **188 testes aprovados, sem integrações puladas, em 22,18 s**, PostgreSQL 16 real e APIs externas simuladas. Ruff aprovado. `pip check`: nenhuma dependência quebrada. Validação do corpus confirmou sete classes de 40 formulações e 70 grupos. Um processo com imports de sklearn/numpy/scipy explicitamente bloqueados importou o agente e carregou o modelo JSON; não houve chamada externa nessa prova.

As **28 referências SQL gerenciais** foram executadas na role restrita. Os **20 cenários de resposta de desenvolvimento com planejador simulado** coincidiram com seus gabaritos independentes. Isso mede compilação, execução e apresentação, sem provar interpretação pelo Gemini. O novo conjunto contém 25 casos de desenvolvimento e dez reservados, independente dos 40 casos antigos e do corpus do classificador.

### Revisão e regressões

Uma revisão independente de toda a alteração encontrou quatro problemas importantes. Todos foram reproduzidos antes da correção: a bateria teve sete falhas e 33 aprovações. Correções: zero `numeric` escalado usa representação decimal fixa sem arredondar; menores rankings seguem SQL personalizado; taxa sem registros conserva NULL; participação/contribuição de taxas seguem executor que preserva numeradores e denominadores. Nenhum achado menor ficou adiado.

O CI identificou mais dois testes que presumiam faturamento em 2026 no perfil original. Uma regressão local de período monetário vazio falhou antes da correção. Comparações aditivas agora usam zero somente com ausência comprovada por COUNT=0; valor desconhecido com registros e taxa sem chamados permanecem NULL. As referências usam soma e contagem, sem depender de registros nos dois anos. Esses ajustes ocorreram antes do reservado gerencial.

### Situação externa

Rodada real de desenvolvimento iniciada no ambiente já configurado, com classificador desligado, fonte `1cc9197`, base comparativa isolada e intervalo de 60 segundos. Resultados finais, identificação do modelo, tokens e fingerprints serão importados do relatório sanitizado do ambiente conectado. Esta página não antecipa taxas de uma rodada incompleta.

Congelamento gerencial, novo reservado e atualização do bot ainda estão em andamento. O bot comparativo anterior permanece preservado enquanto a avaliação é concluída. Confirmação de `/health`, autenticação Telegram e polling não substitui uma mensagem humana para comprovar entrega e continuidade.

Os resultados antigos `59c9eb8` não foram repetidos ou alterados. Outubro/2026 inteiro é cenário sintético e os status correspondem a 31/10/2026; não representam fatos observados de uma empresa real. Aceite do gestor é o anteriormente declarado pelo usuário, sem síntese de feedback; não foi inventada nova validação qualitativa.

### Material da apresentação

Complemento de oito slides, PowerPoint editável, PDF de prévia e roteiro em `C:/Users/arthu/PAC - TCC/apresentacao/`, com sufixo `Treinamento-Gerencial`. Versões anteriores preservadas. Métricas do classificador e resultados do agente aparecem separados; exemplo financeiro identificado como formato demonstrativo com valores SQL previamente conferidos. [Guia de defesa](avaliacao.md#como-explicar-o-treinamento-na-apresentação).

### Rulings da execução

- A ferramenta nativa não resolveu o repositório aninhado; usado worktree manual em pasta ignorada, sem mover trabalho do usuário.
- Cabeçalhos de tarefas adaptados para o formato reconhecido pelos scripts de acompanhamento, sem mudar conteúdo.
- Cluster local existente iniciado sem recriar ou recarregar banco, para verificar integrações.
- Lock de dependências de treino separado: Python 3.12/3.13 para treino; runtime mantém seu suporte anterior e não exige sklearn.
- Classificador desativado por decisão de validação; teste observado não foi usado para retreinar ou escolher novo limiar.
- Evidência temporal reforçada; mês explícito exige limites desse mês. Continuação ambígua pede esclarecimento.
- Resumo limitado por caracteres, permitindo todas as linhas que cabem; cortes têm aviso e preservam dígitos.
- Testes assíncronos no Windows exigiram execução com recursos locais e diretório temporário próprio; sem APIs externas.
- Prompts on/off iguais nos vinte casos conferidos: omitida rodada externa duplicada, sem alegar ganho de acerto ou latência.
- Revisão realizada antes do reservado gerencial, para permitir corrigir achados sem contaminar sua interpretação.
- Filtros/status/médias/arredondamento e menores rankings usam SQL personalizado; chamados abertos são medida, não status financeiro.
- Corpus descrito em grupos independentes, declarando correlação das quatro formulações de cada cenário.
- Zero decimal, taxas e ausência monetária corrigidos por regressões; allowlist não ampliada. Removida sugestão de `extract` do prompt.
- Integração permanece em PR privada draft, conforme autorização anterior; sem nova pergunta de aprovação para a mesma ação.
