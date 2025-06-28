#!/usr/bin/env python3
"""
Streamlitアプリケーション状態監視スクリプト
データベース、API呼び出し、セッション状態を監視
"""

import sqlite3
import time
import logging
from datetime import datetime
import pandas as pd
from pathlib import Path
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AppStateMonitor:
    """アプリケーション状態監視"""
    
    def __init__(self, db_path='j_stock_v2.db'):
        self.db_path = db_path
        self.monitoring_data = {
            'start_time': datetime.now().isoformat(),
            'database': {},
            'api_calls': {},
            'errors': [],
            'performance': {}
        }
    
    def check_database_state(self):
        """データベースの状態確認"""
        logger.info("📊 データベース状態チェック...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 各テーブルのレコード数を確認
            tables = [
                'portfolios',
                'stock_master',
                'financial_metrics',
                'price_history',
                'watchlist',
                'api_cache',
                'app_settings'
            ]
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    self.monitoring_data['database'][table] = {
                        'record_count': count,
                        'status': 'OK'
                    }
                    logger.info(f"  ✅ {table}: {count}レコード")
                except sqlite3.Error as e:
                    self.monitoring_data['database'][table] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    logger.error(f"  ❌ {table}: エラー - {e}")
            
            # ポートフォリオデータの詳細確認
            cursor.execute("""
                SELECT symbol, quantity, average_price, profit_loss_rate_percent
                FROM portfolios
                ORDER BY market_value DESC
                LIMIT 5
            """)
            
            top_holdings = cursor.fetchall()
            if top_holdings:
                logger.info("\n📈 トップ保有銘柄:")
                for symbol, qty, avg_price, pnl in top_holdings:
                    logger.info(f"  - {symbol}: {qty}株 @{avg_price:.1f}円 (損益率: {pnl:.1f}%)")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"データベース接続エラー: {e}")
            self.monitoring_data['errors'].append({
                'type': 'database_connection',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    def check_api_cache(self):
        """APIキャッシュの状態確認"""
        logger.info("\n🔄 APIキャッシュ状態チェック...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # キャッシュの統計情報
            cursor.execute("""
                SELECT 
                    api_name,
                    COUNT(*) as cache_count,
                    MIN(cached_at) as oldest_cache,
                    MAX(cached_at) as newest_cache
                FROM api_cache
                GROUP BY api_name
            """)
            
            cache_stats = cursor.fetchall()
            for api, count, oldest, newest in cache_stats:
                self.monitoring_data['api_calls'][api] = {
                    'cache_count': count,
                    'oldest_entry': oldest,
                    'newest_entry': newest
                }
                logger.info(f"  📦 {api}: {count}件のキャッシュ")
                logger.info(f"     最古: {oldest}")
                logger.info(f"     最新: {newest}")
            
            # 期限切れキャッシュの確認
            cursor.execute("""
                SELECT api_name, COUNT(*) as expired_count
                FROM api_cache
                WHERE datetime(expires_at) < datetime('now')
                GROUP BY api_name
            """)
            
            expired = cursor.fetchall()
            if expired:
                logger.warning("\n⚠️ 期限切れキャッシュ:")
                for api, count in expired:
                    logger.warning(f"  - {api}: {count}件")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"APIキャッシュ確認エラー: {e}")
    
    def check_recent_errors(self):
        """最近のエラーログ確認"""
        logger.info("\n🚨 最近のエラー確認...")
        
        log_files = ['app.log', 'automated_test.log']
        
        for log_file in log_files:
            if Path(log_file).exists():
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[-50:]  # 最後の50行
                    
                    errors = []
                    for line in lines:
                        if 'ERROR' in line or 'CRITICAL' in line:
                            errors.append(line.strip())
                    
                    if errors:
                        logger.warning(f"\n{log_file}の最新エラー:")
                        for error in errors[-3:]:  # 最新3件
                            logger.warning(f"  - {error[:100]}...")
                            self.monitoring_data['errors'].append({
                                'file': log_file,
                                'message': error,
                                'timestamp': datetime.now().isoformat()
                            })
    
    def check_performance_metrics(self):
        """パフォーマンスメトリクスの確認"""
        logger.info("\n⚡ パフォーマンスメトリクス...")
        
        # データベースサイズ確認
        if Path(self.db_path).exists():
            db_size = Path(self.db_path).stat().st_size / (1024 * 1024)  # MB
            self.monitoring_data['performance']['database_size_mb'] = round(db_size, 2)
            logger.info(f"  💾 データベースサイズ: {db_size:.2f} MB")
        
        # API呼び出し頻度の計算
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 過去1時間のAPI呼び出し数
            cursor.execute("""
                SELECT COUNT(*) 
                FROM api_cache 
                WHERE datetime(cached_at) > datetime('now', '-1 hour')
            """)
            
            recent_calls = cursor.fetchone()[0]
            self.monitoring_data['performance']['api_calls_last_hour'] = recent_calls
            logger.info(f"  📡 過去1時間のAPI呼び出し: {recent_calls}回")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"パフォーマンスメトリクス取得エラー: {e}")
    
    def generate_status_report(self):
        """状態レポートの生成"""
        logger.info("\n" + "="*60)
        logger.info("📊 アプリケーション状態レポート")
        logger.info("="*60)
        
        # データベース状態サマリー
        logger.info("\n🗄️ データベース状態:")
        total_records = sum(
            table.get('record_count', 0) 
            for table in self.monitoring_data['database'].values() 
            if isinstance(table, dict) and 'record_count' in table
        )
        logger.info(f"  総レコード数: {total_records}")
        
        # エラーサマリー
        error_count = len(self.monitoring_data['errors'])
        if error_count > 0:
            logger.warning(f"\n⚠️ 検出されたエラー: {error_count}件")
        else:
            logger.info("\n✅ エラーなし")
        
        # 推奨事項
        logger.info("\n💡 推奨事項:")
        
        if error_count > 5:
            logger.info("  1. エラーが多発しています。ログを詳細に確認してください。")
        
        if self.monitoring_data['performance'].get('api_calls_last_hour', 0) > 80:
            logger.info("  2. API呼び出しが多いです。レート制限に注意してください。")
        
        if self.monitoring_data['performance'].get('database_size_mb', 0) > 100:
            logger.info("  3. データベースが大きくなっています。古いデータの整理を検討してください。")
        
        # レポート保存
        report_file = f"app_state_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.monitoring_data, f, indent=2, ensure_ascii=False)
        logger.info(f"\n📄 レポート保存: {report_file}")
        
        return self.monitoring_data


def continuous_monitoring(interval=30):
    """継続的な監視モード"""
    logger.info(f"継続監視モード開始（{interval}秒間隔）")
    logger.info("Ctrl+Cで終了")
    
    monitor = AppStateMonitor()
    
    try:
        while True:
            logger.info(f"\n{'='*60}")
            logger.info(f"監視実行: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info('='*60)
            
            monitor.check_database_state()
            monitor.check_api_cache()
            monitor.check_recent_errors()
            monitor.check_performance_metrics()
            
            # 簡易サマリー
            logger.info("\n📊 クイックサマリー:")
            
            # ポートフォリオ件数
            portfolio_count = monitor.monitoring_data['database'].get('portfolios', {}).get('record_count', 0)
            logger.info(f"  - ポートフォリオ: {portfolio_count}件")
            
            # エラー数
            error_count = len(monitor.monitoring_data['errors'])
            if error_count > 0:
                logger.warning(f"  - エラー: {error_count}件 ⚠️")
            else:
                logger.info("  - エラー: なし ✅")
            
            # API呼び出し
            api_calls = monitor.monitoring_data['performance'].get('api_calls_last_hour', 0)
            logger.info(f"  - API呼び出し（1時間）: {api_calls}回")
            
            logger.info(f"\n次回チェック: {interval}秒後...")
            time.sleep(interval)
            
            # データをリセット（メモリリーク防止）
            monitor.monitoring_data['errors'] = []
            
    except KeyboardInterrupt:
        logger.info("\n監視を終了します...")
        monitor.generate_status_report()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="アプリケーション状態監視")
    parser.add_argument('--continuous', action='store_true', help="継続監視モード")
    parser.add_argument('--interval', type=int, default=30, help="監視間隔（秒）")
    
    args = parser.parse_args()
    
    if args.continuous:
        continuous_monitoring(args.interval)
    else:
        monitor = AppStateMonitor()
        monitor.check_database_state()
        monitor.check_api_cache()
        monitor.check_recent_errors()
        monitor.check_performance_metrics()
        monitor.generate_status_report()