-- Migration: add account_type to crm_accounts
-- Values: 'buyer' (company seeking automation) | 'vendor' (robot company selling automation)
-- Default: 'buyer' preserves existing behaviour for the 200 already-imported accounts

ALTER TABLE crm_accounts
  ADD COLUMN IF NOT EXISTS account_type TEXT NOT NULL DEFAULT 'buyer'
    CHECK (account_type IN ('buyer', 'vendor'));

-- Index for fast filtering in admin queries
CREATE INDEX IF NOT EXISTS idx_crm_accounts_account_type ON crm_accounts (account_type);

COMMENT ON COLUMN crm_accounts.account_type IS
  'buyer = company seeking automation; vendor = robot company that sells automation';
