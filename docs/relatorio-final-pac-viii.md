# Relatório final do assistente conversacional de BI

**Autor:** Arthur Vinicius de Almeida Hassuma. **Curso:** Engenharia de Software, Centro Universitário Católica de Santa Catarina. **Disciplina:** PAC Extensionista VIII. **Local e data:** Jaraguá do Sul, 11 de outubro de 2026.

## 1 INTRODUÇÃO

Este relatório apresenta o desenvolvimento e a avaliação de um assistente conversacional de Business Intelligence para consultas sobre serviços B2B. O protótipo permite que um gestor autorizado formule perguntas em português pelo Telegram e receba indicadores provenientes de uma base PostgreSQL sintética. A entrega dá continuidade à proposta aprovada no PAC Extensionista VII, preservada entre os anexos do repositório.

O problema abordado é a necessidade de consultar indicadores sem escrever SQL ou navegar por ferramentas analíticas. A solução conecta um aplicativo de mensagens a um agente que interpreta a pergunta, solicita esclarecimento quando necessário e consulta dados sob restrições de segurança. O domínio foi inspirado na Galvitech, empresa de desenvolvimento de software sob medida em Joinville, Santa Catarina. Nenhuma informação real de clientes foi utilizada.

A avaliação implementou 40 casos, separados em 20 de desenvolvimento e 20 de teste reservado. Na versão congelada, ambas as partições foram concluídas com 20 casos corretos. O teste reservado apresentou execution accuracy de 16/16 respostas, equivalente a 100%, e acerto de 4/4 esclarecimentos. O tempo médio observado foi de 1,649 segundo para agente e banco. Esse tempo não inclui o transporte Telegram e não comprova a meta de latência ponta a ponta.

O aceite do gestor foi registrado em 11/10/2026 a partir de informação do responsável pelo projeto. Foi disponibilizado apenas o aceite, sem síntese de feedback. Portanto, o relatório distingue a realização declarada da validação qualitativa dos resultados experimentais rastreáveis. Também não afirma redução de tempo em relação a dashboards, pois essa comparação não foi medida.

## 2 DESCRIÇÃO DO PÚBLICO BENEFICIADO PELAS AÇÕES DE EXTENSÃO

O público principal é composto por gestores de empresas de serviços B2B que precisam consultar faturamento, recebimentos, pedidos, contratos e indicadores operacionais. O canal em português permite formular uma solicitação na linguagem habitual de trabalho. Para o MVP, o acesso é limitado a usuários explicitamente autorizados e a conversas privadas no Telegram.

A Galvitech fornece o contexto de domínio descrito na proposta. A base sintética representa clientes, contratos e movimentações associadas, permitindo demonstrar o fluxo sem publicar informações comerciais ou pessoais reais. O aceite informado não autoriza atribuir à empresa resultados econômicos, adoção em produção ou ganhos de produtividade não documentados.

A comunidade acadêmica é beneficiada pela documentação da arquitetura, pelas consultas de referência e pelo registro das limitações. O relatório da etapa anterior descreve avaliação por pares da proposta; esse histórico não foi reinterpretado como nova pesquisa com participantes ou como avaliação do protótipo executada nesta etapa.

## 3 OBJETIVOS

### 3.1 OBJETIVO GERAL

Desenvolver e avaliar um assistente conversacional de BI em português, integrado a um aplicativo de mensagens e a uma base relacional sintética, com consultas somente de leitura e respostas numéricas rastreáveis aos resultados do banco.

### 3.2 OBJETIVOS ESPECÍFICOS

Modelar e carregar uma base de serviços B2B com integridade referencial; implementar a interface Telegram e o backend FastAPI; integrar o modelo Gemini a ferramentas controladas de consulta; tratar ambiguidades e falhas SQL; preservar a precisão dos valores apresentados; e executar uma avaliação com referências independentes dos resultados gerados pelo agente.

Os critérios da proposta incluem um conjunto de 30 a 50 perguntas, execution accuracy estritamente superior a 70%, tempo médio ponta a ponta inferior a dez segundos e validação com gestor. Nesta entrega, o conjunto contém 40 casos e a meta de acurácia foi atingida na amostra reservada. A meta de tempo completo e a comparação com dashboards permanecem sem medição. A validação com gestor foi considerada realizada com aceite declaratório.

## 4 DESCRIÇÃO DAS PRINCIPAIS ATIVIDADES REALIZADAS

### 4.1 Fundamentação e continuidade da proposta

A tradução de linguagem natural para SQL exige interpretar a intenção, relacioná-la ao schema e produzir uma consulta que retorne o resultado esperado. Spider oferece um conjunto de avaliação entre diferentes bancos e domínios (YU et al., 2018). BIRD aborda desafios relacionados a valores de dados, conhecimento e eficiência em bases maiores (LI et al., 2023). Esses trabalhos fundamentam a necessidade de avaliar a execução, mas seus resultados não são diretamente comparáveis ao conjunto restrito deste projeto.

Guo et al. (2019) investigam uma representação intermediária entre linguagem natural e SQL. No protótipo, um planejamento estruturado identifica métrica, medida, período e operação antes da execução. Essa decisão é uma implementação própria e não uma reprodução do IRNet. O uso de templates para totais simples também significa que a avaliação mede um sistema híbrido, e não apenas geração livre de SQL.

A proposta previa Claude ou GPT-4o. Por decisão do responsável, o provedor foi alterado para Gemini. O modelo configurado e resolvido nas rodadas foi gemini-3.5-flash-lite. A disponibilidade observada refere-se ao ambiente e às datas registradas; o nome é um alias e não identifica pesos imutáveis. Nenhum resultado deste relatório depende de atribuir desempenho ao provedor inicialmente proposto.

### 4.2 Modelagem e geração da base sintética

O schema possui cinco entidades: clientes, contratos, pedidos, faturamento e indicadores_operacionais. Cada contrato pertence a um cliente; pedidos, faturamentos e indicadores se relacionam aos contratos e às movimentações correspondentes. Chaves primárias, chaves estrangeiras, constraints e índices estão documentados em db/schema.sql e no dicionário de dados.

A geração utiliza Faker, seed declarada 42 e carga transacional. A base avaliada contém 30 clientes, 56 contratos, 672 pedidos, 628 registros de faturamento e 672 registros de indicadores operacionais. Verificações de consistência examinam os relacionamentos e os valores de domínio. A seed, isoladamente, não garante identidade entre ambientes com bibliotecas diferentes; por isso, os experimentos registram também contagens e hashes do conteúdo das tabelas.

As métricas distinguem faturamento emitido de recebimentos e quantidade de pedidos de seu valor monetário. Perguntas sem período ou com medida indefinida solicitam esclarecimento. Os dados sintéticos de movimentação abrangem 2024 e 2025; perguntas sobre períodos sem registros não devem apresentar um valor financeiro inventado.

### 4.3 Arquitetura e fluxo de consulta

A interface utiliza python-telegram-bot. O backend Python com FastAPI recebe updates, controla autorização, mantém sessões por usuário e orquestra o agente. O agente usa o SDK Gemini e function calling para as ferramentas get_schema e execute_sql. A camada de dados utiliza PostgreSQL 16 e psycopg.

O planejamento pode representar até quatro combinações de métricas, medidas e períodos. Totais simples usam consultas padronizadas; análises e filtros adicionais utilizam SQL gerado pelo modelo dentro da política permitida. Cada consulta mantém resultados próprios. Essa separação evita reutilizar o resultado de uma métrica como resposta para outra.

Quando falta informação necessária, o agente esclarece antes de consultar dados de negócio. Se o SQL falha, o erro do banco retorna ao contexto do modelo para tentativa limitada de correção. A aplicação controla o loop e desativa a execução automática de funções pelo SDK. As assinaturas e os identificadores nativos das chamadas são preservados, sem publicação de seus valores.

Polling e webhook passam pelo mesmo backend. O histórico, a fila e a deduplicação são mantidos em memória. O MVP exige um único processo FastAPI; reiniciar pode perder histórico ou updates aceitos. Não há garantia de entrega exatamente uma vez nem infraestrutura distribuída nesta entrega.

### 4.4 Segurança e origem dos valores

Uma allowlist explícita de nós da árvore sintática PostgreSQL permite somente consultas SELECT sobre tabelas e funções autorizadas. Comandos de escrita, DDL, SELECT INTO, locks e acesso a schemas externos são rejeitados. A segunda barreira é a role readonly_agent, com permissão somente de leitura, sem associação a roles privilegiadas. As transações são read-only.

O limite configurado é de 100 linhas por consulta, timeout SQL de 3.000 milissegundos, até três erros SQL e seis rodadas de ferramentas. Limites evitam execução sem controle, mas não constituem prova da latência média. O acesso administrativo é restrito aos comandos de preparação do banco.

O modelo seleciona uma referência ao resultado e o backend renderiza as células. Valores decimais não são convertidos para ponto flutuante nem arredondados na apresentação. Números e datas apresentados vêm da consulta; cálculos solicitados são realizados em SQL. A origem numérica não garante interpretação correta: filtros, joins e agregações precisam ser avaliados contra o gabarito.

### 4.5 Protocolo experimental

O conjunto versionado possui 40 casos, com 20 de desenvolvimento e 20 reservados. Cada partição contém 16 casos de resposta e quatro casos exclusivos de esclarecimento. Há perguntas com múltiplas métricas e conversas com mais de um turno. No conjunto completo, foram preparadas e executadas 34 consultas SQL de referência.

A revisão técnica do gabarito verifica schema, interpretação e execução SQL. Não foi registrada revisão independente por professor ou especialista de domínio. A aprovação considera o resultado efetivamente selecionado e renderizado, preservando precisão decimal, NULL, duplicatas e ordenação quando relevante. Uma tentativa correta descartada não é premiada. Casos com várias métricas ou turnos só passam se todos os componentes exigidos estiverem corretos.

Execution accuracy utiliza os 16 casos de resposta como denominador. Clarification accuracy utiliza os quatro casos exclusivos de esclarecimento. As duas medidas não são confundidas. Com 16 respostas, pelo menos 12 acertos seriam necessários para superar 70%. Rodadas incompletas mantêm taxas oficiais indisponíveis e preservam os casos não executados.

O executor registra fontes, conjunto, modelo, bibliotecas, limites, conteúdo da base, checkpoints, tentativas SQL, resultado selecionado, consumo informado e duração. A avaliação exige autorização explícita --live. Erros externos interrompem a rodada; não há troca automática de modelo ou repetição em caso de cota. A confirmação final da base invalida as taxas se o conteúdo mudou ou não pôde ser verificado.

### 4.6 Experimentos e resultados

A primeira rodada de desenvolvimento foi interrompida em D08 por HTTP 400, após D01–D07 corretos. Embora uma tentativa SQL de D08 coincidisse com a referência, não houve resultado selecionado; o caso não foi considerado correto. Uma reprodução direcionada passou, sem esclarecer a causa do erro original. A segunda rodada aprovou D01–D09 e parou em D10 por HTTP 429. As taxas dessas rodadas permanecem indisponíveis.

Uma melhoria de diagnóstico passou a registrar categorias fixas de erros da API, sem conservar mensagens brutas. Não houve correção baseada em causa presumida. A terceira rodada, com intervalo de 60 segundos entre turnos, concluiu o desenvolvimento. O sucesso com o intervalo maior não permite determinar se o limite anterior era diário ou por minuto.

Após analisar desenvolvimento sem falhas semânticas, foram congelados os fontes 59c9eb8fa0b73444e770effd3e3e80724049164b, o conjunto 1.0.0, o modelo, os limites e a base. Uma única avaliação reservada foi executada, sem alteração de prompt ou gabarito. Os relatórios e JSON sanitizados permanecem em docs/experimentos; os artefatos brutos são locais e ignorados pelo Git.

| Indicador | Desenvolvimento completo | Teste reservado |
|---|---:|---:|
| Casos corretos | 20/20 | 20/20 |
| Execution accuracy | 16/16 — 100% | 16/16 — 100% |
| Clarification accuracy | 4/4 — 100% | 4/4 — 100% |
| Turnos observados | 21 | 21 |
| Média agente e banco | 1,733 s | 1,649 s |
| Requisições ao SDK | 45 | 48 |
| Tokens informados | 69.695 | 74.713 |
| Base após a rodada | Inalterada | Inalterada |

O identificador de desenvolvimento é 20261011T161317Z-1c15b47d; o reservado é 20261011T163747Z-5fe3b066. Todas as chamadas das duas rodadas completas informaram uso. O número de tokens não foi convertido em custo financeiro. A latência exclui as pausas entre turnos, transporte Telegram, comparação da avaliação e tempo humano.

A meta de acurácia foi atingida nesta amostra reservada. A amostra é pequena, abrange um único domínio e utiliza base sintética e arquitetura híbrida. Não sustenta generalização para bancos arbitrários nem demonstra superioridade a benchmarks publicados. As duas rodadas completas não apresentaram falhas semânticas que justificassem nova alteração de prompt.

### 4.7 Verificação de engenharia e entrega

Na versão congelada, 110 testes de engenharia passaram com PostgreSQL real, sem skips, acompanhados de lint e validação das 34 referências. Esses testes verificam restrições SQL, precisão numérica, tratamento de erros, sessões, autenticação, protocolo do SDK e integração com APIs externas simuladas. Não equivalem a 110 perguntas reais ao Gemini.

O GitHub Actions da consolidação 13ff665 foi aprovado. Os commits posteriores aos fontes congelados incorporaram evidências e documentação. O repositório possui Compose com PostgreSQL 16, instruções de setup, CLI, protocolo, dicionário de dados e exemplos de demonstração. A configuração secreta e os processos originais do bot foram preservados durante os experimentos.

A reprodução final em Linux, com Python 3.12.14, utilizou Docker Compose em projeto, volume e porta exclusivos. Init, seed 42 com 30 clientes, consistência, 110 testes com PostgreSQL real, lint, 34 referências SQL e pip check passaram. A base recém-gerada coincidiu com os hashes congelados; os recursos descartáveis foram removidos. Não houve chamada Gemini ou Telegram. Essa rodada utilizou dependências existentes, sem comprovar uma instalação limpa do lock; os detalhes estão em docs/verificacoes.md.

## 5 AVALIAÇÃO DO PROJETO PELO PÚBLICO BENEFICIADO

A validação com o gestor foi considerada realizada em 11/10/2026, com aceite, conforme informação do responsável pelo projeto. O registro disponível contém somente essa confirmação. Não foram fornecidos questionário, ata, identificação do participante, assinatura ou síntese de feedback, e não se atribuem ao gestor comentários ou notas de satisfação.

O aceite é uma evidência declaratória de aceitação do protótipo e é apresentado separadamente da avaliação experimental. Não confirma a meta de tempo, a comparação com dashboards, a correção de todos os indicadores possíveis ou a implantação produtiva. O registro completo de sua origem e alcance está em docs/avaliacao.md.

O histórico de avaliação por pares descrito no relatório PAC VII permanece como contexto da proposta. Nesta etapa, as contribuições sobre ambiguidades e confiabilidade se refletem no mecanismo de esclarecimento, na autocorreção SQL limitada e na renderização de valores provenientes do banco. Não houve nova coleta de feedback por pares atribuída a este desenvolvimento.

## 6 CONSIDERAÇÕES FINAIS E AUTOAVALIAÇÃO DO PAC EXTENSIONISTA

O objetivo de desenvolver um protótipo funcional e avaliá-lo em base sintética foi alcançado no escopo do MVP. As quatro camadas estão implementadas, o conjunto de 40 casos está documentado e o teste reservado da versão congelada atingiu 100% nos 16 casos de resposta e nos quatro esclarecimentos. O aceite do gestor foi registrado como informação do responsável, sem detalhamento qualitativo adicional.

O principal resultado técnico é a combinação de consultas controladas, barreiras independentes de leitura e apresentação rastreável dos valores. A avaliação passou a preservar rodadas interrompidas, versões e resultados selecionados, permitindo distinguir uma consulta executada de uma resposta efetivamente correta. As falhas externas observadas também evidenciaram a dependência de disponibilidade e cota do provedor.

As principais limitações são a amostra pequena e conhecida no desenvolvimento, a ausência de revisão especializada documentada do gabarito, a base inteiramente sintética, o uso de alias de modelo e a falta de medição do transporte Telegram ponta a ponta. Não foi conduzida comparação cronometrada com dashboards. O aceite simples não substitui uma pesquisa qualitativa detalhada.

A fila e o histórico em memória limitam o uso em produção. Como trabalhos futuros, recomendam-se persistência durável, avaliação em novos períodos e cenários, revisão das regras de negócio por especialista e coleta qualitativa estruturada. Qualquer ajuste guiado pelo teste reservado exige declarar sua reutilização e preparar outra amostra independente. A ampliação para outros canais deve manter as mesmas barreiras de segurança.

A entrega consolida implementação, metodologia, resultados e limitações, sem afirmar que todas as metas originais foram comprovadas. A publicação pública com licença MIT prevista na proposta ainda não foi efetivada: o repositório indicado permanece privado e esta entrega não altera sua visibilidade nem concede uma licença nova. A submissão à instituição e a aprovação docente são atos posteriores à preparação dos artefatos.

## 7 REFERÊNCIAS

GUO, Jiaqi et al. Towards Complex Text-to-SQL in Cross-Domain Database with Intermediate Representation. In: Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics. Florence: ACL, 2019. p. 4524–4535. DOI: 10.18653/v1/P19-1444. Disponível em: https://aclanthology.org/P19-1444/. Acesso em: 11 out. 2026.

LI, Jinyang et al. Can LLM Already Serve as A Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs. Advances in Neural Information Processing Systems, v. 36, 2023. Disponível em: https://papers.neurips.cc/paper_files/paper/2023/hash/83fc8fab1710363050bbd1d4b8cc0021-Abstract-Datasets_and_Benchmarks.html. Acesso em: 11 out. 2026.

YU, Tao et al. Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task. In: Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing. Brussels: ACL, 2018. p. 3911–3921. DOI: 10.18653/v1/D18-1425. Disponível em: https://aclanthology.org/D18-1425/. Acesso em: 11 out. 2026.

HASSUMA, Arthur Vinicius de Almeida. Assistente Conversacional de BI via Aplicativo de Mensagens. Proposta acadêmica PAC Extensionista VII, 2026. Documento de referência preservado em docs/.

HASSUMA, Arthur Vinicius de Almeida. Relatório Final PAC Extensionista VII. Jaraguá do Sul, 28 jun. 2026. Documento de referência preservado em docs/entregaveis/Relatorio-Final-PAC-Arthur-Hassuma.docx.

HASSUMA, Arthur Vinicius de Almeida. Protocolo de avaliação e relatórios de desenvolvimento e teste reservado. Repositório pac_privado, 2026. Versão dos fontes avaliada: 59c9eb8. Documentos em docs/avaliacao.md e docs/experimentos/.

## 8 APÊNDICES

O Apêndice A corresponde ao schema e ao dicionário de dados, em db/schema.sql e docs/projeto.md. O Apêndice B corresponde ao conjunto versionado de 40 casos e suas consultas de referência, em evaluation/cases.json. O Apêndice C reúne o protocolo e os relatórios sanitizados das rodadas, em docs/avaliacao.md e docs/experimentos/.

O Apêndice D é o registro declaratório do aceite do gestor, em docs/avaliacao.md. O Apêndice E é o roteiro de demonstração e reprodução, em docs/apresentacao.md. Esses documentos integram o pacote da entrega; os artefatos brutos, credenciais, ambiente virtual, logs e banco local não o integram.

## 9 ANEXOS

A proposta aprovada e o relatório PAC VII permanecem inalterados no diretório docs/ para referência histórica. Este relatório PAC VIII registra a implementação e a avaliação posteriores; não altera retrospectivamente o conteúdo ou as decisões documentadas na fase de proposta.

## 10 ADENDO DE 10 DE NOVEMBRO DE 2026

Este adendo atualiza o relatório entregue em 11 de outubro de 2026. As seções 1 a 9 descrevem a versão congelada de outubro e permanecem inalteradas como registro histórico; onde divergirem deste adendo, prevalece o adendo. As taxas de 16/16 de outubro pertencem à base original de serviços de software e não foram repetidas sobre o sistema atual. Por isso não são comparáveis com os resultados deste adendo: a base, o domínio, os casos, o classificador e o código são outros, e nenhuma das duas medidas permite afirmar que o sistema melhorou ou piorou.

### 10.1 O que mudou no sistema

Depois de outubro, o domínio da base passou a uma revenda de autopeças (perfil autopecas: 100 clientes, seed 42, de janeiro de 2025 a outubro de 2026), com respostas, vocabulário e rankings ajustados. Foi adicionado um classificador de intenções (TF-IDF com regressão logística), ligado por padrão. A fila de updates, a deduplicação e as sessões passaram a ficar em um schema do PostgreSQL, o que supera a descrição da seção 4.3 (histórico e fila em memória, processo único); a entrega continua pelo menos uma vez, não exatamente uma vez. O sistema opera em uma VM Oracle com Docker, em oito rodadas de implantação registradas em docs/deploy.md. O arquivo de licença MIT foi adicionado ao repositório; esta entrega não altera a visibilidade do repositório.

### 10.2 Reavaliação com o Gemini real no perfil autopecas

Um novo protocolo foi declarado antes das rodadas (docs/avaliacao.md), com o mesmo critério da proposta: execution accuracy acima de 70%, isto é, pelo menos 12 de 16 respostas. Com o modelo gemini-3.5-flash-lite e o classificador ligado, uma execução por conjunto, os resultados foram: desenvolvimento do conjunto A, 14/16 na primeira rodada e 16/16 depois de duas correções no agente e no gabarito, resultado que não é independente; teste reservado do conjunto A, 12/16 respostas, 2/3 esclarecimentos e 1/1 pedido não suportado; teste reservado gerencial, 6/8 respostas, 1/1 esclarecimento e 1/1 pedido não suportado. Os dois reservados atenderam ao critério no limite exato. Três falhas do conjunto A eram de interpretação (T04, T05 e T10), duas eram de forma ou de status (T08 e T18), e as duas do conjunto gerencial (T26 e T28) tinham o número correto com a consulta dividida de modo diferente do gabarito.

### 10.3 Correções e nova medida

As três falhas de interpretação (filtro com grafia diferente da do dado, agrupamento por UF tratado como ranking e média de horas recusada como fora do escopo) foram corrigidas por decisão do responsável. Como as correções nasceram desse reservado, ele foi declarado contaminado e uma partição nova de vinte casos (conjunto C) foi escrita depois, com o critério fixado antes da rodada. Nela, a versão corrigida obteve 13/16 respostas, 3/3 esclarecimentos e 1/1 pedido não suportado, atendendo ao critério. As falhas foram um ranking com formato diferente do gabarito e duas perguntas ambíguas que geraram esclarecimento de medida. Com vinte casos, 12/16 e 13/16 não se distinguem com segurança, e este adendo não afirma melhora.

### 10.4 Classificador de intenções

O conjunto C foi executado com o classificador ligado (13/16 e 14/16 em duas rodadas) e desligado (13/16 nos 16 casos de resposta, em rodada interrompida por indisponibilidade do provedor antes dos dois últimos casos). A diferença não superou a variação entre execuções idênticas; o resultado é, portanto, sem efeito mensurável nesta amostra, o que não prova que o classificador não ajude.

### 10.5 Limitações atualizadas

Permanecem as amostras pequenas e sintéticas, a ausência de revisão especializada dos gabaritos, o aceite declaratório do gestor e a falta de medição ponta a ponta no Telegram. Acrescentam-se: o não determinismo do Gemini e a dependência de disponibilidade e cota do provedor (rodadas foram interrompidas por erro 503); o formato de ranking, que pode divergir do gabarito mesmo com os valores corretos; a execução automática do CI do GitHub, bloqueada por cobrança da conta; e os 52 testes de banco, entre 337, que só rodam com um PostgreSQL de teste configurado. Detalhes e evidências estão em docs/experimentos.md, docs/avaliacao.md e docs/deploy.md.
