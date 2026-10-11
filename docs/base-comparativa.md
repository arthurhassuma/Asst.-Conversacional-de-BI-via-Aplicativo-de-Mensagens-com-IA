# Base sintética para comparações de BI

Perfil `comparativo-v1`, seed 42, **janeiro de 2025 a outubro de 2026**: 22 meses. Preparado em 11/10/2026 por solicitação do responsável. Outubro contém o mês inteiro como cenário sintético, inclusive datas posteriores à preparação. Não são dados observados nem projeções estimadas de uma empresa real. Status representam uma fotografia em **31/10/2026**.

## Conteúdo

| Entidade | Registros |
|---|---:|
| Clientes | 100 |
| Contratos | 681 |
| Pedidos | 5.100 |
| Documentos de faturamento | 5.809 |
| Indicadores operacionais | 1.700 |

Os 12 clientes da carteira inicial têm cadastro anterior ao período; os outros 88 se distribuem pelos 22 meses, com quatro novos clientes por mês. Há quatro segmentos e seis cidades, com UFs coerentes. A carteira combina sustentação recorrente e projetos. Contratos ativos têm término posterior à fotografia. Contratos concluídos e cancelados mantêm seus movimentos históricos.

Cada mês tem novos contratos nos três status, pedidos aprovados/entregues/cancelados, notas pagas/abertas/canceladas, recebimentos, horas e chamados. Cancelamento de um pedido não gera nota. Algumas notas parcelam o pedido, permitindo testar joins sem duplicar os valores. Notas canceladas não integram faturamento emitido ou recebimentos. O total faturado válido não supera o pedido, e pedidos válidos não superam o contrato.

Os valores variam por cliente, mês e entrega. Fatores explícitos de sazonalidade e um fator anual de cenário de 12% alteram os valores-base, junto de variação aleatória determinística. Crescimento de carteira também altera os totais. Essas regras criam um cenário para demonstração, sem sustentar conclusões econômicas sobre a Galvitech. Indicadores incluem situações com zero chamados, horas abaixo/acima do planejado e taxas diferentes entre meses.

[Resumo mensal](base-comparativa-resumo.json) contém contagens, status, valores exatos e hash do conteúdo gerado. SHA256 do JSON canônico dos registros (UTF-8, `ensure_ascii=False`, `sort_keys=True`, `default=str`): `bbef709101afee9888a6232c2d5a5736b241384a9fed9a9eb468d1190a9ab30a`. Identidade depende também das versões das bibliotecas.

## Preparação em banco separado

O perfil `original` continua sendo o padrão e preserva a base usada na avaliação acadêmica. Não substitua o banco dos experimentos. A carga recusa bases preenchidas e não oferece reset automático.

Para Compose, prepare `.env.comparativo` a partir de `.env.example`, com senhas novas e URLs coerentes, `POSTGRES_DB=bi_comparativo` e porta livre, por exemplo `55440`. Não copie valores secretos para o Git ou chat. Use um projeto Compose separado:

```powershell
docker compose --env-file .env.comparativo -p pac-comparativo up -d --wait
python -m scripts.manage_db init --env-file .env.comparativo
python -m scripts.manage_db seed --profile comparativo --clients 100 --seed 42 --start-month 2025-01 --end-month 2026-10 --env-file .env.comparativo
python -m scripts.manage_db validate --env-file .env.comparativo
python -m scripts.manage_db coverage --env-file .env.comparativo
```

`coverage` acessa o banco em transação de leitura, confere as invariantes e exige todas as entidades/status e recebimentos em cada competência. Falta de mês ou status produz erro, sem publicar um resumo parcial como se fosse completo. O perfil exige pelo menos 34 clientes para esse período; 100 é o padrão do CLI quando `--profile comparativo` é informado. O intervalo configurável aceita de um a 24 meses.

Para consultar esta base no agente, a configuração do processo deve apontar `DATABASE_URL` para o novo banco com o login `readonly_agent`. As ferramentas do agente nunca usam a URL administrativa. Preserve a configuração anterior e os tokens existentes. Reinicie o backend com a nova configuração após conferir a carga; não execute dois pollings do mesmo bot. A geração não altera tokens, webhook ou processo Telegram automaticamente.

## Comparações úteis

- “Mostre o faturamento emitido por mês de janeiro de 2025 a outubro de 2026.”
- “Compare o faturamento de janeiro a outubro de 2025 com janeiro a outubro de 2026.”
- “Compare os recebimentos de agosto de 2025 e agosto de 2026.”
- “Mostre as horas previstas e realizadas por mês de janeiro de 2025 a outubro de 2026.”
- “Compare a taxa de resolução de chamados de janeiro a outubro de 2025 e de 2026.”
- “Qual o faturamento por segmento em setembro de 2026?”

Compare períodos equivalentes: 2025 tem 12 meses, 2026 somente dez. Perguntas anuais sem esse cuidado misturam coberturas. A taxa de resolução usa somas dos chamados, sem média simples dos percentuais de cada contrato.

## Separação das evidências

Os experimentos de 40 casos e suas taxas pertencem à base original de 2024/2025 e aos fontes congelados. Não são resultados desta nova base. A ampliação é uma versão posterior para exploração e apresentação. Uma nova avaliação semântica precisaria de novas perguntas reservadas, sem reutilizar a amostra anterior para ajustar o agente.
