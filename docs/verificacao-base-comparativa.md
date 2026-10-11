# Verificação da base comparativa — 11/10/2026

Escopo: cenário sintético de janeiro de 2025 a outubro de 2026, seed 42, 100 clientes. Não altera os resultados acadêmicos congelados na versão `59c9eb8`.

## PostgreSQL local

Carga executada em PostgreSQL 16.14, cluster separado `.local/comparativo/pgdata`, banco `bi_comparativo`, porta 55440. Configuração privada em `.local/comparativo/.env`. O cluster anterior na porta 55439 foi preservado.

- 100 clientes; 681 contratos; 5.100 pedidos; 5.809 notas; 1.700 indicadores.
- 22 meses completos e todos os status previstos em cada mês.
- Seis verificações de integridade aprovadas: clientes com contratos; pedidos e competências dentro do contrato; emissão após pedido e ausência de faturamento de pedido cancelado; limites financeiros por pedido e contrato.
- Faturamento, quantidade de pedidos válidos e recebimentos mensais consultados por `readonly_agent`, com timeout e limite do executor. As 22 linhas de cada resultado coincidem com o resumo mensal do gerador.
- **117 testes de engenharia aprovados** com PostgreSQL real e APIs externas simuladas, em 15,65 s. Ruff aprovado. A cobertura adicional verifica geração determinística, relações temporais/financeiras e ausência de status. A integração não pressupõe mais que 2026 esteja vazio; agosto de 2027 mantém o caso sem registros.

O hash canônico do perfil original, seed 42 e 30 clientes, permaneceu `194ee30b0d09be6fc3c49647c7c849a6246103b07620eae14960949156d12476` antes/depois da alteração. Bibliotecas e seed iguais são necessárias para reprodução. O hash comparativo consta no resumo JSON.

## Exemplos conferidos no banco

| Métrica | Agosto/2025 | Agosto/2026 |
|---|---:|---:|
| Pedidos válidos | 185 | 289 |
| Faturamento emitido válido (BRL) | 1239387,25 | 2060162,05 |
| Recebimentos (BRL) | 897881,27 | 1372786,38 |

Números extraídos de consultas SQL. Não são uma nova rodada de avaliação com Gemini e não demonstram por si só transporte Telegram. A verificação no ambiente conectado deve ser registrada separadamente. Outubro inteiro contém cenário futuro sintético em relação a 11/10/2026.
