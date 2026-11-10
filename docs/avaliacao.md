# Avaliação, treinamento e aceite

Protocolos de avaliação, guia de perguntas, treinamento do classificador de intenções (v1 e v2), como explicá-lo, aceite do gestor e comparação com a proposta.

## Conteúdo

- [Protocolo de avaliação — S7 a S11](#protocolo-de-avaliação--s7-a-s11)
- [Avaliação gerencial — conjunto novo](#avaliação-gerencial--conjunto-novo)
- [Guia de perguntas para o gestor](#guia-de-perguntas-para-o-gestor)
- [Treinamento supervisionado de intenções — versão 1](#treinamento-supervisionado-de-intenções--versão-1)
- [Treinamento supervisionado de intenções — versão 2 (revenda de autopeças)](#treinamento-supervisionado-de-intenções--versão-2-revenda-de-autopeças)
- [Como explicar o treinamento na apresentação](#como-explicar-o-treinamento-na-apresentação)
- [Registro de aceite do gestor](#registro-de-aceite-do-gestor)
- [Comparação da proposta com a implementação](#comparação-da-proposta-com-a-implementação)

## Protocolo de avaliação — S7 a S11

_Origem: `docs/avaliacao.md` (consolidado em 2026-11-09)._

O conjunto `evaluation/cases.json` contém 40 casos: 20 de desenvolvimento (D01–D20) e 20 de teste reservado (T01–T20). Cada partição tem 16 casos com resposta e quatro com esclarecimento. Há conversas com dois turnos e perguntas com duas métricas. Ao todo, são 34 consultas SQL de referência. Os dados são sintéticos, com seed declarada 42 e 30 clientes; o manifesto registra o conteúdo efetivamente encontrado, sem presumir que a seed corresponde à base.

As referências foram verificadas contra o schema e executadas no PostgreSQL 16. Essa revisão técnica não substitui a revisão do gabarito por professor ou especialista do domínio. Cada referência declara sua interpretação, tipos, ordem e SQL. A divisão e o gabarito devem permanecer congelados durante os experimentos. Alterações futuras exigem nova versão, justificativa e rodada independente.

### Execução

Execute na raiz do repositório com o ambiente Python instalado e `DATABASE_URL` da role `readonly_agent`. Não é necessário token Telegram para avaliar o agente.

```powershell
python -m scripts.evaluate validate
python -m scripts.evaluate run --live --split development --interval 60 --limit 20
# Somente após analisar desenvolvimento e congelar os ajustes:
python -m scripts.evaluate run --live --split test --interval 60 --limit 20
```

`--env-file` permite indicar um arquivo local; seu conteúdo e caminho de credenciais não são incorporados à evidência. `validate` executa SQL de referência e não chama Gemini. `run` exige `--live` e chave configurada. Não há fallback de provedor/modelo nem repetição automática em caso de cota. O intervalo controla chamadas entre turnos; function calling pode realizar várias requisições dentro de um turno. Uma resposta HTTP de erro do provedor interrompe a rodada, preservando o que foi executado. O código de saída é 2 para rodada incompleta; uma rodada completa retorna 0 independentemente da acurácia.

Os exemplos usam 60 segundos porque a terceira rodada de desenvolvimento concluiu com esse intervalo após uma rodada de 12 segundos interrompida por HTTP 429. Isso não identifica a causa do limite anterior nem garante disponibilidade futura. O padrão do CLI continua sendo 12 segundos; informe o intervalo explicitamente para reproduzir as rodadas de desenvolvimento concluída e teste reservado. As pausas não entram na latência medida.

### Evidência

Cada rodada cria uma pasta exclusiva em `.local/evaluation/`, ignorada pelo Git:

- `manifest.json`: commit, estado modificado, hashes dos fontes/conjunto, versão do modelo configurado, bibliotecas, parâmetros, limites e contagem/hash de cada tabela.
- `cases.jsonl`: checkpoint por caso, pergunta, resposta, plano, tentativas de SQL, resultado escolhido, referência, duração e consumo de tokens informado pelo SDK. Não inclui chave, token, cabeçalhos ou payload HTTP.
- `summary.json` e `summary.md`: cobertura, erros, casos não executados e indicadores.

Os artefatos contêm consultas e resultados sintéticos. Devem permanecer locais; publicar apenas resumos revisados no repositório privado. Credenciais permanecem no ambiente de origem. O executor não altera tabelas, não envia mensagens Telegram nem reinicia o bot.

Falhas API registram o código e uma categoria indicativa com rótulo fixo (`thought_signature_validation`, `function_response_validation` ou `unclassified`), por requisição e por turno. A classificação reconhece apenas marcadores na mensagem, sem conservá-la, e não equivale a diagnóstico conclusivo. Não há retrospectiva: os erros da versão original permanecem sem categoria detalhada. O aprimoramento de diagnóstico preserva a exceção e não acrescenta retries.

### Critérios

Execution accuracy é a proporção de casos de resposta inteiramente corretos entre os 16 planejados da partição. A arquitetura avaliada é híbrida: o modelo planeja as consultas; totais simples usam SQL de templates e análises usam SQL gerado pelo modelo. A taxa global mede o sistema completo; não deve ser apresentada como taxa exclusiva de geração livre de SQL. O trace registra qual caminho foi usado. Um caso com várias métricas só passa se todas coincidirem. Conversas também precisam acertar o esclarecimento inicial. Comparação usa o resultado escolhido para renderização, sem premiar uma consulta correta que foi descartada pelo agente.

Aliases não importam. Valores decimais são comparados sem arredondamento/tolerância; NULL difere de zero. Duplicatas são preservadas. Ordenação importa quando declarada (rankings/séries); quantidade e posição das colunas precisam coincidir. A coluna auxiliar canônica `registros`, usada pelo prompt e pelo renderer, é validada como contagem inteira não negativa e retirada antes da comparação. Contagem zero não pode ocultar um valor de negócio diferente de zero/NULL. Resultados truncados reprovam. Acurácia de esclarecimento usa os quatro casos exclusivos de esclarecimento como denominador próprio.

Rodadas interrompidas não recebem taxa oficial: o relatório preserva contagens, motivo e casos faltantes. Não confundir cobertura incompleta com uma amostra menor escolhida depois do resultado. Erros do agente em rodada completa contam como falhas. Casos com API simulada são testes de engenharia, nunca evidência da hipótese acadêmica.

A latência observada mede agente e banco, incluindo planejamento e correções, excluindo o intervalo entre casos. Não mede transporte Telegram, tempo humano ou comparação com dashboards. Portanto não comprova isoladamente a meta ponta a ponta inferior a dez segundos da proposta. A meta de acurácia é estritamente maior que 70%; com 16 casos de resposta, pelo menos 12 precisam passar. A amostra é pequena e não sustenta generalização estatística ampla.

### Sequência de ajustes

1. Publicar a versão e registrar uma rodada real de desenvolvimento.
2. Classificar falhas: interpretação, filtro/período, join/agregação, política SQL, resposta, infraestrutura ou cota.
3. Corrigir apenas com base no desenvolvimento, adicionar regressões e repetir sobre a mesma base/conjunto, preservando a rodada anterior.
4. Congelar código e executar teste reservado uma vez. Se suas falhas orientarem novas correções, declarar contaminação e preparar outro teste reservado para uma conclusão independente.
5. Reportar resultados e limitações. Validação qualitativa com gestor e redação final pertencem às semanas seguintes e não são concluídas por esta avaliação.

## Avaliação gerencial — conjunto novo

_Origem: `docs/avaliacao.md` (consolidado em 2026-11-09)._

Conjunto `evaluation/managerial-cases-v1.json`: 35 cenários, IDs independentes dos 40 casos originais. Desenvolvimento D21–D45: 20 respostas, dois esclarecimentos e três explicações de limites. Reservado T21–T30: oito respostas, um esclarecimento e uma explicação de limite. Ao todo, 28 referências SQL, escritas independentemente dos templates de produção e executadas pela role de leitura no PostgreSQL comparativo.

Base: perfil comparativo-v1, seed 42, 100 clientes, janeiro/2025 a outubro/2026. Registrar fingerprint real antes/depois; não executar na base antiga dos experimentos por engano. Outubro inteiro é cenário sintético. Os gabaritos incluem definições de emissão/pagamento, cancelamento, participação e desvio; não são evidência de causa ou previsão. Gabaritos revisados tecnicamente, sem alegar revisão de especialista externo.

As formas de saída esperadas são explícitas: agrupamentos de cliente/contrato incluem identificador e nome, rankings incluem posição calculada e comparações incluem direção calculada. Ordenação é estável. Comparação decimal continua exata, sem tolerância; representação equivalente fora desse contrato não é automaticamente julgada como semanticamente correta. A coluna auxiliar `registros` não é dado de negócio avaliado. Essas restrições do gabarito devem acompanhar qualquer taxa divulgada.

### Engenharia e aprendizagem não são avaliação do Gemini

A classificação de intenções usa outro corpus, com 196/28/56 formulações de treino/validação/teste, sem resultados financeiros. Seu teste reservado já foi executado; não ajustar o classificador usando o desempenho observado. Macro-F1 e accuracy de intenção não medem SQL, esclarecimento ou entrega no Telegram.

Em 12/10/2026 as 28 referências foram executadas no PostgreSQL local. Os 20 cenários de resposta de desenvolvimento também podem ser conferidos com planos e APIs simulados, para validar compilação/renderização contra os gabaritos. Essa verificação não mede interpretação do Gemini nem é rodada real. Os dez cenários reservados do agente só recebem resultado oficial após congelar o código e executar o teste real.

### Rodadas reais

Preparar no ambiente conectado `.local/gerencial.env`, privadamente combinando chave/modelo existentes e DSN readonly da base comparativa. Não incluir senhas, token ou IDs nos relatórios. O executor não precisa de Telegram e não deve enviar mensagens ou reiniciar o bot durante a avaliação.

```sh
python -m scripts.evaluate validate --dataset evaluation/managerial-cases-v1.json --env-file .local/gerencial.env
python -m scripts.evaluate run --live --dataset evaluation/managerial-cases-v1.json --split development --interval 60 --limit 25 --env-file .local/gerencial.env
# Após concluir ajustes de desenvolvimento, revisão e congelamento:
python -m scripts.evaluate run --live --dataset evaluation/managerial-cases-v1.json --split test --interval 60 --limit 10 --env-file .local/gerencial.env
```

Manter classificador desativado por padrão: a validação selecionou limiar com cobertura aceita zero. Conferir em desenvolvimento, separadamente, os exemplos aceitos e os prompts com flag ligada/desligada. Se os prompts forem iguais, não atribuir melhora ao classificador; uma rodada duplicada real sem mudança de entrada não demonstra benefício causal e pode ser substituída por essa conferência de engenharia, com justificativa registrada. Não concluir ganho de latência a partir dessa equivalência de prompts.

O manifesto registra fonte, dataset, modelo configurado, flag do classificador, hashes do artefato/corpus e banco. Tokens e versão resolvida ficam no trace quando o SDK informar. Cota/erro externo interrompe a rodada com checkpoint; não inventar resultados faltantes ou concluir taxa oficial de uma rodada incompleta. Não mudar para provedor/modelo pago ou repetir automaticamente chamadas interrompidas.

Reportar separadamente acerto de respostas, esclarecimentos e explicações de limites. Latência mede agente/banco, sem transporte Telegram. Revisar também legibilidade, períodos mostrados, avisos de parcialidade, fidelidade dos dígitos e ausência de causalidade inventada. Uma resposta numericamente correta não comprova sozinha texto útil ao gestor; revisão técnica não equivale a validação qualitativa humana.

Depois de ajustes baseados em desenvolvimento, congelar versão, dataset e banco antes do reservado. Se resultados reservados orientarem mudanças, declarar contaminação e usar um novo conjunto independente para uma conclusão posterior. Preservar a versão e as métricas antigas `59c9eb8`.

## Guia de perguntas para o gestor

_Origem: `docs/avaliacao.md` (consolidado em 2026-11-09)._

A base é inteiramente sintética, de janeiro de 2025 a outubro de 2026. Outubro contém o mês inteiro como cenário, inclusive dias posteriores a 12/10/2026; não é uma previsão econômica. Ao comparar acumulados, indique janeiro a outubro nos dois anos, para usar períodos equivalentes. Não é necessário conhecer SQL.

### Comparações

- “Compare o faturamento emitido de agosto de 2025 com agosto de 2026. Mostre os valores, diferença e variação percentual.”
- “Como mudou a quantidade de pedidos de março de 2025 para março de 2026?”
- “Tomando janeiro a outubro de 2025 como base, compare os recebimentos com janeiro a outubro de 2026.”
- “Quais segmentos mais contribuíram para a variação do faturamento entre setembro de 2025 e setembro de 2026?”

Os valores base/atual, diferença e percentuais são calculados no banco. Quando a base for zero ou não houver dados comparáveis, o percentual fica indefinido. Contribuição por categoria pode superar a participação intuitiva em uma distribuição: categorias podem compensar aumentos e quedas umas das outras. Não atribuir causas apenas a uma variação.

### Evolução, ranking e concentração

- “Mostre mês a mês o faturamento emitido durante 2025.”
- “Como evoluíram os recebimentos por mês de janeiro a outubro de 2026?”
- “Monte o ranking dos cinco clientes com maior faturamento emitido em setembro de 2026.”
- “Quais são as três cidades com maior valor de pedidos em agosto de 2026?”
- “Distribua o faturamento de julho de 2026 por segmento e mostre a participação percentual.”
- “Liste os nomes dos clientes de Curitiba e seus valores de faturamento emitido em maio de 2026, do maior para o menor.”

O resultado informa quando há um ranking limitado, limite de consulta ou resumo de um detalhamento extenso. Peça filtros específicos para explorar os demais registros. Rankings têm desempate estável; se quiser média/ticket médio, diga isso explicitamente. O agente mantém esse cálculo no SQL personalizado, em vez de usar o template de soma.

### Operação e fluxos financeiros

- “Qual foi o desvio entre horas previstas e realizadas em setembro de 2026? Inclua os totais e o desvio percentual.”
- “Compare horas previstas e realizadas por cliente em janeiro de 2025.”
- “Mostre chamados abertos, resolvidos, saldo e taxa de resolução em maio de 2026.”
- “Confronte o faturamento emitido com os recebimentos de março de 2026 e mostre a diferença.”

Resolução é ponderada pelos chamados abertos, não uma média de taxas por contrato. Faturamento usa emissão e exclui notas canceladas; recebimentos usam pagamento e apenas notas pagas. A diferença entre esses fluxos não comprova inadimplência nem saldo de caixa. Não há custos, despesas ou funcionários nesta base para calcular lucro, margem ou produtividade individual.

### Conversa e apresentação

Use `/limpar` antes de começar um assunto independente. Perguntas sem período, como “Qual o faturamento?”, geram esclarecimento. Continuações inequívocas podem aproveitar o período anterior, mas “no outro ano” sem referência suficiente exige esclarecimento.

As respostas usam 📊 para análise, 📈/📉 para direção comprovada, 🕒 para horas e ℹ️ para limites. Dinheiro tem separadores PT-BR sem perder casas decimais. Percentuais podem ser longos: se quiser apresentação arredondada, peça explicitamente casas decimais; o arredondamento ocorrerá no SQL. O renderizador não cria números ou conclusões livres.

O classificador local foi treinado para reconhecer famílias de análise, não prever faturamento. Por limitações na validação de desenvolvimento, fica desativado por padrão. Gemini e regras do sistema continuam interpretando e atendendo às consultas gerenciais. Não houve ajuste dos pesos do Gemini nem aprendizagem permanente com mensagens.

Para demonstração acadêmica, mostrar primeiro uma comparação, depois contribuição por segmento e por fim horas ou fluxos. Confrontar resultados com SQL de referência. Testes locais simulam APIs; confirmação de entrega de resposta exige uma mensagem humana no Telegram no ambiente conectado.

## Treinamento supervisionado de intenções — versão 1

_Origem: `docs/avaliacao.md` (consolidado em 2026-11-09)._

> **Versão histórica.** Substituída pela [versão 2](#treinamento-supervisionado-de-intenções--versão-2-revenda-de-autopeças) (08/11/2026), em vocabulário de autopeças e em uso no bot. Os números abaixo são da versão 1, que ficou desligada.

Executado em 12/10/2026. Modelo local TF-IDF (palavras/bigramas) + regressão logística. O Gemini não teve seus pesos alterados. Corpus integralmente sintético: 280 formulações em 70 grupos semânticos; 196 treino, 28 validação, 56 teste. São 49 grupos no treino, sete na validação e 14 no teste; as formulações de cada grupo são correlacionadas. Quatro formulações do mesmo cenário permanecem juntas. Rótulos revisados tecnicamente, sem alegar revisão externa por gestores.

O vocabulário/IDF e os coeficientes foram ajustados apenas no treino. C selecionado: 0.5; limiar: 0.7; 625 características. Artefato congelado em 935aa4b antes de executar o teste uma vez. Classes e matrizes completas estão em [resultados JSON](dados/treinamento-intencoes-resultados-v1.json).

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

### Revisão independente — 12/10/2026

Quatro problemas importantes foram reproduzidos antes do congelamento gerencial e corrigidos: transporte de zero `numeric` com escala em formato fixo; pedidos de ranking dos menores encaminhados ao SQL personalizado; taxa ausente preservada como NULL; participação/contribuição de taxas encaminhadas ao SQL personalizado, preservando numeradores e denominadores. Os templates descendentes continuam disponíveis para maiores resultados. Também foi removida a sugestão `extract` incompatível com a allowlist existente.

Regressões primeiro: 7 falhas e 33 aprovações. Após correções e prompt: 187 testes aprovados em 20,49 s, incluindo PostgreSQL real; Ruff aprovado. Nenhum novo teste reservado do agente foi executado nesta verificação. Pesos e resultado reservado do classificador permanecem congelados. O resultado local de engenharia não mede desempenho do Gemini.

#### Compatibilidade com a base original no CI

O CI detectou duas falhas de referência nos testes gerenciais: o perfil original não possui faturamento em 2026. Foi acrescentada regressão para período monetário vazio (1 falha antes da correção). Comparações de medidas aditivas usam zero somente se COUNT comprova ausência; valor NULL com registros e taxa sem chamados permanecem indefinidos. Referências dos testes agora consultam soma e contagem, sem presumir dados em ambos os anos. Após correção: 188 testes passaram em 22,18 s, Ruff aprovado na base comparativa. A confirmação do CI do perfil original será registrada separadamente.

## Treinamento supervisionado de intenções — versão 2 (revenda de autopeças)

_Origem: `docs/avaliacao.md` (consolidado em 2026-11-09)._

Executado em 08/11/2026. Substitui a versão 1 como padrão do bot. O Gemini continua sendo um
modelo previamente treinado pelo provedor; **nenhum peso dele foi alterado**. O que foi treinado é um
classificador local de perguntas (TF-IDF de palavras e bigramas + regressão logística), cuja
inferência roda sem scikit-learn a partir de um JSON.

### Por que uma versão 2

A versão 1 ([resultados](#treinamento-supervisionado-de-intenções--versão-1)) foi treinada em perguntas de serviços de
software, com apenas 4 formas de perguntar por cenário e nenhuma sugestão aceita no limiar
escolhido. Ficou desligada. Com a mudança do domínio para autopeças, o corpus precisava ser
refeito, e o resultado da v1 mostrava que as formas de perguntar eram poucas.

### Dados

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

### Protocolo

[`training/protocol-v2.json`](../training/protocol-v2.json) foi commitado **antes** de qualquer
treino (`9c8714f`), com o critério de uso: no teste reservado, **precisão das sugestões aceitas de
pelo menos 0,90 e cobertura de pelo menos 0,50**. O classificador só seria ligado se os dois valores
fossem atingidos. C e limiar foram escolhidos somente pela validação, e o modelo foi congelado em
commit (`4072831`) antes de o teste ser aberto, uma única vez.

#### Emenda, feita antes do teste

O primeiro treino (14 moldes por intenção, C e limiar escolhidos em duas etapas) deu 75,6% de
acurácia na validação, mas confianças em torno de 0,2 e cobertura de apenas 11% das sugestões
aceitas. Olhando **só a validação**, foram feitas três mudanças, registradas na seção `amendments`
do protocolo: 24 moldes por intenção (mais variedade de escrita), escolha conjunta de C e limiar
pelo macro-F1 com abstenção (que pune cobertura baixa) e limiares 0,3 e 0,4 adicionados à grade. O
critério de uso não mudou. O teste não foi consultado nessa fase.

### Resultados

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
e a previsão de cada pergunta, estão em [`treinamento-intencoes-v2-treino.json`](dados/treinamento-intencoes-v2-treino.json)
e [`treinamento-intencoes-v2-teste.json`](dados/treinamento-intencoes-v2-teste.json).

#### Checagem informal com perguntas reais

Fora do protocolo, o modelo congelado foi aplicado a 22 perguntas que o gestor de fato fez ao bot
nos testes do Telegram, rotuladas à mão por quem escreveu o corpus. **Não é um resultado oficial:**
a amostra é pequena e o rótulo é do mesmo autor. Acertou 17 de 22; aceitou 13 sugestões, 12 corretas.
A que errou foi "Quais os recebimentos em setembro de 2026?" (previsto: ranking, confiança 0,69).
Perguntas curtas e simples (por exemplo, "Faturamento de ontem") tendem a gerar abstenção.

### Como o classificador é usado

Quando a confiança passa de 0,5 e a classe não é genérica, o bot acrescenta ao prompt do planejador
**até dois exemplos de treino daquela intenção**, marcados como "sem autoridade para datas ou SQL".
Ele **não escolhe** métrica, período, SQL, permissões nem números: o planejador do Gemini continua
decidindo, a aplicação valida o plano e o PostgreSQL calcula. Com baixa confiança, intenção genérica,
artefato ausente ou inválido, o caminho padrão é mantido.

Cada pergunta registra no log do backend uma linha como
`INFO:app.bi_agent:intencao rotulo=ranking confianca=0.99 aceita=True`, **sem o texto da pergunta**.
É a evidência verificável de que o classificador está em uso: `docker logs <backend> | grep intencao`.

### O que este resultado permite e não permite afirmar

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

### Reprodução

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

## Como explicar o treinamento na apresentação

_Origem: `docs/avaliacao.md` (consolidado em 2026-11-09)._

Estado em 08/11/2026: versão 2 do classificador, em uso. Detalhes e números em
[treinamento v2](#treinamento-supervisionado-de-intenções--versão-2-revenda-de-autopeças). A [versão 1](#treinamento-supervisionado-de-intenções--versão-1) fica como histórico.

### Qual modelo foi treinado?

Um classificador local de perguntas, com TF-IDF e regressão logística. Entrada: o texto em português.
Alvo: uma de sete intenções (total, comparação, tendência, ranking, segmentação, operacional ou
genérica). O `fit` aprende vocabulário, pesos IDF e coeficientes só com a partição de treino:
aprendizagem supervisionada com rótulos. **O Gemini é um modelo previamente treinado pelo provedor, usado
por API; este projeto não modificou seus pesos.** Dizer "treinamos o Gemini" seria falso.

### Frase pronta

> "Usamos o Gemini já treinado pelo Google, por API, para interpretar as perguntas. Além disso,
> treinamos um classificador supervisionado local, com 1.112 perguntas sintéticas de autopeças, que
> reconhece a intenção da pergunta e, quando está confiante, passa dois exemplos ao Gemini. Foi
> avaliado em 224 perguntas de teste escritas de formas que ele não viu, com critério definido antes:
> acertou 87,9%, e nas sugestões que aceita a precisão é de 95%."

### Resultados que podem ser citados

| Medida | Validação | Teste |
|---|---:|---:|
| Acurácia | 84,8% | 87,9% |
| Macro-F1 | 0,85 | 0,87 |
| Cobertura das sugestões aceitas | 76,8% | 80,8% |
| Precisão das sugestões aceitas | 93,6% | 95,0% |

O critério de uso foi gravado antes do treino (precisão de pelo menos 0,90 e cobertura de pelo menos
0,50 no teste) e foi atingido. A versão 1, com 4 formas de perguntar por cenário, teve acurácia de
42,9% e nenhuma sugestão aceita na validação, e por isso ficou desligada.

### Relação com a disciplina

O fluxo usa preparação de dados, atributos, variável alvo, treino/validação/teste, escolha de
hiperparâmetros, baseline, matriz de confusão, precisão, recall e macro-F1. Classificar uma pergunta
**não equivale a prever** faturamento, vendas ou cancelamento. O BI implementado é descritivo: consulta
e compara registros. Se o objetivo futuro for previsão, é outro alvo e outro protocolo, com divisão
temporal.

### Perguntas difíceis da banca

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

### Como evoluir de forma correta

Coletar perguntas reais de gestores (com consentimento e anonimização), rotulá-las com revisão humana,
criar nova partição de teste independente, melhorar a classe operacional e medir o efeito no bot
(com e sem classificador) em perguntas reais.

Fontes do próprio projeto: [método e resultados](#treinamento-supervisionado-de-intenções--versão-2-revenda-de-autopeças),
`training/build_corpus_v2.py`, `training/fit.py`, `training/protocol-v2.json` e `app/intent_classifier.py`.

## Registro de aceite do gestor

_Origem: `docs/avaliacao.md` (consolidado em 2026-11-09)._

Data do aceite: **11/10/2026**.

O responsável pelo projeto informou que a validação com o gestor foi realizada e autorizou registrar o aceite nesta data. O registro é declaratório, fornecido pelo responsável, e não uma observação independente dos agentes de desenvolvimento.

Foi informado somente o aceite. Não foram fornecidos nome do participante, questionário, ata, gravação, assinatura, notas de usabilidade, síntese de feedback ou declarações textuais. Não se atribuem ao gestor comentários específicos, benefícios mensurados, comparação com dashboards ou confirmação das métricas de desempenho.

Este registro atende à continuidade solicitada para S11–S12 como realização e aceite declarados. Não substitui aprovação docente, assinatura institucional ou um estudo qualitativo com instrumento e resultados documentados. A identidade do participante não integra os artefatos publicados.

## Comparação da proposta com a implementação

_Origem: `docs/avaliacao.md` (consolidado em 2026-11-09)._

### Status atualizado em 11/10/2026

O usuário ampliou o escopo até a entrega final e autorizou usar o ambiente conectado. O [índice final](README.md#entrega-final--pac-extensionista-viii) reúne relatório, aceite declarado e reprodução Docker. Há 40 casos (20 desenvolvimento e 20 reservados), executor e referências SQL documentados no [protocolo](#protocolo-de-avaliação--s7-a-s11). A [terceira rodada](experimentos.md#desenvolvimento--rodada-3-11102026) concluiu 20/20 casos de desenvolvimento, sem falhas: 16/16 respostas e 4/4 esclarecimentos. Esses resultados medem o sistema híbrido nesta amostra; não são acurácia exclusiva da geração livre de SQL.

| Semanas da Tabela 2, p. 5 | Entrega | Status atual |
|---|---|---|
| S1–S2 | Revisão bibliográfica | Fundamentação retomada no relatório final com Spider, IRNet e BIRD; não se afirma revisão sistemática |
| S2–S3 | Modelagem | Schema e dicionário implementados |
| S3–S4 | Dados sintéticos | Geração reproduzível, carga e consistência verificadas |
| S4–S6 | Agente | Implementado com Gemini, mudança autorizada de provedor |
| S6–S7 | Mensageria | Telegram e FastAPI funcionais no ambiente conectado; os experimentos preservam o bot |
| S7–S8 | Perguntas de validação | 40 casos, referências revisadas tecnicamente e divisão congelada |
| S8–S10 | Experimentos | Desenvolvimento e teste reservado concluídos: 20/20 casos em cada partição |
| S10–S11 | Ajustes e iterações | Diagnóstico e regressões entregues; desenvolvimento analisado, versão congelada e avaliação reservada concluída sem falhas semânticas |
| S11–S12 | Validação com a Galvitech | Aceite declarado pelo responsável em 11/10/2026; sem identidade, instrumento ou feedback documentado |
| S12–S14 | Redação final | Relatório PAC VIII preparado em Markdown, Word e PDF |
| S14–S16 | Revisão e entrega | Artefatos revisados, reprodução Docker, roteiro e pacote preparados; submissão institucional posterior |

O [teste reservado](experimentos.md#teste-reservado--11102026) aprovou 16/16 respostas (execution accuracy de 100%) e 4/4 esclarecimentos (100%) na mesma versão congelada, atingindo a meta de acurácia superior a 70% nesta amostra. A média de 1,649 s da avaliação reservada exclui transporte Telegram e não comprova a meta ponta a ponta abaixo de dez segundos. A amostra pequena não sustenta generalização ampla. O aceite do gestor foi registrado conforme declaração do responsável; a comparação com dashboards e a coleta qualitativa estruturada não foram medidas. Consulte a [verificação atual](verificacoes.md#verificação-de-engenharia-e-continuidade-até-s10s11). Sem data de início definida, esta comparação de entregas não determina atraso no calendário.

### Diagnóstico histórico de 10/10/2026

A tabela e os registros abaixo preservam a revisão anterior à ampliação de escopo e não representam o status atual da avaliação.

Revisão em 10/10/2026. Fonte: `Asst. Conversacional de BI via Aplicativo de Mensagens com IA N3.pdf`, cinco páginas, preservado neste diretório. Base de código: `arthurhassuma/pac_privado`, commit `31ad3a4`, com os ajustes desta revisão.

O PDF é uma referência acadêmica, não uma autorização para alterar o escopo. Prevalecem as decisões posteriores do usuário: migração para Gemini e desenvolvimento até as Fases 0–3. As metas experimentais não são critérios já comprovados pelos testes de engenharia.

### Correspondência com a proposta

| Requisito e localização no PDF | Implementação / evidência | Situação |
|---|---|---|
| BI por mensagens para gestores B2B, em PT-BR (p. 1–2, §§ 1 e 3.1) | Telegram privado, comandos, perguntas e erros em português; `app/messaging.py`, `app/prompts.py` | Implementado; aceitação externa informada pelo usuário, sem evidência técnica reproduzida nesta revisão |
| Quatro camadas: Telegram, FastAPI, agente, PostgreSQL (p. 2, § 3.2) | `app/telegram_bot.py`, `app/main.py`, `app/bi_agent.py`, `app/database_tools.py` | Implementado; polling local também passa pelo webhook FastAPI |
| Claude/Anthropic ou GPT-4o/OpenAI (p. 2, §§ 3.1–3.2) | SDK oficial Gemini, function calling nativo e preservação das assinaturas do modelo | Alteração autorizada pelo usuário; documentar no relatório futuro, sem modificar a proposta aprovada |
| Python 3.12, PostgreSQL 16, psycopg, Faker (p. 2, § 3.2) | Projeto declara Python 3.11+; verificado em Python 3.13.1 e PostgreSQL 16.14; psycopg e Faker presentes | Versão de execução Python difere da referência; compatibilidade com todas as versões declaradas não foi comprovada |
| Clientes, contratos, pedidos, faturamento, indicadores (p. 2, § 3.1) | Cinco entidades relacionadas, PK/FK, constraints e índices; `db/schema.sql` e dicionário | Implementado |
| Base inteiramente sintética e reproduzível (p. 2–3) | `scripts/seed.py`, seed explícita, dinheiro decimal, validação de seis invariantes | Implementado; seed 42 validada no PostgreSQL |
| `get_schema` e `execute_sql`; somente SELECT, timeout, limite de linhas (p. 2, § 3.2) | Validação AST por allowlist, role restrita independente, timeout no servidor e limite externo | Implementado e coberto por testes de engenharia com PostgreSQL real |
| Respostas humanizadas, exclusivamente textuais (p. 1–2) | Introduções e rótulos controlados; nesta revisão, frase natural para um único agregado `total`, com valor exato da célula | Implementado com apresentação deliberadamente restrita para preservar a origem numérica; não inclui conclusões livres do LLM |
| Few-shot e tratamento de ambiguidade/SQL incorreto (p. 2, § 5) | Planejador exige métrica/medida/período; exemplos PT-BR, retorno do erro ao modelo e tentativas limitadas | Implementado; qualidade semântica do LLM ainda precisa da avaliação futura |
| Execution accuracy superior a 70%, 30–50 perguntas (p. 1–2, §§ 1 e 4) | Não há conjunto acadêmico nem resultados de execution accuracy | Fase 4 em diante; os testes de engenharia não comprovam a hipótese |
| Tempo médio ponta a ponta inferior a dez segundos (p. 2, § 4) | Timeout de SQL e orçamento do agente são limites de segurança, não medidas de latência média | Meta não medida; não confundir duração da suíte com tempo de resposta ao gestor |
| Validação com ao menos um gestor da Galvitech (p. 2, § 4) | Não realizada nesta sessão | Etapa posterior |
| Repositório público sob MIT e base sintética pública (p. 3, disponibilidade dos artefatos) | Repositório indicado é privado; ausência de `LICENSE` na revisão | Divergência a resolver antes da publicação acadêmica; visibilidade e licenciamento não foram alterados |
| Sem gráficos, voz ou fine-tuning (p. 2–3, limitações e trabalhos futuros) | Respostas textuais; nenhum desses recursos adicionado | Alinhado |

Os números das respostas são copiados das células da consulta, sem arredondamento no renderizador. Isso evita números livres na apresentação, mas **não garante que o LLM escolheu os filtros, joins ou cálculos corretos**. Um SELECT semanticamente incorreto ainda pode produzir números válidos: essa distinção deve permanecer na avaliação e no relatório.

### Cronograma: PDF e escopo da sessão

A Tabela 2, p. 5, foi conferida visualmente. O cronograma original prevê modelagem em S2–S3, geração em S3–S4, agente em S4–S6 e mensageria em S6–S7. Perguntas de validação aparecem em S7–S8; experimentos em S8–S10.

O pedido desta sessão reorganizou o trabalho em Fases 0–3 até S9 e excluiu expressamente o conjunto acadêmico, experimentos, validação qualitativa e redação final. Portanto, estar em S9 no pedido **não autoriza antecipar** a avaliação da tabela original. O [roteiro até dezembro](apresentacao.md#roteiro-de-entrega-do-pac) é planejamento posterior, não comprovação de atividades realizadas.

### Resultado desta revisão

- Clone da versão privada em pasta própria, preservando a cópia anterior e seu `.env`.
- Respostas naturais para agregados únicos, usando exclusivamente valor retornado pelo banco; NULL, ausência de registros e truncamento mantêm tratamento explícito.
- Diagnóstico `python -m scripts.check_connections`: configuração local sem rede por padrão; `--testar-conexoes` verifica banco, resposta mínima do Gemini e autenticação Telegram. Não envia mensagens nem altera webhook/polling.
- 77 testes aprovados, sem skips, com PostgreSQL real e APIs externas simuladas. Conferir os detalhes e limites em [verificação de 10/10](verificacoes.md#verificação-da-continuidade--10102026).

### Fechamento da Fase 3 e continuidade

O usuário informa que Gemini e Telegram já conectam em outro ambiente. O repositório GitHub contém o código, mas não expõe seu `.env` nem comprova qual processo está rodando. Nesta máquina, a cópia original tem credenciais externas vazias, e o clone novo não possui `.env`. Isso não invalida a conexão informada; limita o que foi possível verificar independentemente aqui.

No ambiente em execução, aplicar as mudanças e registrar o teste funcional de `/start`, pergunta ambígua, continuação com período, conferência contra SQL de referência e `/limpar`. Um diagnóstico de conexão positivo não substitui esse roteiro. Depois, em sessão própria, preparar as 30–50 perguntas com referências, medir execution accuracy e latência, iterar os prompts, validar qualitativamente e redigir os resultados. Registrar a mudança de provedor, versão efetivamente usada e divergência de publicação/licença.

## Reavaliação no perfil autopecas (protocolo declarado antes da rodada)

As medições com o Gemini de outubro de 2026 (20/20 no desenvolvimento e no teste reservado) usaram a base original, de serviços de software. Depois delas mudaram o domínio (revenda de autopeças), o formato das respostas, o vocabulário, o classificador de intenções (v2, ligado) e vários trechos do agente. Este protocolo define uma nova medição sobre o sistema atual, com os critérios fixados **antes** de qualquer rodada.

**Base.** Perfil `autopecas`, seed 42, 100 clientes, janeiro/2025 a outubro/2026 (`bi-db seed --profile autopecas --clients 100 --seed 42 --start-month 2025-01 --end-month 2026-10`). O manifesto registra o fingerprint das tabelas antes e depois, e a rodada é invalidada se a base mudar.

**Conjunto A: `evaluation/cases-autopecas.json` (versão 3.1.0, SHA256 `e4c8b43081b9fd9820f55ab42c2b340d66fe33311f102aa066932e7d0d7dc611`; a versão 3.0.0, usada na primeira rodada de desenvolvimento, tinha o SHA256 `4fca7b2e13f8eb6aab26cba9212e76017da654886995195b02a6e83d25dc8128`).** Adaptação dos 40 casos originais: mesmos IDs, categorias e divisão (D01–D20 desenvolvimento, T01–T20 teste reservado). Mudam só as datas (deslocadas para a faixa carregada), o vocabulário da revenda (pedidos de venda, ocorrências de pós-venda), o filtro de UF (Paraná, mais seletivo que Santa Catarina, que tem 66 dos 100 clientes) e dois casos que repetiam esclarecimentos: D17 e T20 passam a ser pedidos não suportados (lucro e margem, sem dados de custo). Cada partição fica com 16 respostas, 3 esclarecimentos e 1 pedido não suportado. As referências SQL são executadas ao vivo na base carregada (34 consultas validadas em modo offline, sem chamar o Gemini). Por derivar do conjunto original, **não é independente dele**: as perguntas seguem os mesmos modelos já conhecidos.

**Conjunto B: `evaluation/managerial-cases-v1.json`, partição reservada T21–T30.** Dez cenários gerenciais (oito respostas, um esclarecimento, um pedido não suportado) cuja execução real nunca foi feita: os registros anteriores cobrem só o desenvolvimento (24/25 em 12/10/2026). Os casos foram escritos antes das mudanças de novembro e não foram usados para ajustar prompts ou código.

**Configuração.** Modelo `gemini-3.5-flash-lite`, classificador de intenções ligado (como em produção), `--interval 60`, sem fallback de provedor ou modelo e sem repetição automática de chamadas.

**Critérios (fixados antes da rodada).**

- Conjunto A, por partição: a meta é *execution accuracy* estritamente maior que 70% sobre os 16 casos de resposta, isto é, pelo menos 12 de 16, como no protocolo original. Esclarecimentos (3) e pedidos não suportados (1) são reportados à parte, com contagens absolutas; seus denominadores são pequenos demais para taxa.
- Conjunto B reservado: pelo menos 6 de 8 casos de resposta corretos (acima de 70%); o esclarecimento e o pedido não suportado são reportados à parte.
- Rodada interrompida (cota, erro do provedor) não recebe taxa oficial e não é completada com resultados inventados.

**Ordem.**

1. Rodar o desenvolvimento do conjunto A e classificar as falhas (interpretação, filtro/período, join/agregação, política SQL, resposta, infraestrutura ou cota).
2. Corrigir só com base no desenvolvimento, com regressões, e repetir o desenvolvimento preservando a rodada anterior.
3. Congelar o código e executar **uma vez** o teste reservado do conjunto A e o reservado do conjunto B. Se as falhas do reservado orientarem correções, declarar a contaminação e não apresentá-lo como independente.

```powershell
python -m scripts.evaluate validate --dataset evaluation/cases-autopecas.json --env-file .local/avaliacao.env
python -m scripts.evaluate run --live --dataset evaluation/cases-autopecas.json --split development --interval 60 --limit 20 --env-file .local/avaliacao.env
# Depois de analisar o desenvolvimento e congelar os ajustes:
python -m scripts.evaluate run --live --dataset evaluation/cases-autopecas.json --split test --interval 60 --limit 20 --env-file .local/avaliacao.env
python -m scripts.evaluate run --live --dataset evaluation/managerial-cases-v1.json --split test --interval 60 --limit 10 --env-file .local/avaliacao.env
```

**Emenda 1 (após a primeira rodada de desenvolvimento, 09/11/2026).** A rodada com a versão 3.0.0 passou no critério (14/16) e revelou dois pontos, tratados antes de qualquer teste reservado e com a rodada original preservada em [experimentos](experimentos.md#reavaliação-no-perfil-autopecas--desenvolvimento-do-conjunto-a-300-09112026):

- **Gabarito (D08, T08).** As referências dos dois rankings usavam o formato antigo (`cliente`, `total`), mas o produto responde rankings no formato canônico (`item` = identificador e nome, `valor`, `posicao`), o mesmo dos casos gerenciais. A versão 3.1.0 só troca a forma dessas duas referências; perguntas, períodos e filtros não mudam. O resultado numérico do D08 já estava correto, e o rastro salvo da rodada, reavaliado offline com o gabarito 3.1.0, passa.
- **Planejador (D04).** O Gemini marcou "ranking" sem agrupamento nem limite num total com filtro (`excluindo os cancelados`), e o agente respondeu com um esclarecimento indevido. O agente passa a tratar esse plano como total com filtro quando o gestor não pediu ranking, top, maiores, menores ou lista (`normalize_unranked_plan`), com teste de regressão.

A taxa da 3.0.0 (14/16) continua sendo a medida oficial daquela rodada. A rodada de desenvolvimento seguinte usou a 3.1.0 e o agente corrigido (16/16).

**Resultado dos reservados (09/11/2026, código congelado, uma rodada cada, sem correção posterior).**

| Conjunto | Respostas | Esclarecimentos | Não suportado | Critério |
|---|---|---|---|---|
| A, reservado (T01–T20) | 12/16 (75%) | 2/3 | 1/1 | ≥ 12/16: atendido no limite |
| B, reservado (T21–T30) | 6/8 (75%) | 1/1 | 1/1 | ≥ 6/8: atendido no limite |

Nenhum resultado reservado orientou correção, então os dois seguem independentes. O desenvolvimento (16/16) não é independente, porque o agente e o gabarito foram ajustados a partir dele. Detalhes e classificação das sete falhas em [experimentos](experimentos.md#reavaliação-no-perfil-autopecas--teste-reservado-do-conjunto-a-310-09112026).

**Emenda 2 (após os reservados, 09/11/2026): contaminação declarada.** Por decisão do responsável, as falhas T04, T05 e T10 do reservado do conjunto A foram corrigidas (ver [experimentos](experimentos.md#correção-das-falhas-do-reservado-do-conjunto-a-09112026)). Como as correções nasceram dessas falhas, o reservado do conjunto A (T01–T20) **deixa de ser independente** para a versão corrigida do agente; os 12/16 continuam sendo a medida oficial da versão `0cbe39d`. O reservado gerencial (T21–T30) não orientou nenhuma correção, e seus 6/8 também valem só para a versão `0cbe39d`. Uma conclusão independente sobre a versão corrigida exige uma partição nova de casos, escrita sem consultar os resultados anteriores, e não existe ainda.

**Limites.** Amostras pequenas e sintéticas: não sustentam generalização. Os gabaritos foram revisados tecnicamente, sem revisão de especialista externo. A latência mede agente e banco, sem o transporte do Telegram. Os resultados serão registrados em [experimentos](experimentos.md).

