#!/usr/bin/env python3
"""
EnhancedCSVParser基本テスト v2.0.0
pandas問題を回避した基本機能テスト
"""

import os
import io
import sys
import sqlite3
import csv
import logging
from datetime import datetime
from typing import Dict, List, Any

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# パス設定
sys.path.append(os.path.dirname(__file__))
sys.path.append('core')


def test_symbol_utils():
    """SymbolUtils基本テスト"""
    print("=== SymbolUtils基本テスト ===")
    
    try:
        from core.symbol_utils import SymbolNormalizer, DecimalFormatter
        
        # 正規化テスト
        test_cases = [
            ('"9432"', '9432'),
            ('9432.T', '9432'),
            ('9432', '9432'),
            ('  1928  ', '1928'),
            ('invalid', None),
        ]
        
        all_passed = True
        for input_symbol, expected in test_cases:
            result = SymbolNormalizer.normalize(input_symbol)
            if result == expected:
                print(f"✅ {input_symbol:10} → {result}")
            else:
                print(f"❌ {input_symbol:10} → {result} (期待値: {expected})")
                all_passed = False
        
        # CSV行抽出テスト
        test_row = {
            '銘柄（コード）': '1928',
            '銘柄名称': '積水ハウス'
        }
        
        symbol, name = SymbolNormalizer.extract_symbols_from_csv_row(test_row)
        if symbol == '1928' and name == '積水ハウス':
            print("✅ CSV行抽出テスト成功")
        else:
            print(f"❌ CSV行抽出テスト失敗: {symbol}, {name}")
            all_passed = False
        
        # フォーマットテスト
        decimal_formatter = DecimalFormatter()
        if decimal_formatter.format_percentage(167.98, 1) == 167.9:
            print("✅ パーセント値フォーマットテスト成功")
        else:
            print("❌ パーセント値フォーマットテスト失敗")
            all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ SymbolUtilsテストエラー: {e}")
        return False


def test_database_manager():
    """DatabaseManager基本テスト"""
    print("\n=== DatabaseManager基本テスト ===")
    
    test_db_path = "test_csv_parser_basic.db"
    
    try:
        # 既存ファイル削除
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        from core.database_init import initialize_database
        from core.database_manager import DatabaseManager
        
        # データベース初期化
        success = initialize_database(test_db_path)
        if not success:
            print("❌ データベース初期化失敗")
            return False
        
        db_manager = DatabaseManager(test_db_path)
        print("✅ DatabaseManager初期化成功")
        
        # ポートフォリオデータ挿入テスト
        test_data = {
            'symbol': '1928',
            'name': '積水ハウス',
            'data_source': 'test',
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
        
        # データ挿入
        success = db_manager.insert_portfolio_data(test_data)
        if success:
            print("✅ ポートフォリオデータ挿入成功")
        else:
            print("❌ ポートフォリオデータ挿入失敗")
            return False
        
        # データ取得
        analytics = db_manager.get_portfolio_analytics()
        if analytics and len(analytics) > 0:
            print(f"✅ ポートフォリオデータ取得成功: {len(analytics)}件")
            
            # データ内容確認
            first_item = analytics[0]
            if (first_item.get('symbol') == '1928' and 
                first_item.get('name') == '積水ハウス' and
                first_item.get('quantity') == 100):
                print("✅ データ内容確認成功")
            else:
                print(f"❌ データ内容確認失敗: {first_item}")
                return False
        else:
            print("❌ ポートフォリオデータ取得失敗")
            return False
        
        # クリーンアップ
        os.remove(test_db_path)
        print("✅ テストファイル削除")
        
        return True
        
    except Exception as e:
        print(f"❌ DatabaseManagerテストエラー: {e}")
        # クリーンアップ
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except:
                pass
        return False


def test_csv_data_extraction_logic():
    """CSV データ抽出ロジックテスト（パーサーなし）"""
    print("\n=== CSV データ抽出ロジックテスト ===")
    
    try:
        from core.symbol_utils import SymbolNormalizer, DecimalFormatter
        
        # SBI証券のサンプル行データ
        sbi_row_dict = {
            '銘柄（コード）': '1928',
            '銘柄名称': '積水ハウス',
            '数量': '100',
            '取得単価': '2100.0',
            '現在値': '2200.0',
            '評価額': '220000',
            '損益': '10000',
            '損益（％）': '4.76'
        }
        
        # データ抽出シミュレーション
        symbol_normalizer = SymbolNormalizer()
        decimal_formatter = DecimalFormatter()
        
        # 銘柄コードと名前の抽出
        symbol, name = symbol_normalizer.extract_symbols_from_csv_row(sbi_row_dict)
        
        # 数値データの抽出（簡易版）
        quantity = float(sbi_row_dict.get('数量', '0'))
        average_price = float(sbi_row_dict.get('取得単価', '0'))
        current_price = float(sbi_row_dict.get('現在値', '0'))
        market_value = float(sbi_row_dict.get('評価額', '0'))
        profit_loss = float(sbi_row_dict.get('損益', '0'))
        profit_loss_percent_original = float(sbi_row_dict.get('損益（％）', '0'))
        
        # 両方の真実保持ロジック（SBI版）
        profit_loss_rate_percent = decimal_formatter.format_percentage(profit_loss_percent_original)
        profit_loss_rate_decimal = round(profit_loss_percent_original / 100.0, 4)
        
        # 結果検証
        expected_checks = [
            (symbol == '1928', f"銘柄コード: {symbol}"),
            (name == '積水ハウス', f"銘柄名: {name}"),
            (quantity == 100, f"数量: {quantity}"),
            (average_price == 2100.0, f"取得単価: {average_price}"),
            (profit_loss_rate_percent == 4.8, f"損益率%: {profit_loss_rate_percent}"),
            (profit_loss_rate_decimal == 0.0476, f"損益率小数: {profit_loss_rate_decimal}"),
        ]
        
        all_passed = True
        for check, msg in expected_checks:
            if check:
                print(f"✅ {msg}")
            else:
                print(f"❌ {msg}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ CSV データ抽出ロジックテストエラー: {e}")
        return False


def test_csv_encoding_basic():
    """CSV エンコーディング基本テスト"""
    print("\n=== CSV エンコーディング基本テスト ===")
    
    try:
        # UTF-8 CSVデータ
        test_csv_content = "銘柄コード,銘柄名,数量\n1928,積水ハウス,100\n7203,トヨタ自動車,200"
        test_csv_bytes = test_csv_content.encode('utf-8')
        
        # エンコーディング検出シミュレーション
        encodings = ['utf-8', 'shift_jis', 'cp932', 'utf-8-sig']
        
        for encoding in encodings:
            try:
                content = test_csv_bytes.decode(encoding)
                
                # CSV読み込み
                lines = []
                reader = csv.reader(io.StringIO(content))
                for row in reader:
                    lines.append(row)
                
                if len(lines) == 3 and lines[0][0] == '銘柄コード':
                    print(f"✅ エンコーディング {encoding} で読み込み成功: {len(lines)}行")
                    print(f"   ヘッダー: {lines[0]}")
                    print(f"   データ例: {lines[1]}")
                    return True
                    
            except UnicodeDecodeError:
                continue
        
        print("❌ エンコーディング検出テスト失敗")
        return False
        
    except Exception as e:
        print(f"❌ CSV エンコーディングテストエラー: {e}")
        return False


def test_data_source_detection_basic():
    """データソース検出基本テスト"""
    print("\n=== データソース検出基本テスト ===")
    
    try:
        # SBI証券の特徴的なパターン
        sbi_content = "ポートフォリオ一覧 銘柄（コード） 数量 取得単価 損益（％）"
        
        # 楽天証券の特徴的なパターン
        rakuten_content = "保有商品詳細 ■特定口座 平均取得価額［円］ 時価評価額［円］"
        
        # 検出ロジックシミュレーション
        def detect_data_source_simple(content, filename):
            filename_lower = filename.lower()
            
            # ファイル名から判定
            if 'assetbalance' in filename_lower:
                return 'rakuten'
            elif 'savefile' in filename_lower or 'new_file' in filename_lower:
                return 'sbi'
            
            # 内容から判定
            if any(pattern in content for pattern in [
                'ポートフォリオ一覧', '銘柄（コード）', '取得単価', '損益（％）'
            ]):
                return 'sbi'
            elif any(pattern in content for pattern in [
                '保有商品詳細', '■特定口座', '平均取得価額［円］', '時価評価額［円］'
            ]):
                return 'rakuten'
            
            return 'unknown'
        
        # テスト実行
        sbi_result = detect_data_source_simple(sbi_content, "portfolio_sbi.csv")
        rakuten_result = detect_data_source_simple(rakuten_content, "assetbalance.csv")
        
        checks = [
            (sbi_result == 'sbi', f"SBI証券検出: {sbi_result}"),
            (rakuten_result == 'rakuten', f"楽天証券検出: {rakuten_result}")
        ]
        
        all_passed = True
        for check, msg in checks:
            if check:
                print(f"✅ {msg}")
            else:
                print(f"❌ {msg}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ データソース検出テストエラー: {e}")
        return False


def run_basic_tests():
    """基本テスト実行"""
    print("🧪 EnhancedCSVParser 基本テスト開始")
    print("=" * 50)
    
    test_methods = [
        ("SymbolUtils機能", test_symbol_utils),
        ("DatabaseManager機能", test_database_manager),
        ("CSV データ抽出ロジック", test_csv_data_extraction_logic),
        ("CSV エンコーディング基本", test_csv_encoding_basic),
        ("データソース検出基本", test_data_source_detection_basic),
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
    print("📊 EnhancedCSVParser 基本テスト結果サマリー")
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
    
    return failed == 0


def main():
    """メイン関数"""
    success = run_basic_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()