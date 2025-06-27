"""
Database Manager Module
データベースアクセス・管理クラス
"""

import sqlite3
import logging
import json
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple, Any
from contextlib import contextmanager
try:
    from .database_init import DatabaseInitializer
    from .symbol_utils import SymbolNormalizer, DecimalFormatter
except ImportError:
    # テスト実行時の対応
    from database_init import DatabaseInitializer
    from symbol_utils import SymbolNormalizer, DecimalFormatter

logger = logging.getLogger(__name__)


class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self, db_path: str = "stock_watchdog.db"):
        """
        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = db_path
        self.connection = None
        self.symbol_normalizer = SymbolNormalizer()
        self.decimal_formatter = DecimalFormatter()
        
        # データベースが存在しない場合は初期化
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """データベースが存在しない場合は初期化"""
        try:
            initializer = DatabaseInitializer(self.db_path)
            if not initializer.db_path.exists():
                logger.info("データベースが存在しないため初期化します")
                initializer.initialize_database()
        except Exception as e:
            logger.error(f"データベース初期化エラー: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """データベース接続のコンテキストマネージャ"""
        try:
            conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30
            )
            conn.execute("PRAGMA foreign_keys = ON")
            conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能
            yield conn
        except sqlite3.Error as e:
            logger.error(f"データベース接続エラー: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def transaction(self):
        """トランザクション管理のコンテキストマネージャ"""
        with self.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"トランザクションロールバック: {e}")
                raise
    
    # ===== ポートフォリオデータ管理 =====
    
    def insert_portfolio_data(self, portfolio_data: Dict[str, Any]) -> bool:
        """ポートフォリオデータを挿入・更新"""
        try:
            # 銘柄コード正規化
            symbol = self.symbol_normalizer.normalize(portfolio_data.get('symbol', ''))
            if not symbol:
                logger.error(f"無効な銘柄コード: {portfolio_data.get('symbol')}")
                return False
            
            # 数値フォーマット
            data = {
                'symbol': symbol,
                'data_source': portfolio_data.get('data_source', ''),
                'quantity': int(portfolio_data.get('quantity', 0)),
                'average_price': self.decimal_formatter.format_price(portfolio_data.get('average_price')),
                'total_cost': self.decimal_formatter.format_price(portfolio_data.get('total_cost')),
                'market_value': self.decimal_formatter.format_price(portfolio_data.get('market_value')),
                'profit_loss': self.decimal_formatter.format_price(portfolio_data.get('profit_loss')),
                'profit_loss_rate_original': portfolio_data.get('profit_loss_rate_original'),
                'profit_loss_rate_percent': self.decimal_formatter.format_percentage(
                    portfolio_data.get('profit_loss_rate_percent')
                ),
                'profit_loss_rate_decimal': portfolio_data.get('profit_loss_rate_decimal')
            }
            
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO portfolios 
                    (symbol, data_source, quantity, average_price, total_cost, 
                     market_value, profit_loss, profit_loss_rate_original,
                     profit_loss_rate_percent, profit_loss_rate_decimal, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    data['symbol'], data['data_source'], data['quantity'],
                    data['average_price'], data['total_cost'], data['market_value'],
                    data['profit_loss'], data['profit_loss_rate_original'],
                    data['profit_loss_rate_percent'], data['profit_loss_rate_decimal']
                ))
                
                logger.info(f"ポートフォリオデータ挿入: {symbol} ({data['data_source']})")
                return True
                
        except Exception as e:
            logger.error(f"ポートフォリオデータ挿入エラー: {e}")
            return False
    
    def get_portfolio_data(self, symbol: Optional[str] = None, 
                          data_source: Optional[str] = None) -> List[Dict[str, Any]]:
        """ポートフォリオデータを取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM portfolios"
                params = []
                
                if symbol or data_source:
                    conditions = []
                    if symbol:
                        normalized_symbol = self.symbol_normalizer.normalize(symbol)
                        conditions.append("symbol = ?")
                        params.append(normalized_symbol)
                    if data_source:
                        conditions.append("data_source = ?")
                        params.append(data_source)
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY symbol, data_source"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"ポートフォリオデータ取得エラー: {e}")
            return []
    
    def delete_portfolio_data(self, symbol: str, data_source: str) -> bool:
        """ポートフォリオデータを削除"""
        try:
            normalized_symbol = self.symbol_normalizer.normalize(symbol)
            if not normalized_symbol:
                return False
            
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM portfolios 
                    WHERE symbol = ? AND data_source = ?
                """, (normalized_symbol, data_source))
                
                deleted_count = cursor.rowcount
                logger.info(f"ポートフォリオデータ削除: {normalized_symbol} ({data_source}) - {deleted_count}件")
                return deleted_count > 0
                
        except Exception as e:
            logger.error(f"ポートフォリオデータ削除エラー: {e}")
            return False
    
    # ===== 銘柄マスターデータ管理 =====
    
    def insert_stock_master(self, stock_data: Dict[str, Any]) -> bool:
        """銘柄マスターデータを挿入・更新"""
        try:
            symbol = self.symbol_normalizer.normalize(stock_data.get('symbol', ''))
            if not symbol:
                return False
            
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO stocks 
                    (symbol, name, market, sector, industry, currency, 
                     current_price, previous_close, market_cap, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    symbol,
                    stock_data.get('name', stock_data.get('long_name', '')),
                    stock_data.get('market', stock_data.get('exchange', '')),
                    stock_data.get('sector', ''),
                    stock_data.get('industry', ''),
                    stock_data.get('currency', 'JPY'),
                    self.decimal_formatter.format_price(stock_data.get('current_price')),
                    self.decimal_formatter.format_price(stock_data.get('previous_close')),
                    stock_data.get('market_cap')
                ))
                
                logger.info(f"銘柄マスターデータ挿入: {symbol}")
                return True
                
        except Exception as e:
            logger.error(f"銘柄マスターデータ挿入エラー: {e}")
            return False
    
    def get_stock_master(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """銘柄マスターデータを取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if symbol:
                    normalized_symbol = self.symbol_normalizer.normalize(symbol)
                    cursor.execute("SELECT * FROM stocks WHERE symbol = ?", (normalized_symbol,))
                else:
                    cursor.execute("SELECT * FROM stocks ORDER BY symbol")
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"銘柄マスターデータ取得エラー: {e}")
            return []
    
    # ===== 財務指標データ管理 =====
    
    def insert_financial_metrics(self, symbol: str, metrics_data: Dict[str, Any], 
                                metric_date: Optional[date] = None) -> bool:
        """財務指標データを挿入・更新"""
        try:
            normalized_symbol = self.symbol_normalizer.normalize(symbol)
            if not normalized_symbol:
                return False
            
            if metric_date is None:
                metric_date = date.today()
            
            # Yahoo Finance指標をそのまま保存し、表示用は変換
            data = {
                'yahoo_dividend_yield': metrics_data.get('dividendYield'),
                'yahoo_trailing_pe': self.decimal_formatter.format_price(metrics_data.get('trailingPE')),
                'yahoo_price_to_book': self.decimal_formatter.format_price(metrics_data.get('priceToBook')),
                'yahoo_return_on_equity': metrics_data.get('returnOnEquity'),
                'yahoo_profit_margins': metrics_data.get('profitMargins'),
                'yahoo_operating_margins': metrics_data.get('operatingMargins'),
                'yahoo_dividend_rate': self.decimal_formatter.format_price(metrics_data.get('dividendRate')),
                
                # 表示用変換（%形式）
                'display_dividend_yield': self.decimal_formatter.format_percentage(
                    metrics_data.get('dividendYield', 0) * 100 if metrics_data.get('dividendYield') else None
                ),
                'display_return_on_equity': self.decimal_formatter.format_percentage(
                    metrics_data.get('returnOnEquity', 0) * 100 if metrics_data.get('returnOnEquity') else None
                ),
                'display_profit_margins': self.decimal_formatter.format_percentage(
                    metrics_data.get('profitMargins', 0) * 100 if metrics_data.get('profitMargins') else None
                )
            }
            
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO financial_indicators 
                    (symbol, dividend_yield, pe_ratio, pb_ratio, roe, dividend_rate, 
                     data_date, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    normalized_symbol, 
                    metrics_data.get('dividendYield'),
                    self.decimal_formatter.format_price(metrics_data.get('trailingPE')),
                    self.decimal_formatter.format_price(metrics_data.get('priceToBook')),
                    metrics_data.get('returnOnEquity'),
                    self.decimal_formatter.format_price(metrics_data.get('dividendRate')),
                    metric_date
                ))
                
                logger.info(f"財務指標データ挿入: {normalized_symbol} ({metric_date})")
                return True
                
        except Exception as e:
            logger.error(f"財務指標データ挿入エラー: {e}")
            return False
    
    # ===== API使用量管理 =====
    
    def log_api_usage(self, api_name: str, response_status: int, 
                     symbol: Optional[str] = None, request_type: str = "",
                     processing_time_ms: Optional[int] = None) -> bool:
        """API使用量をログ"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO api_usage_log 
                    (api_name, response_status, symbol, request_type, processing_time_ms)
                    VALUES (?, ?, ?, ?, ?)
                """, (api_name, response_status, symbol, request_type, processing_time_ms))
                
                return True
                
        except Exception as e:
            logger.error(f"API使用量ログエラー: {e}")
            return False
    
    def get_api_usage_stats(self, api_name: str, hours: int = 1) -> Dict[str, Any]:
        """API使用量統計を取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_requests,
                        COUNT(CASE WHEN response_status = 200 THEN 1 END) as successful_requests,
                        AVG(processing_time_ms) as avg_processing_time
                    FROM api_usage_log 
                    WHERE api_name = ? 
                    AND request_timestamp > datetime('now', '-{} hours')
                """.format(hours), (api_name,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return {}
                
        except Exception as e:
            logger.error(f"API使用量統計取得エラー: {e}")
            return {}
    
    # ===== 設定管理 =====
    
    def get_setting(self, setting_name: str) -> Optional[Dict[str, Any]]:
        """設定値を取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT value FROM settings 
                    WHERE key = ?
                """, (setting_name,))
                
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return None
                
        except Exception as e:
            logger.error(f"設定取得エラー: {e}")
            return None
    
    def update_setting(self, setting_name: str, setting_value: Dict[str, Any]) -> bool:
        """設定値を更新"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO settings 
                    (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (setting_name, json.dumps(setting_value)))
                
                logger.info(f"設定更新: {setting_name}")
                return True
                
        except Exception as e:
            logger.error(f"設定更新エラー: {e}")
            return False
    
    # ===== 統合ビュー =====
    
    def get_portfolio_analytics(self) -> List[Dict[str, Any]]:
        """ポートフォリオ分析データを取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM portfolios ORDER BY symbol")
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"ポートフォリオ分析データ取得エラー: {e}")
            return []


# 便利関数
def get_database_manager(db_path: str = "stock_watchdog.db") -> DatabaseManager:
    """データベースマネージャーのインスタンスを取得"""
    return DatabaseManager(db_path)


if __name__ == "__main__":
    # テスト実行
    print("=== データベースマネージャーテスト ===")
    
    db = DatabaseManager("test_db_manager.db")
    
    # テストデータ挿入
    test_portfolio = {
        'symbol': '9432.T',
        'data_source': 'test',
        'quantity': 100,
        'average_price': 150.5,
        'market_value': 15500.0,
        'profit_loss': 500.0,
        'profit_loss_rate_percent': 3.3
    }
    
    if db.insert_portfolio_data(test_portfolio):
        print("✅ ポートフォリオデータ挿入成功")
        
        # データ取得テスト
        data = db.get_portfolio_data('9432')
        if data:
            print(f"✅ データ取得成功: {len(data)}件")
            print(f"   銘柄: {data[0]['symbol']}")
        else:
            print("❌ データ取得失敗")
    else:
        print("❌ ポートフォリオデータ挿入失敗")