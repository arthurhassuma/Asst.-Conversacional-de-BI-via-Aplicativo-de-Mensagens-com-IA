# Comparação da proposta com a implementação

Revisão em 10/10/2026. Fonte: `Asst. Conversacional de BI via Aplicativo de Mensagens com IA N3.pdf`, cinco páginas, preservado neste diretório. Base de código: `arthurhassuma/pac_privado`, commit `31ad3a4`, com os ajustes desta revisão.

O PDF é uma referência acadêmica, não uma autorização para alterar o escopo. Prevalecem as decisões posteriores do usuário: migração para Gemini e desenvolvimento até as Fases 0–3. As metas experimentais não são critérios já comprovados pelos testes de engenharia.

## Correspondência com a proposta

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

## Cronograma: PDF e escopo da sessão

A Tabela 2, p. 5, foi conferida visualmente. O cronograma original prevê modelagem em S2–S3, geração em S3–S4, agente em S4–S6 e mensageria em S6–S7. Perguntas de validação aparecem em S7–S8; experimentos em S8–S10.

O pedido desta sessão reorganizou o trabalho em Fases 0–3 até S9 e excluiu expressamente o conjunto acadêmico, experimentos, validação qualitativa e redação final. Portanto, estar em S9 no pedido **não autoriza antecipar** a avaliação da tabela original. O [roteiro até dezembro](roteiro-entrega-dezembro.md) é planejamento posterior, não comprovação de atividades realizadas.

## Resultado desta revisão

- Clone da versão privada em pasta própria, preservando a cópia anterior e seu `.env`.
- Respostas naturais para agregados únicos, usando exclusivamente valor retornado pelo banco; NULL, ausência de registros e truncamento mantêm tratamento explícito.
- Diagnóstico `python -m scripts.check_connections`: configuração local sem rede por padrão; `--testar-conexoes` verifica banco, resposta mínima do Gemini e autenticação Telegram. Não envia mensagens nem altera webhook/polling.
- 77 testes aprovados, sem skips, com PostgreSQL real e APIs externas simuladas. Conferir os detalhes e limites em [verificação de 10/10](verificacao-2026-10-10.md).

## Fechamento da Fase 3 e continuidade

O usuário informa que Gemini e Telegram já conectam em outro ambiente. O repositório GitHub contém o código, mas não expõe seu `.env` nem comprova qual processo está rodando. Nesta máquina, a cópia original tem credenciais externas vazias, e o clone novo não possui `.env`. Isso não invalida a conexão informada; limita o que foi possível verificar independentemente aqui.

No ambiente em execução, aplicar as mudanças e registrar o teste funcional de `/start`, pergunta ambígua, continuação com período, conferência contra SQL de referência e `/limpar`. Um diagnóstico de conexão positivo não substitui esse roteiro. Depois, em sessão própria, preparar as 30–50 perguntas com referências, medir execution accuracy e latência, iterar os prompts, validar qualitativamente e redigir os resultados. Registrar a mudança de provedor, versão efetivamente usada e divergência de publicação/licença.
