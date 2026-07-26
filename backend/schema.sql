-- Zielit data-onboarding backend — PostgreSQL schema
-- One row per customer, one row per file they send us, one row per contact
-- loaded from those files, and saved audience "segments" built from rules.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE customers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    contact_email   TEXT NOT NULL,
    api_key         TEXT UNIQUE NOT NULL,       -- used for API-connection customers
    sftp_username   TEXT UNIQUE,                -- used for SFTP customers
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE uploads (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id     UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    filename        TEXT NOT NULL,
    source          TEXT NOT NULL CHECK (source IN ('sftp', 'api')),
    status          TEXT NOT NULL DEFAULT 'processing'
                        CHECK (status IN ('processing', 'complete', 'failed')),
    row_count       INTEGER DEFAULT 0,
    loaded_count    INTEGER DEFAULT 0,
    error_count     INTEGER DEFAULT 0,
    error_report    JSONB,                      -- list of {row, reason}
    uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ
);

-- One row per contact per customer. Re-uploading the same email updates
-- the existing row (upsert on customer_id + email) rather than duplicating it.
CREATE TABLE contacts (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id         UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    email               TEXT NOT NULL,
    first_name          TEXT,
    last_name           TEXT,
    company             TEXT,
    industry            TEXT,
    job_title           TEXT,
    country             TEXT,
    engagement_score    INTEGER DEFAULT 0,       -- 0-100, higher = more engaged
    last_purchase_date  DATE,
    consent_status      TEXT NOT NULL DEFAULT 'unknown'
                            CHECK (consent_status IN ('opted_in', 'opted_out', 'unknown')),
    consent_date        DATE,
    tags                TEXT[] DEFAULT '{}',
    source_upload_id    UUID REFERENCES uploads(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (customer_id, email)
);

CREATE INDEX idx_contacts_customer ON contacts(customer_id);
CREATE INDEX idx_contacts_engagement ON contacts(customer_id, engagement_score);
CREATE INDEX idx_contacts_industry ON contacts(customer_id, industry);
CREATE INDEX idx_contacts_consent ON contacts(customer_id, consent_status);

-- Saved audiences. `rules` is a small JSON rule-set (see segmentation.py)
-- so segments can be rebuilt live against the latest contact data.
CREATE TABLE segments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id     UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    rules           JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
