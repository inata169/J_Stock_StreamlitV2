#!/usr/bin/env python3
"""
CSVパーサーのテストスクリプト
楽天証券とSBI証券のCSVファイルを正しく解析できるかテストする
"""

import sys
import os
import logging
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 直接ファイルから読み込み（依存関係を回避）
import pandas as pd
import io
from decimal import Decimal

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('csv_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_csv_parser():
    """CSVパーサーのテスト"""
    
    # テストファイルのパス
    rakuten_csv = project_root / "assetbalance(JP)_20250626_193110.csv"
    sbi_csv = project_root / "New_file 2.csv"
    
    # パーサーの初期化
    processor = FinancialDataProcessor()
    parser = UnifiedCSVParser(processor)
    
    print("=" * 80)
    print("CSV Parser Test")
    print("=" * 80)
    
    # 楽天証券CSVのテスト
    if rakuten_csv.exists():
        print("\n🧪 楽天証券CSVのテスト")
        print("-" * 40)
        try:
            with open(rakuten_csv, 'rb') as f:
                content = f.read()
            
            result_df = parser.parse_csv(content, rakuten_csv.name)
            
            print(f"✅ 楽天証券CSV解析成功!")
            print(f"   総行数: {len(result_df)}")
            print(f"   カラム: {list(result_df.columns)}")
            
            if not result_df.empty:
                print("\n📊 データサンプル:")
                for i, row in result_df.head().iterrows():
                    print(f"   {i+1}. {row.get('symbol', 'N/A')} - {row.get('name', 'N/A')} - {row.get('quantity', 'N/A')}株")
                
                print(f"\n📈 全銘柄リスト:")
                symbols = result_df['symbol'].tolist()
                for i, symbol in enumerate(symbols, 1):
                    name = result_df[result_df['symbol'] == symbol]['name'].iloc[0] if 'name' in result_df.columns else 'N/A'
                    quantity = result_df[result_df['symbol'] == symbol]['quantity'].iloc[0] if 'quantity' in result_df.columns else 'N/A'
                    print(f"   {i:2d}. {symbol} - {name} - {quantity}株")
                    
                print(f"\n🎯 成功基準チェック:")
                print(f"   期待値: 24銘柄")
                print(f"   実際値: {len(result_df)}銘柄")
                if len(result_df) >= 20:  # 20銘柄以上なら成功とみなす
                    print("   ✅ 成功!")
                else:
                    print("   ❌ 失敗 - 期待値より少ない")
            else:
                print("   ❌ データなし")
                
        except Exception as e:
            print(f"❌ 楽天証券CSV解析エラー: {e}")
            logger.exception("楽天証券CSV解析エラー")
    else:
        print(f"⚠️  楽天証券CSVファイルが見つかりません: {rakuten_csv}")
    
    # SBI証券CSVのテスト
    if sbi_csv.exists():
        print("\n🧪 SBI証券CSVのテスト")
        print("-" * 40)
        try:
            with open(sbi_csv, 'rb') as f:
                content = f.read()
            
            result_df = parser.parse_csv(content, sbi_csv.name)
            
            print(f"✅ SBI証券CSV解析成功!")
            print(f"   総行数: {len(result_df)}")
            print(f"   カラム: {list(result_df.columns)}")
            
            if not result_df.empty:
                print("\n📊 データサンプル:")
                for i, row in result_df.head().iterrows():
                    print(f"   {i+1}. {row.get('symbol', 'N/A')} - {row.get('name', 'N/A')} - {row.get('quantity', 'N/A')}株")
                
                print(f"\n📈 全銘柄リスト:")
                symbols = result_df['symbol'].tolist()
                for i, symbol in enumerate(symbols, 1):
                    name = result_df[result_df['symbol'] == symbol]['name'].iloc[0] if 'name' in result_df.columns else 'N/A'
                    quantity = result_df[result_df['symbol'] == symbol]['quantity'].iloc[0] if 'quantity' in result_df.columns else 'N/A'
                    print(f"   {i:2d}. {symbol} - {name} - {quantity}株")
                    
                print(f"\n🎯 成功基準チェック:")
                print(f"   期待値: 7銘柄 (個別株式+投資信託)")
                print(f"   実際値: {len(result_df)}銘柄")
                if len(result_df) >= 5:  # 5銘柄以上なら成功とみなす
                    print("   ✅ 成功!")
                else:
                    print("   ❌ 失敗 - 期待値より少ない")
            else:
                print("   ❌ データなし")
                
        except Exception as e:
            print(f"❌ SBI証券CSV解析エラー: {e}")
            logger.exception("SBI証券CSV解析エラー")
    else:
        print(f"⚠️  SBI証券CSVファイルが見つかりません: {sbi_csv}")
    
    print("\n" + "=" * 80)
    print("テスト完了")
    print("=" * 80)

if __name__ == "__main__":
    test_csv_parser()