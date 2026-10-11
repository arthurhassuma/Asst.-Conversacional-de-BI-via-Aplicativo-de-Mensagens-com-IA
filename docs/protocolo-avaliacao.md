# Protocolo de avaliação — S7 a S11

O conjunto `evaluation/cases.json` contém 40 casos: 20 de desenvolvimento (D01–D20) e 20 de teste reservado (T01–T20). Cada partição tem 16 casos com resposta e quatro com esclarecimento. Há conversas com dois turnos e perguntas com duas métricas. Ao todo, são 34 consultas SQL de referência. Os dados são sintéticos, com seed declarada 42 e 30 clientes; o manifesto registra o conteúdo efetivamente encontrado, sem presumir que a seed corresponde à base.

As referências foram verificadas contra o schema e executadas no PostgreSQL 16. Essa revisão técnica não substitui a revisão do gabarito por professor ou especialista do domínio. Cada referência declara sua interpretação, tipos, ordem e SQL. A divisão e o gabarito devem permanecer congelados durante os experimentos. Alterações futuras exigem nova versão, justificativa e rodada independente.

## Execução

Execute na raiz do repositório com o ambiente Python instalado e `DATABASE_URL` da role `readonly_agent`. Não é necessário token Telegram para avaliar o agente.

```powershell
python -m scripts.evaluate validate
python -m scripts.evaluate run --live --split development --interval 60 --limit 20
# Somente após analisar desenvolvimento e congelar os ajustes:
python -m scripts.evaluate run --live --split test --interval 60 --limit 20
```

`--env-file` permite indicar um arquivo local; seu conteúdo e caminho de credenciais não são incorporados à evidência. `validate` executa SQL de referência e não chama Gemini. `run` exige `--live` e chave configurada. Não há fallback de provedor/modelo nem repetição automática em caso de cota. O intervalo controla chamadas entre turnos; function calling pode realizar várias requisições dentro de um turno. Uma resposta HTTP de erro do provedor interrompe a rodada, preservando o que foi executado. O código de saída é 2 para rodada incompleta; uma rodada completa retorna 0 independentemente da acurácia.

Os exemplos usam 60 segundos porque a terceira rodada de desenvolvimento concluiu com esse intervalo após uma rodada de 12 segundos interrompida por HTTP 429. Isso não identifica a causa do limite anterior nem garante disponibilidade futura. O padrão do CLI continua sendo 12 segundos; informe o intervalo explicitamente para reproduzir as rodadas de desenvolvimento concluída e teste reservado. As pausas não entram na latência medida.

## Evidência

Cada rodada cria uma pasta exclusiva em `.local/evaluation/`, ignorada pelo Git:

- `manifest.json`: commit, estado modificado, hashes dos fontes/conjunto, versão do modelo configurado, bibliotecas, parâmetros, limites e contagem/hash de cada tabela.
- `cases.jsonl`: checkpoint por caso, pergunta, resposta, plano, tentativas de SQL, resultado escolhido, referência, duração e consumo de tokens informado pelo SDK. Não inclui chave, token, cabeçalhos ou payload HTTP.
- `summary.json` e `summary.md`: cobertura, erros, casos não executados e indicadores.

Os artefatos contêm consultas e resultados sintéticos. Devem permanecer locais; publicar apenas resumos revisados no repositório privado. Credenciais permanecem no ambiente de origem. O executor não altera tabelas, não envia mensagens Telegram nem reinicia o bot.

Falhas API registram o código e uma categoria indicativa com rótulo fixo (`thought_signature_validation`, `function_response_validation` ou `unclassified`), por requisição e por turno. A classificação reconhece apenas marcadores na mensagem, sem conservá-la, e não equivale a diagnóstico conclusivo. Não há retrospectiva: os erros da versão original permanecem sem categoria detalhada. O aprimoramento de diagnóstico preserva a exceção e não acrescenta retries.

## Critérios

Execution accuracy é a proporção de casos de resposta inteiramente corretos entre os 16 planejados da partição. A arquitetura avaliada é híbrida: o modelo planeja as consultas; totais simples usam SQL de templates e análises usam SQL gerado pelo modelo. A taxa global mede o sistema completo; não deve ser apresentada como taxa exclusiva de geração livre de SQL. O trace registra qual caminho foi usado. Um caso com várias métricas só passa se todas coincidirem. Conversas também precisam acertar o esclarecimento inicial. Comparação usa o resultado escolhido para renderização, sem premiar uma consulta correta que foi descartada pelo agente.

Aliases não importam. Valores decimais são comparados sem arredondamento/tolerância; NULL difere de zero. Duplicatas são preservadas. Ordenação importa quando declarada (rankings/séries); quantidade e posição das colunas precisam coincidir. A coluna auxiliar canônica `registros`, usada pelo prompt e pelo renderer, é validada como contagem inteira não negativa e retirada antes da comparação. Contagem zero não pode ocultar um valor de negócio diferente de zero/NULL. Resultados truncados reprovam. Acurácia de esclarecimento usa os quatro casos exclusivos de esclarecimento como denominador próprio.

Rodadas interrompidas não recebem taxa oficial: o relatório preserva contagens, motivo e casos faltantes. Não confundir cobertura incompleta com uma amostra menor escolhida depois do resultado. Erros do agente em rodada completa contam como falhas. Casos com API simulada são testes de engenharia, nunca evidência da hipótese acadêmica.

A latência observada mede agente e banco, incluindo planejamento e correções, excluindo o intervalo entre casos. Não mede transporte Telegram, tempo humano ou comparação com dashboards. Portanto não comprova isoladamente a meta ponta a ponta inferior a dez segundos da proposta. A meta de acurácia é estritamente maior que 70%; com 16 casos de resposta, pelo menos 12 precisam passar. A amostra é pequena e não sustenta generalização estatística ampla.

## Sequência de ajustes

1. Publicar a versão e registrar uma rodada real de desenvolvimento.
2. Classificar falhas: interpretação, filtro/período, join/agregação, política SQL, resposta, infraestrutura ou cota.
3. Corrigir apenas com base no desenvolvimento, adicionar regressões e repetir sobre a mesma base/conjunto, preservando a rodada anterior.
4. Congelar código e executar teste reservado uma vez. Se suas falhas orientarem novas correções, declarar contaminação e preparar outro teste reservado para uma conclusão independente.
5. Reportar resultados e limitações. Validação qualitativa com gestor e redação final pertencem às semanas seguintes e não são concluídas por esta avaliação.
