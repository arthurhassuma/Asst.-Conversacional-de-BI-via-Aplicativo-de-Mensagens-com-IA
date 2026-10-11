# Verificação e ativação da base comparativa

11/10/2026 (America/Sao_Paulo). Fonte preparada: `11f8ecf19b241bdece42dd04e3195b9405d1e9b4`, em checkout separado `/workspace/pac_privado-comparativo`. Evidências publicadas somente na branch `codex/base-comparativa-verificacao`, criada a partir dessa versão; o branch de apresentação não foi alterado.

## Carga e identidade

PostgreSQL 16 em projeto Compose `codex-pac-comparativo-3cb7b9ef`, volume exclusivo e porta local `127.0.0.1:58917`, banco **bi_comparativo**. Senhas de teste novas e configuração privada em `.local/comparativo.env`, permissão 0600 e ignorada pelo Git. Compose validado com `config --quiet`, sem imprimir valores interpolados; imagem existente usada com `--pull never`.

Comandos executados com `--env-file .local/comparativo.env`:

```sh
python -m scripts.manage_db init --env-file .local/comparativo.env
python -m scripts.manage_db seed --profile comparativo --clients 100 --seed 42 --start-month 2025-01 --end-month 2026-10 --env-file .local/comparativo.env
python -m scripts.manage_db validate --env-file .local/comparativo.env
python -m scripts.manage_db coverage --env-file .local/comparativo.env
```

Todos concluíram com saída 0. Contagens verificadas:

| Entidade | Registros |
|---|---:|
| Clientes | 100 |
| Contratos | 681 |
| Pedidos | 5.100 |
| Faturamento | 5.809 |
| Indicadores operacionais | 1.700 |

Cobertura completa dos 22 meses, de janeiro/2025 a outubro/2026, incluindo entidades, status e recebimentos mensais. Os seis critérios de consistência retornaram zero inconsistências.

Hash canônico dos dados **gerados**: `bbef709101afee9888a6232c2d5a5736b241384a9fed9a9eb468d1190a9ab30a`, conforme `json.dumps(..., ensure_ascii=False, sort_keys=True, default=str)`. Todos os registros carregados foram lidos pela role restrita e comparados em valor com o gerador: iguais. A serialização bruta do PostgreSQL pode incluir zeros adicionais pela escala `numeric` do schema; não confundir esse JSON com a serialização do gerador. Fingerprints separados das tabelas ficaram nas evidências locais.

## Engenharia e consultas

Python 3.12.14 e dependências existentes reutilizados, sem reinstalação. Com `TEST_DATABASE_URL` da nova base:

- `python -m pytest -q --strict-markers`: **117 passed in 3.17s**, incluindo PostgreSQL real, sem skips.
- `python -m ruff check app scripts tests evaluation`: aprovado.
- As seis referências de `docs/consultas-base-comparativa.sql` executaram pela role `readonly_agent`, em transações de leitura. Linhas retornadas por consulta: **22, 2, 22, 22, 22, 4**, sem truncamento.
- A consulta anual original com `extract` foi recusada pela allowlist do agente. Conforme correção documental autorizada, foram feitas apenas as substituições para `date_part('year', emissao)` e `date_part('month', emissao)`. Depois disso, as seis referências também passaram pela ferramenta SQL do agente. Não foi relaxada a política nem alterado código de produto.

Não foi reexecutado o conjunto reservado e nenhuma taxa acadêmica anterior é atribuída a esta base.

## Dois exemplos reais com Gemini

Foram executados **exatamente dois exemplos**, sem histórico anterior, perguntando a quantidade total de pedidos e o faturamento emitido de agosto de cada ano. O modelo planejou duas métricas; totais vieram dos templates do agente. Cada exemplo usou uma requisição SDK, com uma tentativa por requisição. Modelo resolvido: `gemini-3.5-flash-lite`; sem troca de modelo ou plano de cobrança.

| Período | Pedidos selecionados | Faturamento emitido selecionado | Resultado |
|---|---:|---:|---|
| Agosto/2025 | 185 | R$ 1.239.387,25 | Resposta final correta |
| Agosto/2026 | 289 | R$ 2.060.162,05 | Resposta final correta |

Gemini respondeu aos dois exemplos; nenhum erro externo ou bloqueio de cota ocorreu. São verificações manuais pontuais, não uma nova avaliação de acurácia. Não houve repetição de exemplos.

## Bot ligado à nova base

Os processos originais identificados estavam ativos e o backend respondeu à verificação de saúde antes da troca. Foi preservado rollback privado com comandos, diretórios e ambiente originais, sem modificar `/workspace/pac_privado/.env`.

O supervisor antigo foi encerrado primeiro, para impedir o reinício concorrente do polling. Só depois de confirmar seu encerramento e o do filho foi encerrado o backend antigo. O novo gerenciador usa o mesmo lock de polling; inicializa o backend com um worker e apenas um polling.

Verificações após a troca:

- Backend com checkout novo e `DATABASE_URL` da role `readonly_agent` em **bi_comparativo**, conferidos privadamente no processo; URL administrativa vazia no ambiente do bot.
- `/health`: HTTP200, Telegram autenticado, IA e banco configurados.
- Autenticação Telegram ocorreu na inicialização (`getMe`); o log sanitizado registrou “Polling ativo”. Isso comprova autenticação/recebimento iniciado, **não entrega de uma resposta no chat**.
- Varredura dos processos confirmou exatamente **um polling**. Processos novos: gerenciador 826287, backend 826288, polling 826291, no momento da verificação.
- Chave Gemini, token Telegram e IDs autorizados existentes foram reutilizados somente privadamente. Não houve envio proativo de mensagens.
- O restart criou sessões de conversa novas em memória. Um teste humano no chat privado ainda deve confirmar pergunta, resposta e continuidade, por exemplo com os dois períodos acima.

Runtime local: `.local/runtime-manager.py`; estado `.local/runtime-state.json`; log sanitizado `.local/runtime.log`. Rollback: executar `/workspace/pac_privado/.venv/bin/python /workspace/pac_privado-comparativo/.local/rollback-original.py`. Esse helper encerra o gerenciador novo antes de restaurar backend e supervisor originais. A configuração privada de rollback é 0600 e ignorada; o rollback foi preparado e inspecionado, mas não executado, para manter o bot na base nova. O volume comparativo permanece ativo porque agora serve o bot.

## Preservação e limites

A base dos experimentos manteve exatamente o fingerprint anterior; o checkout congelado `59c9eb8` e seus hashes de fontes continuam intactos. O `.env` original permaneceu byte a byte igual. As rodadas acadêmicas e seus artefatos não foram alterados. Apenas os processos desse bot foram substituídos pela configuração comparativa autorizada.

Outubro/2026 contém o mês inteiro como **cenário futuro sintético** em relação a 11/10/2026; status representam uma fotografia em **31/10/2026**. Não são fatos observados de uma empresa real.

Evidências locais ignoradas: `.local/preparation.json`, `.local/coverage.json`, `.local/reference-queries.json`, `.local/manual-examples.json` e `.local/switch-result.json`. Não foram publicados credenciais, valores de assinaturas, bancos ou logs HTTP brutos. `main` permanece sem merge.
