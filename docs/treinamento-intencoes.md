# Treinamento supervisionado de intenções — versão 1

Executado em 12/10/2026. Modelo local TF-IDF (palavras/bigramas) + regressão logística. O Gemini não teve seus pesos alterados. Corpus integralmente sintético: 280 formulações em 70 grupos semânticos; 196 treino, 28 validação, 56 teste. Quatro formulações do mesmo cenário permanecem juntas. Rótulos revisados tecnicamente, sem alegar revisão externa por gestores.

O vocabulário/IDF e os coeficientes foram ajustados apenas no treino. C selecionado: 0.5; limiar: 0.7; 625 características. Artefato congelado em 935aa4b antes de executar o teste uma vez. Classes e matrizes completas estão em [resultados JSON](treinamento-intencoes-resultados-v1.json).

| Medida | Validação | Teste reservado |
|---|---:|---:|
| Accuracy sem abstinência | 0.428571 | 0.857143 |
| Macro-F1 sem abstinência | 0.389610 | 0.800000 |
| Accuracy baseline majoritário | 0.142857 | 0.142857 |
| Cobertura das sugestões aceitas | 0.000000 | 0.000000 |

A apresentação desta tabela arredonda métricas experimentais para seis casas; o JSON preserva os resultados computados. Não representa arredondamento de respostas de negócio.

A validação mostrou representação insuficiente: o limiar selecionado abstém de sugerir exemplos. Por essa evidência de desenvolvimento, a integração ficará desativada por padrão, com fallback genérico. Esse treinamento comprova execução do método, não qualidade suficiente de classificação para produção. A separação por grupos é mais exigente que separar paráfrases aleatoriamente. Um corpus futuro exige novos cenários, perguntas independentes e novo teste reservado; esta versão não será ajustada usando o teste observado.

Nenhuma destas métricas é acurácia de SQL ou do Gemini. Avaliação das análises gerenciais será documentada separadamente. A matriz de confusão permite identificar classes frágeis; corpus pequeno e formulações sintéticas não sustentam generalização para gestores reais.

Reprodução (Python 3.12/3.13): instalar requirements-lock.txt e requirements-training-lock.txt; executar python -m scripts.train_intents validate, depois train e test em diretórios novos conforme o plano. O bot carrega JSON com inferência equivalente, sem depender de sklearn no runtime e sem treinar durante conversas. Dependências de treino ficam em lock separado para preservar o runtime original.
