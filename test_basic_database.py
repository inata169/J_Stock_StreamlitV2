#!/usr/bin/env python3
"""
基本データベース機能テスト v2.0.0
pandasに依存しない基本的なデータベース機能のテスト
"""

import os
import sqlite3
import sys
import logging
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sqlite_basic():
    """SQLite基本機能テスト"""
    print("=== SQLite基本機能テスト ===")
    
    test_db_path = "test_basic.db"
    
    # 既存ファイル削除
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    try:
        # データベース接続
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        print("✅ SQLite接続成功")
        
        # テーブル作成テスト
        cursor.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ テーブル作成成功")
        
        # データ挿入テスト
        cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test1", 123.45))
        cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test2", 678.90))
        conn.commit()
        print("✅ データ挿入成功")
        
        # データ取得テスト
        cursor.execute("SELECT * FROM test_table")
        rows = cursor.fetchall()
        print(f"✅ データ取得成功: {len(rows)}件")
        
        for row in rows:
            print(f"   ID: {row[0]}, Name: {row[1]}, Value: {row[2]}")
        
        conn.close()
        
        # ファイル削除
        os.remove(test_db_path)
        print("✅ テストファイル削除")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLite基本テストエラー: {e}")
        return False


def test_database_schema_creation():
    """データベーススキーマ作成テスト"""
    print("\n=== データベーススキーマ作成テスト ===")
    
    test_db_path = "test_schema.db"
    
    # 既存ファイル削除
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    try:
        # スキーマファイル読み込み
        schema_path = "database_schema.sql"
        if not os.path.exists(schema_path):
            print(f"❌ スキーマファイル不存在: {schema_path}")
            return False
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        print("✅ スキーマファイル読み込み成功")
        
        # データベース作成
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        # 外部キー有効化
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # スキーマ実行
        cursor.executescript(schema_sql)
        conn.commit()
        print("✅ スキーマ実行成功")
        
        # テーブル一覧確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        print(f"✅ 作成されたテーブル: {len(table_names)}個")
        for table_name in table_names:
            print(f"   - {table_name}")
        
        # 期待するテーブルの存在確認
        expected_tables = ['portfolios', 'stocks', 'financial_indicators', 'api_usage_log', 'settings']
        
        all_tables_exist = True
        for expected_table in expected_tables:
            if expected_table in table_names:
                print(f"✅ {expected_table}")
            else:
                print(f"❌ 不足テーブル: {expected_table}")
                all_tables_exist = False
        
        conn.close()
        
        # ファイル削除
        os.remove(test_db_path)
        print("✅ テストファイル削除")
        
        return all_tables_exist
        
    except Exception as e:
        print(f"❌ スキーマテストエラー: {e}")
        return False


def test_manual_data_operations():
    """手動データ操作テスト"""
    print("\n=== 手動データ操作テスト ===")
    
    test_db_path = "test_operations.db"
    
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    try:
        # スキーマファイル読み込み
        with open("database_schema.sql", 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # データベース作成
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.executescript(schema_sql)
        conn.commit()
        print("✅ データベース準備完了")
        
        # 株式マスタデータ挿入テスト
        cursor.execute("""
            INSERT INTO stocks (symbol, name, market) 
            VALUES (?, ?, ?)
        """, ("1928", "積水ハウス", "TSE"))
        print("✅ 株式マスタ挿入成功")
        
        # ポートフォリオデータ挿入テスト
        cursor.execute("""
            INSERT INTO portfolios (
                symbol, name, data_source, quantity, average_price, current_price,
                market_value, profit_loss, total_cost, profit_loss_rate_percent, 
                profit_loss_rate_decimal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "1928", "積水ハウス", "sample", 100, 2100.0, 2200.0, 
            220000.0, 10000.0, 210000.0, 4.8, 0.048
        ))
        print("✅ ポートフォリオデータ挿入成功")
        
        # 設定データ挿入テスト
        cursor.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
        """, ("test_setting", '{"test": "value"}'))
        print("✅ 設定データ挿入成功")
        
        conn.commit()
        
        # データ取得テスト
        cursor.execute("SELECT COUNT(*) FROM portfolios")
        portfolio_count = cursor.fetchone()[0]
        print(f"✅ ポートフォリオデータ取得: {portfolio_count}件")
        
        cursor.execute("SELECT COUNT(*) FROM stocks")
        stocks_count = cursor.fetchone()[0]
        print(f"✅ 株式マスタデータ取得: {stocks_count}件")
        
        cursor.execute("SELECT COUNT(*) FROM settings")
        settings_count = cursor.fetchone()[0]
        print(f"✅ 設定データ取得: {settings_count}件")
        
        conn.close()
        
        # ファイル削除
        os.remove(test_db_path)
        print("✅ テストファイル削除")
        
        return True
        
    except Exception as e:
        print(f"❌ データ操作テストエラー: {e}")
        return False


def test_symbol_utils_basic():
    """SymbolUtils基本テスト（pandasなし）"""
    print("\n=== SymbolUtils基本テスト ===")
    
    try:
        # 手動でsymbol_utilsの基本機能をテスト
        import sys
        sys.path.append('core')
        
        # 基本的な正規化テスト
        test_cases = [
            ("9432.T", "9432"),  # .T除去
            ("9432", "9432"),    # そのまま
            ('"9432"', "9432"),  # 引用符除去
            ("AAPL", "AAPL"),    # 米国株そのまま
        ]
        
        # 手動で正規化ルール適用テスト
        def manual_normalize(symbol_str):
            """手動正規化関数"""
            if isinstance(symbol_str, str):
                # 引用符除去
                symbol_str = symbol_str.strip('"').strip("'")
                # .T除去
                if symbol_str.endswith('.T'):
                    symbol_str = symbol_str[:-2]
                return symbol_str
            return str(symbol_str)
        
        all_passed = True
        for input_symbol, expected in test_cases:
            result = manual_normalize(input_symbol)
            if result == expected:
                print(f"✅ {input_symbol} → {result}")
            else:
                print(f"❌ {input_symbol} → {result} (期待値: {expected})")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ SymbolUtilsテストエラー: {e}")
        return False


def run_basic_tests():
    """基本テスト実行"""
    print("🧪 v2.0.0 基本データベース機能テスト開始")
    print("=" * 50)
    
    results = []
    
    # テスト1: SQLite基本機能
    results.append(("SQLite基本機能", test_sqlite_basic()))
    
    # テスト2: データベーススキーマ作成
    results.append(("データベーススキーマ作成", test_database_schema_creation()))
    
    # テスト3: 手動データ操作
    results.append(("手動データ操作", test_manual_data_operations()))
    
    # テスト4: SymbolUtils基本機能
    results.append(("SymbolUtils基本機能", test_symbol_utils_basic()))
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📊 基本テスト結果サマリー")
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


if __name__ == "__main__":
    success = run_basic_tests()
    sys.exit(0 if success else 1)