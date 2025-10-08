-- Create system_config table for storing app configuration
-- Used for DriverPulse auth data refreshed by GitHub Actions

CREATE TABLE IF NOT EXISTS system_config (
    config_key TEXT PRIMARY KEY,
    config_value TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add index for updated_at for monitoring freshness
CREATE INDEX IF NOT EXISTS idx_system_config_updated_at ON system_config(updated_at);

-- Add comments
COMMENT ON TABLE system_config IS 'System-wide configuration key-value store';
COMMENT ON COLUMN system_config.config_key IS 'Unique configuration key (e.g., driver_pulse_auth)';
COMMENT ON COLUMN system_config.config_value IS 'Configuration value stored as JSON text';
COMMENT ON COLUMN system_config.updated_at IS 'Last update timestamp (monitored by GitHub Actions)';
