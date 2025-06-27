#!/usr/bin/env python3
"""
シンプルなCSV検査スクリプト
依存関係を最小化してCSVファイルの内容を直接確認
"""

import csv
from pathlib import Path

def read_csv_with_encoding(file_path, encoding):
    """指定したエンコーディングでCSVを読み込み"""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            lines = f.readlines()
        return lines, True
    except UnicodeDecodeError:
        return [], False

def analyze_csv(file_path, name):
    """CSVファイルを分析"""
    print(f"\n{'='*60}")
    print(f"📊 {name} CSV分析")
    print(f"{'='*60}")
    
    # 複数のエンコーディングを試す
    encodings = ['utf-8', 'shift_jis', 'cp932', 'utf-8-sig']
    
    lines = []
    successful_encoding = None
    
    for encoding in encodings:
        lines, success = read_csv_with_encoding(file_path, encoding)
        if success and lines:
            successful_encoding = encoding
            break
    
    if not lines:
        print("❌ ファイルを読み込めませんでした")
        return
    
    print(f"✅ 読み込み成功: {successful_encoding}")
    print(f"📏 総行数: {len(lines)}")
    
    # 最初の20行を表示
    print(f"\n📝 最初の20行:")
    for i, line in enumerate(lines[:20]):
        line = line.strip()
        if line:
            print(f"   {i+1:2d}: {line[:80]}{'...' if len(line) > 80 else ''}")
        else:
            print(f"   {i+1:2d}: (空行)")
    
    # CSV構造分析
    print(f"\n🔎 CSV構造分析:")
    
    # ヘッダー行を探す
    header_candidates = []
    for i, line in enumerate(lines):
        if ('銘柄コード' in line and '銘柄名' in line) or \
           ('�R�[�h' in line and '����' in line):  # 文字化けパターン
            header_candidates.append((i, line.strip()))
    
    if header_candidates:
        print(f"   ヘッダー候補: {len(header_candidates)}個")
        for i, (line_num, content) in enumerate(header_candidates):
            print(f"     {i+1}. 行{line_num+1}: {content[:60]}...")
    else:
        print("   ❌ ヘッダー行が見つかりません")
    
    # データ行の推定
    data_rows = 0
    for line in lines:
        # 数字4桁（銘柄コード）を含む行をカウント
        if any(c.isdigit() for c in line) and len([c for c in line if c.isdigit()]) >= 4:
            # 簡単なパターンマッチ（4桁数字が含まれる）
            import re
            if re.search(r'\b\d{4}\b', line):
                data_rows += 1
    
    print(f"   推定データ行数: {data_rows}行")
    
    # 特別なパターンを検索
    special_patterns = {
        '特定口座': 0,
        'NISA': 0,
        '成長投資枠': 0,
        '合計': 0,
        '■': 0,
        'ポートフォリオ': 0,
        '投資信託': 0
    }
    
    for line in lines:
        for pattern, count in special_patterns.items():
            if pattern in line:
                special_patterns[pattern] += 1
    
    print(f"   特別なパターン:")
    for pattern, count in special_patterns.items():
        if count > 0:
            print(f"     {pattern}: {count}回")

def main():
    """メイン処理"""
    print("📋 CSV分析ツール")
    
    # ファイルパス
    project_root = Path(__file__).parent
    rakuten_csv = project_root / "assetbalance(JP)_20250626_193110.csv"
    sbi_csv = project_root / "New_file 2.csv"
    
    # 楽天証券CSV分析
    if rakuten_csv.exists():
        analyze_csv(rakuten_csv, "楽天証券")
    else:
        print(f"⚠️  楽天証券CSVファイルが見つかりません: {rakuten_csv}")
    
    # SBI証券CSV分析
    if sbi_csv.exists():
        analyze_csv(sbi_csv, "SBI証券")
    else:
        print(f"⚠️  SBI証券CSVファイルが見つかりません: {sbi_csv}")
    
    print(f"\n{'='*60}")
    print("分析完了")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()