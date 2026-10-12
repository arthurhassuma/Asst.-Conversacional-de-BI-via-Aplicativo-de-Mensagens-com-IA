# Comandos em português e calendário relativo

Alteração solicitada em 12/10/2026, posterior às versões de avaliação e apresentação já publicadas. Não altera gabaritos, dados, modelo de intenções ou resultados históricos.

## Comandos

`/comecar` e `/começar` digitados iniciam a mesma conversa de `/start`, com opções de métrica. `/ajuda` é alternativa de `/help`. O menu nativo Telegram usa nomes ASCII (`/comecar`, `/ajuda`, `/limpar`), pois nomes de BotCommand não admitem acento. O handler também aceita o texto digitado `/começar`.

## Datas relativas

A referência é a data atual em America/Sao_Paulo. O planejador continua escolhendo métrica, medida e tipo de análise; o backend resolve expressões relativas com evidência literal do usuário antes de consultar o banco e valida esses intervalos.

- “Esse/este ano”, “ano atual”, “neste ano”: 01/janeiro até hoje inclusive.
- “Ano passado/anterior”, “último ano”, sozinho: ano anterior completo.
- Mês nomeado com ano relativo, por exemplo “fevereiro desse ano”: mês inteiro do ano atual.
- “Fevereiro desse ano, compare com o ano passado”: fevereiro completo em ambos os anos, ano anterior como base.
- “Compare ano atual com ano anterior”: 01/janeiro até o mesmo mês/dia atual inclusive em ambos os anos; o ano anterior é a base. A resposta mostra os dois intervalos efetivos. Uma base explicitamente indicada é respeitada.

Inícios inclusivos e fins exclusivos; 29/fevereiro é ajustado para 28/fevereiro no ano não bissexto. Datas explícitas não são substituídas. Perguntas sem período/evidência continuam pedindo esclarecimento; não foi criado período padrão. Intervalos com vários meses permanecem tratados pelo contrato existente do plano, sem substituir por um mês arbitrário.

Na data da implementação, 12/10/2026: ano atual é 01/01/2026–12/10/2026; a comparação equivalente anterior é 01/01/2025–12/10/2025. A base comparativa continua sintética e pode conter períodos futuros; expressões anuais atuais não estendem a consulta até datas futuras.

## Verificação

68 checks selecionados passaram: calendário, dia bissexto/virada de ano, evidência inventada, datas explícitas, integração do planejador, comandos, contexto e apresentação. 26 checks PostgreSQL/e2e com APIs simuladas passaram; Ruff aprovado. Não foram repetidos treinamento, teste de classificação ou conjuntos reservados. Dois exemplos diretos de faturamento relativo foram usados para verificação do Gemini, com uma tentativa por requisição; evidências locais privadas não incluem envio proativo Telegram.
