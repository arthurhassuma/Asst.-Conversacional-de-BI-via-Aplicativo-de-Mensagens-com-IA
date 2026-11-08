# Hospedagem do agente na Oracle

Arquivos recuperados do pacote usado em 13/10/2026, cuja aplicação tem origem no
commit `a971546f25adbf996bfc1279637042125b6a4882`. O Dockerfile, entrypoint,
dockerignore, Compose e configurador foram preservados byte a byte. Apenas a
organização de Compose/configurador passa de `.local/hospedagem/` para
`deploy/oracle/` no repositório. Os caminhos relativos `./private` continuam
resolvidos junto desses dois arquivos.

Adicionar estes arquivos ao GitHub não atualiza a instalação existente. A VM
implantada em 13/10 continua com sua estrutura `.local/hospedagem/`; não mova os
arquivos privados nem refaça init/seed/configuração nessa VM para fazer o commit.

## Componentes

- Dockerfile e runtime_entrypoint.py na raiz: imagem Python 3.13 com três modos:
  backend, polling e manage-db. Credenciais administrativas são removidas dos
  modos de aplicação.
- compose.yaml: PostgreSQL 16, backend e um polling, todos com restart
  unless-stopped; setup separado por profile; volume pgdata persistente.
- configure.py: entrada oculta para credenciais existentes; senhas novas do
  banco novo e segredo de encaminhamento. Diretório private 0700 e arquivos 0600.
- .gitignore local: exclui todo private/, inclusive database.env/setup.env/
  application.env, que não seriam cobertos por padrões limitados a `.env`.

## Instalação futura em servidor novo

Execute somente com um checkout completo do projeto, Docker/Compose, Python e
Git disponíveis. Use configuração de acesso GitHub do responsável, preservando
TLS e credenciais privadas. Os comandos seguintes partem da raiz do checkout e
não foram executados durante a recuperação de 02/11/2026. Para atualizar a VM
já implantada (sem clone git), veja "Atualizar código já implantado" abaixo.

```bash
sudo systemctl enable --now docker
sudo docker build --build-arg SOURCE_COMMIT="$(git rev-parse HEAD)" -t pac-bi-runtime:local .
sudo python3 deploy/oracle/configure.py
sudo docker compose -p pac-bi-24h -f deploy/oracle/compose.yaml config --quiet
sudo docker compose -p pac-bi-24h -f deploy/oracle/compose.yaml up -d db
```

O configurador recusa sobrescrever arquivos existentes. Preserve o modelo
utilizado; o original foi gemini-3.5-flash-lite. Execute com sudo como na
implantação original: o Compose usa UID/GID 0 por padrão para ler arquivos 0600.
Capabilities removidas e filesystem readonly não equivalem a execução não root.
Não execute `docker compose config` sem --quiet para compartilhar configuração.

Somente para base nova, uma vez:

```bash
sudo docker compose -p pac-bi-24h -f deploy/oracle/compose.yaml --profile setup run --rm setup manage-db init
sudo docker compose -p pac-bi-24h -f deploy/oracle/compose.yaml --profile setup run --rm setup manage-db seed --profile comparativo --clients 100 --seed 42 --start-month 2025-01 --end-month 2026-10
sudo docker compose -p pac-bi-24h -f deploy/oracle/compose.yaml --profile setup run --rm setup manage-db validate
sudo docker compose -p pac-bi-24h -f deploy/oracle/compose.yaml --profile setup run --rm setup manage-db coverage
sudo docker compose -p pac-bi-24h -f deploy/oracle/compose.yaml up -d --wait --wait-timeout 120 backend
curl --fail http://127.0.0.1:8000/health
```

Esperado no perfil sintético: 100 clientes, 681 contratos, 5100 pedidos, 5809
faturamentos e 1700 indicadores. Outubro inteiro é cenário sintético futuro na
data histórica de implantação, com fotografia de status em 31/10/2026.

Só depois de encerrar o receptor anterior e conferir o backend:

```bash
sudo docker compose -p pac-bi-24h -f deploy/oracle/compose.yaml up -d polling
sudo docker compose -p pac-bi-24h -f deploy/oracle/compose.yaml ps
```

Envie /comecar e uma pergunta conhecida pelo Telegram para confirmar entrega.
Health/autenticação não demonstram sozinhos consulta e resposta real do agente.
Não mantenha dois pollings para o mesmo token. Os códigos do bot permanecem nos
fontes já versionados; este diretório não substitui app/, scripts/ ou db/.

## Operação da VM original

Na raiz ~/pac_privado da VM original, o caminho continua sendo:

```bash
sudo docker compose -p pac-bi-24h -f .local/hospedagem/compose.yaml ps
curl --fail http://127.0.0.1:8000/health
```

Não use comandos de remoção de volumes como tentativa de recuperação. Um estado
unhealthy não provoca restart automaticamente; unless-stopped reage à saída do
processo/retorno do daemon e respeita parada intencional. A VM precisa permanecer
ligada e ter acesso às APIs e quota de IA. Volume não é backup; não houve SLA,
reboot observado ou plano completo de recuperação de desastre demonstrado.

**Confirmado em 02/11/2026: `~/pac_privado` nessa VM não é um clone git**, mesmo
com `git` instalado no sistema. Foi implantado via ZIP copiado por `scp` (ver
`README-INSTALACAO.md` e `SOURCE_COMMIT.txt` no próprio checkout da VM). `git pull`
falha com `fatal: not a git repository`. Para atualizar código nela, use `scp`.

## Atualizar código já implantado (sem tocar no banco)

Transfira só os arquivos alterados por `scp`, reconstrua a imagem e recrie
backend/polling — o volume `pgdata` não é tocado nesse fluxo:

```powershell
# No Windows local, na raiz do checkout
scp -i caminho\da\chave.pem app\arquivo1.py app\arquivo2.py usuario@ip-da-vm:~/pac_privado/app/
```

```bash
# Na VM, via SSH
cd ~/pac_privado
sudo docker build --no-cache --build-arg SOURCE_COMMIT="$(cat SOURCE_COMMIT.txt)" -t pac-bi-runtime:local .
sudo docker compose -p pac-bi-24h -f .local/hospedagem/compose.yaml up -d backend polling
curl --fail http://127.0.0.1:8000/health
```

Use `--no-cache` no build: já observamos o Docker reaproveitar a camada de
`COPY requirements-lock.txt` mesmo após o arquivo mudar no host, mantendo uma
dependência antiga e quebrando o build silenciosamente. Teste a mudança real no
Telegram depois do `curl` — `/health` não confirma que a lógica nova está no ar.

## Trocar o banco pelo perfil comparativo-v2 (destrutivo, decisão do responsável)

O `comparativo-v2` tem o mesmo escopo do perfil já implantado (100 clientes, 100%
dos meses jan/2025–out/2026, mesmas regras de cobertura de status), corrigindo
apenas a repetição de dia do pedido e de descrições. Trocar o banco da VM apaga o
volume `pgdata` atual: histórico de qualquer dado real que tenha entrado na base
desde 13/10/2026 (ex.: conversas que tenham gerado efeitos observáveis, se houver)
seria perdido. Confirme que está de acordo antes de rodar os comandos abaixo.

Atualize o código primeiro (seção anterior, via `scp`) se ainda não tiver feito.

```bash
cd ~/pac_privado

# 1. Backup do volume atual antes de qualquer coisa destrutiva
sudo docker compose -p pac-bi-24h -f .local/hospedagem/compose.yaml exec -T db \
  pg_dump -U bi_owner -d bi_comparativo > ~/backup-pgdata-$(date +%Y%m%d).sql

# 2. Parar os serviços que dependem do banco
sudo docker compose -p pac-bi-24h -f .local/hospedagem/compose.yaml stop backend polling

# 3. Remover o volume atual (irreversível; o backup do passo 1 é a única forma de voltar atrás)
sudo docker compose -p pac-bi-24h -f .local/hospedagem/compose.yaml down
sudo docker volume rm pac-bi-24h_pgdata

# 4. Recriar o banco vazio e reseedar com o perfil corrigido
sudo docker compose -p pac-bi-24h -f .local/hospedagem/compose.yaml up -d db
sudo docker compose -p pac-bi-24h -f .local/hospedagem/compose.yaml --profile setup run --rm setup manage-db init
sudo docker compose -p pac-bi-24h -f .local/hospedagem/compose.yaml --profile setup run --rm setup manage-db seed --profile comparativo-v2 --clients 100 --seed 42 --start-month 2025-01 --end-month 2026-10
sudo docker compose -p pac-bi-24h -f .local/hospedagem/compose.yaml --profile setup run --rm setup manage-db validate
sudo docker compose -p pac-bi-24h -f .local/hospedagem/compose.yaml --profile setup run --rm setup manage-db coverage

# 5. Religar backend e polling
sudo docker compose -p pac-bi-24h -f .local/hospedagem/compose.yaml up -d --wait --wait-timeout 120 backend
curl --fail http://127.0.0.1:8000/health
sudo docker compose -p pac-bi-24h -f .local/hospedagem/compose.yaml up -d polling
```

O passo 3 é o ponto sem volta: depois de `docker volume rm`, só o backup do passo 1
recupera os dados anteriores (via `psql ... < backup-pgdata-AAAAMMDD.sql` num banco
novo). Teste a mudança num ambiente separado antes, se possível, e confirme com um
`/comecar` e uma pergunta real pelo Telegram após o passo 5.

## Trocar o banco pelo perfil autopecas (destrutivo, decisão do responsável)

O perfil `autopecas` (revenda pequena-média, 100 clientes, jan/2025–out/2026, sem "Empresa
Fictícia" nos nomes) substitui a base de serviços de software. Mudou também o código do
backend (formato das respostas, vocabulário e prompts), então faça as duas coisas:

1. Envie o código novo e reconstrua com `--no-cache` (seção sobre atualização de código acima).
2. Siga os passos 1 a 5 da seção anterior (backup, parar, remover o volume, recriar), trocando
   as duas linhas de carga por:

```bash
sudo docker compose -p pac-bi-24h -f .local/hospedagem/compose.yaml --profile setup run --rm setup manage-db seed --profile autopecas --clients 100 --seed 42 --start-month 2025-01 --end-month 2026-10
sudo docker compose -p pac-bi-24h -f .local/hospedagem/compose.yaml --profile setup run --rm setup manage-db coverage --profile autopecas --start-month 2025-01 --end-month 2026-10
```

Os comentários do schema são só documentação do banco: o agente lê o glossário do código. Se
quiser atualizá-los sem recriar a base, execute `db/migrations/2026-11-autopecas-comentarios.sql`
com o usuário proprietário. Valem os mesmos avisos de ponto sem volta da seção anterior.

## Ligar o classificador de intenções (treinamento v2)

O classificador v2 vem ligado por padrão no código e no `.env.example`, mas dois pontos da
instalação original o mantinham desligado:

1. O `configure.py` (preservado byte a byte) grava `INTENT_CLASSIFIER_ENABLED=false` no arquivo
   privado do servidor, e o valor do arquivo prevalece sobre o padrão do código.
2. O `runtime_entrypoint.py` original **forçava `intent_classifier_enabled=False`** em todos os modos
   de aplicação, ignorando o arquivo privado. Essa linha foi removida em 08/11/2026 (o resto do
   arquivo é igual ao original; veja `alterados_depois_da_recuperacao` em
   [origem-recuperacao.json](origem-recuperacao.json)). Sem essa correção, ligar a variável não tem efeito.

Em um servidor já configurado, envie `app/`, `training/` e `runtime_entrypoint.py`, reconstrua com
`--no-cache` e então:

```bash
cd ~/pac_privado
sudo sed -i 's/^INTENT_CLASSIFIER_ENABLED=.*/INTENT_CLASSIFIER_ENABLED=true/' .local/hospedagem/private/application.env
sudo grep -c '^INTENT_CLASSIFIER_ENABLED=true' .local/hospedagem/private/application.env   # deve imprimir 1
C="sudo docker compose -p pac-bi-24h -f .local/hospedagem/compose.yaml"
$C up -d --force-recreate backend polling
```

Esse arquivo contém segredos: não mostre seu conteúdo, só conte a linha com `grep -c`.

**Como confirmar o uso.** Mande uma pergunta ao bot (no Telegram, não no terminal) e leia o log do
backend, que não contém o texto da pergunta:

```bash
$C logs backend --tail 50 | grep intencao
```

Esperado: `INFO:app.bi_agent:intencao rotulo=ranking confianca=0.99 aceita=True`. Se nenhuma linha
aparecer **depois** de uma pergunta, o classificador não está em uso. Também dá para conferir se o
processo viu a variável: `$C exec backend printenv INTENT_CLASSIFIER_ENABLED` deve imprimir `True`.

## Credenciais e limites

Nenhum arquivo private/, .env, banco, log, chave SSH ou valor de credencial faz
parte desta entrega. Banco não tem porta pública; backend publica só loopback.
Condições Always Free e quotas precisam ser conferidas no provedor. Estes
arquivos não habilitam cobrança, fallback pago ou mudança de modelo.

O inventário está em [origem-recuperacao.json](origem-recuperacao.json) e a
evidência em [registro da hospedagem](../../docs/hospedagem-oracle-2026-10-13.md).
