# Apresentação e opções no Telegram

Alteração posterior ao congelamento `ed38382`, solicitada em 12/10/2026 após teste humano no bot.

Percentuais são exibidos com exatamente duas casas decimais e arredondamento decimal HALF_UP, incluindo variação, participação e taxa de resolução. Exemplo: 187,8237825408560075% → 187,82%. O arredondamento afeta somente texto, nunca células SQL, cálculos, referências, traces ou dados armazenados. NULL continua “não informado”; percentuais próximos de zero não exibem zero negativo.

Mensagens de resultado, ausência de registros, boas-vindas e limite de previsão não incluem mais o aviso sobre dados sintéticos. Essa natureza continua registrada nas definições e documentação da base; avisos sobre resultado parcial ou base não comparável foram preservados.

Esclarecimentos de métrica/medida oferecem teclado de opções Telegram (`ReplyKeyboardMarkup`), como Valor/Quantidade/Ambos, Horas previstas/Horas realizadas/Ambas e as medidas de chamados. O botão envia texto normal no mesmo chat, usando o histórico existente. O teclado é removido após resposta/limpeza. Perguntas de datas/períodos explícitos continuam com entrada de texto. Não usa enquete de votação, callback ou processamento de votos; mantém a validação existente de chat privado e IDs autorizados.

Verificação: 66 checks selecionados de apresentação, backend, agente/renderização e transporte simulado passaram; 26 checks de PostgreSQL/e2e com APIs simuladas passaram; Ruff aprovado. Nenhum teste de classificação, treinamento, reservado antigo ou gerencial real foi reexecutado. As métricas publicadas das versões congeladas permanecem atribuídas a essas versões.
