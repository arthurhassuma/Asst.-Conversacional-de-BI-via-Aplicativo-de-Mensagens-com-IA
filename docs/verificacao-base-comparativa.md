# Verificação da base comparativa — 11/10/2026

Escopo: cenário sintético de janeiro de 2025 a outubro de 2026, seed 42, 100 clientes. Não altera os resultados acadêmicos congelados na versão `59c9eb8`.

## PostgreSQL local

Carga executada em PostgreSQL 16.14, cluster separado `.local/comparativo/pgdata`, banco `bi_comparativo`, porta 55440. Configuração privada em `.local/comparativo/.env`. O cluster anterior na porta 55439 foi preservado.

- 100 clientes; 681 contratos; 5.100 pedidos; 5.809 notas; 1.700 indicadores.
- 22 meses completos e todos os status previstos em cada mês.
- Seis verificações de integridade aprovadas: clientes com contratos; pedidos e competências dentro do contrato; emissão após pedido e ausência de faturamento de pedido cancelado; limites financeiros por pedido e contrato.
- Faturamento, quantidade de pedidos válidos e recebimentos mensais consultados por `readonly_agent`, com timeout e limite do executor. As 22 linhas de cada resultado coincidem com o resumo mensal do gerador.
- As seis referências SQL também passaram pelo executor de leitura: 22, 2, 22, 22, 22 e 4 linhas. A comparação de janeiro a outubro retornou BRL 8904430,85 em 2025 e 18433975,14 em 2026. A referência usa `date_part`, compatível com a allowlist atual, sem ampliar permissões.
- **117 testes de engenharia aprovados** com PostgreSQL real e APIs externas simuladas, em 15,65 s. Ruff aprovado. A cobertura adicional verifica geração determinística, relações temporais/financeiras e ausência de status. A integração não pressupõe mais que 2026 esteja vazio; agosto de 2027 mantém o caso sem registros.

O hash canônico do perfil original, seed 42 e 30 clientes, permaneceu `194ee30b0d09be6fc3c49647c7c849a6246103b07620eae14960949156d12476` antes/depois da alteração. Bibliotecas e seed iguais são necessárias para reprodução. O hash comparativo consta no resumo JSON.

## Exemplos conferidos no banco

| Métrica | Agosto/2025 | Agosto/2026 |
|---|---:|---:|
| Pedidos válidos | 185 | 289 |
| Faturamento emitido válido (BRL) | 1239387,25 | 2060162,05 |
| Recebimentos (BRL) | 897881,27 | 1372786,38 |

Números extraídos de consultas SQL. Não são uma nova rodada de avaliação com Gemini e não demonstram por si só transporte Telegram. A verificação no ambiente conectado deve ser registrada separadamente. Outubro inteiro contém cenário futuro sintético em relação a 11/10/2026.

## Apresentação

Foi criada uma revisão de 14 slides em `apresentacao/Apresentacao-PAC-VIII-Arthur-Hassuma-Base-Comparativa.pptx`, na pasta de trabalho do responsável (fora deste repositório), com PDF de visualização e roteiro correspondente. A revisão mostra as novas contagens e comparação de agosto, e identifica que as taxas dos experimentos pertencem à base original. Os exemplos novos estão identificados como resultados esperados conferidos por SQL. A versão anterior foi preservada. Validação estrutural e geométrica aprovada; cinco tabelas editáveis, fonte Arial e revisão visual dos 14 slides. O PDF foi montado das prévias renderizadas; o PowerPoint mantém textos e tabelas editáveis.

## Ambiente conectado

A [verificação em Docker, Gemini e Telegram](verificacao-base-comparativa-ambiente-conectado.md) foi concluída no ambiente conectado em 11/10/2026, com fonte documental publicada no commit `00b9c8428f22820b1b44b1b209c5faae41d7be1d`. A nova base foi ligada ao bot, com um único polling e rollback preservado. Os dois exemplos Gemini conferiram 185 pedidos / 1239387,25 em agosto de 2025 e 289 pedidos / 2060162,05 em agosto de 2026. A entrega de resposta no chat ainda depende da mensagem humana no Telegram. São exemplos pontuais; não alteram as métricas dos experimentos anteriores.
