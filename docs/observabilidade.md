# Observabilidade

Como o assistente é monitorado em produção. A estratégia tem três camadas, da mais simples à mais completa, e **nenhuma delas registra o texto das perguntas dos gestores**.

| Camada | O que mostra | Onde |
|---|---|---|
| Saúde | o processo está de pé e configurado | `GET /health` |
| Logs | eventos sem conteúdo (`consulta_concluida duracao_ms=… linhas=…`, `intencao rotulo=…`), rotação de 10 MB × 3 | `docker compose logs`, `journalctl -u pac-update` |
| Métricas | volume, desfecho, latência, erros do provedor e do banco | `GET /metrics` (formato Prometheus) |

## Métricas

O backend expõe `GET /metrics` em texto no formato do Prometheus, sem dependência nova. Os rótulos têm poucos valores possíveis, e as séries **não contêm pergunta, resposta, nome de cliente nem identificador de usuário**.

| Métrica | Tipo | Rótulo | O que responde |
|---|---|---|---|
| `bi_updates_total` | contador | `result`: `aceito`, `duplicado`, `fila_cheia`, `recusado_autenticacao`, `invalido`, `corpo_grande`, `bot_nao_configurado`, `falha_estado` | O webhook está recebendo e aceitando? Há tentativas indevidas? |
| `bi_questions_total` | contador | `status`: `answer`, `clarification_*`, `unsupported_request`, `invalid_question`, `provider_error`, `transport_error`, `error` | Como terminam as perguntas? Qual a taxa de falha? |
| `bi_question_duration_seconds` | histograma | – | Quanto demora uma resposta (p50, p95)? |
| `bi_gemini_requests_total` | contador | – | Quantas chamadas ao Gemini por pergunta (custo e cota)? |
| `bi_provider_errors_total` | contador | `code` (HTTP) | O provedor está limitando (429) ou indisponível (503)? |
| `bi_queries_total` | contador | `path`: `modelo_fixo`, `sql_livre` | Quanto do tráfego usa SQL livre? |
| `bi_sql_executions_total` | contador | `outcome`: `ok`, `timeout`, `db_error`, `recusado` | O banco está saudável? A política SQL está recusando? |
| `bi_sql_duration_seconds` | histograma | `outcome` | Quanto demora o banco? |
| `bi_build_info` | indicador | `revision` | Qual commit está rodando (liga métrica ao deploy) |
| `bi_process_start_time_seconds` | indicador | – | Quando o processo reiniciou |

Consulta rápida na VM, sem Prometheus:
```bash
curl -s http://127.0.0.1:8000/metrics | grep -E '^bi_(questions|updates|provider_errors)_total'
```

**Acesso.** O backend escuta só em `127.0.0.1:8000` na VM. Se o `/metrics` for exposto de outra forma (por exemplo atrás de um proxy do webhook), defina `METRICS_TOKEN` no `.env`: o endpoint passa a exigir `Authorization: Bearer <token>`.

## Painel e alertas (opcional)

`deploy/observability/` traz um Prometheus que coleta o `/metrics` a cada 15 s, guarda 15 dias e avalia as regras de `alerts.yml`. Roda como projeto separado (`pac-obs`) e entra na rede do projeto principal, então **não participa do deploy** nem é reiniciado pelo atualizador:

A pasta do projeto na VM não é um clone do git, então baixe os três arquivos (revise-os antes e fixe o commit):

```bash
C=<COMMIT-REVISADO>
B=https://raw.githubusercontent.com/arthurhassuma/Asst.-Conversacional-de-BI-via-Aplicativo-de-Mensagens-com-IA/$C/deploy/observability
mkdir -p ~/assistente-bi/observabilidade && cd ~/assistente-bi/observabilidade
for f in compose.yaml prometheus.yml alerts.yml; do curl -fsSL $B/$f -o $f; done
sudo docker compose -p pac-obs -f ~/assistente-bi/observabilidade/compose.yaml up -d
# a interface fica em 127.0.0.1:9090; para vê-la do seu computador:
#   ssh -L 9090:127.0.0.1:9090 ubuntu@<ip-da-vm>   e abra http://localhost:9090
```

Limite de memória de 192 MB, pensado para a VM de 1 GB. Se faltar memória, não suba o Prometheus: o `/metrics` e os logs continuam servindo.

| Alerta | Condição | O que fazer |
|---|---|---|
| `BackendForaDoAr` | sem resposta ao `/metrics` por 2 min | `docker compose ps` e logs do backend |
| `TaxaDeFalhaAlta` | mais de 20% das perguntas em 15 min terminam em falha (mínimo de 5 perguntas) | ver o desfecho por `status` e os logs |
| `CotaOuLimiteDoGemini` | algum 429 em 15 min | conferir a cota no Google AI Studio |
| `RespostasLentas` | p95 acima de 20 s por 10 min | ver Gemini e `bi_sql_duration_seconds` |
| `FilaCheia` | update recusado por fila cheia | aumentar `INBOX_MAX_PENDING` ou achar o gargalo |
| `ConsultasSQLComTimeout` | mais de 3 timeouts de SQL em 15 min | carga do banco e SQLs livres gerados |

## Limites

- **Não há notificação.** Os alertas aparecem na interface do Prometheus (aba Alerts); nada avisa o responsável por e-mail ou Telegram. Alertmanager (ou um aviso pelo próprio bot) é o próximo passo.
- **Contadores zeram quando o backend reinicia** (inclusive a cada deploy). Use `increase()` e `rate()`, como nas regras, e `bi_process_start_time_seconds` para ver reinícios.
- **Só o processo do backend é instrumentado.** O processo `polling` apenas repassa mensagens; se ele cair, o sintoma é `bi_updates_total{result="aceito"}` parar de crescer.
- **Sem rastreamento distribuído e sem painel pronto de Grafana.** Os gráficos são consultas PromQL na interface do Prometheus.
- O Prometheus e as regras foram validados como YAML, **mas não foram executados em uma VM real**; a primeira subida é o teste de ponta a ponta.
