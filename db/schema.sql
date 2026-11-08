-- Dados inteiramente sintéticos. Execute com o proprietário administrativo.
-- Domínio: revenda de autopeças. Nomes de tabelas e colunas são mantidos por compatibilidade.
CREATE TABLE clientes (
    id integer PRIMARY KEY,
    nome varchar(160) NOT NULL,
    segmento varchar(80) NOT NULL,
    cidade varchar(100) NOT NULL,
    uf char(2) NOT NULL CHECK (uf ~ '^[A-Z]{2}$'),
    cadastrado_em date NOT NULL
);

CREATE TABLE contratos (
    id integer PRIMARY KEY,
    cliente_id integer NOT NULL REFERENCES clientes(id),
    descricao varchar(200) NOT NULL,
    modalidade varchar(30) NOT NULL CHECK (modalidade IN ('projeto', 'sustentacao')),
    inicio date NOT NULL,
    fim date NOT NULL CHECK (fim >= inicio),
    valor_contratado numeric(14,2) NOT NULL CHECK (valor_contratado > 0),
    status varchar(20) NOT NULL CHECK (status IN ('ativo', 'concluido', 'cancelado'))
);

CREATE TABLE pedidos (
    id integer PRIMARY KEY,
    contrato_id integer NOT NULL REFERENCES contratos(id),
    descricao varchar(200) NOT NULL,
    data_pedido date NOT NULL,
    valor numeric(14,2) NOT NULL CHECK (valor > 0),
    status varchar(20) NOT NULL CHECK (status IN ('aprovado', 'entregue', 'cancelado'))
);

CREATE TABLE faturamento (
    id integer PRIMARY KEY,
    pedido_id integer NOT NULL REFERENCES pedidos(id),
    numero_documento varchar(40) NOT NULL UNIQUE,
    emissao date NOT NULL,
    vencimento date NOT NULL CHECK (vencimento >= emissao),
    pagamento date CHECK (pagamento >= emissao),
    valor numeric(14,2) NOT NULL CHECK (valor > 0),
    status varchar(20) NOT NULL CHECK (status IN ('aberta', 'paga', 'cancelada')),
    CHECK ((status = 'paga') = (pagamento IS NOT NULL))
);

CREATE TABLE indicadores_operacionais (
    id integer PRIMARY KEY,
    contrato_id integer NOT NULL REFERENCES contratos(id),
    competencia date NOT NULL CHECK (extract(day FROM competencia) = 1),
    horas_previstas numeric(10,2) NOT NULL CHECK (horas_previstas > 0),
    horas_realizadas numeric(10,2) NOT NULL CHECK (horas_realizadas >= 0),
    chamados_abertos integer NOT NULL CHECK (chamados_abertos >= 0),
    chamados_resolvidos integer NOT NULL CHECK (chamados_resolvidos BETWEEN 0 AND chamados_abertos),
    UNIQUE (contrato_id, competencia)
);

CREATE INDEX ON contratos(cliente_id);
CREATE INDEX ON contratos(inicio, fim);
CREATE INDEX ON pedidos(contrato_id, data_pedido);
CREATE INDEX ON pedidos(data_pedido);
CREATE INDEX ON faturamento(pedido_id);
CREATE INDEX ON faturamento(emissao);
CREATE INDEX ON faturamento(pagamento) WHERE pagamento IS NOT NULL;
CREATE INDEX ON indicadores_operacionais(competencia);

COMMENT ON TABLE clientes IS 'Clientes B2B da revenda de autopeças (oficinas, auto elétricas, funilarias, autocenters, frotas, retíficas e lojas). Dados sintéticos, sem identificação fiscal ou contato real.';
COMMENT ON TABLE contratos IS 'Contratos de fornecimento. Modalidade sustentacao = reposição recorrente de peças; projeto = fornecimento pontual por demanda. Valor contratado não equivale a receita faturada.';
COMMENT ON TABLE pedidos IS 'Pedidos de venda de peças vinculados ao contrato de fornecimento, por data de aprovação.';
COMMENT ON TABLE faturamento IS 'Notas fiscais sintéticas. Faturamento usa emissão e exclui canceladas; recebimentos usam pagamento e status paga.';
COMMENT ON TABLE indicadores_operacionais IS 'Medições mensais por contrato: horas de atendimento (balcão e televendas) e ocorrências de pós-venda (garantias, trocas e devoluções). Taxa de resolução = soma resolvidos / soma abertos.';
COMMENT ON COLUMN indicadores_operacionais.horas_previstas IS 'Horas de atendimento previstas no mês.';
COMMENT ON COLUMN indicadores_operacionais.horas_realizadas IS 'Horas de atendimento efetivamente realizadas no mês.';
COMMENT ON COLUMN indicadores_operacionais.chamados_abertos IS 'Ocorrências de pós-venda (garantia, troca, devolução) abertas no mês.';
COMMENT ON COLUMN indicadores_operacionais.chamados_resolvidos IS 'Ocorrências de pós-venda da mesma coorte do mês que já foram resolvidas.';
