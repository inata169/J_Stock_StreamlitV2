"""
Database Initialization Module
SQLiteデータベースの初期化・管理
"""

import sqlite3
import logging
import json
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """データベース初期化クラス"""
    
    def __init__(self, db_path: str = "stock_watchdog.db"):
        """
        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = Path(db_path)
        self.connection = None
    
    def connect(self) -> sqlite3.Connection:
        """データベースに接続"""
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,  # マルチスレッド対応
                timeout=30  # 30秒タイムアウト
            )
            # SQLiteの外部キー制約を有効化
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.execute("PRAGMA journal_mode = WAL")  # パフォーマンス向上
            logger.info(f"データベース接続成功: {self.db_path}")
            return self.connection
        except sqlite3.Error as e:
            logger.error(f"データベース接続エラー: {e}")
            raise
    
    def create_tables(self) -> bool:
        """全テーブルを作成"""
        if not self.connection:
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            # 1. ポートフォリオメインテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    data_source TEXT NOT NULL,
                    
                    -- 証券会社独自データ
                    quantity INTEGER NOT NULL,
                    average_price REAL,
                    total_cost REAL,
                    market_value REAL,
                    profit_loss REAL,
                    
                    -- 損益率（両方の真実を保持）
                    profit_loss_rate_original REAL,     -- 元の値（SBI: 167.98、楽天: null）
                    profit_loss_rate_percent REAL,      -- %表示用（167.9%）
                    profit_loss_rate_decimal REAL,      -- 小数表示用（1.6790）
                    
                    -- メタデータ
                    import_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    
                    UNIQUE(symbol, data_source)
                )
            """)
            
            # 2. 銘柄マスターテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_master (
                    symbol TEXT PRIMARY KEY,
                    
                    -- 基本情報
                    long_name TEXT,
                    short_name TEXT,
                    sector TEXT,
                    industry TEXT,
                    exchange TEXT,
                    currency TEXT DEFAULT 'JPY',
                    
                    -- 価格データ
                    current_price REAL,
                    previous_close REAL,
                    day_high REAL,
                    day_low REAL,
                    
                    -- 時価総額・企業規模
                    market_cap INTEGER,
                    shares_outstanding INTEGER,
                    
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 3. 財務指標テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS financial_indicators (
                    symbol TEXT,
                    data_date DATE,
                    
                    -- Yahoo Finance 原始値（小数形式）
                    dividend_yield REAL,                 -- 配当利回り（0.0500形式）
                    pe_ratio REAL,                       -- 実績PER（15.5倍）
                    pb_ratio REAL,                       -- PBR（1.2倍）
                    roe REAL,                            -- ROE（0.1500形式）
                    profit_margins REAL,                 -- 純利益率（0.1000形式）
                    operating_margins REAL,              -- 営業利益率
                    dividend_rate REAL,                  -- 年間配当額（円）
                    
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    
                    PRIMARY KEY (symbol, data_date),
                    FOREIGN KEY (symbol) REFERENCES stock_master(symbol)
                )
            """)
            
            # 4. API制限管理テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_name TEXT,
                    request_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    response_status INTEGER,
                    rate_limit_remaining INTEGER,
                    rate_limit_reset DATETIME,
                    request_type TEXT,
                    symbol TEXT,
                    processing_time_ms INTEGER
                )
            """)
            
            # 5. 更新設定テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS update_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_name TEXT UNIQUE,
                    setting_value TEXT,  -- JSON形式
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.connection.commit()
            logger.info("テーブル作成完了")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"テーブル作成エラー: {e}")
            return False
    
    def create_indexes(self) -> bool:
        """インデックスを作成（パフォーマンス最適化）"""
        try:
            cursor = self.connection.cursor()
            
            # パフォーマンス向上のためのインデックス
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_portfolios_symbol ON portfolios(symbol)",
                "CREATE INDEX IF NOT EXISTS idx_portfolios_updated ON portfolios(last_updated)",
                "CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage_log(request_timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_financial_indicators_date ON financial_indicators(data_date)",
                "CREATE INDEX IF NOT EXISTS idx_api_usage_api_name ON api_usage_log(api_name)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            self.connection.commit()
            logger.info("インデックス作成完了")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"インデックス作成エラー: {e}")
            return False
    
    def insert_default_settings(self) -> bool:
        """デフォルト設定を挿入"""
        try:
            cursor = self.connection.cursor()
            
            default_settings = [
                {
                    'setting_name': 'update_strategy',
                    'setting_value': json.dumps({
                        "mode": "normal", 
                        "interval": 3600, 
                        "batch_size": 20
                    })
                },
                {
                    'setting_name': 'api_limits',
                    'setting_value': json.dumps({
                        "yahoo_finance": {
                            "requests": 100, 
                            "window": 3600
                        }, 
                        "backoff_enabled": True
                    })
                }
            ]
            
            for setting in default_settings:
                cursor.execute("""
                    INSERT OR REPLACE INTO update_settings 
                    (setting_name, setting_value, updated_at) 
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (setting['setting_name'], setting['setting_value']))
            
            self.connection.commit()
            logger.info("デフォルト設定挿入完了")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"デフォルト設定挿入エラー: {e}")
            return False
    
    def create_views(self) -> bool:
        """表示用ビューを作成"""
        try:
            cursor = self.connection.cursor()
            
            # ポートフォリオ分析ビュー
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS portfolio_analytics AS
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
                    fm.dividend_yield,
                    fm.pe_ratio,
                    fm.roe,
                    
                    -- 組み合わせ指標
                    ROUND(p.quantity * fm.dividend_rate, 1) AS annual_dividend_income,
                    ROUND(p.market_value / sm.market_cap * 100, 4) AS ownership_percentage,
                    
                    p.data_source,
                    p.last_updated

                FROM portfolios p
                LEFT JOIN stock_master sm ON p.symbol = sm.symbol
                LEFT JOIN financial_indicators fm ON p.symbol = fm.symbol 
                    AND fm.data_date = DATE('now')
            """)
            
            self.connection.commit()
            logger.info("ビュー作成完了")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"ビュー作成エラー: {e}")
            return False
    
    def initialize_database(self) -> bool:
        """データベース全体を初期化"""
        logger.info("データベース初期化開始")
        
        try:
            # 接続
            self.connect()
            
            # テーブル作成
            if not self.create_tables():
                return False
            
            # インデックス作成
            if not self.create_indexes():
                return False
            
            # ビュー作成
            if not self.create_views():
                return False
            
            # デフォルト設定挿入
            if not self.insert_default_settings():
                return False
            
            logger.info("データベース初期化完了")
            return True
            
        except Exception as e:
            logger.error(f"データベース初期化エラー: {e}")
            return False
        finally:
            if self.connection:
                self.connection.close()
    
    def check_database_health(self) -> dict:
        """データベースの健全性チェック"""
        if not self.connection:
            self.connect()
        
        health_info = {}
        
        try:
            cursor = self.connection.cursor()
            
            # テーブル存在確認
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            health_info['tables'] = tables
            
            # 各テーブルのレコード数
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                health_info[f'{table}_count'] = count
            
            # データベースサイズ
            health_info['db_size_bytes'] = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            return health_info
            
        except sqlite3.Error as e:
            logger.error(f"データベース健全性チェックエラー: {e}")
            return {"error": str(e)}


# メイン関数群
def initialize_database(db_path: str = "stock_watchdog.db") -> bool:
    """データベース初期化のメイン関数"""
    initializer = DatabaseInitializer(db_path)
    return initializer.initialize_database()

def initialize_stock_database(db_path: str = "stock_watchdog.db") -> bool:
    """データベース初期化のメイン関数（互換性のため）"""
    return initialize_database(db_path)


def check_db_health(db_path: str = "stock_watchdog.db") -> dict:
    """データベース健全性チェックのメイン関数"""
    initializer = DatabaseInitializer(db_path)
    return initializer.check_database_health()


if __name__ == "__main__":
    # テスト実行
    print("=== データベース初期化テスト ===")
    
    # 初期化実行
    result = initialize_database("test_stock_watchdog.db")
    if result:
        print("✅ データベース初期化成功")
        
        # 健全性チェック
        health = check_db_health("test_stock_watchdog.db")
        print("\n📊 データベース健全性:")
        for key, value in health.items():
            print(f"   {key}: {value}")
    else:
        print("❌ データベース初期化失敗")