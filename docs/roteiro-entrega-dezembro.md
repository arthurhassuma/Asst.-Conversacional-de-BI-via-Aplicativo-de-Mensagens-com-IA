# Roteiro de entrega do PAC

Atualizado em 04/10/2026. Meta de trabalho: **01/12/2026**, interpretando o pedido
de entrega no início de dezembro. Ajustar se houver data oficial da instituição.

## Resultado esperado

Um gestor autorizado faz perguntas em português em chat privado no Telegram,
recebe esclarecimento quando necessário e obtém indicadores rastreáveis à base
sintética. A entrega inclui código reproduzível, avaliação com evidências,
relatório acadêmico e demonstração. Não pressupõe disponibilidade de produção,
múltiplos processos ou persistência de filas e sessões.

## Prioridades e critérios

| Período | Entrega | Critério para concluir |
|---|---|---|
| 04–11/10 | Publicação, CI e teste real | Código privado publicado; suíte com PostgreSQL aprovada; `/start`, pergunta ambígua, continuação e `/limpar` verificados com Gemini/Telegram reais; resultado comparado com SQL de referência |
| 12–25/10 | Conjunto de avaliação | 30–50 perguntas, categorizadas por métrica, período, junção, ambiguidade e recusa; SQL e resultado de referência revisados; separar casos de ajuste e avaliação final |
| 26/10–08/11 | Avaliação e correções | Registrar modelo, versão, seed, resultado esperado/obtido, falhas, latência e esclarecimentos; corrigir os erros observados com regressões; medir novamente sem inventar resultados |
| 09–15/11 | Versão candidata | Setup a partir de checkout limpo, Compose verificado, roteiro completo de demonstração, recuperação de falhas documentada; congelar novas funcionalidades |
| 16–22/11 | Relatório e validação qualitativa | Metodologia, resultados, limitações e mudança de provedor coerentes com evidências; feedback de avaliadores autorizado e anonimizado |
| 23–30/11 | Revisão e margem de segurança | Revisar normas institucionais, referências e anexos; ensaiar demonstração; gerar pacote e marcar versão de entrega |
| 01/12 | Entrega alvo | Código, instruções, relatório e demonstração consistentes com a versão marcada |

As datas são planejamento, não comprovam atividades realizadas nem criam execução
automática em segundo plano.

## Próxima etapa concreta: teste real

1. No checkout escolhido, preparar o banco sintético e seu usuário somente leitura.
2. Configurar localmente `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`,
   `TELEGRAM_ALLOWED_USER_IDS` e `TELEGRAM_WEBHOOK_SECRET`; conferir modelo e cota.
3. Iniciar um processo FastAPI e polling conforme README. O registro ou remoção
   de webhook deve respeitar qualquer configuração do bot já em uso.
4. Enviar manualmente `/start`, `Qual o faturamento?`, `janeiro de 2025` e `/limpar`.
5. Conferir o valor com a consulta de referência do README usando a role de leitura.
6. Registrar data, commit, modelo, pergunta, resposta, valor esperado e resultado
   da comparação, sem tokens ou identificação pessoal.

**Aceitação:** ambiguidade não executa consulta de negócio; continuação usa o
período informado; valor coincide com a referência; limpeza reinicia o contexto;
usuário não autorizado não obtém resposta com dados. Falhas externas devem
produzir mensagem controlada, sem credenciais ou diagnóstico interno.

## Avaliação acadêmica

O código existente e os 65 testes não comprovam acerto semântico do LLM. Para a
próxima etapa, recomenda-se um arquivo de casos com identificador, categoria,
pergunta, contexto, comportamento esperado e SQL de referência, acompanhado de
um executor opt-in que não chama provedores por padrão. Cada rodada deve preservar
o conjunto e o commit usados. Definir a meta de acerto com a orientação acadêmica
antes da rodada final; não escolher o critério depois de conhecer os resultados.

## Limites de escopo

Priorizar o fluxo existente e a comprovação da qualidade. Dashboard novo,
novos canais de mensagens, múltiplos provedores simultâneos e infraestrutura
distribuída ficam fora desta entrega, salvo mudança explícita de prioridade.
Reinício pode perder fila e histórico: essa limitação precisa aparecer no relatório
e no roteiro de demonstração.
