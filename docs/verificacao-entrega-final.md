# Verificação de reprodução para entrega final

Data: 11/10/2026 (America/Sao_Paulo). Verificações executadas no ambiente em nuvem Linux x86_64, com Python 3.12.14 e dependências existentes em `/workspace/pac_privado/.venv`. Nenhuma chamada Gemini/Telegram foi feita, nenhum resultado reservado orientou ajustes e nenhuma feature ou fonte congelado foi alterado.

## Identidade conferida

- Checkout de execução isolado: `/workspace/pac_privado-desenvolvimento-rodada3`, HEAD destacado em `59c9eb8fa0b73444e770effd3e3e80724049164b`.
- Todos os hashes de aplicação, avaliação, scripts e SQL coincidem com o manifesto da rodada3 `20261011T161317Z-1c15b47d`; os fontes continuam idênticos após os checks. Relatórios locais não rastreados são apenas evidências previamente publicadas, não mudanças de produto.
- Conjunto v1.0.0: SHA256 `6a42eeb54169b15751eec3ff2e7657f52cdab96dc674dbaa7be16bc5c620bc2c`.
- Fontes, hash agregado: `d46a1a6fbb6c79507704cc03ff8aa6fe5db48c1788fb588e7f1d2442d7b0d860`.
- Base congelada, hash agregado: `d4f6623f1de2d8050ca3901b231ff00e05f1627bb09ecf8f7a7f0db86578cf6d`. Agregados usam SHA256 de `evaluation.runner.dump` (UTF-8, chaves ordenadas, indentação 2).
- A versão documental `13ff665a49f7cf0b0143e034f7ee4f1be8d37cfd` foi obtida e inspecionada sem mudar HEAD: seus fontes congelados e workflow são idênticos aos de `59c9eb8`. Seu commit imediato altera apenas documentação; a diferença acumulada inclui relatórios de evidências.

## Docker/Compose e isolamento

Docker CLI e daemon 28.4.0 e Compose v2.40.3 disponíveis. A imagem `postgres:16` já existia; não houve instalação de Docker nem download de imagem (`--pull never`).

A reprodução usou o `docker-compose.yml` original com projeto exclusivo `codex-pac-final-429b23fb50`, volume próprio do projeto e porta `127.0.0.1:53581`. A configuração foi validada com `config --quiet`, sem imprimir configuração interpolada. `--env-file /dev/null` impediu carregar configuração secreta original no Compose. Senhas administrativas e de leitura novas foram geradas apenas em memória e passadas no ambiente dos subprocessos; não são salvas ou publicadas. As configurações Gemini e Telegram desses subprocessos ficaram vazias.

Comandos Docker executados, todos com saída 0:

```sh
docker --version
docker compose version
docker info --format '{{.ServerVersion}}'
docker compose --env-file /dev/null -f docker-compose.yml -p codex-pac-final-429b23fb50 config --quiet
docker compose --env-file /dev/null -f docker-compose.yml -p codex-pac-final-429b23fb50 up -d --pull never
docker compose --env-file /dev/null -f docker-compose.yml -p codex-pac-final-429b23fb50 exec -T db pg_isready -U bi_owner -d bi_sintetico
docker compose --env-file /dev/null -f docker-compose.yml -p codex-pac-final-429b23fb50 down --volumes --remove-orphans
```

As variáveis de banco desses comandos apontavam exclusivamente ao banco descartável; os valores não aparecem no documento. Após a limpeza, consultas filtradas pelo rótulo desse projeto confirmaram ausência de containers e volumes remanescentes. Nenhum recurso de outro projeto foi removido.

## Reprodução da preparação e checks

No checkout congelado, com Python existente e ambiente apontando ao banco isolado:

| Comando | Evidência | Saída |
|---|---|---:|
| `python -m scripts.manage_db init` | Schema e role somente leitura criados em cluster novo | 0 |
| `python -m scripts.manage_db seed --seed 42 --clients 30` | 30 clientes, 56 contratos, 672 pedidos, 628 registros de faturamento, 672 indicadores | 0 |
| `python -m scripts.manage_db validate` | Zero inconsistências nos seis critérios | 0 |
| `python -m pytest -q --strict-markers` | **110 passed in 2.97s**, com PostgreSQL real e sem skips | 0 |
| `python -m ruff check app scripts tests evaluation` | Todos os checks aprovados | 0 |
| `python -m scripts.evaluate validate --env-file /dev/null` | **34 referências SQL validadas**, nenhuma chamada Gemini | 0 |
| `python -m pip check` | Nenhuma dependência incompatível | 0 |

O fingerprint completo da base isolada recém-gerada coincidiu exatamente com o manifesto congelado, inclusive hashes e contagens das cinco tabelas. A validação das referências é um check SQL somente leitura, não uma nova avaliação de modelo nem uma repetição do teste reservado.

O `pip check` também passou antes da reprodução. O aviso de cache não gravável do pip não afetou o resultado; nenhuma dependência foi instalada ou atualizada.

## Workflow da versão documental

O workflow `.github/workflows/tests.yml` de `13ff665` foi comparado byte a byte com o da versão congelada: idêntico. SHA256 `05f301e538abf692f0cabe55a84d3b6fbe1b5300e1d061db2ed79bc5ed259f0d`.

Foi conferido que ele prepara PostgreSQL 16 descartável, usa Python 3.13, instala `requirements-lock.txt`, executa `pip check`, lint, init/seed/validate e `pytest -q --strict-markers`. A sequência de checks de banco, lint e testes foi reproduzida localmente nesta verificação, além das 34 referências SQL.

A consulta read-only `gh run list --repo arthurhassuma/pac_privado --commit 13ff665a49f7cf0b0143e034f7ee4f1be8d37cfd --json databaseId,headSha,status,conclusion,url --limit 10` retornou **Forbidden** no acesso à API GitHub. Portanto, a aprovação remota informada pelo coordenador não foi confirmada independentemente aqui; nenhum workflow foi disparado. O acesso Git para obter código funcionou. Não se deve apresentar a reprodução local como execução GitHub Actions observada.

## Preservação e limitações

- A base original foi acessada somente para fingerprint antes/depois: conteúdo inalterado e igual ao manifesto congelado.
- O hash do `.env` original permaneceu igual, sem publicar conteúdo ou hash secreto. Os mesmos processos originais do backend, supervisor e bot permaneceram ativos; não houve reinício ou envio de mensagens.
- Evidências locais sanitizadas: `.local/final-delivery/verification.json`, ignorado pelo Git. Apenas este documento é publicado na branch `codex/experimento-desenvolvimento`; não há merge em main.
- Foi verificada a reprodução com dependências existentes e Python 3.12.14. Não se verificou instalação limpa do lock nem execução Python 3.13/GitHub Actions nesta rodada.
- Estes são checks de engenharia/reprodução, não novo experimento de acurácia ou medida Telegram ponta a ponta.
- O usuário informou validação e aceite do gestor em 11/10/2026, sem síntese de feedback. Isso é informação recebida, não observação ou validação realizada por este executor. Nenhuma síntese de feedback foi inventada.
