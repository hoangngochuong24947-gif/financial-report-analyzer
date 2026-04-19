CREATE DATABASE IF NOT EXISTS financial_analyzer
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE financial_analyzer;

CREATE TABLE IF NOT EXISTS stocks (
  stock_code VARCHAR(16) NOT NULL PRIMARY KEY,
  stock_name VARCHAR(128) NOT NULL,
  market VARCHAR(32) NOT NULL,
  latest_report_date DATE NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS archive_manifests (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  stock_code VARCHAR(16) NOT NULL,
  stock_name VARCHAR(128) NOT NULL,
  market VARCHAR(32) NOT NULL,
  dataset VARCHAR(64) NOT NULL,
  fetched_at VARCHAR(32) NOT NULL,
  report_date DATE NULL,
  raw_path TEXT NOT NULL,
  csv_path TEXT NOT NULL,
  manifest_path TEXT NOT NULL,
  row_count INT NOT NULL DEFAULT 0,
  status VARCHAR(32) NOT NULL DEFAULT 'success',
  request_url TEXT NULL,
  request_params JSON NULL,
  error_message TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_archive_manifest_path (manifest_path(255)),
  KEY idx_archive_manifests_stock_dataset (stock_code, dataset),
  KEY idx_archive_manifests_report_date (report_date),
  CONSTRAINT fk_archive_manifests_stock
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS balance_sheet_summary (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  stock_code VARCHAR(16) NOT NULL,
  report_date DATE NOT NULL,
  total_current_assets DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  total_non_current_assets DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  total_assets DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  total_current_liabilities DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  total_non_current_liabilities DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  total_liabilities DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  total_equity DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_balance_stock_period (stock_code, report_date),
  KEY idx_balance_report_date (report_date),
  CONSTRAINT fk_balance_stock
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS income_statement_summary (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  stock_code VARCHAR(16) NOT NULL,
  report_date DATE NOT NULL,
  total_revenue DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  operating_cost DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  operating_profit DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  total_profit DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  net_income DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_income_stock_period (stock_code, report_date),
  KEY idx_income_report_date (report_date),
  CONSTRAINT fk_income_stock
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cashflow_statement_summary (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  stock_code VARCHAR(16) NOT NULL,
  report_date DATE NOT NULL,
  operating_cashflow DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  investing_cashflow DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  financing_cashflow DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  net_cashflow DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_cashflow_stock_period (stock_code, report_date),
  KEY idx_cashflow_report_date (report_date),
  CONSTRAINT fk_cashflow_stock
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS statement_line_items (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  stock_code VARCHAR(16) NOT NULL,
  statement_type VARCHAR(32) NOT NULL,
  report_date DATE NOT NULL,
  row_key VARCHAR(255) NOT NULL,
  label VARCHAR(255) NOT NULL,
  section_name VARCHAR(255) NULL,
  raw_value TEXT NULL,
  normalized_value DECIMAL(24, 2) NOT NULL DEFAULT 0.00,
  display_value VARCHAR(255) NULL,
  unit VARCHAR(32) NULL,
  source VARCHAR(64) NULL,
  is_estimated TINYINT(1) NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_statement_line (stock_code, statement_type, report_date, row_key),
  KEY idx_statement_line_stock_type_period (stock_code, statement_type, report_date),
  CONSTRAINT fk_statement_line_stock
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS financial_indicators (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  stock_code VARCHAR(16) NOT NULL,
  report_date DATE NULL,
  latest_report_label VARCHAR(64) NULL,
  metric VARCHAR(128) NOT NULL,
  latest_value_raw VARCHAR(255) NULL,
  latest_value_num DECIMAL(24, 8) NOT NULL DEFAULT 0.00000000,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_indicator_stock_metric_period (stock_code, metric, report_date),
  KEY idx_indicator_stock_report_date (stock_code, report_date),
  CONSTRAINT fk_indicator_stock
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
