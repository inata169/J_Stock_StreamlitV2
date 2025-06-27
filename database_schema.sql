-- 日本株ウォッチドッグ Version 2.0 データベーススキーマ
-- 両方の真実を保持する設計

-- 1. ポートフォリオメインテーブル（証券会社データ中心）
CREATE TABLE portfolios (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(4) NOT NULL,           -- 銘柄コード（9432形式、.Tなし）
    data_source VARCHAR(20) NOT NULL,     -- 'rakuten' または 'sbi'
    
    -- 証券会社独自データ（真実の値）
    quantity INTEGER NOT NULL,            -- 保有数量（株）
    average_price DECIMAL(10,1),          -- 平均取得価額（円、小数点1桁）
    total_cost DECIMAL(12,1),             -- 取得総額（円）
    market_value DECIMAL(12,1),           -- 時価評価額（円）
    profit_loss DECIMAL(12,1),            -- 評価損益（円）
    
    -- 証券会社の損益率（原始値保持）
    profit_loss_rate_original DECIMAL(8,2),     -- 元の値（SBI: 167.98、楽天: null）
    profit_loss_rate_percent DECIMAL(8,1),      -- %表示用（167.9%）
    profit_loss_rate_decimal DECIMAL(8,4),      -- 小数表示用（1.6790）
    
    -- メタデータ
    import_timestamp TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(symbol, data_source)
);

-- 2. 銘柄マスターテーブル（Yahoo Finance データ）
CREATE TABLE stock_master (
    symbol VARCHAR(4) PRIMARY KEY,        -- 銘柄コード（統一形式）
    
    -- 基本情報
    long_name VARCHAR(200),               -- 企業名
    short_name VARCHAR(100),              -- 略称
    sector VARCHAR(100),                  -- セクター
    industry VARCHAR(100),                -- 業界
    exchange VARCHAR(20),                 -- 取引所
    currency VARCHAR(10) DEFAULT 'JPY',   -- 通貨
    
    -- 価格データ
    current_price DECIMAL(10,1),          -- 現在価格（円、小数点1桁）
    previous_close DECIMAL(10,1),         -- 前日終値
    day_high DECIMAL(10,1),               -- 日中高値
    day_low DECIMAL(10,1),                -- 日中安値
    
    -- 時価総額・企業規模
    market_cap BIGINT,                    -- 時価総額（円）
    shares_outstanding BIGINT,            -- 発行済株式数
    
    last_updated TIMESTAMP DEFAULT NOW()
);

-- 3. 財務指標テーブル（Yahoo Finance + 両方の真実保持）
CREATE TABLE financial_metrics (
    symbol VARCHAR(4),
    metric_date DATE,
    
    -- Yahoo Finance 原始値（小数形式）
    yahoo_dividend_yield DECIMAL(8,4),           -- 配当利回り（0.0500形式）
    yahoo_trailing_pe DECIMAL(8,1),              -- 実績PER（15.5倍）
    yahoo_price_to_book DECIMAL(8,1),            -- PBR（1.2倍）
    yahoo_return_on_equity DECIMAL(8,4),         -- ROE（0.1500形式）
    yahoo_profit_margins DECIMAL(8,4),           -- 純利益率（0.1000形式）
    yahoo_operating_margins DECIMAL(8,4),        -- 営業利益率
    yahoo_dividend_rate DECIMAL(8,1),            -- 年間配当額（円）
    
    -- 表示用変換値（%形式）
    display_dividend_yield DECIMAL(6,1),         -- 5.0%
    display_return_on_equity DECIMAL(6,1),       -- 15.0%
    display_profit_margins DECIMAL(6,1),         -- 10.0%
    
    -- 組み合わせ算出指標
    portfolio_dividend_yield DECIMAL(6,1),       -- ポートフォリオ配当利回り
    per_weighted_avg DECIMAL(8,1),               -- PER加重平均
    
    last_updated TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (symbol, metric_date),
    FOREIGN KEY (symbol) REFERENCES stock_master(symbol)
);

-- 4. API制限管理テーブル
CREATE TABLE api_usage_log (
    id SERIAL PRIMARY KEY,
    api_name VARCHAR(50),                 -- 'yahoo_finance', 'j_quants'
    request_timestamp TIMESTAMP DEFAULT NOW(),
    response_status INTEGER,              -- HTTPステータス
    rate_limit_remaining INTEGER,         -- 残りリクエスト数
    rate_limit_reset TIMESTAMP,           -- リセット時刻
    request_type VARCHAR(50),             -- 'stock_info', 'financial_data'
    symbol VARCHAR(4),                    -- 対象銘柄
    processing_time_ms INTEGER            -- 処理時間（ミリ秒）
);

-- 5. 更新設定テーブル
CREATE TABLE update_settings (
    id SERIAL PRIMARY KEY,
    setting_name VARCHAR(50) UNIQUE,      -- 'update_strategy', 'api_limits'
    setting_value JSONB,                  -- 設定値（JSON形式）
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- デフォルト設定の挿入
INSERT INTO update_settings (setting_name, setting_value) VALUES 
('update_strategy', '{"mode": "normal", "interval": 3600, "batch_size": 20}'),
('api_limits', '{"yahoo_finance": {"requests": 100, "window": 3600}, "backoff_enabled": true}');

-- 6. 表示用統合ビュー
CREATE VIEW portfolio_analytics AS
SELECT 
    p.symbol,
    sm.long_name,
    sm.sector,
    p.quantity,
    p.average_price,
    p.market_value,
    p.profit_loss,
    
    -- 両方の損益率表示
    p.profit_loss_rate_percent AS sbi_profit_loss_pct,
    p.profit_loss_rate_decimal AS decimal_profit_loss,
    
    -- Yahoo Finance指標
    fm.display_dividend_yield,
    fm.yahoo_trailing_pe,
    fm.display_return_on_equity,
    
    -- 組み合わせ指標
    ROUND(p.quantity * fm.yahoo_dividend_rate, 1) AS annual_dividend_income,
    ROUND(p.market_value / sm.market_cap * 100, 4) AS ownership_percentage,
    
    p.data_source,
    p.last_updated

FROM portfolios p
LEFT JOIN stock_master sm ON p.symbol = sm.symbol
LEFT JOIN financial_metrics fm ON p.symbol = fm.symbol 
    AND fm.metric_date = CURRENT_DATE;

-- インデックス作成（パフォーマンス最適化）
CREATE INDEX idx_portfolios_symbol ON portfolios(symbol);
CREATE INDEX idx_portfolios_updated ON portfolios(last_updated);
CREATE INDEX idx_api_usage_timestamp ON api_usage_log(request_timestamp);
CREATE INDEX idx_financial_metrics_date ON financial_metrics(metric_date);