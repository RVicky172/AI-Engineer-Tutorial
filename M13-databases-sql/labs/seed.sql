-- ITSM-style practice schema for M13 (loaded automatically by docker compose on first start).
-- To reload: docker compose down -v && docker compose up -d

CREATE TABLE teams (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE
);

CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    email       TEXT NOT NULL UNIQUE,
    full_name   TEXT NOT NULL,
    team_id     INT REFERENCES teams(id),
    salary      NUMERIC(10,2)          -- sensitive: the agent must NOT be able to read this
);

CREATE TABLE services (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    tier        INT NOT NULL CHECK (tier BETWEEN 1 AND 3),   -- 1 = business critical
    owner_team  INT REFERENCES teams(id)
);

CREATE TABLE incidents (
    id           SERIAL PRIMARY KEY,
    number       TEXT NOT NULL UNIQUE,
    service_id   INT REFERENCES services(id),
    priority     TEXT NOT NULL CHECK (priority IN ('P1','P2','P3','P4')),
    state        TEXT NOT NULL CHECK (state IN ('new','in_progress','on_hold','resolved','closed')),
    short_desc   TEXT NOT NULL,
    opened_by    INT REFERENCES users(id),
    assigned_to  INT REFERENCES users(id),
    opened_at    TIMESTAMPTZ NOT NULL,
    resolved_at  TIMESTAMPTZ
);

CREATE TABLE changes (
    id           SERIAL PRIMARY KEY,
    number       TEXT NOT NULL UNIQUE,
    service_id   INT REFERENCES services(id),
    risk         TEXT NOT NULL CHECK (risk IN ('low','medium','high')),
    description  TEXT NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    succeeded    BOOLEAN
);

INSERT INTO teams (name) VALUES ('Payments'), ('Platform'), ('Identity'), ('Data');

INSERT INTO users (email, full_name, team_id, salary) VALUES
 ('asha@example.com',  'Asha Rao',      1, 95000), ('ben@example.com',   'Ben Ortiz',     1, 88000),
 ('chen@example.com',  'Chen Wei',      2, 102000), ('dana@example.com',  'Dana Kim',      2, 91000),
 ('eli@example.com',   'Eli Novak',     3, 87000), ('farah@example.com', 'Farah Haddad',  4, 99000);

INSERT INTO services (name, tier, owner_team) VALUES
 ('payments-api', 1, 1), ('checkout-web', 1, 1), ('k8s-platform', 1, 2),
 ('sso', 1, 3), ('reporting', 3, 4), ('etl-pipeline', 2, 4);

-- 120 incidents spread over the last 90 days
INSERT INTO incidents (number, service_id, priority, state, short_desc, opened_by, assigned_to, opened_at, resolved_at)
SELECT
  'INC' || lpad(g::text, 7, '0'),
  1 + (g % 6),
  (ARRAY['P1','P2','P3','P3','P4','P4'])[1 + (g % 6)],
  (ARRAY['new','in_progress','on_hold','resolved','closed','closed'])[1 + (g * 7 % 6)],
  (ARRAY['High latency','5xx errors spike','Login failures','Job failed','Disk full','Certificate expiring'])[1 + (g * 5 % 6)],
  1 + (g % 6),
  CASE WHEN g % 5 = 0 THEN NULL ELSE 1 + ((g + 2) % 6) END,
  now() - (g * interval '18 hours'),
  CASE WHEN (g * 7 % 6) >= 3 THEN now() - (g * interval '18 hours') + ((g % 48) + 1) * interval '1 hour' END
FROM generate_series(1, 120) g;

INSERT INTO changes (number, service_id, risk, description, scheduled_at, succeeded)
SELECT
  'CHG' || lpad(g::text, 7, '0'),
  1 + (g % 6),
  (ARRAY['low','medium','high'])[1 + (g % 3)],
  (ARRAY['Deploy new version','Rotate certificates','Scale node group','DB minor upgrade'])[1 + (g % 4)],
  now() - (g * interval '2 days'),
  CASE WHEN g % 7 = 0 THEN false ELSE true END
FROM generate_series(1, 40) g;

-- Read-only role for the text-to-SQL agent (lab-01)
CREATE ROLE agent_ro LOGIN PASSWORD 'agent_ro';
ALTER ROLE agent_ro SET default_transaction_read_only = on;
ALTER ROLE agent_ro SET statement_timeout = '5s';
GRANT CONNECT ON DATABASE itsm TO agent_ro;
GRANT USAGE ON SCHEMA public TO agent_ro;
GRANT SELECT ON teams, services, incidents, changes TO agent_ro;
-- Column-level grant: agent can see users but not salary
GRANT SELECT (id, email, full_name, team_id) ON users TO agent_ro;
