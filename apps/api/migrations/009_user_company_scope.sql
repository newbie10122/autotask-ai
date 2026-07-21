CREATE TABLE IF NOT EXISTS app_user_company_scopes (
    username TEXT NOT NULL REFERENCES app_users(username) ON DELETE CASCADE,
    company_id BIGINT NOT NULL REFERENCES autotask_companies(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (username, company_id)
);

CREATE INDEX IF NOT EXISTS app_user_company_scopes_company_idx
    ON app_user_company_scopes(company_id);
