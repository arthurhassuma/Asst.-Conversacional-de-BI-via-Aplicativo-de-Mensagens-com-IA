# Guia de reprodução

Este guia permite que outra pessoa refaça, passo a passo, as verificações do projeto e confira os
resultados. Cada etapa traz o comando, o resultado esperado e o que foi **de fato medido** na
verificação de 10/11/2026 (versão `v1.0.1`). O que não pôde ser verificado está marcado como tal.

> **Sobre os hashes de commit.** Este repositório foi publicado em 12/11/2026 com o histórico reescrito (sem documentos internos de processo e sem os trailers de co-autoria), então os hashes mudaram. Os citados nos arquivos `.md` já foram convertidos para este histórico. Hashes em arquivos `.json` de evidência (`docs/dados/`), nos relatórios DOCX/PDF e nas apresentações são os do repositório privado original. O código e os conjuntos de avaliação são os mesmos; a equivalência de `v1.0.1` aqui está na tag de mesmo nome.

Há três caminhos, do mais barato ao mais caro:

| Caminho | O que reproduz | Precisa de Gemini? | Duração |
|---|---|---|---|
| A. Verificação offline | Testes, lint, base sintética e referências SQL dos conjuntos de avaliação | Não | 10 a 15 min |
| B. Imagem Docker | Que a imagem do backend constrói e carrega as dependências travadas | Não | 4 a 5 min |
| C. Avaliação real | As taxas de acerto com o Gemini (opcional) | **Sim**, consome cota | 25 min por conjunto |

Os caminhos A e B não enviam nada ao Gemini nem ao Telegram. O caminho C **não reproduz números
idênticos**: o Gemini não é determinístico (o mesmo caso mudou de resultado entre duas execuções
iguais), e o resultado esperado é uma faixa, não um valor fixo.

## Requisitos

- Git, Python 3.13 (o lock foi verificado com 3.13) e Docker com Compose.
- Um PostgreSQL 16 acessível. No caminho A você pode usar o Docker do projeto ou um PostgreSQL local.
- Para o caminho C: uma chave do Gemini (Google AI Studio) com cota disponível.

Todos os comandos abaixo partem da raiz do repositório. Em PowerShell, ative o ambiente com
`.\.venv\Scripts\Activate.ps1`; em Linux e macOS, com `source .venv/bin/activate`.

## Caminho A: verificação offline

### A.1 Instalar

```bash
git clone https://github.com/arthurhassuma/pac_privado.git
cd pac_privado
git checkout v1.0.1            # o repositório é privado: é preciso ter acesso
python -m venv .venv
# ative o ambiente (ver acima) e então:
python -m pip install -r requirements-lock.txt
python -m pip install -r requirements-training-lock.txt
python -m pip install -e . --no-deps
python -m pip check            # esperado: "No broken requirements found."
python -m ruff check app scripts tests evaluation training    # esperado: "All checks passed!"
```

### A.2 Subir o PostgreSQL

Com o Docker do projeto (o `docker-compose.yml` da raiz sobe só o banco):

```bash
cp .env.example .env
# edite .env e troque POSTGRES_PASSWORD, READONLY_PASSWORD e as duas URLs para senhas suas,
# mantendo as senhas consistentes com as URLs (ver a tabela de variáveis no README)
docker compose up -d --wait
```

Sem Docker, use qualquer PostgreSQL 16 com um banco vazio e um usuário proprietário; ajuste
`ADMIN_DATABASE_URL` e `DATABASE_URL` de acordo. As etapas seguintes usam só essas duas URLs.

### A.3 Testes da suíte completa (receita do CI)

Esta é a mesma sequência do job `.github/workflows/tests.yml`. Use um banco **descartável**, porque os
testes de estado durável recriam o schema `estado` e a role `app_estado`.

```bash
# variáveis (exemplo com senhas de teste; troque as URLs pelas do seu banco descartável)
export ADMIN_DATABASE_URL="postgresql://bi_owner:SENHA_ADMIN@127.0.0.1:PORTA/bi_sintetico"
export DATABASE_URL="postgresql://readonly_agent:SENHA_LEITURA@127.0.0.1:PORTA/bi_sintetico"
export TEST_DATABASE_URL="$DATABASE_URL"
export READONLY_PASSWORD="SENHA_LEITURA"
export TEST_STATE_ADMIN_URL="$ADMIN_DATABASE_URL"
export GEMINI_API_KEY="" TELEGRAM_BOT_TOKEN=""

python -m scripts.manage_db init
python -m scripts.manage_db seed --seed 42 --clients 30
python -m scripts.manage_db validate
python -m pytest -q --strict-markers
python -m scripts.train_intents validate
```

Resultado esperado:

| Etapa | Esperado |
|---|---|
| `init` | `Schema e role somente leitura criados.` |
| `seed` | 30 clientes, 56 contratos, 672 pedidos, 628 faturamentos, 672 indicadores |
| `validate` | todos os contadores de inconsistência em 0 |
| `pytest` com as variáveis acima | **337 passados, 0 falhas** |
| `pytest` sem `TEST_DATABASE_URL` e `TEST_STATE_ADMIN_URL` | 285 passados, 52 pulados |
| `train_intents validate` | 7 classes, 40 exemplos por classe, divisões treino 196, validação 28, teste 56 |

**Medido em 10/11/2026**, num PostgreSQL 16.14 nativo (sem Docker), Python 3.13.1: todos os valores
acima. A execução revelou um teste que dependia dos dados do perfil `autopecas` e falhava no perfil
`original`. A tag `v1.0.0` ainda contém esse teste (1 falha com banco no perfil `original`); a correção
está em `v1.0.1`, e por isso este guia usa essa versão.

### A.4 Perfil de autopeças e referências dos conjuntos de avaliação

Os conjuntos de avaliação são validados contra o perfil `autopecas`. Use outro banco (ou outro
schema limpo), porque `init` e `seed` recusam um banco já preenchido:

```bash
python -m scripts.manage_db init
python -m scripts.manage_db seed --profile autopecas --clients 100 --seed 42 --start-month 2025-01 --end-month 2026-10
python -m scripts.manage_db validate
python -m scripts.evaluate validate --dataset evaluation/cases-autopecas.json
python -m scripts.evaluate validate --dataset evaluation/managerial-cases-v1.json
python -m scripts.evaluate validate --dataset evaluation/cases-autopecas-reservado-2.json
```

Cada `evaluate validate` executa as consultas de referência contra a base e confere a estrutura do
conjunto, sem chamar o Gemini. Esperado:

| Conjunto | Versão | Casos | Referências SQL | SHA256 (início) |
|---|---|---|---|---|
| `evaluation/cases-autopecas.json` (A) | 3.1.0 | 40 | 34 | `e4c8b43081b9` |
| `evaluation/managerial-cases-v1.json` (B) | managerial-v1 | 35 | 28 | `cdb71fa885cd` |
| `evaluation/cases-autopecas-reservado-2.json` (C) | 1.0.0 | 20 | 17 | `45d5b1204532` |

Para conferir um hash: `sha256sum evaluation/cases-autopecas.json` (Linux e macOS) ou
`Get-FileHash evaluation\cases-autopecas.json` (PowerShell). Os conjuntos usam fim de linha LF
(`.gitattributes`); um checkout com CRLF muda o hash sem mudar o conteúdo.

**Medido em 10/11/2026**: 34, 28 e 17 referências validadas, com os três hashes acima, sobre a base
`autopecas` (100 clientes, seed 42).

## Caminho B: imagem Docker

```bash
docker build --build-arg SOURCE_COMMIT="$(git rev-parse HEAD)" -t pac-bi-runtime:local .
docker image inspect pac-bi-runtime:local --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}'
```

O `Dockerfile` instala o lock e executa `pip check`, então um build concluído já valida as
dependências. Esperado: build sem erro (cerca de 3 a 4 minutos, a maior parte na instalação das
dependências) e o rótulo igual ao commit.

Para subir backend e banco em contêineres, o fluxo documentado e usado na implantação está em
`deploy/oracle/README.md` (seção "Instalação futura em servidor novo"). Ele depende de
`deploy/oracle/configure.py`, que gera os arquivos privados de configuração, e de um token do
Telegram; não faz parte da verificação offline.

**Não verificado em 10/11/2026**: a máquina usada na verificação não tinha Docker, então o caminho B
**não foi executado a partir deste guia**. O mesmo build foi executado na VM de produção em 10/11/2026
(235 s, com `pip check` aprovado), conforme `docs/deploy.md`, rodada 8, e a reprodução Docker completa
de outubro (versão anterior) está em `docs/verificacoes.md`. Quem seguir este caminho deve registrar o
resultado.

## Caminho C: avaliação real com o Gemini (opcional)

Consome a cota do Gemini e leva cerca de 25 minutos por conjunto de 20 casos, com `--interval 60`.
Rodadas interrompidas por cota (`429`) ou indisponibilidade (`503`) não geram taxa oficial e devem ser
refeitas do zero. O protocolo, os critérios e a regra de contaminação estão em `docs/avaliacao.md`:
rode o conjunto reservado **uma vez**, com o código congelado, e nunca para ajustar prompts.

```bash
# arquivo local (ignorado pelo Git) com GEMINI_API_KEY, GEMINI_MODEL=gemini-3.5-flash-lite,
# INTENT_CLASSIFIER_ENABLED=true e DATABASE_URL apontando para a base autopecas
python -m scripts.evaluate run --live --dataset evaluation/cases-autopecas-reservado-2.json \
  --split test --interval 60 --limit 20 --env-file .local/avaliacao.env
```

Os resultados e o manifesto (commit, hash do conjunto, impressão digital da base antes e depois) ficam
em `.local/evaluation/`. A rodada só é válida se a base não mudou (`database_after.unchanged: true`).

Resultados observados nesta versão (uma execução cada, não reproduzíveis exatamente):

| Conjunto | Respostas corretas | Critério |
|---|---|---|
| C, partição nova (T41–T60), medido em `7e13ab2` (difere da `v1.0.1` só por rótulos de renderização) | 13/16 (14/16 em uma repetição) | ao menos 12/16 |
| A reservado, versão anterior às correções | 12/16 | ao menos 12/16 |
| Gerencial reservado, versão anterior às correções | 6/8 | ao menos 6/8 |

Espere variação de um ou dois casos entre execuções iguais. Um resultado dentro dessa faixa confirma a
reprodução; um resultado muito abaixo (por exemplo, menos de 10/16 no conjunto C) merece investigação.

## Problemas comuns

- **`init` recusa o banco:** ele não altera schema ou role existentes. Use um banco novo.
- **`seed` recusa o banco:** a carga só roda em banco vazio; não há comando de reset destrutivo.
- **Hash diferente do esperado:** confira o fim de linha (LF) do arquivo e se está na tag `v1.0.1`.
- **`429` ou `503` na avaliação:** é cota ou indisponibilidade do provedor; aguarde e refaça a rodada
  completa. Não complete uma rodada interrompida com resultados de outra.
- **Teste `test_percent_operator_and_like_patterns` falhando:** ele espera os dados do perfil
  `original` (30 clientes). Rode os testes de banco no banco da seção A.3, não no `autopecas`.
- **psycopg assíncrono no Windows:** o projeto usa psycopg síncrono com `asyncio.to_thread` por causa
  do loop de eventos do Windows; não troque por psycopg assíncrono.

## Registro da verificação

| Data | Ambiente | O que foi executado | Resultado |
|---|---|---|---|
| 10/11/2026 | Windows 11, Python 3.13.1, PostgreSQL 16.14 nativo | A.1 (lint) e A.3 completos; A.4 | 337 testes sem falhas (285 sem banco); contagens, corpus e referências conforme o esperado |
| 10/11/2026 | VM Oracle (Ubuntu, Docker) | Build da imagem (parte do caminho B) | Aprovado em 235 s; ver `docs/deploy.md`, rodada 8 |
| não executado | qualquer | B completo a partir deste guia; instalação limpa do lock em uma máquina nova (A.1) | pendente |

A instalação limpa do lock (A.1) usou nesta verificação o ambiente virtual já existente, e não uma
máquina nova; o guia ainda precisa ser seguido do zero por outra pessoa para validar essa etapa.
