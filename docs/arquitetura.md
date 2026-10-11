# Desenho das Fases 0–3

## Objetivo e limites
Gestores consultam indicadores B2B em português por Telegram, sem SQL. Dados integralmente sintéticos. Python/FastAPI orquestra; Gemini decide consultas; psycopg acessa PostgreSQL 16. Este desenho registra a implementação das Fases 0–3. A continuidade posterior acrescentou avaliação e relatório final: veja [entrega final](entrega-final.md). A [migração de provedor](migracao-gemini.md) foi autorizada pelo usuário para usar a cota gratuita.

## Decisões
- Um processo FastAPI, sessões em memória por usuário/chat, TTL, limite de sessões e histórico; reiniciar apaga sessões. Locks por sessão serializam perguntas. Para múltiplos workers será necessário armazenamento compartilhado.
- Webhook autenticado com segredo, lista explícita de usuários e chats privados. Polling é alternativa local que também passa pelo backend FastAPI. Transporte não concede acesso SQL administrativo.
- Planejamento sem tools decide métrica e período. Ambiguidade impede qualquer SQL e produz esclarecimento fixo em PT-BR. Contexto de perguntas anteriores pode preencher essas lacunas.
- Loop Gemini nativo com exatamente `get_schema` e `execute_sql`. Erros de PostgreSQL entram como functionResponse contendo error e diagnóstico; tentativas e duração limitadas. Execução automática de funções pelo SDK desativada; a aplicação controla cada chamada. Conteúdo e assinaturas nativos são preservados entre chamadas.
- SQL parseado com AST PostgreSQL: somente SELECT, incluindo CTEs de leitura e agregações. Allowlist de nós, funções e cinco tabelas; rejeita comandos embutidos, SELECT INTO, locks, funções arbitrárias, schemas externos e consultas múltiplas.
- Segunda barreira: login readonly_agent, somente SELECT, sem associação a outras roles; transação read-only, statement_timeout, lock_timeout, limite de linhas e tamanho da resposta.
- Resposta final usa um envelope que referencia um resultado da consulta atual. O backend escreve a frase introdutória em PT-BR e formata células exatas; texto livre do modelo não chega ao usuário. Assim números, datas e valores tabulados vêm das células retornadas. Valores decimais nunca viram float e não sofrem arredondamento no renderizador. Cálculos e arredondamentos explicitamente solicitados acontecem em SQL.
- Histórico contém turnos completos, inclusive tool calls/resultados. Evidências finais são sempre de consultas da pergunta corrente. Nenhuma credencial ou conteúdo de conversa vai para logs.

## Modelo B2B
clientes → contratos → pedidos → faturamento, com indicadores mensais por contrato. Pedido é contratação de um serviço; faturamento é nota sintética emitida (pode estar paga, aberta ou cancelada). Não confundir valor contratado, pedidos e receita recebida. Indicadores armazenam horas previstas/realizadas e chamados abertos/resolvidos, sem média de percentuais.

## Alternativas consideradas
Validar apenas dígitos de prosa livre permite números por extenso e associação incorreta: descartado. Usar prosa livre com prompt somente não garante a regra anti-alucinação: descartado. Renderização determinística reduz flexibilidade textual, mas oferece rastreabilidade de cada célula.

## Verificação
Testes de segurança SQL, valores exatos, ambiguidade, retry, sessões, autenticação e duplicação de updates. Integração com PostgreSQL 16 local: schema, carga, consistência, role e timeout reais. Integração HTTP/Telegram com serviços externos substituídos apenas na fronteira de rede. A continuidade posterior executou experimentos reais no ambiente conectado e reprodução Docker; os registros datados em docs/ distinguem os resultados destas verificações iniciais.
