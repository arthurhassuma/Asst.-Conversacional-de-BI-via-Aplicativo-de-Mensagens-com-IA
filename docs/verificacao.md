# Verificação da entrega — Fases 0–3

Executada em 27/09/2026, Windows, Python 3.13.1, PostgreSQL 16.14. Dependências exatas em `requirements-lock.txt`.

## Resultado observado

- **58 testes passaram**, sem skips na execução completa com TEST_DATABASE_URL apontando à base isolada.
- `ruff check app scripts tests`: sem erros após ajustes; formatação aplicada.
- `pip check`: sem conflitos de dependências; `compileall` de app/scripts sem erros.
- `bi-db validate`: zero ocorrências em todas as seis verificações de consistência.
- Comandos CLI instalados e executados; saída sem chave de IA é controlada em português. Erros de argumentos são traduzidos.
- `.env`, `.local/` e `.venv/` confirmados como ignorados pelo Git. Repositório Git inicializado localmente, sem remote configurado.

## Carga real

Cluster próprio em `.local/pgdata`, porta 55439, escuta apenas 127.0.0.1. Senhas aleatórias, autenticação SCRAM. O serviço PostgreSQL já existente no computador não foi alterado.

| Tabela | Linhas |
|---|---:|
| clientes | 30 |
| contratos | 56 |
| pedidos | 672 |
| faturamento | 628 |
| indicadores_operacionais | 672 |

Seed 42 e 30 clientes. O servidor temporário foi encerrado após os testes; a carga ficou persistida para retomada. Consulte README para iniciar/parar esse cluster ou recriar o ambiente via Docker em volume próprio.

## O que os testes provaram

- SELECTs analíticos válidos, rejeição de múltiplos comandos, DML em CTE, SELECT INTO, locks, funções fora da allowlist, schemas externos, tipos perigosos e CTE fora do escopo lexical.
- Negação de INSERT, UPDATE, DELETE, CREATE TABLE e CREATE TEMP TABLE pelo PostgreSQL, **sem passar pelo validador da aplicação e mesmo após solicitar transação de escrita**.
- statement_timeout real, recuperação após timeout, limite de linhas externo e precisão decimal exata.
- Serialização de intervalos/durações e consultas com `%`/LIKE; foram escritos testes que reproduziram as falhas antes das correções.
- Esclarecimento antes de SQL, validação de evidência do período, contexto de continuação, erro SQL retornado ao modelo, correção e limite de tentativas, usando respostas de API simuladas.
- Sessões isoladas e limitadas, TTL, serialização por usuário, autenticação do webhook, recusa de usuários/grupos, deduplicação e datas de updates.
- Teste de fluxo completo: HTTP do webhook → SDK Anthropic com transporte simulado → get_schema/execute_sql → **PostgreSQL real** → renderização → SDK Telegram com transporte simulado. Resultado conferido contra consulta independente ao banco.

## Revisão e correções

Revisão independente somente leitura realizada ao final. Identificou o tratamento ausente de `timedelta`, corrigido com regressão real no PostgreSQL. O histórico enviado ao planejador foi reduzido a mensagens textuais, enquanto o executor mantém os blocos de tools e suas definições. O caso de escopo de CTE foi identificado na revisão local e corrigido com teste que antes falhava.

## Pendências explícitas

- **Não foi feito teste real Anthropic/Telegram**, por decisão do usuário. Nenhum token externo foi fornecido ou mensagem real enviada. Simulações não confirmam acesso ao modelo, validade do token, entrega remota, qualidade de interpretação ou autocorreção pelo LLM real.
- **Docker Compose não foi executado**, pois Docker não está disponível nesta máquina. O SQL e o seeder foram executados no PostgreSQL 16 nativo; o arquivo Compose permanece a verificar em ambiente com Docker.
- O system prompt tem exemplos e tratamento dos erros de engenharia observados, mas sua iteração empírica com Claude real depende da configuração externa.
- Histórico/fila/deduplicação são locais e voláteis. Reinícios podem perder mensagens aceitas ou reprocessar entregas antigas; não há garantia de exatamente uma vez. Um único worker FastAPI é obrigatório.
- Origem dos números é garantida pelo renderizador; correção de métrica, filtros, joins e interpretação pelo modelo ainda precisa ser avaliada.

As Fases 0–2 e o código da Fase 3 foram implementados e testados localmente. A aceitação manual externa da Fase 3 está pendente. Nenhum conjunto de avaliação acadêmica, rodada de experimentos, validação qualitativa ou redação final foi iniciado.
