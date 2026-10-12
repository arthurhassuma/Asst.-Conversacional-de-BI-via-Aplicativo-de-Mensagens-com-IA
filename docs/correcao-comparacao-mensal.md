# Comparação mensal com o ano anterior — 12/10/2026

## Problema e correção

O pedido “Nesse ano, teve algum mês que teve faturamento menor que o do ano
passado?” já especifica comparação por mês. A validação antiga rejeitava planos
`tendencia` com `comparison_period`, perguntando desnecessariamente se o usuário
queria comparar períodos. Mesmo com um plano `comparacao/mes`, não havia template
mensal: o executor dependia de SQL gerado e a resposta livre de campos não
distinguia com clareza ausência de quedas de ausência de dados.

A correção preserva uma intenção mensal de queda explicitamente presente no
pedido, inclusive ao responder ao esclarecimento pendente. Conserva a validação
de datas/evidências e os filtros. O planejador passa a explicar esse caso e a
substituição de setembro/pedidos por ano/faturamento na nova pergunta.

O SQL controlado agrega cada período separadamente, alinha os mesmos meses e
calcula diferença, percentual e direção no PostgreSQL. Aceita somente intervalos
com cortes de calendário compatíveis, dentro de um ano cada; outras situações e
filtros personalizados continuam no executor habitual. Não altera a allowlist.
Meses sem linhas de uma das partes usam zero somente com contagem que comprova
ausência; valores NULL existentes e taxas sem denominador continuam indefinidos.

O renderer apresenta somente os meses com queda quando solicitados; sem queda,
informa isso expressamente. Distingue base sem registros, valores indefinidos e
resultado truncado. Comparações mensais gerais conservam todos os meses. Os
percentuais permanecem com duas casas na apresentação; células SQL não são
arredondadas. O último mês parcial recebe aviso.

## Evidências e limites

- Base de código anterior: `583080dc98e95c8c1096671cb482ac244a6253bb`.
- Diagnóstico anterior com a pergunta isolada: plano `comparacao/mes` válido,
  seis requisições Gemini e resposta com detalhamento de campos sem conclusão.
  O esclarecimento do print é compatível com a barreira de validação identificada;
  não se afirma que o plano original do chat foi capturado.
- Verificação final usa planejador simulado e PostgreSQL readonly real. Planos
  incorretamente classificados como `tendencia` são normalizados antes do SQL.
  As somas de cada mês são verificadas contra SELECTs independentes sem joins.
- No cenário Jan–12/Out de 2026 versus Jan–12/Out de 2025: dez meses com registros,
  nenhum com queda. Resposta local informa ausência de queda; outubro é parcial.
- Cobertura adicional: queda real, aumento, entrada/saída, base zero, NULL,
  esclarecimento pendente, troca de assunto, filtros, corte incompatível,
  anos bissextos e truncamento.
- Suíte final: 209 testes aprovados em 3,60s, com PostgreSQL real. Ruff,
  formatação e `pip check` aprovados. Treinamento/teste do classificador e
  conjuntos reservados não foram reexecutados, nem alterados.
- Fingerprints das bases comparativa e original iguais aos manifests anteriores.
  Modelo, chaves, role readonly e flags do bot são preservados.
- O teste adicional online com contexto do print foi recusado pela revisão
  automática por envolver envio de contexto conversacional ao Gemini. Não foi
  executado por outro caminho, nem se atribui esse bloqueio à cota Gemini.
  A entrega corrigida foi validada depois pelo teste humano descrito abaixo.

Artefatos de diagnóstico e configuração permanecem locais/ignorados em `.local/`;
não se publicam credenciais, logs brutos ou histórico pessoal. A alteração de
produto não modifica resultados de experimentos congelados anteriores.

## Implantação e confirmação humana

Código implantado: `686b21cd7d1e6da32d234edc832488c0efb0d54b`, publicado na
branch `codex/comparacao-mensal`. O checkout ativo continua em
`/workspace/pac_privado-periodos`, atualizado por fast-forward; o runtime anterior
foi encerrado antes do novo início. Main não recebeu merge.

- Backend `/health`: HTTP 200 e configuração Telegram/IA/banco presente.
- Exatamente um processo de polling; supervisor registra o commit implantado.
- Mesma base `bi_comparativo`, modelo, chave, token, IDs, role e classificador
  desabilitado. Nenhuma mensagem Telegram proativa foi enviada.
- Fingerprints original/comparativo conferidos novamente após implantação e
  iguais aos manifests anteriores.
- Rollback privado preserva commit `583080dc98e95c8c1096671cb482ac244a6253bb`
  e supervisor anterior, sem copiar credenciais.
- Arthur enviou `/comecar` e repetiu a pergunta no Telegram; confirmou neste chat
  “Respondeu corretamente”. Essa é a evidência humana de entrega; não se afirma
  que health sozinho a comprova, nem se atribuem tokens/latência a esse teste.
- Instruções de retomada atualizadas no rascunho do ambiente. Exigem publicação
  pelas configurações do ambiente para uso em retomadas futuras.
