-- Dados inteiramente sintéticos. Execute com o proprietário administrativo.
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

COMMENT ON TABLE clientes IS 'Empresas fictícias B2B, sem identificação fiscal ou contato real.';
COMMENT ON TABLE contratos IS 'Escopo contratado. Valor contratado não equivale a receita faturada.';
COMMENT ON TABLE pedidos IS 'Pedidos de serviços vinculados ao contrato, por data de aprovação.';
COMMENT ON TABLE faturamento IS 'Documentos sintéticos. Faturamento usa emissão e exclui canceladas; recebimentos usam pagamento e status paga.';
COMMENT ON TABLE indicadores_operacionais IS 'Medições mensais por contrato. Taxa de resolução = soma resolvidos / soma abertos.';
