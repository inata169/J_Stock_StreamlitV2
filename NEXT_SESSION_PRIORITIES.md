# 次回セッション優先事項 - 日本株ウォッチドッグ v2.0.0

## 🚨 最高優先（即座に修正）

### 1. CSV処理エラーの修正
```
エラー: "['name'] not in index"
場所: pages/portfolio.py
原因: カラム名の不整合
```

**修正方針:**
- CSVから読み込んだデータのカラム構造を確認
- `portfolio.py`で期待するカラム名と実際のカラム名の整合
- 不足カラムのデフォルト値設定

### 2. ポートフォリオ分析エラーの修正
```
エラー: float() argument must be a string or a real number, not 'NoneType'
場所: pages/portfolio.py - ポートフォリオ分析処理
原因: None値の数値変換エラー
```

**修正方針:**
- None値チェックの追加
- デフォルト値の設定
- エラーハンドリングの強化

## 🔧 推奨修正手順

### Step 1: 問題特定
```bash
# 開発開始前の健全性チェック
python3 test_comprehensive_health_check.py --quick

# アプリ起動
python3 -m streamlit run app.py --server.port 8502
```

### Step 2: データ構造確認
```python
# CSVデータの実際の構造を確認
import pandas as pd
df = pd.read_csv("your_csv_file.csv")
print("Columns:", df.columns.tolist())
print("Data types:", df.dtypes)
print("Null values:", df.isnull().sum())
```

### Step 3: エラー箇所の特定
- `pages/portfolio.py` - line 241 付近のエラー
- データフレーム処理でのカラム参照エラー
- 数値変換処理でのNone値エラー

## 📊 既知の動作状況

### ✅ 正常動作
- アプリ起動: 成功
- データベース初期化: 成功
- CSV読み込み: 7件成功
- データベース保存: 30銘柄成功
- Yahoo Finance API: 動作（制限内）

### ❌ エラー発生
- ポートフォリオ画面での分析表示
- CSV処理後のデータ表示

## 🎯 修正後の確認項目

1. **CSV読み込み後の表示**
   - ポートフォリオ概要の正常表示
   - 数値データの正しい表示
   - エラーメッセージの解消

2. **データの整合性**
   - SBI証券データの正しい処理
   - 楽天証券データの正しい処理
   - 両データソースの統合表示

3. **エラーハンドリング**
   - None値の適切な処理
   - カラム不足時の適切な対応
   - ユーザーフレンドリーなエラーメッセージ

## 🔄 開発フロー

```bash
# 1. 開発開始
python3 test_comprehensive_health_check.py --quick

# 2. 問題修正
# エディタでのコード修正

# 3. 動作確認  
python3 -m streamlit run app.py --server.port 8502

# 4. テスト実行
python3 test_comprehensive_health_check.py --quick

# 5. 問題が解決したらコミット
git add .
git commit -m "fix: resolve CSV processing and portfolio analysis errors"
git push origin main
```

## 🧪 テスト準備

### 確認用CSVファイル
- `New_file 2.csv` (SBI証券形式)
- `assetbalance(JP)_20250626_193110.csv` (楽天証券形式)

### テストシナリオ
1. SBI証券CSVの読み込み
2. ポートフォリオ画面での表示確認
3. エラーメッセージの確認
4. 修正後の再テスト

## 📚 参考情報

### 関連ファイル
- `pages/portfolio.py` - メイン修正対象
- `core/enhanced_csv_parser.py` - CSV処理ロジック
- `core/database_manager.py` - データベース操作

### ログ参照
- `app.log` - アプリケーションログ
- `health_check.log` - 診断ログ

---

**🎯 目標**: CSV処理エラーの完全解決とポートフォリオ機能の完全復旧  
**⏱️ 推定作業時間**: 30-45分  
**🔧 修正レベル**: 中程度（エラーハンドリング強化）

*Prepared: 2025-06-27 22:59*