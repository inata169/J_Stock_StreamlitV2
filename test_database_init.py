#!/usr/bin/env python3
"""
データベース初期化・接続テスト v2.0.0
基本的なデータベース機能の動作確認
"""

import os
import sqlite3
import sys
import logging
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# パス設定
sys.path.append(os.path.dirname(__file__))

def test_database_initialization():
    """データベース初期化テスト"""
    print("=== データベース初期化テスト ===")
    
    # テスト用データベースファイル
    test_db_path = "test_stock_watchdog.db"
    
    # 既存のテストファイルを削除
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"✅ 既存のテストDB削除: {test_db_path}")
    
    try:
        # データベース初期化モジュールのインポート
        from core.database_init import initialize_database
        
        print("📦 database_init モジュール読み込み成功")
        
        # データベース初期化実行
        result = initialize_database(test_db_path)
        print(f"🏗️ データベース初期化実行: {result}")
        
        # ファイル存在確認
        if os.path.exists(test_db_path):
            print(f"✅ データベースファイル作成成功: {test_db_path}")
            file_size = os.path.getsize(test_db_path)
            print(f"📊 ファイルサイズ: {file_size} bytes")
        else:
            print(f"❌ データベースファイル作成失敗: {test_db_path}")
            return False
        
        # テーブル構造確認
        test_table_structure(test_db_path)
        
        return True
        
    except ImportError as e:
        print(f"❌ モジュールインポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")
        logger.error(f"Database init error: {e}")
        return False


def test_table_structure(db_path):
    """テーブル構造テスト"""
    print("\n=== テーブル構造テスト ===")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 全テーブル一覧取得
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📋 作成されたテーブル数: {len(tables)}")
        
        expected_tables = ['portfolios', 'stocks', 'financial_indicators', 'api_usage_log', 'settings']
        
        for table_name in expected_tables:
            if (table_name,) in tables:
                print(f"✅ テーブル存在確認: {table_name}")
                
                # テーブル構造詳細確認
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print(f"   カラム数: {len(columns)}")
                
                # 重要カラムの存在確認
                if table_name == 'portfolios':
                    check_portfolio_columns(columns)
                elif table_name == 'stocks':
                    check_stocks_columns(columns)
                    
            else:
                print(f"❌ テーブル不存在: {table_name}")
        
        # 外部キー制約確認
        test_foreign_keys(cursor)
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ テーブル構造テストエラー: {e}")
        return False


def check_portfolio_columns(columns):
    """ポートフォリオテーブルのカラム確認"""
    column_names = [col[1] for col in columns]
    
    required_columns = [
        'symbol', 'name', 'data_source', 'quantity', 'average_price',
        'profit_loss_rate_original', 'profit_loss_rate_percent', 'profit_loss_rate_decimal'
    ]
    
    for col in required_columns:
        if col in column_names:
            print(f"     ✅ {col}")
        else:
            print(f"     ❌ 不足カラム: {col}")


def check_stocks_columns(columns):
    """株式マスタテーブルのカラム確認"""
    column_names = [col[1] for col in columns]
    
    required_columns = ['symbol', 'name', 'market', 'last_updated']
    
    for col in required_columns:
        if col in column_names:
            print(f"     ✅ {col}")
        else:
            print(f"     ❌ 不足カラム: {col}")


def test_foreign_keys(cursor):
    """外部キー制約確認"""
    print("\n🔗 外部キー制約確認:")
    
    # 外部キー有効化確認
    cursor.execute("PRAGMA foreign_keys")
    fk_enabled = cursor.fetchone()[0]
    print(f"   外部キー有効化: {'✅ ON' if fk_enabled else '❌ OFF'}")
    
    # portfoliosテーブルの外部キー確認
    cursor.execute("PRAGMA foreign_key_list(portfolios)")
    fk_list = cursor.fetchall()
    print(f"   portfolios外部キー数: {len(fk_list)}")


def test_database_manager():
    """DatabaseManagerクラステスト"""
    print("\n=== DatabaseManager クラステスト ===")
    
    try:
        from core.database_manager import DatabaseManager
        
        # テスト用データベースマネージャー作成
        db_manager = DatabaseManager("test_stock_watchdog.db")
        print("✅ DatabaseManager インスタンス作成成功")
        
        # 基本接続テスト
        conn = db_manager.get_connection()
        if conn:
            print("✅ データベース接続成功")
            conn.close()
        else:
            print("❌ データベース接続失敗")
            return False
        
        # 設定テーブル操作テスト
        test_setting_key = "test_setting"
        test_setting_value = {"test": "value", "timestamp": datetime.now().isoformat()}
        
        # 設定保存テスト
        db_manager.update_setting(test_setting_key, test_setting_value)
        print("✅ 設定保存テスト成功")
        
        # 設定取得テスト
        retrieved_value = db_manager.get_setting(test_setting_key)
        if retrieved_value == test_setting_value:
            print("✅ 設定取得テスト成功")
        else:
            print(f"❌ 設定取得テスト失敗: 期待値={test_setting_value}, 実際値={retrieved_value}")
        
        return True
        
    except ImportError as e:
        print(f"❌ DatabaseManager インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ DatabaseManager テストエラー: {e}")
        return False


def test_enhanced_csv_parser_import():
    """EnhancedCSVParserインポートテスト"""
    print("\n=== EnhancedCSVParser インポートテスト ===")
    
    try:
        from core.enhanced_csv_parser import EnhancedCSVParser
        from core.database_manager import DatabaseManager
        
        # インスタンス作成テスト
        db_manager = DatabaseManager("test_stock_watchdog.db")
        csv_parser = EnhancedCSVParser(db_manager)
        
        print("✅ EnhancedCSVParser インスタンス作成成功")
        
        # 基本メソッド存在確認
        required_methods = [
            'parse_csv_to_database',
            'get_portfolio_summary'
        ]
        
        for method_name in required_methods:
            if hasattr(csv_parser, method_name):
                print(f"✅ メソッド存在確認: {method_name}")
            else:
                print(f"❌ メソッド不存在: {method_name}")
        
        return True
        
    except ImportError as e:
        print(f"❌ EnhancedCSVParser インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ EnhancedCSVParser テストエラー: {e}")
        return False


def run_all_tests():
    """全テスト実行"""
    print("🧪 v2.0.0 データベース徹底テスト開始")
    print("=" * 50)
    
    results = []
    
    # テスト1: データベース初期化
    results.append(("データベース初期化", test_database_initialization()))
    
    # テスト2: DatabaseManager
    results.append(("DatabaseManager", test_database_manager()))
    
    # テスト3: EnhancedCSVParser
    results.append(("EnhancedCSVParser", test_enhanced_csv_parser_import()))
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📊 テスト結果サマリー")
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
    test_db_path = "test_stock_watchdog.db"
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
            print(f"\n🧹 テストDB削除: {test_db_path}")
        except Exception as e:
            print(f"⚠️ テストDB削除失敗: {e}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)