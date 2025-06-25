# CLAUDE.md - 日本株ウォッチドッグ Streamlit版

## 🚨 プロジェクト方針
**学習・研究専用ツール** - 投資判断は自己責任で
- ✅ メイン投資: インデックス投資 90-95%
- 🧪 このツール: 市場理解の学習用 0%実投資

## 🏗️ アーキテクチャ設計（v0.3.0）

### 統一データ処理システム
```
外部API → FinancialDataProcessor → 正規化データ → 各機能
         ↑ 全データ必須通過点（生データ直接使用禁止）
```

### コアモジュール責務
1. **FinancialDataProcessor** - データ正規化・異常値検出
   - 配当利回り70%→7%等の単位エラー自動修正
   - PER<0→None等の範囲検証
   - 🟡軽微→🟠注意→🔴重大の3段階警告

2. **MultiDataSourceManager** - API生データ取得のみ
   - Yahoo Finance/J Quants API連携
   - 取得後即座にFinancialDataProcessor経由

3. **InvestmentStrategyAnalyzer** - 戦略分析
   - 統一キー使用（dividend_yield, pe_ratio等）
   - 旧キー（pbr, per等）は使用禁止

4. **ChartDataManager** - チャート生成
   - 配当データ検証（1円≤年間配当≤1000円）
   - 異常値自動修正機能

### 🚨 開発必須チェック
```bash
# 統一プロセッサバイパス検出
grep -r "dividendYield\|info\.get" --include="*.py" .

# 重複計算検出
grep -r "dividend.*yield.*=" --include="*.py" .
```

## 📱 Streamlit UI仕様

### セッション状態設計
```python
st.session_state = {
    # コアデータ
    'portfolio_data': pd.DataFrame,
    'watchlist': List[Dict],
    'data_source_manager': MultiDataSourceManager,
    
    # UI状態
    'current_page': str,
    'api_error_count': int,
    
    # 分析結果キャッシュ
    'strategy_analysis_results': Dict,
    'chart_data_cache': Dict
}
```

### 標準UIパターン
```python
# 3列メトリクス
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("総評価額", "¥1,234,567", delta="+4.8%")

# データテーブル（大量データ対応）
st.dataframe(
    data=df,
    use_container_width=True,
    height=400,
    column_config={
        "評価額": st.column_config.NumberColumn(format="¥%d")
    }
)

# エラー段階表示
if critical: st.error("🔴 重大エラー")
elif warning: st.warning("🟠 注意")
else: st.success("✅ 正常")
```

### パフォーマンス最適化
```python
# 階層キャッシュ戦略
@st.cache_data(ttl=300)  # 5分: 価格データ
@st.cache_data(ttl=900)  # 15分: 財務データ
@st.cache_data(ttl=3600, persist="disk")  # 1時間: 履歴データ

# API制限保護（1時間100リクエスト）
if len(recent_requests) > 100:
    st.error("API制限到達")
```

## 🔧 実装ガイドライン

### 品質向上の改善提案

1. **エラーバウンダリー実装**
```python
@contextmanager
def error_boundary(operation_name: str):
    try:
        yield
    except Exception as e:
        logger.error(f"{operation_name}: {e}")
        st.error(f"処理エラー: {operation_name}")
        # 自動リカバリー試行
```

2. **プログレッシブエンハンスメント**
```python
# 基本機能を確保しつつ段階的に機能追加
if advanced_features_available():
    render_advanced_charts()
else:
    render_basic_charts()
```

3. **型安全性の強化**
```python
from typing import TypedDict, Optional
from decimal import Decimal

class NormalizedStockData(TypedDict):
    dividend_yield: Optional[Decimal]
    pe_ratio: Optional[Decimal]
    pb_ratio: Optional[Decimal]
    current_price: Decimal
```

4. **監視・アラート機能**
```python
# 異常検知の自動通知
if anomaly_detected:
    send_slack_notification(f"異常検知: {symbol}")
    log_to_monitoring_service(anomaly_details)
```

5. **A/Bテスト基盤**
```python
def feature_flag(feature_name: str, user_id: str) -> bool:
    """機能フラグによる段階的リリース"""
    return hash(f"{feature_name}:{user_id}") % 100 < rollout_percentage
```

## 📊 バージョン履歴

### v0.3.0 - 統一データ処理
- 🎯 3段階警告システム（軽微/注意/重大）
- 📊 包括的異常値検出（ROE/時価総額/出来高）
- ✅ 実銘柄検証済み（積水ハウス他5銘柄）

### v0.2.2 - 重要バグ修正
- 🔥 配当利回り477%→4.77%修正
- 🛡️ 財務指標異常値検出強化

### 今後の展開
- **高優先**: エラーハンドリング強化、API制限対策
- **中優先**: キャッシュ最適化、J Quants連携
- **低優先**: 認証機能、カスタム戦略

## 🚀 クイックスタート

```bash
# セットアップ
git clone <repository>
python -m venv .venv
source .venv/bin/activate  # Win: .venv\Scripts\activate
pip install -r requirements.txt

# 起動
streamlit run app.py
# → http://localhost:8501

# トラブルシューティング
streamlit cache clear  # キャッシュクリア
streamlit run app.py --server.port 8502  # ポート変更
```

## 📁 プロジェクト構造

```
J_Stock_Streamlit/
├── app.py                          # エントリポイント
├── pages/                          # UI層
│   ├── portfolio.py               # ポートフォリオ管理
│   ├── strategy.py                # 戦略分析
│   └── charts.py                  # チャート表示
├── core/                          # ビジネスロジック層
│   ├── financial_data_processor.py # ★統一データ処理
│   ├── multi_data_source.py       # データ取得
│   └── investment_strategies.py   # 戦略分析
└── requirements.txt               # 依存関係
```

## 🎯 開発哲学

**学習ツールとしての価値創造**
- 市場メカニズムの理解促進
- 財務分析スキルの習得支援
- リスク管理の実践的学習

**技術的優位性**
- 統一データ処理による信頼性
- リアルタイムデータ活用
- 直感的UI/UXデザイン

---
*Streamlit版 v0.3.0 - 学習と研究のための株式市場分析ツール*