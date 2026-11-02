# Hospedagem Oracle: entrega histórica e recuperação dos arquivos

## Conferência anterior à publicação, realizada em 02/11/2026

A consulta Git read-only ao origin confirmou main em
`a971546f25adbf996bfc1279637042125b6a4882`. Os cinco arquivos de runtime/Compose/
configuração não existem nessa árvore. Não há commit remoto desses arquivos
nessa main no momento da consulta. O commit a971546 é datado de 12/10 no Git;
13/10 é a data da preparação e implantação do pacote, não a data desse commit.

O ZIP enviado pelo usuário tem 123813 bytes e SHA256
`26e8b1987386c7d727f9e70ead7a67da5f89af1683b66bda74816537be08bd17`, idêntico ao
registro original. As 53 entradas do seu manifesto foram conferidas e os 43
arquivos já rastreados no repositório coincidem byte a byte com a main. Portanto
o pacote não contém uma versão diferente dos fontes do agente para substituir
os ajustes de 12/10; contém esses fontes e os complementos de hospedagem.

A recuperação inicial preservou e preparou os arquivos fora do checkout. Após
autorização do usuário, os nove arquivos desta entrega são versionados, sem
executar comandos na VM. Compose/configurador foram reorganizados em deploy/oracle,
com .gitignore para private/ e guia atualizado. Hashes dos cinco originais estão
em deploy/oracle/origem-recuperacao.json.

## Distinção entre as etapas

- 12/10: evolução gerencial, correção D38, UX, percentuais, comandos em português,
  opções de esclarecimento, datas relativas e comparação mensal. São fontes já
  incorporados à main mencionada; resultados congelados mantêm suas versões.
- 13/10: empacotamento, imagem Docker, Compose, configuração privada, preparação
  da VM e da base, transferência para um receptor e validação humana.

## Evidência histórica de implantação

Conforme capturas e confirmações nesta conversa: VM Oracle Ubuntu 24.04,
VM.Standard.E2.1.Micro indicada Always Free elegível, 1 OCPU/1 GB RAM, região
Vinhedo; Docker e Compose instalados. O usuário executou SSH/SCP e os comandos;
o agente não estabeleceu SSH direto na VM.

Imagem pac-bi-runtime:local construída com pip check. Projeto pac-bi-24h, banco
bi_comparativo separado e carga com seed 42, 100 clientes e 22 meses. Contagens observadas:
100/681/5100/5809/1700; seis critérios de validate com resultado zero.
Backend/banco saudáveis e autenticação Telegram observados. Após encerrar o
supervisor/polling antigos e bloquear reativação local, o novo polling foi ligado.
O usuário demonstrou /comecar, /limpar e consulta de faturamento e confirmou
continuidade depois de fechar o terminal, Docker enabled e restart unless-stopped.

Essas são evidências históricas, não verificação de saúde atual da VM em novembro.
Não houve medição de uptime de 24 h, reboot da VM, fatura, backup/restore ou SLA. Health
não testa cada dependência por consulta. Não foi observado coverage/fingerprint
completo pós-carga na VM; verificações isoladas anteriores não substituem isso.

## Pacote original e manifesto

O ZIP completo também contém README-INSTALACAO.md, verify-package.py,
source-manifest.json, SOURCE_COMMIT.txt e guias em .local/hospedagem. Eles descrevem
o layout e os hashes do release original. Não se devem colar esses hashes como
manifesto do novo layout GitHub: os caminhos foram reorganizados e a documentação
é nova. O ZIP original pode ser preservado como release histórico separado.

Não foram incluídos configurações privadas, valores secretos, IP, chave SSH,
dump de banco ou logs. Não houve nova chamada Gemini/Telegram, treinamento,
avaliação reservada ou alteração do servidor durante esta recuperação.
