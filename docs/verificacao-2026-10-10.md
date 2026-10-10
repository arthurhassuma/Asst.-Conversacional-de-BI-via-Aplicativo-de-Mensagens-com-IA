# Verificação da continuidade — 10/10/2026

## Código e ambiente

Fonte: `arthurhassuma/pac_privado`, base `31ad3a4`, branch `codex/alinhamento-proposta`. Clone em `C:/Users/arthu/PAC - TCC/pac_privado`; arquivos da cópia anterior preservados. Proposta PDF e relatório DOCX já estão versionados em `docs/`.

Usado o ambiente Python 3.13.1 existente na pasta superior e o cluster PostgreSQL 16.14 dedicado do projeto, porta 55439. O login de teste foi `readonly_agent`; a URL foi carregada em memória, sem impressão de credenciais. Não foi preciso instalar dependências nem copiar `.env` para o clone.

O cluster estava parado antes da revisão, foi iniciado para as verificações e encerrado ao final, preservando os dados. Nenhum serviço do ambiente conectado informado pelo usuário foi alterado.

## Evidência de engenharia

- Antes das mudanças: 52 testes aprovados e 13 testes de integração ignorados por ausência de `TEST_DATABASE_URL`.
- Depois das mudanças e revisão, com PostgreSQL: **77 testes aprovados, sem skips** (17,75 segundos nesta execução). Essa duração é da suíte, não latência média do assistente.
- Novos casos verificam frases controladas com precisão decimal, zero vindo de célula, NULL sem inventar zero, aviso de truncamento, diagnóstico sem rede por padrão, credenciais ausentes, autenticação pelos SDKs, schema incompleto e erro de cota sem revelar segredos.
- O fluxo completo testa webhook FastAPI, protocolo Gemini, PostgreSQL real e envio pelo SDK Telegram com transporte externo simulado. O valor renderizado é conferido com consulta independente.
- Os testes de PostgreSQL verificam também a negação de escrita, timeout, limite de linhas e consistência da base sintética.
- Diagnóstico executado contra o banco real: conexão somente leitura e metadados confirmados. As seis verificações de consistência retornaram zero ocorrências.
- `ruff check app scripts tests`, `compileall` e `git diff --check` passaram; `pip check` não encontrou conflitos de dependências.
- Revisão independente identificou que o alias `total` não comprova soma ou moeda. A apresentação foi corrigida para frase neutra, com regressões para média de horas e variação percentual; não acrescenta `R$`, percentuais ou afirmações de soma pelo alias.

## Limites da verificação

O usuário confirmou conexão Gemini/Telegram em outro ambiente. Não recebemos credenciais e não realizamos chamadas reais a esses dois serviços nesta sessão. Nenhuma mensagem foi enviada pelo assistente ao Telegram e nenhum webhook foi registrado ou removido.

`--testar-conexoes` faz uma chamada pequena de geração ao Gemini, consumindo a cota do projeto configurado. A verificação Telegram usa apenas `getMe`. São testes de conectividade, não testes de interpretação, function calling real ou entrega ponta a ponta. O diagnóstico não verifica plano de cobrança.

Docker Compose e avaliação acadêmica não foram executados. Permanecem fora desta evidência: accuracy, latência média real, feedback da Galvitech e hipótese científica.

## Registro a preencher no ambiente conectado

| Campo | Valor |
|---|---|
| Data e commit usados no teste manual | Não registrado nesta revisão |
| Modelo configurado e versão resolvida | Não registrado nesta revisão |
| `/start` e pergunta `Qual o faturamento?` | Confirmar pergunta de esclarecimento |
| Continuação `janeiro de 2025` | Conferir valor contra SQL do README |
| SQL de referência / valor esperado / valor recebido | Registrar sem credenciais nem identificação pessoal |
| `/limpar` seguido de pergunta sem período | Confirmar novo esclarecimento |
| Observações e falhas externas | Registrar fielmente, sem considerar simulações como acesso real |

O documento `verificacao.md` conserva a primeira entrega de 27/09, anterior à migração. `publicacao-github.md` conserva a importação de 04/10. Este registro complementa esses históricos; não altera seus resultados retroativamente.
