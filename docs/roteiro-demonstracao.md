# Demonstração e reprodução da entrega

Use somente a base sintética e um usuário autorizado. O roteiro é uma orientação de apresentação; não é registro de que uma nova demonstração foi executada. Credenciais ficam no `.env`, nunca nos slides, terminal gravado ou pacote.

## Preparação

1. Instale as dependências conforme README e prepare um banco PostgreSQL16 isolado. `bi-db init` e `bi-db seed --seed 42 --clients 30` recusam recursos já existentes ou base preenchida; não use reset destrutivo.
2. Execute `bi-db validate` e `python -m scripts.evaluate validate`. Esta etapa não chama Gemini. Compare as contagens com o relatório, considerando versões das bibliotecas.
3. Configure o modelo, a chave Gemini, o token Telegram, o segredo e os IDs permitidos no ambiente de demonstração. Respeite a configuração do bot em uso; não execute webhook e polling simultaneamente.
4. Confira saúde do backend e utilize apenas um processo FastAPI. Reiniciar perde sessões e fila em memória.

## Apresentação sugerida de cinco a oito minutos

| Momento | Ação | O que demonstrar |
|---|---|---|
| Contexto | Explicar serviço B2B e base sintética | Pergunta em português e indicadores sem dados reais |
| Arquitetura | Mostrar Telegram → FastAPI → Gemini → PostgreSQL | Quatro camadas e role somente leitura |
| Ambiguidade | Enviar `Qual o faturamento?` | Esclarecimento do período antes de SQL |
| Continuação | Responder `janeiro de 2025` | Resposta numérica com período e conferência SQL |
| Múltiplas métricas | Enviar `Qual o total de pedidos e o faturamento emitido em agosto de 2025?` | Resultados independentes por métrica |
| Contexto | Enviar `/limpar` e uma nova pergunta | Reinício explícito da conversa |
| Evidência | Mostrar relatório do teste reservado | 16/16 respostas, 4/4 esclarecimentos, limites da amostra |
| Encerramento | Explicar aceite e limitações | Aceite simples de11/10/2026, sem feedback atribuído |

## Conferência independente

Use a role de leitura para conferir a resposta de faturamento, sem mostrar a URL ou senha de conexão:

```sql
SELECT SUM(valor) AS total
FROM faturamento
WHERE emissao >= DATE '2025-01-01'
  AND emissao < DATE '2025-02-01'
  AND status <> 'cancelada';
```

A apresentação copia o valor produzido na base atual, sem fixar um número a partir de memória. Os relatórios versionados referem-se à base cujo hash foi registrado; não atribua seus valores a uma base regenerada sem comparação.

## Falhas e medição

Em cota ou indisponibilidade, mostre a mensagem controlada e encerre a chamada; não habilite cobrança ou mude modelo para concluir a apresentação. As evidências congeladas continuam disponíveis offline. Nunca exponha corpos HTTP, assinaturas de ferramentas ou logs que possam conter conteúdo interno.

Para comprovar a meta ponta a ponta em uma coleta futura, registre envio no cliente Telegram e recebimento da resposta usando o mesmo relógio, versão, pergunta, base e condição de rede. Meça múltiplas interações sem incluir espera humana por esclarecimento na duração automática, declarando o critério. Não substitua essa medição pela latência agente+banco nem atribua uma comparação com dashboards sem executar um protocolo equivalente.
