# Dicionário de dados

PostgreSQL 16, schema `public`. DDL e constraints: [schema.sql](../db/schema.sql).
Todos os registros são fictícios. Não se gera CNPJ, telefone ou e-mail. Valores monetários são BRL, armazenados como `numeric`, sem ponto flutuante. Datas não têm horário. IDs inteiros são gerados pelo seeder, sem sequências.

## clientes
Uma empresa B2B pode ter vários contratos.

| Campo | Tipo | Significado / restrição |
|---|---|---|
| id | integer | PK |
| nome | varchar(160) | Razão social fictícia, prefixo Empresa Fictícia |
| segmento | varchar(80) | Setor econômico |
| cidade | varchar(100) | Município sintético |
| uf | char(2) | UF, duas letras maiúsculas |
| cadastrado_em | date | Data de cadastro; referência temporal de novos clientes |

## contratos
Contrato de projeto ou sustentação, pertencente a um cliente.

| Campo | Tipo | Significado / restrição |
|---|---|---|
| id | integer | PK |
| cliente_id | integer | FK clientes.id |
| descricao | varchar(200) | Serviço contratado |
| modalidade | varchar(30) | projeto ou sustentacao |
| inicio | date | Início da vigência |
| fim | date | Fim inclusivo da vigência; não anterior ao início |
| valor_contratado | numeric(14,2) | Total previsto do contrato, estritamente positivo |
| status | varchar(20) | ativo, concluido ou cancelado |

## pedidos
Pedidos de serviço gerados ao longo da vigência do contrato. Na base padrão há um pedido por mês de cada contrato.

| Campo | Tipo | Significado / restrição |
|---|---|---|
| id | integer | PK |
| contrato_id | integer | FK contratos.id |
| descricao | varchar(200) | Entrega de serviço |
| data_pedido | date | Data da contratação/aprovação do pedido |
| valor | numeric(14,2) | Valor do pedido, positivo |
| status | varchar(20) | aprovado, entregue ou cancelado |

## faturamento
Um pedido pode gerar vários documentos. A base padrão gera um documento por pedido não cancelado. Não há FK redundante para cliente/contrato: derivar pelo pedido evita vínculos contraditórios.

| Campo | Tipo | Significado / restrição |
|---|---|---|
| id | integer | PK |
| pedido_id | integer | FK pedidos.id |
| numero_documento | varchar(40) | Identificador único com prefixo SINT |
| emissao | date | Data de emissão, referência de faturamento |
| vencimento | date | Vencimento, não anterior à emissão |
| pagamento | date, nullable | Data efetiva do pagamento; não anterior à emissão |
| valor | numeric(14,2) | Valor faturado positivo |
| status | varchar(20) | aberta, paga ou cancelada; pagamento existe se e somente se paga |

## indicadores_operacionais
Uma medição por contrato/competência. Chamados são uma coorte aberta no mês: resolvidos se refere à mesma coorte, não ao estoque anterior.

| Campo | Tipo | Significado / restrição |
|---|---|---|
| id | integer | PK |
| contrato_id | integer | FK contratos.id |
| competencia | date | Primeiro dia do mês; UNIQUE com contrato_id |
| horas_previstas | numeric(10,2) | Horas planejadas, positivas |
| horas_realizadas | numeric(10,2) | Horas realizadas, não negativas; podem exceder a previsão |
| chamados_abertos | integer | Coorte de chamados abertos no mês, não negativa |
| chamados_resolvidos | integer | Entre zero e chamados_abertos |

Todos os campos são NOT NULL, exceto pagamento. PKs, FKs, checks locais e UNIQUE são garantidos pelo banco. Regras entre tabelas (pedido dentro da vigência, faturamento após pedido e totais até o contratado) são garantidas pelo gerador e verificadas pelo comando `bi-db validate`; não há triggers para essas regras. O agente não pode escrever dados.

## Definições de consulta

| Métrica | Data / filtro | Cálculo |
|---|---|---|
| Faturamento emitido | emissao; excluir cancelada | SUM(faturamento.valor) |
| Recebimentos | pagamento; status paga | SUM(faturamento.valor) |
| Valor de pedidos | data_pedido; excluir cancelado | SUM(pedidos.valor) |
| Quantidade de pedidos | data_pedido; excluir cancelado | COUNT(*) |
| Novos contratos | inicio | COUNT(*) ou SUM(valor_contratado), conforme pedido |
| Contratos vigentes | sobreposição da vigência com período | Solicitar intenção explícita; não confundir com novos contratos |
| Novos clientes | cadastrado_em | COUNT(*) |
| Horas | competencia | SUM(horas_previstas) ou SUM(horas_realizadas) |
| Taxa de resolução | competencia | SUM(chamados_resolvidos)::numeric / NULLIF(SUM(chamados_abertos),0) |

Intervalos de consulta são início inclusivo e fim exclusivo. A taxa é fração; multiplicar por cem em SQL se o usuário solicitar porcentagem. Arredondar em SQL somente quando solicitado. SUM sem registros resulta NULL; COUNT resulta zero. Não somar contratos depois de joins que multipliquem suas linhas. Agregar cada fato antes de combinar fatos diferentes.

## Base padrão e índices
Seed padrão 42, 30 clientes, contratos nos anos 2024/2025, cadastros em 2023; pagamentos podem avançar para 2026. Quantidades dependem de seed e versão do Faker; `requirements-lock.txt` registra o ambiente verificado. Valores de pedidos mensais ficam entre cinco e trinta mil reais. A carga recusa tabelas previamente preenchidas, preservando dados existentes.

Índices: FKs de contratos/pedidos/faturamento; data_pedido, emissao, pagamento não nulo; vigência dos contratos; competencia e chave única (contrato_id, competencia).
