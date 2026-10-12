# Guia de perguntas para o gestor

A base é inteiramente sintética, de janeiro de 2025 a outubro de 2026. Outubro contém o mês inteiro como cenário, inclusive dias posteriores a 12/10/2026; não é uma previsão econômica. Ao comparar acumulados, indique janeiro a outubro nos dois anos, para usar períodos equivalentes. Não é necessário conhecer SQL.

## Comparações

- “Compare o faturamento emitido de agosto de 2025 com agosto de 2026. Mostre os valores, diferença e variação percentual.”
- “Como mudou a quantidade de pedidos de março de 2025 para março de 2026?”
- “Tomando janeiro a outubro de 2025 como base, compare os recebimentos com janeiro a outubro de 2026.”
- “Quais segmentos mais contribuíram para a variação do faturamento entre setembro de 2025 e setembro de 2026?”

Os valores base/atual, diferença e percentuais são calculados no banco. Quando a base for zero ou não houver dados comparáveis, o percentual fica indefinido. Contribuição por categoria pode superar a participação intuitiva em uma distribuição: categorias podem compensar aumentos e quedas umas das outras. Não atribuir causas apenas a uma variação.

## Evolução, ranking e concentração

- “Mostre mês a mês o faturamento emitido durante 2025.”
- “Como evoluíram os recebimentos por mês de janeiro a outubro de 2026?”
- “Monte o ranking dos cinco clientes com maior faturamento emitido em setembro de 2026.”
- “Quais são as três cidades com maior valor de pedidos em agosto de 2026?”
- “Distribua o faturamento de julho de 2026 por segmento e mostre a participação percentual.”
- “Liste os nomes dos clientes de Curitiba e seus valores de faturamento emitido em maio de 2026, do maior para o menor.”

O resultado informa quando há um ranking limitado, limite de consulta ou resumo de um detalhamento extenso. Peça filtros específicos para explorar os demais registros. Rankings têm desempate estável; se quiser média/ticket médio, diga isso explicitamente. O agente mantém esse cálculo no SQL personalizado, em vez de usar o template de soma.

## Operação e fluxos financeiros

- “Qual foi o desvio entre horas previstas e realizadas em setembro de 2026? Inclua os totais e o desvio percentual.”
- “Compare horas previstas e realizadas por cliente em janeiro de 2025.”
- “Mostre chamados abertos, resolvidos, saldo e taxa de resolução em maio de 2026.”
- “Confronte o faturamento emitido com os recebimentos de março de 2026 e mostre a diferença.”

Resolução é ponderada pelos chamados abertos, não uma média de taxas por contrato. Faturamento usa emissão e exclui notas canceladas; recebimentos usam pagamento e apenas notas pagas. A diferença entre esses fluxos não comprova inadimplência nem saldo de caixa. Não há custos, despesas ou funcionários nesta base para calcular lucro, margem ou produtividade individual.

## Conversa e apresentação

Use `/limpar` antes de começar um assunto independente. Perguntas sem período, como “Qual o faturamento?”, geram esclarecimento. Continuações inequívocas podem aproveitar o período anterior, mas “no outro ano” sem referência suficiente exige esclarecimento.

As respostas usam 📊 para análise, 📈/📉 para direção comprovada, 🕒 para horas e ℹ️ para limites. Dinheiro tem separadores PT-BR sem perder casas decimais. Percentuais podem ser longos: se quiser apresentação arredondada, peça explicitamente casas decimais; o arredondamento ocorrerá no SQL. O renderizador não cria números ou conclusões livres.

O classificador local foi treinado para reconhecer famílias de análise, não prever faturamento. Por limitações na validação de desenvolvimento, fica desativado por padrão. Gemini e regras do sistema continuam interpretando e atendendo às consultas gerenciais. Não houve ajuste dos pesos do Gemini nem aprendizagem permanente com mensagens.

Para demonstração acadêmica, mostrar primeiro uma comparação, depois contribuição por segmento e por fim horas ou fluxos. Confrontar resultados com SQL de referência. Testes locais simulam APIs; confirmação de entrega de resposta exige uma mensagem humana no Telegram no ambiente conectado.
