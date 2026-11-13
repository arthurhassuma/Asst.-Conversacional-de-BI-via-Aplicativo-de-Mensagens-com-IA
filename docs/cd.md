# Entrega contínua (CD)

O deploy não usa SSH nem `scp`. O pipeline testa, constrói e publica a imagem; a VM **busca** a versão promovida. Nenhuma chave de acesso à VM existe no GitHub, e a VM não precisa de porta aberta para o pipeline.

```
push na main
   │
   ▼
PAC checks (ruff, 349 testes com Postgres, corpus)        ── falhou? para aqui
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

Não foi verificado em uma VM real: a primeira execução na VM é o teste de ponta a ponta. O Compose recria os contêineres quando o ID da imagem muda, e há um intervalo curto sem resposta do bot durante a troca. Uma VM com 1 GB de RAM baixa a imagem sem construí-la, o que é mais leve do que o fluxo manual anterior (`docker build --no-cache`).

## Segurança

- Sem SSH e sem chave de acesso à VM no GitHub; o único segredo do pipeline é o `GITHUB_TOKEN` temporário.
- A imagem não contém segredos: as credenciais ficam em `private/*.env` na VM, montadas em tempo de execução.
- `workflow_run` só dispara para `push` na `main` com `PAC checks` verde; pull requests não publicam imagem.
- O deploy manual por `scp`, descrito em `deploy/oracle/README.md`, fica documentado apenas como recuperação de emergência.

Realizado dia 12/11/2026
