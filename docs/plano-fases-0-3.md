# Plano de implementação das Fases 0–3

**Objetivo:** entregar as quatro camadas com testes locais e instruções reproduzíveis.
**Spec:** [arquitetura.md](arquitetura.md). **Execução:** nesta sessão, mantendo o escopo autorizado.

## Restrições globais
PostgreSQL 16, PT-BR, dados sintéticos, SELECT apenas, login independente somente leitura, timeout e limite de linhas, números renderizados das consultas, esclarecimento antes de SQL, autocorreção limitada. Nenhuma atividade de Fase 4.

## Tarefas e contratos
- [x] Banco e geração: `db/schema.sql`, `db/roles.sql`, Compose, `scripts/seed.py`, `scripts/manage_db.py`. `generate_data(seed, clients)` retorna as cinco coleções; carga transacional recusa banco já povoado. Verificar FK, datas, totais e determinismo em testes e PostgreSQL.
- [x] Segurança: `app/database_tools.py`, `app/sql_policy.py`. `validate_select(sql)` devolve SQL validado; `DatabaseTools.get_schema()` devolve metadados; `execute_sql(sql)` devolve columns/rows/truncated/error, com Decimal serializado como string. Escrever ataques e agregações válidas antes da implementação; executar teste vermelho, implementar, repetir.
- [x] Agente: `app/bi_agent.py`, `app/prompts.py`, `app/rendering.py`. `BIAgent.answer(question, history)` devolve resposta e mensagens do turno completo. Primeiro testar ambiguidade sem SQL, erro→correção, referência inválida e número exato; implementar e verificar.
- [x] Backend: `app/main.py`, `app/sessions.py`, `app/telegram_bot.py`, `app/cli.py`. FastAPI aceita updates autenticados e os processa em fila limitada; replay em memória, sessões isoladas e acesso restrito. Testar HTTP negado/aceito, deduplicação e locks. Polling encaminha updates ao mesmo webhook local.
- [x] Entrega: README, dicionário completo, comandos de setup, testes unitários e integração local, registro de limitações e teste manual pendente.

## Pontos de revisão
CTE com escrita, funções com efeitos colaterais, números em prosa ou cabeçalhos, mensagem ambígua com histórico, duplicação/concor­rência no webhook. Acrescentar casos à tarefa responsável e revisar a integração inteira ao final.

## Registro final
58 testes aprovados com PostgreSQL real. Teste externo Anthropic/Telegram e execução do Compose pendentes, conforme docs/verificacao.md.
