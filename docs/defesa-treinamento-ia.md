# Como explicar o treinamento na apresentação

Estado em 08/11/2026: versão 2 do classificador, em uso. Detalhes e números em
[treinamento v2](treinamento-intencoes-v2.md). A [versão 1](treinamento-intencoes.md) fica como histórico.

## Qual modelo foi treinado?

Um classificador local de perguntas, com TF-IDF e regressão logística. Entrada: o texto em português.
Alvo: uma de sete intenções (total, comparação, tendência, ranking, segmentação, operacional ou
genérica). O `fit` aprende vocabulário, pesos IDF e coeficientes só com a partição de treino:
aprendizagem supervisionada com rótulos. **O Gemini é um modelo previamente treinado pelo provedor, usado
por API; este projeto não modificou seus pesos.** Dizer "treinamos o Gemini" seria falso.

## Frase pronta

> "Usamos o Gemini já treinado pelo Google, por API, para interpretar as perguntas. Além disso,
> treinamos um classificador supervisionado local, com 1.112 perguntas sintéticas de autopeças, que
> reconhece a intenção da pergunta e, quando está confiante, passa dois exemplos ao Gemini. Foi
> avaliado em 224 perguntas de teste escritas de formas que ele não viu, com critério definido antes:
> acertou 87,9%, e nas sugestões que aceita a precisão é de 95%."

## Resultados que podem ser citados

| Medida | Validação | Teste |
|---|---:|---:|
| Acurácia | 84,8% | 87,9% |
| Macro-F1 | 0,85 | 0,87 |
| Cobertura das sugestões aceitas | 76,8% | 80,8% |
| Precisão das sugestões aceitas | 93,6% | 95,0% |

O critério de uso foi gravado antes do treino (precisão de pelo menos 0,90 e cobertura de pelo menos
0,50 no teste) e foi atingido. A versão 1, com 4 formas de perguntar por cenário, teve acurácia de
42,9% e nenhuma sugestão aceita na validação, e por isso ficou desligada.

## Relação com a disciplina

O fluxo usa preparação de dados, atributos, variável alvo, treino/validação/teste, escolha de
hiperparâmetros, baseline, matriz de confusão, precisão, recall e macro-F1. Classificar uma pergunta
**não equivale a prever** faturamento, vendas ou cancelamento. O BI implementado é descritivo: consulta
e compara registros. Se o objetivo futuro for previsão, é outro alvo e outro protocolo, com divisão
temporal.

## Perguntas difíceis da banca

**"O classificador melhora as respostas?"** Não medimos. O que está medido é a qualidade da
classificação. O papel dele é modesto: sugere até dois exemplos ao planejador, sem escolher métrica,
período, SQL, permissão ou número. Uma comparação do bot com e sem classificador seria o próximo
experimento.

**"Os dados de treino são reais?"** Não: são sintéticos, gerados por moldes, e nenhuma conversa de
gestor foi usada. Por isso não há dado pessoal no treino.

**"O teste é independente?"** É independente do treino (os moldes do teste nunca aparecem no treino),
mas é sintético e foi escrito pela mesma equipe. Uma checagem informal com 22 perguntas reais deu 77% de
acerto, abaixo dos 87,9% do teste: perguntas reais curtas e simples são mais difíceis.

**"Por que o resultado melhorou tanto em relação à versão 1?"** Mais formas de perguntar (24 por
intenção, em vez de 4), domínio coerente com a base e escolha conjunta de C e limiar pela validação. O
protocolo e uma emenda, feita olhando só a validação, estão em `training/protocol-v2.json`.

**"Qual a classe mais fraca?"** Operacional (F1 de 0,67): perguntas como "faturamento emitido versus
recebimentos" são confundidas com comparação.

**"Isso é overfitting?"** A acurácia de treino é de 100%, então o modelo memoriza o treino. A avaliação em
moldes novos (87,9%) é o que sustenta a generalização, e ela é limitada pelo tamanho e pelo caráter
sintético do corpus.

## Como evoluir de forma correta

Coletar perguntas reais de gestores (com consentimento e anonimização), rotulá-las com revisão humana,
criar nova partição de teste independente, melhorar a classe operacional e medir o efeito no bot
(com e sem classificador) em perguntas reais.

Fontes do próprio projeto: [método e resultados](treinamento-intencoes-v2.md),
`training/build_corpus_v2.py`, `training/fit.py`, `training/protocol-v2.json` e `app/intent_classifier.py`.
