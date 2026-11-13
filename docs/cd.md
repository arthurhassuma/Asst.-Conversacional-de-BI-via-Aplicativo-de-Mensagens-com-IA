# Entrega contínua (CD)

O deploy não usa SSH nem `scp`. O pipeline testa, constrói e publica a imagem; a VM **busca** a versão promovida. Nenhuma chave de acesso à VM existe no GitHub, e a VM não precisa de porta aberta para o pipeline.

```
push na main
   │
   ▼
PAC checks (ruff, 359 testes com Postgres, corpus)        ── falhou? para aqui
   │ sucesso
   ▼
Release / build ── constrói a imagem, publica ghcr.io/arthurhassuma/pac-bi-assistant:sha-<commit>
   │               e faz um teste de fumaça (revisão da imagem == commit; import da aplicação)
   ▼
Release / promote ── ambiente `production` (pode exigir aprovação)
   │                  retagueia a imagem testada como `:production`
   ▼
VM: pac-update.timer (a cada 2 min) ── docker pull :production
        imagem mudou? ── sim ─► recria backend e polling ─► /health ok? ── sim ─► registra a revisão
                                                                 └─ não ─► volta à imagem anterior
```

## Ambientes

| Ambiente        | Onde                                       | Como é atualizado                                                            |
| --------------- | ------------------------------------------ | ---------------------------------------------------------------------------- |
| Desenvolvimento | máquina local e Postgres descartável do CI | a cada commit (`PAC checks`)                                                 |
| Produção        | VM Oracle, Docker Compose (`pac-bi-24h`)   | pela promoção `:production`, com aprovação opcional no ambiente `production` |

A imagem `sha-<commit>` é o artefato testado e imutável; `:production` só aponta para uma delas.

## Configuração única

**No GitHub**

1. Settings → Environments → `production` → Required reviewers: adicione a si mesmo. Sem isso a promoção é automática.
2. Depois da primeira execução do `Release`, abra o pacote `pac-bi-assistant` (aba Packages do perfil) e, em Package settings, confira se a visibilidade é **Public** (a VM baixa sem credenciais; a imagem não contém segredos).

**Na VM** (uma vez; revise o script antes, porque ele roda como root)

```bash
sudo curl -fsSL https://raw.githubusercontent.com/arthurhassuma/Asst.-Conversacional-de-BI-via-Aplicativo-de-Mensagens-com-IA/<COMMIT-REVISADO>/deploy/oracle/pac-update.sh -o /usr/local/bin/pac-update
sudo chmod 0755 /usr/local/bin/pac-update
# o mesmo para pac-update.service e pac-update.timer, em /etc/systemd/system/
# ajuste Environment=PAC_COMPOSE_FILE no .service para o compose.yaml da VM
sudo systemctl daemon-reload
sudo systemctl enable --now pac-update.timer
sudo systemctl start pac-update.service
sudo journalctl -u pac-update -n 50 --no-pager
```

## Operação

| Tarefa                          | Comando                                                                                                                                                       |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Ver o que a VM aplicou          | `cat /var/lib/pac-update/deployed-revision` e `sudo journalctl -u pac-update`                                                                                 |
| Pausar atualizações             | `sudo systemctl stop pac-update.timer`                                                                                                                        |
| Reverter para a versão anterior | `sudo docker tag pac-bi-runtime:previous pac-bi-runtime:local && sudo docker compose -p pac-bi-24h -f <compose.yaml> up -d backend polling` (e pause o timer) |
| Reverter por pipeline           | rode `Release` manualmente a partir de um commit anterior e aprove a promoção                                                                                 |
| Imagem que falhou               | fica registrada em `/var/lib/pac-update/failed` e não é tentada de novo; uma nova promoção volta a tentar                                                     |

Depois de qualquer atualização, envie uma pergunta conhecida pelo Telegram: `/health` não prova que a lógica nova responde.

## O que o script garante (e o que não)

Verificado em `tests/test_deploy_update.py`, com `docker` e `curl` simulados: não faz nada se a imagem não mudou; mantém a imagem anterior; volta a ela se o Compose ou o `/health` falharem; não repete uma imagem que falhou; ignora execuções concorrentes; mantém a versão atual se o GHCR estiver fora do ar.

O Compose recria os contêineres quando o ID da imagem muda, e há um intervalo curto sem resposta do bot durante a troca (o Telegram guarda as mensagens pendentes). Uma VM com 1 GB de RAM baixa a imagem sem construí-la, o que é mais leve do que o fluxo manual anterior (`docker build --no-cache`).

## Validação na VM real (12/11/2026)

VM Oracle `VM.Standard.E2.1.Micro` (1 OCPU, 1 GB de RAM), Ubuntu 24.04, Docker Compose, projeto `pac-bi-24h`. Os horários abaixo estão em UTC; em Brasília ainda era 12/11/2026.

| Evento | Resultado |
|---|---|
| Primeira atualização, manual (`systemctl start pac-update.service`) | 01:26:15 a 01:27:17; revisão `4fd644916a9c0822be63995b53a747b0d9892e25`; backend `Healthy` em cerca de 40 s; banco não recriado; o bot respondeu depois |
| Perguntas pelo Telegram depois da troca | modelo fixo (faturamento de janeiro de 2025) e SQL livre (faturamento de Jaraguá do Sul e cadastros por UF) responderam |
| Ciclo automático: commit `ca4a991` → `PAC checks` e `CodeQL` verdes → `Release` (build e promoção) → VM | a VM baixou a imagem às 01:43:11 e concluiu às 01:44:22 (1 min 11 s), sem nenhum comando manual; `/var/lib/pac-update/deployed-revision` ficou com `ca4a9919866d84eeba389fc008b566e4110ac63d` |
| Reinício da VM (`sudo reboot`, por atualização de kernel pendente) | depois de 1 min ligada, Docker e `pac-update.timer` ativos; os três contêineres (`db`, `backend`, `polling`) voltaram sozinhos, há 38 s, com `backend` e `db` `healthy`; `/health` respondeu (`estado_duravel: true`); a revisão aplicada continuou `7c55b54958f036920f53e2d1526b2407006fdb92`; pico de carga de 4,48 no primeiro minuto, em 1 OCPU |

Limites da validação:

- O ramo de **reversão** só foi exercitado nos testes com `docker` e `curl` simulados; não houve falha real na VM.
- O ambiente `production` não tem revisor configurado, então a promoção é automática.
- Todo commit na `main` que passa no CI gera um deploy, inclusive os que só mudam documentação.
- Em 12/11/2026 a pasta do projeto na VM foi renomeada de `~/pac_privado` para `~/assistente-bi`; o nome do projeto do Compose (`pac-bi-24h`) não mudou e não deve mudar, para não perder o volume do banco.

## Segurança

- Sem SSH e sem chave de acesso à VM no GitHub; o único segredo do pipeline é o `GITHUB_TOKEN` temporário.
- A imagem não contém segredos: as credenciais ficam em `private/*.env` na VM, montadas em tempo de execução.
- `workflow_run` só dispara para `push` na `main` com `PAC checks` verde; pull requests não publicam imagem.
- O deploy manual por `scp`, descrito em `deploy/oracle/README.md`, fica documentado apenas como recuperação de emergência.
