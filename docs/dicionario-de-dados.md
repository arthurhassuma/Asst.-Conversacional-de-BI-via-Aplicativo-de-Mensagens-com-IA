# Dicionário de dados

PostgreSQL 16, schema `public`. DDL e constraints: [schema.sql](../db/schema.sql).
**Domínio:** revenda de autopeças de porte pequeno a médio, que vende a oficinas, frotas e lojas. Os nomes de tabelas e colunas vêm da versão inicial (serviços de software) e foram mantidos por compatibilidade com o SQL, os testes e a avaliação; o significado de negócio é o da tabela abaixo.

| Nome no banco | Significado no negócio |
|---|---|
| `contratos` | Contratos de fornecimento. `sustentacao` = reposição recorrente de peças; `projeto` = fornecimento pontual por demanda |
| `pedidos` | Pedidos de venda de peças |
| `faturamento` | Notas fiscais |
| `indicadores_operacionais.horas_*` | Horas de atendimento (balcão e televendas) |
| `indicadores_operacionais.chamados_*` | Ocorrências de pós-venda: garantias, trocas e devoluções |

Todos os registros são fictícios. Não se gera CNPJ, telefone ou e-mail. Valores monetários são BRL, armazenados como `numeric`, sem ponto flutuante. Datas não têm horário. IDs inteiros são gerados pelo seeder, sem sequências.

## clientes
Um cliente (oficina, auto elétrica, funilaria, autocenter, frota, retífica ou loja) pode ter vários contratos.

| Campo | Tipo | Significado / restrição |
|---|---|---|
| id | integer | PK |
| nome | varchar(160) | Nome comercial fictício (ex.: Auto Mecânica Santa Cruz). Os perfis antigos usam o prefixo Empresa Fictícia |
| segmento | varchar(80) | Tipo de cliente: Oficina mecânica, Auto elétrica, Funilaria e pintura, Autocenter, Frota e transportadora, Loja de autopeças ou Retífica de motores (perfil autopecas) |
| cidade | varchar(100) | Município sintético |
| uf | char(2) | UF, duas letras maiúsculas |
| cadastrado_em | date | Data de cadastro; referência temporal de novos clientes |

## contratos
Contrato de fornecimento (reposição recorrente ou fornecimento pontual), pertencente a um cliente.

| Campo | Tipo | Significado / restrição |
|---|---|---|
| id | integer | PK |
| cliente_id | integer | FK clientes.id |
| descricao | varchar(200) | Objeto do fornecimento |
| modalidade | varchar(30) | projeto ou sustentacao |
| inicio | date | Início da vigência |
| fim | date | Fim inclusivo da vigência; não anterior ao início |
| valor_contratado | numeric(14,2) | Total previsto do contrato, estritamente positivo |
| status | varchar(20) | ativo, concluido ou cancelado |

## pedidos
Pedidos de venda gerados ao longo da vigência do contrato. No perfil original há um pedido por mês de cada contrato; no perfil autopecas a quantidade varia por cliente e mês.

| Campo | Tipo | Significado / restrição |
|---|---|---|
| id | integer | PK |
| contrato_id | integer | FK contratos.id |
| descricao | varchar(200) | Peças vendidas (ex.: Pastilhas e discos de freio) |
| data_pedido | date | Data da venda/aprovação do pedido |
| valor | numeric(14,2) | Valor do pedido, positivo |
| status | varchar(20) | aprovado, entregue ou cancelado |

## faturamento
Um pedido pode gerar vários documentos. A base padrão gera um documento por pedido não cancelado. Não há FK redundante para cliente/contrato: derivar pelo pedido evita vínculos contraditórios.

| Campo | Tipo | Significado / restrição |
|---|---|---|
| id | integer | PK |
| pedido_id | integer | FK pedidos.id |
| numero_documento | varchar(40) | Identificador único da nota (prefixo SINT, COMP ou NF, conforme o perfil) |
| emissao | date | Data de emissão, referência de faturamento |
| vencimento | date | Vencimento, não anterior à emissão |
| pagamento | date, nullable | Data efetiva do pagamento; não anterior à emissão |
| valor | numeric(14,2) | Valor faturado positivo |
| status | varchar(20) | aberta, paga ou cancelada; pagamento existe se e somente se paga |

## indicadores_operacionais
Uma medição por contrato/competência. Ocorrências de pós-venda (colunas `chamados_*`) são uma coorte aberta no mês: resolvidos se refere à mesma coorte, não ao estoque anterior.

| Campo | Tipo | Significado / restrição |
|---|---|---|
| id | integer | PK |
| contrato_id | integer | FK contratos.id |
| competencia | date | Primeiro dia do mês; UNIQUE com contrato_id |
| horas_previstas | numeric(10,2) | Horas de atendimento planejadas, positivas |
| horas_realizadas | numeric(10,2) | Horas de atendimento realizadas, não negativas; podem exceder a previsão |
| chamados_abertos | integer | Coorte de ocorrências de pós-venda abertas no mês, não negativa |
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
**Perfil `autopecas` (recomendado para a apresentação):** `bi-db seed --profile autopecas --clients 100 --seed 42 --start-month 2025-01 --end-month 2026-10`. Cobre 22 meses com 100 clientes, cerca de 730 contratos, 7,7 mil pedidos e 8,1 mil notas. Escala de revenda pequena-média: em média R$ 350–410 mil e 320–360 pedidos por mês, ticket médio perto de R$ 1.100 (de R$ 60 a R$ 40 mil por pedido). Pedidos têm quantidade e valor variáveis por cliente e dia útil; notas têm prazo por segmento (15 a 45 dias), parcelamento ocasional, inadimplência pequena e pedidos `aprovado` só nos últimos dias do cenário. Em janeiro de 2025 os recebimentos são baixos porque o cenário não traz notas de dezembro de 2024. Nenhum nome de cliente contém "Empresa Fictícia".

Perfis anteriores (`original`, `original-v2`, `comparativo`, `comparativo-v2`) permanecem para reproduzir a avaliação congelada e o hash de `docs/base-comparativa.md`. Neles: seed padrão 42, 30 clientes, contratos nos anos 2024/2025, cadastros em 2023; pagamentos podem avançar para 2026. Quantidades dependem de seed e versão do Faker; `requirements-lock.txt` registra o ambiente verificado. No perfil original, os pedidos mensais ficam entre cinco e trinta mil reais. A carga recusa tabelas previamente preenchidas, preservando dados existentes.

Índices: FKs de contratos/pedidos/faturamento; data_pedido, emissao, pagamento não nulo; vigência dos contratos; competencia e chave única (contrato_id, competencia).
