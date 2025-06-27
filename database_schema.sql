-- 日本株ウォッチドッグ Version 2.0 データベーススキーマ（SQLite版）
-- 両方の真実を保持する設計

-- SQLite設定
PRAGMA foreign_keys = ON;

-- 1. ポートフォリオメインテーブル（証券会社データ中心）
CREATE TABLE portfolios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,                 -- 銘柄コード（9432形式、.Tなし）
    name TEXT,                            -- 銘柄名
    data_source TEXT NOT NULL,            -- 'rakuten' または 'sbi'
    
    -- 証券会社独自データ（真実の値）
    quantity INTEGER NOT NULL,            -- 保有数量（株）
    average_price REAL,                   -- 平均取得価額（円）
    current_price REAL,                   -- 現在価格（円）
    total_cost REAL,                      -- 取得総額（円）
    market_value REAL,                    -- 時価評価額（円）
    profit_loss REAL,                     -- 評価損益（円）
    
    -- 証券会社の損益率（原始値保持）
    profit_loss_rate_original REAL,      -- 元の値（SBI: 167.98、楽天: null）
    profit_loss_rate_percent REAL,       -- %表示用（167.9%）
    profit_loss_rate_decimal REAL,       -- 小数表示用（1.6790）
    
    -- メタデータ
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(symbol, data_source)
);

-- 2. 株式マスターテーブル（Yahoo Finance データ）
CREATE TABLE stocks (
    symbol TEXT PRIMARY KEY,              -- 銘柄コード（統一形式）
    name TEXT,                            -- 企業名
    market TEXT,                          -- 取引所
    sector TEXT,                          -- セクター
    industry TEXT,                        -- 業界
    currency TEXT DEFAULT 'JPY',          -- 通貨
    
    -- 価格データ
    current_price REAL,                   -- 現在価格（円）
    previous_close REAL,                  -- 前日終値
    market_cap INTEGER,                   -- 時価総額（円）
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 財務指標テーブル（Yahoo Finance データ）
CREATE TABLE financial_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    
    -- Yahoo Finance 指標
    dividend_yield REAL,                  -- 配当利回り（小数形式: 0.05 = 5%）
    pe_ratio REAL,                        -- PER
    pb_ratio REAL,                        -- PBR
    roe REAL,                            -- ROE（小数形式）
    dividend_rate REAL,                   -- 年間配当額（円）
    
    -- メタデータ
    data_date DATE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
);

-- 4. API使用ログテーブル
CREATE TABLE api_usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_name TEXT NOT NULL,               -- 'yahoo_finance', 'j_quants'
    request_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_status INTEGER,              -- HTTPステータス
    symbol TEXT,                          -- 対象銘柄
    processing_time_ms INTEGER,           -- 処理時間（ミリ秒）
    request_type TEXT                     -- 'stock_info', 'financial_data'
);

-- 5. 設定テーブル
CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,             -- 設定キー
    value TEXT,                           -- 設定値（JSON形式）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成（パフォーマンス最適化）
CREATE INDEX idx_portfolios_symbol ON portfolios(symbol);
CREATE INDEX idx_portfolios_updated ON portfolios(last_updated);
CREATE INDEX idx_api_usage_timestamp ON api_usage_log(request_timestamp);
CREATE INDEX idx_financial_indicators_symbol ON financial_indicators(symbol);

-- デフォルト設定の挿入
INSERT INTO settings (key, value) VALUES 
('update_strategy', '{"mode": "normal", "interval": 3600, "batch_size": 20}'),
('api_limits', '{"yahoo_finance": {"requests": 100, "window": 3600}, "backoff_enabled": true}');