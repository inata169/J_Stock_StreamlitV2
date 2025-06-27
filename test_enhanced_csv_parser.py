#!/usr/bin/env python3
"""
EnhancedCSVParser単体テスト v2.0.0
両方の真実を保持するCSVパーサーの包括的テスト
"""

import os
import io
import sys
import sqlite3
import tempfile
import logging
from datetime import datetime
from typing import Dict, List, Any

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# パス設定
sys.path.append(os.path.dirname(__file__))
sys.path.append('core')

# pandas問題対応：環境変数設定
os.environ['PYTHONPATH'] = os.path.dirname(__file__)

# モジュールインポート
try:
    # pandasエラーを回避するため、先にテスト
    try:
        import pandas as pd
        print("📦 pandas利用可能")
    except ImportError:
        print("⚠️ pandas利用不可 - 単純なCSV処理モードで実行")
    
    from core.enhanced_csv_parser import EnhancedCSVParser
    from core.database_manager import DatabaseManager
    from core.database_init import initialize_database
    print("✅ 必要なモジュールのインポート成功")
    
except ImportError as e:
    print(f"❌ モジュールインポートエラー: {e}")
    sys.exit(1)


class TestEnhancedCSVParser:
    """EnhancedCSVParserのテストクラス"""
    
    def __init__(self):
        self.test_db_path = "test_enhanced_csv_parser.db"
        self.db_manager = None
        self.csv_parser = None
        
    def setUp(self):
        """テスト環境のセットアップ"""
        # 既存テストDBを削除
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        
        # データベース初期化
        try:
            success = initialize_database(self.test_db_path)
            if not success:
                raise Exception("データベース初期化失敗")
            
            self.db_manager = DatabaseManager(self.test_db_path)
            self.csv_parser = EnhancedCSVParser(self.db_manager)
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
    
    def test_csv_encoding_detection(self):
        """CSV エンコーディング検出テスト"""
        print("\n=== CSV エンコーディング検出テスト ===")
        
        # UTF-8テストデータ
        utf8_data = "銘柄コード,銘柄名,保有数量\n1928,積水ハウス,100\n"
        utf8_bytes = utf8_data.encode('utf-8')
        
        try:
            lines, encoding = self.csv_parser._read_csv_with_encoding(utf8_bytes)
            
            if encoding == 'utf-8' and len(lines) == 2:
                print("✅ UTF-8エンコーディング検出成功")
                print(f"   検出エンコーディング: {encoding}")
                print(f"   読み込み行数: {len(lines)}")
                print(f"   ヘッダー: {lines[0]}")
                return True
            else:
                print(f"❌ UTF-8エンコーディング検出失敗: {encoding}, 行数: {len(lines)}")
                return False
                
        except Exception as e:
            print(f"❌ エンコーディング検出エラー: {e}")
            return False
    
    def test_data_source_detection(self):
        """データソース検出テスト"""
        print("\n=== データソース検出テスト ===")
        
        # SBI証券テストデータ
        sbi_data = [
            ["ポートフォリオ一覧"],
            ["銘柄（コード）", "銘柄名称", "数量", "取得単価", "現在値", "評価額", "損益", "損益（％）"],
            ["1928", "積水ハウス", "100", "2100", "2200", "220000", "10000", "4.76"]
        ]
        
        # 楽天証券テストデータ
        rakuten_data = [
            ["保有商品詳細"],
            ["■特定口座"],
            ["銘柄コード", "銘柄名", "保有数量［株］", "平均取得価額［円］", "現在値［円］", "時価評価額［円］", "評価損益［円］"],
            ["1928", "積水ハウス", "100", "2100", "2200", "220000", "10000"]
        ]
        
        # テスト実行
        results = []
        
        # SBI証券検出テスト
        sbi_source = self.csv_parser._detect_data_source(sbi_data, "portfolio_sbi.csv")
        if sbi_source == 'sbi':
            print("✅ SBI証券データソース検出成功")
            results.append(True)
        else:
            print(f"❌ SBI証券データソース検出失敗: {sbi_source}")
            results.append(False)
        
        # 楽天証券検出テスト
        rakuten_source = self.csv_parser._detect_data_source(rakuten_data, "assetbalance.csv")
        if rakuten_source == 'rakuten':
            print("✅ 楽天証券データソース検出成功")
            results.append(True)
        else:
            print(f"❌ 楽天証券データソース検出失敗: {rakuten_source}")
            results.append(False)
        
        return all(results)
    
    def test_sbi_data_extraction(self):
        """SBI証券データ抽出テスト"""
        print("\n=== SBI証券データ抽出テスト ===")
        
        # SBI証券テストデータ（実際のSBI証券フォーマット）
        sbi_csv_lines = [
            ["ポートフォリオ一覧", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["銘柄（コード）", "銘柄名称", "数量", "取得単価", "現在値", "評価額", "損益", "損益（％）"],
            ["1928", "積水ハウス", "100", "2100.0", "2200.0", "220000", "10000", "4.76"],
            ["7203", "トヨタ自動車", "200", "1800.0", "1850.0", "370000", "10000", "2.78"],
            ["", "", "", "", "", "", "", ""]  # 空行
        ]
        
        try:
            portfolio_data = self.csv_parser._extract_sbi_data(sbi_csv_lines)
            
            if len(portfolio_data) == 2:
                print(f"✅ SBI証券データ抽出成功: {len(portfolio_data)}件")
                
                # 1件目の検証
                first_item = portfolio_data[0]
                expected_checks = [
                    (first_item['symbol'] == '1928', f"銘柄コード: {first_item['symbol']}"),
                    (first_item['name'] == '積水ハウス', f"銘柄名: {first_item['name']}"),
                    (first_item['quantity'] == 100, f"数量: {first_item['quantity']}"),
                    (first_item['data_source'] == 'sbi', f"データソース: {first_item['data_source']}"),
                    (first_item['profit_loss_rate_original'] == 4.76, f"元損益率: {first_item['profit_loss_rate_original']}"),
                ]
                
                all_passed = True
                for check, msg in expected_checks:
                    if check:
                        print(f"   ✅ {msg}")
                    else:
                        print(f"   ❌ {msg}")
                        all_passed = False
                
                return all_passed
            else:
                print(f"❌ SBI証券データ抽出失敗: 期待2件、実際{len(portfolio_data)}件")
                return False
                
        except Exception as e:
            print(f"❌ SBI証券データ抽出エラー: {e}")
            return False
    
    def test_rakuten_data_extraction(self):
        """楽天証券データ抽出テスト"""
        print("\n=== 楽天証券データ抽出テスト ===")
        
        # 楽天証券テストデータ（実際の楽天証券フォーマット）
        rakuten_csv_lines = [
            ["保有商品詳細"],
            ["■特定口座"],
            ["銘柄コード", "銘柄名", "保有数量［株］", "平均取得価額［円］", "現在値［円］", "時価評価額［円］", "評価損益［円］", "取得総額［円］"],
            ["1928", "積水ハウス", "100", "2100.0", "2200.0", "220000", "10000", "210000"],
            ["7203", "トヨタ自動車", "200", "1800.0", "1850.0", "370000", "10000", "360000"],
            ["合計", "", "", "", "", "590000", "20000", "570000"],
            ["■NISA成長投資枠"],
            ["銘柄コード", "銘柄名", "保有数量［株］", "平均取得価額［円］", "現在値［円］", "時価評価額［円］", "評価損益［円］"],
            ["6758", "ソニーグループ", "50", "12000.0", "13000.0", "650000", "50000"]
        ]
        
        try:
            portfolio_data = self.csv_parser._extract_rakuten_data(rakuten_csv_lines)
            
            if len(portfolio_data) >= 2:
                print(f"✅ 楽天証券データ抽出成功: {len(portfolio_data)}件")
                
                # 1件目の検証（特定口座）
                first_item = portfolio_data[0]
                expected_checks = [
                    (first_item['symbol'] == '1928', f"銘柄コード: {first_item['symbol']}"),
                    (first_item['name'] == '積水ハウス', f"銘柄名: {first_item['name']}"),
                    (first_item['quantity'] == 100, f"数量: {first_item['quantity']}"),
                    (first_item['data_source'] == 'rakuten', f"データソース: {first_item['data_source']}"),
                    (first_item['profit_loss_rate_original'] is None, f"元損益率: {first_item['profit_loss_rate_original']}"),
                ]
                
                all_passed = True
                for check, msg in expected_checks:
                    if check:
                        print(f"   ✅ {msg}")
                    else:
                        print(f"   ❌ {msg}")
                        all_passed = False
                
                return all_passed
            else:
                print(f"❌ 楽天証券データ抽出失敗: 期待2件以上、実際{len(portfolio_data)}件")
                return False
                
        except Exception as e:
            print(f"❌ 楽天証券データ抽出エラー: {e}")
            return False
    
    def test_both_truths_preservation(self):
        """両方の真実保持テスト"""
        print("\n=== 両方の真実保持テスト ===")
        
        # SBI証券の損益率（167.98%の場合）
        sbi_row_dict = {
            '銘柄（コード）': '1928',
            '銘柄名称': '積水ハウス',
            '数量': '100',
            '取得単価': '1500.0',
            '現在値': '4020.0',
            '評価額': '402000',
            '損益': '252000',
            '損益（％）': '167.98'
        }
        
        sbi_item = self.csv_parser._extract_stock_item(sbi_row_dict, 'sbi')
        
        if sbi_item:
            # SBI: 167.98% → percent=167.9, decimal=1.6798
            expected_original = 167.98
            expected_percent = 167.9  # 小数点1桁
            expected_decimal = 1.6798  # 小数形式
            
            checks = [
                (sbi_item['profit_loss_rate_original'] == expected_original, 
                 f"SBI元の値: {sbi_item['profit_loss_rate_original']} (期待: {expected_original})"),
                (sbi_item['profit_loss_rate_percent'] == expected_percent,
                 f"SBI%表示: {sbi_item['profit_loss_rate_percent']} (期待: {expected_percent})"),
                (sbi_item['profit_loss_rate_decimal'] == expected_decimal,
                 f"SBI小数: {sbi_item['profit_loss_rate_decimal']} (期待: {expected_decimal})")
            ]
            
            all_passed = True
            for check, msg in checks:
                if check:
                    print(f"   ✅ {msg}")
                else:
                    print(f"   ❌ {msg}")
                    all_passed = False
            
            return all_passed
        else:
            print("❌ SBI証券の両方の真実保持テスト失敗: データ抽出不可")
            return False
    
    def test_database_integration(self):
        """データベース統合テスト"""
        print("\n=== データベース統合テスト ===")
        
        # テストCSVデータを作成
        test_csv_content = """銘柄（コード）,銘柄名称,数量,取得単価,現在値,評価額,損益,損益（％）
1928,積水ハウス,100,2100.0,2200.0,220000,10000,4.76
7203,トヨタ自動車,200,1800.0,1850.0,370000,10000,2.78"""
        
        test_csv_bytes = test_csv_content.encode('utf-8')
        
        try:
            # CSV解析・データベース保存
            success, result = self.csv_parser.parse_csv_to_database(
                test_csv_bytes, 
                "test_sbi.csv", 
                data_source="sbi"
            )
            
            if success:
                print(f"✅ CSV解析・DB保存成功: {result['success_count']}件")
                print(f"   データソース: {result['data_source']}")
                print(f"   エンコーディング: {result['encoding']}")
                
                # データベースから確認
                portfolio_summary = self.csv_parser.get_portfolio_summary()
                
                if "error" not in portfolio_summary:
                    print(f"✅ ポートフォリオサマリー取得成功")
                    print(f"   総銘柄数: {portfolio_summary['total_holdings']}")
                    print(f"   総評価額: ¥{portfolio_summary['total_market_value']:,.0f}")
                    print(f"   データソース: {portfolio_summary['data_sources']}")
                    return True
                else:
                    print(f"❌ ポートフォリオサマリー取得失敗: {portfolio_summary['error']}")
                    return False
            else:
                print(f"❌ CSV解析・DB保存失敗: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ データベース統合テストエラー: {e}")
            return False
    
    def test_error_handling(self):
        """エラーハンドリングテスト"""
        print("\n=== エラーハンドリングテスト ===")
        
        test_results = []
        
        # 不正なエンコーディングテスト
        try:
            invalid_bytes = b'\xff\xfe\x00\x00invalid'  # 不正なバイト列
            lines, encoding = self.csv_parser._read_csv_with_encoding(invalid_bytes)
            print("❌ 不正エンコーディングテスト失敗: エラーが発生しなかった")
            test_results.append(False)
        except ValueError as e:
            print(f"✅ 不正エンコーディングテスト成功: {e}")
            test_results.append(True)
        except Exception as e:
            print(f"❌ 不正エンコーディングテスト失敗: 予期しないエラー {e}")
            test_results.append(False)
        
        # 空のCSVテスト
        try:
            empty_csv = b""
            success, result = self.csv_parser.parse_csv_to_database(empty_csv, "empty.csv")
            if not success and "error" in result:
                print("✅ 空CSVエラーハンドリング成功")
                test_results.append(True)
            else:
                print("❌ 空CSVエラーハンドリング失敗")
                test_results.append(False)
        except Exception as e:
            print(f"✅ 空CSVエラーハンドリング成功（例外処理）: {e}")
            test_results.append(True)
        
        # 無効なデータテスト
        try:
            invalid_csv = "無効な列1,無効な列2\nデータ1,データ2\n".encode('utf-8')
            success, result = self.csv_parser.parse_csv_to_database(invalid_csv, "invalid.csv")
            if not success or result.get('success_count', 0) == 0:
                print("✅ 無効データエラーハンドリング成功")
                test_results.append(True)
            else:
                print("❌ 無効データエラーハンドリング失敗")
                test_results.append(False)
        except Exception as e:
            print(f"✅ 無効データエラーハンドリング成功（例外処理）: {e}")
            test_results.append(True)
        
        return all(test_results)
    
    def run_all_tests(self):
        """全テスト実行"""
        print("🧪 EnhancedCSVParser 単体テスト開始")
        print("=" * 50)
        
        # セットアップ
        if not self.setUp():
            print("❌ テスト環境セットアップ失敗")
            return False
        
        # テスト実行
        test_methods = [
            ("CSVエンコーディング検出", self.test_csv_encoding_detection),
            ("データソース検出", self.test_data_source_detection),
            ("SBI証券データ抽出", self.test_sbi_data_extraction),
            ("楽天証券データ抽出", self.test_rakuten_data_extraction),
            ("両方の真実保持", self.test_both_truths_preservation),
            ("データベース統合", self.test_database_integration),
            ("エラーハンドリング", self.test_error_handling),
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
        print("📊 EnhancedCSVParser テスト結果サマリー")
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
    tester = TestEnhancedCSVParser()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()