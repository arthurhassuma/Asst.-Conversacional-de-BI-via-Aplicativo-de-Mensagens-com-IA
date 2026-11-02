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
não foram executados durante a recuperação de 02/11/2026.

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

## Credenciais e limites

Nenhum arquivo private/, .env, banco, log, chave SSH ou valor de credencial faz
parte desta entrega. Banco não tem porta pública; backend publica só loopback.
Condições Always Free e quotas precisam ser conferidas no provedor. Estes
arquivos não habilitam cobrança, fallback pago ou mudança de modelo.

O inventário está em [origem-recuperacao.json](origem-recuperacao.json) e a
evidência em [registro da hospedagem](../../docs/hospedagem-oracle-2026-10-13.md).
