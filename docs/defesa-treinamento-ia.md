# Como explicar o treinamento na apresentação

## Qual modelo foi treinado?

Foi treinado um classificador local de perguntas com TF-IDF e regressão logística. Sua entrada é o texto em português; seu alvo é uma das sete intenções: total, comparação, tendência, ranking, segmentação, operacional ou genérica. O `fit` aprende vocabulário, pesos IDF e coeficientes usando somente a partição de treino. Isso constitui aprendizagem supervisionada com rótulos. O Gemini continua sendo um modelo previamente treinado pelo provedor; este projeto não modificou seus pesos.

## Relação com aprendizagem de máquina e análise preditiva

O fluxo usa conceitos das disciplinas: preparação de dados, atributos, variável alvo, treino/validação/teste, escolha de hiperparâmetro, baseline, matriz de confusão, precision, recall e macro F1. A regressão logística também pode ser usada em problemas de churn, mas aqui o alvo é uma intenção textual. Classificar uma pergunta não equivale a prever faturamento, vendas ou cancelamento de clientes. O BI gerencial implementado é descritivo: consulta e compara registros.

Cada cenário do corpus possui quatro formulações relacionadas. As quatro ficam na mesma partição para evitar que uma paráfrase apareça no treino e sua equivalente no teste. As 280 formulações correspondem a 70 grupos; a quantidade efetiva de cenários independentes é menor que a quantidade de textos. Todos são sintéticos e revisados tecnicamente. Não houve coleta nem treinamento com mensagens de gestores.

## O que os resultados permitem afirmar?

O experimento foi executado, tem artefato versionado e é reproduzível. O hiperparâmetro e o limiar foram selecionados com validação, antes de abrir o teste. A validação teve 12/28 acertos brutos; o teste teve 48/56 e macro F1 de 0,8. A classe operacional teve 0/8 acertos no teste. Esses resultados não medem correção de SQL, competência do Gemini ou satisfação do gestor.

Com o limiar congelado de 0,7, nenhuma sugestão foi aceita em validação ou teste. Por isso, o classificador permanece desligado por padrão e o agente usa seu planejador genérico. A conclusão é que o protótipo demonstra o método, mas ainda precisa de outros cenários para uso operacional. Não se deve ajustar o limiar olhando esse teste e depois apresentá-lo como evidência independente.

## Como o treinamento se relaciona com as respostas gerenciais?

Quando habilitado e suficientemente confiante, o classificador pode sugerir até dois exemplos do treino ao planejador. Ele não escolhe datas, métricas, SQL, permissões ou números finais. A aplicação valida o plano; o PostgreSQL calcula diferenças, percentuais, participações, posições e desvios. O renderizador usa as células retornadas, com texto controlado em português e emojis. Uma consulta SQL pode ser executável e ainda interpretar errado o pedido; a avaliação gerencial usa referências independentes para verificar essa distinção.

## Se a banca perguntar sobre melhoria comprovada

Não houve benefício demonstrado do classificador nesta versão. Os prompts com a classificação ligada e desligada foram iguais nos vinte exemplos de resposta de desenvolvimento conferidos localmente, porque nenhuma sugestão ultrapassou o limiar. Não repetimos uma rodada real idêntica para atribuir um ganho inexistente. As novas consultas gerenciais, os controles e a apresentação dos resultados foram implementados separadamente e têm verificações próprias.

## Como evoluir de forma correta?

Ampliar cenários e diversidade linguística, especialmente operacional; submeter rótulos a revisão humana; criar novas partições por cenário; comparar alternativas na validação; congelar a decisão; avaliar uma única vez em outro reservado independente. Se o objetivo futuro for previsão de negócio, definir outro alvo e outro protocolo, com divisão temporal e histórico apropriado. Não usar dados sintéticos de outubro/2026 como fatos reais observados.

Fontes do próprio projeto: [método e resultados](treinamento-intencoes.md), [relatório completo](treinamento-intencoes-resultados-v1.json), [protocolo gerencial](protocolo-avaliacao-gerencial.md), `training/fit.py` e `app/intent_classifier.py`.
