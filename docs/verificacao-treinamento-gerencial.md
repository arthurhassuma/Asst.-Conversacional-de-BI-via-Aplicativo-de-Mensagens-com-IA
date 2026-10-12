# Verificação do treinamento e das análises gerenciais — 12/10/2026

## Entrega e resultados locais

Plano aprovado pelo usuário, executado pelo próprio agente em checkout isolado. Branch `codex/treinamento-intencoes-implementacao`, [PR privada draft 4](https://github.com/arthurhassuma/pac_privado/pull/4), base `codex/base-comparativa`. Não houve merge em `main`, publicação pública ou mudança de licença. O PDF final anteriormente modificado pelo usuário foi preservado fora desta alteração.

Implementados: corpus supervisionado por grupos, treino TF-IDF/regressão logística, exportação JSON, inferência sem bibliotecas de treino, sugestão opcional de exemplos de treino, contrato gerencial, comparação/contribuição/séries/rankings/participação/desvios/fluxos, renderer PT-BR com emojis, conjunto gerencial independente, documentação e CI. As quatro camadas, duas tools, allowlist SELECT, role readonly, timeout, limite e autocorreção permanecem.

Treinamento real: 280 formulações sintéticas em 70 cenários, divididos por grupo em 196/28/56 textos (49/7/14 grupos). Artefato congelado em `935aa4b` antes de executar o teste uma única vez. Validação bruta 12/28; teste bruto 48/56, macro F1 0,8. Classe operacional 0/8 no teste. Limiar 0,7 teve cobertura aceita zero em validação e teste. Por essa evidência da validação, o classificador fica desligado por padrão. Não há benefício demonstrado para o agente. [Resultados completos](treinamento-intencoes-resultados-v1.json).

Verificação local mais recente: **188 testes aprovados, sem integrações puladas, em 22,18 s**, PostgreSQL 16 real e APIs externas simuladas. Ruff aprovado. `pip check`: nenhuma dependência quebrada. Validação do corpus confirmou sete classes de 40 formulações e 70 grupos. Um processo com imports de sklearn/numpy/scipy explicitamente bloqueados importou o agente e carregou o modelo JSON; não houve chamada externa nessa prova.

As **28 referências SQL gerenciais** foram executadas na role restrita. Os **20 cenários de resposta de desenvolvimento com planejador simulado** coincidiram com seus gabaritos independentes. Isso mede compilação, execução e apresentação, sem provar interpretação pelo Gemini. O novo conjunto contém 25 casos de desenvolvimento e dez reservados, independente dos 40 casos antigos e do corpus do classificador.

## Revisão e regressões

Uma revisão independente de toda a alteração encontrou quatro problemas importantes. Todos foram reproduzidos antes da correção: a bateria teve sete falhas e 33 aprovações. Correções: zero `numeric` escalado usa representação decimal fixa sem arredondar; menores rankings seguem SQL personalizado; taxa sem registros conserva NULL; participação/contribuição de taxas seguem executor que preserva numeradores e denominadores. Nenhum achado menor ficou adiado.

O CI identificou mais dois testes que presumiam faturamento em 2026 no perfil original. Uma regressão local de período monetário vazio falhou antes da correção. Comparações aditivas agora usam zero somente com ausência comprovada por COUNT=0; valor desconhecido com registros e taxa sem chamados permanecem NULL. As referências usam soma e contagem, sem depender de registros nos dois anos. Esses ajustes ocorreram antes do reservado gerencial.

## Situação externa

Rodada real de desenvolvimento iniciada no ambiente já configurado, com classificador desligado, fonte `1cc9197`, base comparativa isolada e intervalo de 60 segundos. Resultados finais, identificação do modelo, tokens e fingerprints serão importados do relatório sanitizado do ambiente conectado. Esta página não antecipa taxas de uma rodada incompleta.

Congelamento gerencial, novo reservado e atualização do bot ainda estão em andamento. O bot comparativo anterior permanece preservado enquanto a avaliação é concluída. Confirmação de `/health`, autenticação Telegram e polling não substitui uma mensagem humana para comprovar entrega e continuidade.

Os resultados antigos `59c9eb8` não foram repetidos ou alterados. Outubro/2026 inteiro é cenário sintético e os status correspondem a 31/10/2026; não representam fatos observados de uma empresa real. Aceite do gestor é o anteriormente declarado pelo usuário, sem síntese de feedback; não foi inventada nova validação qualitativa.

## Material da apresentação

Complemento de oito slides, PowerPoint editável, PDF de prévia e roteiro em `C:/Users/arthu/PAC - TCC/apresentacao/`, com sufixo `Treinamento-Gerencial`. Versões anteriores preservadas. Métricas do classificador e resultados do agente aparecem separados; exemplo financeiro identificado como formato demonstrativo com valores SQL previamente conferidos. [Guia de defesa](defesa-treinamento-ia.md).

## Rulings da execução

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
