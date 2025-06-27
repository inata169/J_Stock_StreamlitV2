#!/usr/bin/env python3
"""
直接データベーステスト v2.0.0
pandas問題を回避した直接的なデータベーステスト
"""

import os
import sqlite3
import logging
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_database_schema_compliance():
    """データベーススキーマ準拠テスト"""
    print("=== データベーススキーマ準拠テスト ===")
    
    test_db_path = "test_direct_db.db"
    
    # 既存ファイル削除
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    try:
        # スキーマファイル読み込み
        with open("database_schema.sql", 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # データベース作成・スキーマ実行
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.executescript(schema_sql)
        conn.commit()
        
        print("✅ データベース作成・スキーマ実行成功")
        
        # テーブル一覧確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        expected_tables = ['portfolios', 'stocks', 'financial_indicators', 'api_usage_log', 'settings']
        missing_tables = set(expected_tables) - set(tables)
        
        if not missing_tables:
            print(f"✅ 必要なテーブル確認成功: {len(expected_tables)}個")
            for table in expected_tables:
                print(f"   - {table}")
        else:
            print(f"❌ 不足テーブル: {missing_tables}")
            return False
        
        # ポートフォリオテーブル構造確認
        cursor.execute("PRAGMA table_info(portfolios)")
        portfolio_columns = {col[1] for col in cursor.fetchall()}
        
        required_portfolio_columns = {
            'symbol', 'name', 'data_source', 'quantity', 'average_price',
            'profit_loss_rate_original', 'profit_loss_rate_percent', 'profit_loss_rate_decimal'
        }
        
        missing_columns = required_portfolio_columns - portfolio_columns
        if not missing_columns:
            print("✅ ポートフォリオテーブル構造確認成功")
        else:
            print(f"❌ ポートフォリオテーブル不足カラム: {missing_columns}")
            return False
        
        conn.close()
        os.remove(test_db_path)
        return True
        
    except Exception as e:
        print(f"❌ データベーススキーマ準拠テストエラー: {e}")
        return False


def test_direct_crud_operations():
    """直接CRUD操作テスト"""
    print("\n=== 直接CRUD操作テスト ===")
    
    test_db_path = "test_direct_crud.db"
    
    # 既存ファイル削除
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    try:
        # データベース・スキーマ作成
        with open("database_schema.sql", 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.executescript(schema_sql)
        conn.commit()
        
        # CREATE: ポートフォリオデータ挿入
        portfolio_data = [
            ('1928', '積水ハウス', 'sbi', 100, 2100.0, 2200.0, 220000.0, 10000.0, 210000.0, 4.76, 4.8, 0.048),
            ('7203', 'トヨタ自動車', 'rakuten', 200, 1800.0, 1850.0, 370000.0, 10000.0, 360000.0, None, 2.8, 0.028)
        ]
        
        cursor.executemany("""
            INSERT INTO portfolios 
            (symbol, name, data_source, quantity, average_price, current_price, 
             market_value, profit_loss, total_cost, profit_loss_rate_original, 
             profit_loss_rate_percent, profit_loss_rate_decimal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, portfolio_data)
        
        print(f"✅ ポートフォリオデータ挿入成功: {len(portfolio_data)}件")
        
        # READ: データ取得
        cursor.execute("SELECT COUNT(*) FROM portfolios")
        count = cursor.fetchone()[0]
        
        if count == 2:
            print(f"✅ データ取得確認成功: {count}件")
        else:
            print(f"❌ データ取得確認失敗: 期待2件、実際{count}件")
            return False
        
        # READ: 条件指定取得
        cursor.execute("SELECT * FROM portfolios WHERE symbol = ?", ('1928',))
        sbi_data = cursor.fetchall()
        
        if len(sbi_data) == 1 and sbi_data[0][1] == '1928':
            print("✅ 条件指定取得成功")
        else:
            print(f"❌ 条件指定取得失敗: {sbi_data}")
            return False
        
        # UPDATE: データ更新
        cursor.execute("""
            UPDATE portfolios 
            SET current_price = ?, market_value = ?, profit_loss = ? 
            WHERE symbol = ? AND data_source = ?
        """, (2300.0, 230000.0, 20000.0, '1928', 'sbi'))
        
        updated_rows = cursor.rowcount
        if updated_rows == 1:
            print("✅ データ更新成功")
        else:
            print(f"❌ データ更新失敗: {updated_rows}行更新")
            return False
        
        # 更新確認
        cursor.execute("SELECT current_price, market_value FROM portfolios WHERE symbol = ?", ('1928',))
        updated_data = cursor.fetchone()
        
        if updated_data and updated_data[0] == 2300.0 and updated_data[1] == 230000.0:
            print("✅ 更新内容確認成功")
        else:
            print(f"❌ 更新内容確認失敗: {updated_data}")
            return False
        
        # DELETE: データ削除
        cursor.execute("DELETE FROM portfolios WHERE symbol = ? AND data_source = ?", ('7203', 'rakuten'))
        deleted_rows = cursor.rowcount
        
        if deleted_rows == 1:
            print("✅ データ削除成功")
        else:
            print(f"❌ データ削除失敗: {deleted_rows}行削除")
            return False
        
        # 削除確認
        cursor.execute("SELECT COUNT(*) FROM portfolios")
        remaining_count = cursor.fetchone()[0]
        
        if remaining_count == 1:
            print("✅ 削除確認成功")
        else:
            print(f"❌ 削除確認失敗: 残存{remaining_count}件")
            return False
        
        conn.commit()
        conn.close()
        os.remove(test_db_path)
        return True
        
    except Exception as e:
        print(f"❌ 直接CRUD操作テストエラー: {e}")
        return False


def test_foreign_key_constraints():
    """外部キー制約テスト"""
    print("\n=== 外部キー制約テスト ===")
    
    test_db_path = "test_foreign_key.db"
    
    # 既存ファイル削除
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    try:
        # データベース・スキーマ作成
        with open("database_schema.sql", 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.executescript(schema_sql)
        conn.commit()
        
        # 外部キー有効化確認
        cursor.execute("PRAGMA foreign_keys")
        fk_enabled = cursor.fetchone()[0]
        
        if fk_enabled:
            print("✅ 外部キー制約有効化確認")
        else:
            print("❌ 外部キー制約無効")
            return False
        
        # 株式マスターデータ挿入
        cursor.execute("""
            INSERT INTO stocks (symbol, name, market) 
            VALUES (?, ?, ?)
        """, ('1928', '積水ハウス', 'TSE'))
        
        # 財務指標データ挿入（正常パターン）
        cursor.execute("""
            INSERT INTO financial_indicators (symbol, dividend_yield, pe_ratio) 
            VALUES (?, ?, ?)
        """, ('1928', 0.035, 15.2))
        
        print("✅ 外部キー制約正常パターン成功")
        
        # 外部キー制約違反テスト
        try:
            cursor.execute("""
                INSERT INTO financial_indicators (symbol, dividend_yield, pe_ratio) 
                VALUES (?, ?, ?)
            """, ('9999', 0.04, 12.0))  # 存在しない銘柄
            
            print("❌ 外部キー制約違反テスト失敗: エラーが発生しなかった")
            return False
            
        except sqlite3.IntegrityError as e:
            if "FOREIGN KEY constraint failed" in str(e):
                print("✅ 外部キー制約違反テスト成功")
            else:
                print(f"❌ 予期しないエラー: {e}")
                return False
        
        conn.close()
        os.remove(test_db_path)
        return True
        
    except Exception as e:
        print(f"❌ 外部キー制約テストエラー: {e}")
        return False


def test_data_types_and_constraints():
    """データ型・制約テスト"""
    print("\n=== データ型・制約テスト ===")
    
    test_db_path = "test_data_types.db"
    
    # 既存ファイル削除
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    try:
        # データベース・スキーマ作成
        with open("database_schema.sql", 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.executescript(schema_sql)
        conn.commit()
        
        # 数値型テスト
        cursor.execute("""
            INSERT INTO portfolios (symbol, data_source, quantity, average_price, 
                                  profit_loss_rate_decimal) 
            VALUES (?, ?, ?, ?, ?)
        """, ('1928', 'test', 100, 2100.123, 0.048765))
        
        cursor.execute("SELECT average_price, profit_loss_rate_decimal FROM portfolios WHERE symbol = ?", ('1928',))
        numeric_data = cursor.fetchone()
        
        if numeric_data and isinstance(numeric_data[0], float) and isinstance(numeric_data[1], float):
            print("✅ 数値型データ挿入・取得成功")
        else:
            print(f"❌ 数値型データテスト失敗: {numeric_data}")
            return False
        
        # NULL値テスト
        cursor.execute("""
            INSERT INTO portfolios (symbol, data_source, quantity) 
            VALUES (?, ?, ?)
        """, ('7203', 'test', 200))
        
        cursor.execute("SELECT profit_loss_rate_original FROM portfolios WHERE symbol = ?", ('7203',))
        null_data = cursor.fetchone()
        
        if null_data and null_data[0] is None:
            print("✅ NULL値処理テスト成功")
        else:
            print(f"❌ NULL値処理テスト失敗: {null_data}")
            return False
        
        # UNIQUE制約テスト
        try:
            cursor.execute("""
                INSERT INTO portfolios (symbol, data_source, quantity) 
                VALUES (?, ?, ?)
            """, ('1928', 'test', 300))  # 既存の(symbol, data_source)ペア
            
            print("❌ UNIQUE制約テスト失敗: エラーが発生しなかった")
            return False
            
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                print("✅ UNIQUE制約テスト成功")
            else:
                print(f"❌ 予期しないエラー: {e}")
                return False
        
        conn.close()
        os.remove(test_db_path)
        return True
        
    except Exception as e:
        print(f"❌ データ型・制約テストエラー: {e}")
        return False


def run_direct_database_tests():
    """直接データベーステスト実行"""
    print("🧪 直接データベーステスト開始")
    print("=" * 50)
    
    test_methods = [
        ("データベーススキーマ準拠", test_database_schema_compliance),
        ("直接CRUD操作", test_direct_crud_operations),
        ("外部キー制約", test_foreign_key_constraints),
        ("データ型・制約", test_data_types_and_constraints),
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
    print("📊 直接データベーステスト結果サマリー")
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
    import sys
    success = run_direct_database_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()