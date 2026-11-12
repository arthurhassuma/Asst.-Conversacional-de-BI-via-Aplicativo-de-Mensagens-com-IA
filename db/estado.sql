CREATE SCHEMA IF NOT EXISTS estado;

CREATE TABLE IF NOT EXISTS estado.updates (
    update_id bigint PRIMARY KEY,
    payload jsonb,
    status varchar(12) NOT NULL DEFAULT 'pendente'
        CHECK (status IN ('pendente', 'processando', 'concluido', 'falhou')),
    tentativas integer NOT NULL DEFAULT 0,
    recebido_em timestamptz NOT NULL DEFAULT now(),
    reservado_ate timestamptz,
    concluido_em timestamptz
);
CREATE INDEX IF NOT EXISTS updates_fila
    ON estado.updates (recebido_em, update_id) WHERE status IN ('pendente', 'processando');
CREATE INDEX IF NOT EXISTS updates_concluidos
    ON estado.updates (concluido_em) WHERE concluido_em IS NOT NULL;

CREATE TABLE IF NOT EXISTS estado.sessoes (
    chat_id bigint NOT NULL,
    user_id bigint NOT NULL,
    turnos jsonb NOT NULL DEFAULT '[]'::jsonb,
    atualizado_em timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (chat_id, user_id)
);

REVOKE ALL ON SCHEMA estado FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA estado FROM PUBLIC;
GRANT USAGE ON SCHEMA estado TO app_estado;
GRANT SELECT, INSERT, UPDATE, DELETE ON estado.updates, estado.sessoes TO app_estado;
