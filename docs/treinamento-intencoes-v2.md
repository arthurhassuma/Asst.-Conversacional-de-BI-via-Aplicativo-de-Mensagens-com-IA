# Treinamento supervisionado de intenções — versão 2 (revenda de autopeças)

Executado em 08/11/2026. Substitui a versão 1 como padrão do bot. O Gemini continua sendo um
modelo previamente treinado pelo provedor; **nenhum peso dele foi alterado**. O que foi treinado é um
classificador local de perguntas (TF-IDF de palavras e bigramas + regressão logística), cuja
inferência roda sem scikit-learn a partir de um JSON.

## Por que uma versão 2

A versão 1 ([resultados](treinamento-intencoes.md)) foi treinada em perguntas de serviços de
software, com apenas 4 formas de perguntar por cenário e nenhuma sugestão aceita no limiar
escolhido. Ficou desligada. Com a mudança do domínio para autopeças, o corpus precisava ser
refeito, e o resultado da v1 mostrava que as formas de perguntar eram poucas.

## Dados

Corpus integralmente **sintético**, em vocabulário de autopeças (pedidos de venda, contratos de
fornecimento, horas de atendimento, ocorrências de pós-venda), gerado por
[`training/build_corpus_v2.py`](../training/build_corpus_v2.py) com semente 42. Nenhuma mensagem de
gestor foi usada, e o bot não treina com conversas.

- 7 intenções: total, comparação, tendência, ranking, segmentação, operacional e genérica.
- 24 formas de perguntar (**moldes**) por intenção, com métricas, períodos e filtros variando
  dentro de cada molde: 168 moldes e 1.560 perguntas.
- **16 moldes por intenção no treino, 4 na validação e 4 no teste.** Os moldes da validação e do
  teste nunca aparecem no treino. A medida, portanto, é sobre perguntas escritas de um jeito que o
  modelo não viu, e não só outro mês ou outra métrica no mesmo molde.
- 1.112 perguntas de treino, 224 de validação e 224 de teste.

## Protocolo

[`training/protocol-v2.json`](../training/protocol-v2.json) foi commitado **antes** de qualquer
treino (`9c8714f`), com o critério de uso: no teste reservado, **precisão das sugestões aceitas de
pelo menos 0,90 e cobertura de pelo menos 0,50**. O classificador só seria ligado se os dois valores
fossem atingidos. C e limiar foram escolhidos somente pela validação, e o modelo foi congelado em
commit (`4072831`) antes de o teste ser aberto, uma única vez.

### Emenda, feita antes do teste

O primeiro treino (14 moldes por intenção, C e limiar escolhidos em duas etapas) deu 75,6% de
acurácia na validação, mas confianças em torno de 0,2 e cobertura de apenas 11% das sugestões
aceitas. Olhando **só a validação**, foram feitas três mudanças, registradas na seção `amendments`
do protocolo: 24 moldes por intenção (mais variedade de escrita), escolha conjunta de C e limiar
pelo macro-F1 com abstenção (que pune cobertura baixa) e limiares 0,3 e 0,4 adicionados à grade. O
critério de uso não mudou. O teste não foi consultado nessa fase.

## Resultados

Hiperparâmetros escolhidos: **C = 100, limiar de confiança = 0,5**, 1.059 características.

| Medida | Validação | Teste reservado |
|---|---:|---:|
| Acurácia sem abstenção | 0,848 | **0,879** |
| Macro-F1 sem abstenção | 0,850 | **0,874** |
| Cobertura das sugestões aceitas | 0,768 | **0,808** |
| Precisão das sugestões aceitas | 0,936 | **0,950** |
| Acurácia do baseline (classe majoritária) | 0,143 | 0,143 |

Critério de uso (precisão de pelo menos 0,90 e cobertura de pelo menos 0,50) no teste:
**atingido.** Para comparação, a v1 teve acurácia de 0,429 e macro-F1 de 0,39 na validação, e nenhuma
sugestão aceita.

F1 por classe no teste: ranking 1,00, tendência 0,98, segmentação 0,96, total 0,91, genérica 0,81,
comparação 0,78 e **operacional 0,67**. A classe operacional é a mais frágil: 11 de 32 perguntas
foram confundidas com comparação (por exemplo, "faturamento emitido versus recebimentos"), e
entre as genéricas, 7 de 32 foram classificadas como comparação e 3 como total. Os relatórios completos, com a matriz de confusão
e a previsão de cada pergunta, estão em [`treinamento-intencoes-v2-treino.json`](treinamento-intencoes-v2-treino.json)
e [`treinamento-intencoes-v2-teste.json`](treinamento-intencoes-v2-teste.json).

### Checagem informal com perguntas reais

Fora do protocolo, o modelo congelado foi aplicado a 22 perguntas que o gestor de fato fez ao bot
nos testes do Telegram, rotuladas à mão por quem escreveu o corpus. **Não é um resultado oficial:**
a amostra é pequena e o rótulo é do mesmo autor. Acertou 17 de 22; aceitou 13 sugestões, 12 corretas.
A que errou foi "Quais os recebimentos em setembro de 2026?" (previsto: ranking, confiança 0,69).
Perguntas curtas e simples (por exemplo, "Faturamento de ontem") tendem a gerar abstenção.

## Como o classificador é usado

Quando a confiança passa de 0,5 e a classe não é genérica, o bot acrescenta ao prompt do planejador
**até dois exemplos de treino daquela intenção**, marcados como "sem autoridade para datas ou SQL".
Ele **não escolhe** métrica, período, SQL, permissões nem números: o planejador do Gemini continua
decidindo, a aplicação valida o plano e o PostgreSQL calcula. Com baixa confiança, intenção genérica,
artefato ausente ou inválido, o caminho padrão é mantido.

Cada pergunta registra no log do backend uma linha como
`INFO:app.bi_agent:intencao rotulo=ranking confianca=0.99 aceita=True`, **sem o texto da pergunta**.
É a evidência verificável de que o classificador está em uso: `docker logs <backend> | grep intencao`.

## O que este resultado permite e não permite afirmar

- Permite: um classificador supervisionado foi treinado, avaliado em teste reservado segundo um
  protocolo declarado antes e está em uso no bot.
- **Não permite afirmar** que ele melhora as respostas. Não houve comparação do bot com e sem o
  classificador; o ganho nas respostas do Gemini **não foi medido**.
- Não mede a correção do SQL nem o desempenho do Gemini.
- O teste é sintético e foi escrito pela mesma equipe do treino, com moldes de estilo parecido. Perguntas
  de gestores reais podem ser mais difíceis; a checagem informal (77% de acerto) sugere isso.
- O corpus tem concordância gramatical às vezes imperfeita ("Como recebimentos se reparte…") e 168
  moldes, não 1.560 perguntas independentes.
- O ajuste de C é de 100, o maior da grade, e a acurácia de treino é de 100%: o modelo memoriza o
  treino. A avaliação em moldes novos é o que sustenta a generalização, e ela é limitada.

## Reprodução

```powershell
python -m pip install -r requirements-training-lock.txt
python -m training.build_corpus_v2
python -m scripts.train_intents validate --corpus training/questions-v2.json
python -m scripts.train_intents train --corpus training/questions-v2.json `
  --c-grid 0.5,1,2,5,10,20,50,100 --thresholds 0.3,0.4,0.5,0.6,0.7 --joint-selection `
  --seed 42 --output .local/intent-v2-treino
```

O teste só deve ser executado com o modelo congelado, uma vez, em pasta nova:
`python -m scripts.train_intents test --corpus training/questions-v2.json --model training/intent-model-v2.json --output .local/intent-v2-teste`.
Pastas existentes são recusadas. Os testes automatizados (`tests/test_intent_v2.py`) conferem que o
modelo pertence ao corpus commitado e que ele ainda atende ao critério declarado.
