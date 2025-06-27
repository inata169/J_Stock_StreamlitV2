#!/usr/bin/env python3
"""
DatabaseManager CRUD操作テスト v2.0.0
データベース管理機能の包括的テスト
"""

import os
import sys
import sqlite3
import tempfile
import logging
from datetime import datetime, date
from typing import Dict, List, Any

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# パス設定
sys.path.append(os.path.dirname(__file__))
sys.path.append('core')


class TestDatabaseManagerCRUD:
    """DatabaseManager CRUD操作のテストクラス"""
    
    def __init__(self):
        self.test_db_path = "test_database_manager_crud.db"
        self.db_manager = None
        
    def setUp(self):
        """テスト環境のセットアップ"""
        # 既存テストDBを削除
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        
        try:
            from core.database_init import initialize_database
            from core.database_manager import DatabaseManager
            
            # データベース初期化
            success = initialize_database(self.test_db_path)
            if not success:
                raise Exception("データベース初期化失敗")
            
            self.db_manager = DatabaseManager(self.test_db_path)
            print(f"✅ テスト環境セットアップ完了: {self.test_db_path}")
            return True
            
        except Exception as e:
            print(f"❌ テスト環境セットアップ失敗: {e}")
            return False
    
    def tearDown(self):
        """テスト環境のクリーンアップ"""
        try:
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
            print("🧹 テスト環境クリーンアップ完了")
        except Exception as e:
            print(f"⚠️ クリーンアップエラー: {e}")
    
    def test_portfolio_crud_operations(self):
        """ポートフォリオデータ CRUD操作テスト"""
        print("\n=== ポートフォリオデータ CRUD操作テスト ===")
        
        # テストデータ準備
        test_portfolio_1 = {
            'symbol': '1928',
            'name': '積水ハウス',
            'data_source': 'sbi',
            'quantity': 100,
            'average_price': 2100.0,
            'current_price': 2200.0,
            'market_value': 220000.0,
            'profit_loss': 10000.0,
            'total_cost': 210000.0,
            'profit_loss_rate_original': 4.76,
            'profit_loss_rate_percent': 4.8,
            'profit_loss_rate_decimal': 0.048
        }
        
        test_portfolio_2 = {
            'symbol': '7203',
            'name': 'トヨタ自動車',
            'data_source': 'rakuten',
            'quantity': 200,
            'average_price': 1800.0,
            'current_price': 1850.0,
            'market_value': 370000.0,
            'profit_loss': 10000.0,
            'total_cost': 360000.0,
            'profit_loss_rate_original': None,  # 楽天証券にはない
            'profit_loss_rate_percent': 2.8,
            'profit_loss_rate_decimal': 0.028
        }
        
        try:
            # CREATE: ポートフォリオデータ挿入テスト
            print("📝 CREATE: ポートフォリオデータ挿入テスト")
            
            success1 = self.db_manager.insert_portfolio_data(test_portfolio_1)
            success2 = self.db_manager.insert_portfolio_data(test_portfolio_2)
            
            if success1 and success2:
                print("✅ ポートフォリオデータ挿入成功（2件）")
            else:
                print(f"❌ ポートフォリオデータ挿入失敗: success1={success1}, success2={success2}")
                return False
            
            # READ: 全データ取得テスト
            print("\n📖 READ: 全データ取得テスト")
            all_portfolio_data = self.db_manager.get_portfolio_data()
            
            if len(all_portfolio_data) == 2:
                print(f"✅ 全データ取得成功: {len(all_portfolio_data)}件")
                for item in all_portfolio_data:
                    print(f"   - {item['symbol']}: {item['name']} ({item['data_source']})")
            else:
                print(f"❌ 全データ取得失敗: 期待2件、実際{len(all_portfolio_data)}件")
                return False
            
            # READ: 条件指定取得テスト
            print("\n🔍 READ: 条件指定取得テスト")
            
            # 銘柄指定
            sbi_data = self.db_manager.get_portfolio_data(symbol='1928')
            if len(sbi_data) == 1 and sbi_data[0]['symbol'] == '1928':
                print("✅ 銘柄指定取得成功")
            else:
                print(f"❌ 銘柄指定取得失敗: {sbi_data}")
                return False
            
            # データソース指定
            rakuten_data = self.db_manager.get_portfolio_data(data_source='rakuten')
            if len(rakuten_data) == 1 and rakuten_data[0]['data_source'] == 'rakuten':
                print("✅ データソース指定取得成功")
            else:
                print(f"❌ データソース指定取得失敗: {rakuten_data}")
                return False
            
            # UPDATE: データ更新テスト（INSERT OR REPLACEによる）
            print("\n🔄 UPDATE: データ更新テスト")
            updated_portfolio = test_portfolio_1.copy()
            updated_portfolio['current_price'] = 2300.0
            updated_portfolio['market_value'] = 230000.0
            updated_portfolio['profit_loss'] = 20000.0
            
            success_update = self.db_manager.insert_portfolio_data(updated_portfolio)
            if success_update:
                print("✅ データ更新成功")
                
                # 更新確認
                updated_data = self.db_manager.get_portfolio_data(symbol='1928')
                if (len(updated_data) == 1 and 
                    updated_data[0]['current_price'] == 2300.0 and
                    updated_data[0]['market_value'] == 230000.0):
                    print("✅ 更新内容確認成功")
                else:
                    print(f"❌ 更新内容確認失敗: {updated_data[0]}")
                    return False
            else:
                print("❌ データ更新失敗")
                return False
            
            # DELETE: データ削除テスト
            print("\n🗑️ DELETE: データ削除テスト")
            
            success_delete = self.db_manager.delete_portfolio_data('7203', 'rakuten')
            if success_delete:
                print("✅ データ削除成功")
                
                # 削除確認
                remaining_data = self.db_manager.get_portfolio_data()
                if len(remaining_data) == 1 and remaining_data[0]['symbol'] == '1928':
                    print("✅ 削除確認成功")
                else:
                    print(f"❌ 削除確認失敗: 残存{len(remaining_data)}件")
                    return False
            else:
                print("❌ データ削除失敗")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ ポートフォリオCRUDテストエラー: {e}")
            return False
    
    def test_stocks_crud_operations(self):
        """株式マスターデータ CRUD操作テスト"""
        print("\n=== 株式マスターデータ CRUD操作テスト ===")
        
        # テストデータ準備
        test_stock = {
            'symbol': '1928',
            'name': '積水ハウス',
            'market': 'TSE',
            'sector': 'Real Estate',
            'industry': 'Construction',
            'currency': 'JPY',
            'current_price': 2200.0,
            'previous_close': 2180.0,
            'market_cap': 1500000000000
        }
        
        try:
            # CREATE: 株式マスターデータ挿入
            print("📝 CREATE: 株式マスターデータ挿入")
            success = self.db_manager.insert_stock_master(test_stock)
            
            if success:
                print("✅ 株式マスターデータ挿入成功")
            else:
                print("❌ 株式マスターデータ挿入失敗")
                return False
            
            # READ: 株式マスターデータ取得
            print("\n📖 READ: 株式マスターデータ取得")
            
            # 全データ取得
            all_stocks = self.db_manager.get_stock_master()
            if len(all_stocks) == 1:
                print(f"✅ 全株式マスターデータ取得成功: {len(all_stocks)}件")
            else:
                print(f"❌ 全株式マスターデータ取得失敗: {len(all_stocks)}件")
                return False
            
            # 特定銘柄取得
            specific_stock = self.db_manager.get_stock_master('1928')
            if (len(specific_stock) == 1 and 
                specific_stock[0]['symbol'] == '1928' and
                specific_stock[0]['name'] == '積水ハウス'):
                print("✅ 特定銘柄データ取得成功")
            else:
                print(f"❌ 特定銘柄データ取得失敗: {specific_stock}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 株式マスターCRUDテストエラー: {e}")
            return False
    
    def test_financial_indicators_operations(self):
        """財務指標データ操作テスト"""
        print("\n=== 財務指標データ操作テスト ===")
        
        # テストデータ準備
        test_metrics = {
            'dividendYield': 0.035,  # 3.5%
            'trailingPE': 15.2,
            'priceToBook': 1.1,
            'returnOnEquity': 0.12,  # 12%
            'dividendRate': 77.0,
        }
        
        try:
            # 財務指標データ挿入
            success = self.db_manager.insert_financial_metrics('1928', test_metrics, date.today())
            
            if success:
                print("✅ 財務指標データ挿入成功")
                return True
            else:
                print("❌ 財務指標データ挿入失敗")
                return False
                
        except Exception as e:
            print(f"❌ 財務指標データテストエラー: {e}")
            return False
    
    def test_api_usage_logging(self):
        """API使用量ログテスト"""
        print("\n=== API使用量ログテスト ===")
        
        try:
            # API使用量ログ記録
            success1 = self.db_manager.log_api_usage('yahoo_finance', 200, '1928', 'stock_info', 150)
            success2 = self.db_manager.log_api_usage('yahoo_finance', 200, '7203', 'stock_info', 200)
            success3 = self.db_manager.log_api_usage('yahoo_finance', 429, '9432', 'stock_info', None)
            
            if success1 and success2 and success3:
                print("✅ API使用量ログ記録成功（3件）")
            else:
                print(f"❌ API使用量ログ記録失敗: {success1}, {success2}, {success3}")
                return False
            
            # API使用量統計取得
            stats = self.db_manager.get_api_usage_stats('yahoo_finance', 1)
            
            if (stats and 
                stats.get('total_requests') == 3 and
                stats.get('successful_requests') == 2):
                print("✅ API使用量統計取得成功")
                print(f"   総リクエスト: {stats['total_requests']}")
                print(f"   成功リクエスト: {stats['successful_requests']}")
                return True
            else:
                print(f"❌ API使用量統計取得失敗: {stats}")
                return False
                
        except Exception as e:
            print(f"❌ API使用量ログテストエラー: {e}")
            return False
    
    def test_settings_management(self):
        """設定管理テスト"""
        print("\n=== 設定管理テスト ===")
        
        try:
            # 設定保存
            test_setting = {
                'update_interval': 3600,
                'api_enabled': True,
                'max_retries': 3
            }
            
            success = self.db_manager.update_setting('test_config', test_setting)
            if success:
                print("✅ 設定保存成功")
            else:
                print("❌ 設定保存失敗")
                return False
            
            # 設定取得
            retrieved_setting = self.db_manager.get_setting('test_config')
            
            if (retrieved_setting and 
                retrieved_setting['update_interval'] == 3600 and
                retrieved_setting['api_enabled'] is True):
                print("✅ 設定取得成功")
                print(f"   取得した設定: {retrieved_setting}")
                return True
            else:
                print(f"❌ 設定取得失敗: {retrieved_setting}")
                return False
                
        except Exception as e:
            print(f"❌ 設定管理テストエラー: {e}")
            return False
    
    def test_transaction_management(self):
        """トランザクション管理テスト"""
        print("\n=== トランザクション管理テスト ===")
        
        try:
            # トランザクション成功パターン
            with self.db_manager.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO portfolios (symbol, data_source, quantity) 
                    VALUES (?, ?, ?)
                """, ('TEST', 'test', 100))
                print("✅ トランザクション成功パターン実行")
            
            # データ確認
            test_data = self.db_manager.get_portfolio_data(symbol='TEST')
            if len(test_data) == 1:
                print("✅ トランザクションコミット確認成功")
            else:
                print("❌ トランザクションコミット確認失敗")
                return False
            
            # トランザクション失敗パターン（ロールバック）
            try:
                with self.db_manager.transaction() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO portfolios (symbol, data_source, quantity) 
                        VALUES (?, ?, ?)
                    """, ('TEST2', 'test', 200))
                    # 意図的にエラーを発生
                    raise Exception("テスト用エラー")
            except Exception as e:
                if "テスト用エラー" in str(e):
                    print("✅ トランザクション失敗パターン実行（意図的）")
                else:
                    raise
            
            # ロールバック確認
            test_data2 = self.db_manager.get_portfolio_data(symbol='TEST2')
            if len(test_data2) == 0:
                print("✅ トランザクションロールバック確認成功")
                return True
            else:
                print("❌ トランザクションロールバック確認失敗")
                return False
                
        except Exception as e:
            print(f"❌ トランザクション管理テストエラー: {e}")
            return False
    
    def test_data_validation_and_normalization(self):
        """データ検証・正規化テスト"""
        print("\n=== データ検証・正規化テスト ===")
        
        try:
            # 銘柄コード正規化テスト
            test_portfolios = [
                {'symbol': '1928.T', 'data_source': 'test', 'quantity': 100},  # .T除去
                {'symbol': '"7203"', 'data_source': 'test', 'quantity': 200},  # 引用符除去
                {'symbol': '  9432  ', 'data_source': 'test', 'quantity': 300},  # 空白除去
            ]
            
            success_count = 0
            for portfolio in test_portfolios:
                if self.db_manager.insert_portfolio_data(portfolio):
                    success_count += 1
            
            if success_count == 3:
                print("✅ 銘柄コード正規化テスト成功")
            else:
                print(f"❌ 銘柄コード正規化テスト失敗: {success_count}/3")
                return False
            
            # 正規化結果確認
            normalized_data = self.db_manager.get_portfolio_data()
            expected_symbols = {'1928', '7203', '9432'}
            actual_symbols = {item['symbol'] for item in normalized_data if item['data_source'] == 'test'}
            
            if expected_symbols.issubset(actual_symbols):
                print("✅ 正規化結果確認成功")
                print(f"   正規化された銘柄: {sorted(actual_symbols & expected_symbols)}")
                return True
            else:
                print(f"❌ 正規化結果確認失敗: 期待{expected_symbols}, 実際{actual_symbols}")
                return False
                
        except Exception as e:
            print(f"❌ データ検証・正規化テストエラー: {e}")
            return False
    
    def run_all_tests(self):
        """全テスト実行"""
        print("🧪 DatabaseManager CRUD操作テスト開始")
        print("=" * 50)
        
        # セットアップ
        if not self.setUp():
            print("❌ テスト環境セットアップ失敗")
            return False
        
        # テスト実行
        test_methods = [
            ("ポートフォリオCRUD操作", self.test_portfolio_crud_operations),
            ("株式マスターCRUD操作", self.test_stocks_crud_operations),
            ("財務指標データ操作", self.test_financial_indicators_operations),
            ("API使用量ログ", self.test_api_usage_logging),
            ("設定管理", self.test_settings_management),
            ("トランザクション管理", self.test_transaction_management),
            ("データ検証・正規化", self.test_data_validation_and_normalization),
        ]
        
        results = []
        for test_name, test_method in test_methods:
            try:
                result = test_method()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} テスト実行エラー: {e}")
                results.append((test_name, False))
        
        # 結果サマリー
        print("\n" + "=" * 50)
        print("📊 DatabaseManager CRUD操作テスト結果サマリー")
        print("=" * 50)
        
        passed = 0
        failed = 0
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print(f"\n合計: {passed + failed}テスト")
        print(f"成功: {passed}")
        print(f"失敗: {failed}")
        
        # クリーンアップ
        self.tearDown()
        
        return failed == 0


def main():
    """メイン関数"""
    tester = TestDatabaseManagerCRUD()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()