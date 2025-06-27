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

## 🗄️ データベース設計（v2.0）

### 統一データベースアーキテクチャ

**設計哲学**: 「両方の真実を保持」
- ✅ 証券会社データ（SBI：167.98%、楽天：計算値）
- ✅ Yahoo Financeデータ（0.1598小数形式）
- ✅ 表示時に両方表示で透明性確保
- ✅ 計算なしで直接比較可能

### データベーススキーマ

#### 1. ポートフォリオメインテーブル
```sql
CREATE TABLE portfolios (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(4) NOT NULL,           -- 9432形式（.Tなし）
    data_source VARCHAR(20),              -- 'rakuten' or 'sbi'
    
    -- 証券会社データ（真実の値）
    quantity INTEGER NOT NULL,            -- 保有数量
    average_price DECIMAL(10,1),          -- 平均取得価額（小数1桁）
    market_value DECIMAL(12,1),           -- 時価評価額
    profit_loss DECIMAL(12,1),            -- 評価損益
    
    -- 両方の損益率（真実保持）
    profit_loss_rate_original DECIMAL(8,2),     -- 元値（SBI:167.98、楽天:null）
    profit_loss_rate_percent DECIMAL(8,1),      -- %表示（167.9%）
    profit_loss_rate_decimal DECIMAL(8,4),      -- 小数表示（1.6790）
    
    import_timestamp TIMESTAMP DEFAULT NOW()
);
```

#### 2. 銘柄マスターテーブル
```sql
CREATE TABLE stock_master (
    symbol VARCHAR(4) PRIMARY KEY,        -- 統一銘柄コード
    long_name VARCHAR(200),               -- 企業名
    sector VARCHAR(100),                  -- セクター
    current_price DECIMAL(10,1),          -- 現在価格（小数1桁）
    market_cap BIGINT,                    -- 時価総額
    shares_outstanding BIGINT             -- 発行済株式数
);
```

#### 3. 財務指標テーブル（両方の真実保持）
```sql
CREATE TABLE financial_metrics (
    symbol VARCHAR(4),
    metric_date DATE,
    
    -- Yahoo Finance原始値（小数形式）
    yahoo_dividend_yield DECIMAL(8,4),           -- 0.0500形式
    yahoo_trailing_pe DECIMAL(8,1),              -- 15.5倍
    yahoo_return_on_equity DECIMAL(8,4),         -- 0.1500形式
    
    -- 表示用変換値（%形式）
    display_dividend_yield DECIMAL(6,1),         -- 5.0%
    display_return_on_equity DECIMAL(6,1),       -- 15.0%
    
    PRIMARY KEY (symbol, metric_date)
);
```

#### 4. J-Quants統合用テーブル（拡張予定）
```sql
-- 四半期財務データ（J-Quants独自）
CREATE TABLE quarterly_financials (
    symbol VARCHAR(4),
    quarter_date DATE,
    earnings_per_share DECIMAL(8,2),             -- EPS
    cash_flows_operating DECIMAL(12,0),          -- 営業CF
    cash_flows_investing DECIMAL(12,0),          -- 投資CF
    cash_flows_financing DECIMAL(12,0),          -- 財務CF
    PRIMARY KEY (symbol, quarter_date)
);

-- 市場センチメント（J-Quants独自）
CREATE TABLE market_sentiment (
    symbol VARCHAR(4),
    sentiment_date DATE,
    short_selling_ratio DECIMAL(6,2),            -- 空売り比率
    credit_balance DECIMAL(15,0),                -- 信用残高
    institutional_trading DECIMAL(15,0),         -- 機関投資家売買
    PRIMARY KEY (symbol, sentiment_date)
);
```

### 🔧 統一単位処理システム

#### 銘柄コード正規化
```python
class SymbolNormalizer:
    RULES = [
        (r'^"([^"]+)"$', r'\1'),           # "9432" → 9432
        (r'^(\d{4})\.T$', r'\1'),          # 9432.T → 9432
        (r'^(\d{4})\s.*$', r'\1'),         # "9432 NTT" → 9432
    ]
    
    @classmethod
    def normalize(cls, symbol: str) -> str:
        """統一形式（4桁数字）に正規化"""
        # 各正規化ルールを適用
        # 日本株パターン（4桁数字）を検証
```

#### 単位変換処理
```python
class UnifiedDataConverter:
    @staticmethod
    def convert_percentage_to_decimal(value, source_format):
        """単位統一変換"""
        if source_format == 'sbi_percent':
            return float(value) / 100.0    # 167.98% → 1.6798
        elif source_format == 'yahoo_decimal':
            return float(value)            # 0.1598 → そのまま
        
    @staticmethod
    def format_decimal(value, decimals=1):
        """小数点桁数統一（1桁固定）"""
        return round(float(value), decimals)
```

### 📊 CSV処理アーキテクチャ

#### EnhancedCSVParser
```python
class EnhancedCSVParser:
    """新スキーマ対応統一CSVパーサー"""
    
    def parse_csv_to_database(self, file_content, filename):
        """CSVファイルを解析して直接データベースに保存"""
        # 1. エンコーディング自動検出（UTF-8/Shift_JIS）
        # 2. データソース自動判定（楽天/SBI）
        # 3. フィールドマッピング適用
        # 4. 単位正規化処理
        # 5. データベース直接保存
        
    def _extract_stock_item(self, row_dict, data_source):
        """両方の真実を保持した銘柄データ抽出"""
        # SBI証券: 167.98% → percent=167.9, decimal=1.679
        # 楽天証券: 計算 → percent=計算結果, decimal=計算結果
```

### ⚡ API制限管理システム

#### AdaptiveAPIManager
```python
class AdaptiveAPIManager:
    """適応的API制限管理"""
    
    API_CONFIGS = {
        'yahoo_finance': {
            'requests_per_hour': 100,
            'backoff_enabled': True
        },
        'j_quants': {
            'requests_per_hour': 500,
            'backoff_enabled': True
        }
    }
    
    def can_make_request(self, api_name, priority):
        """優先度付きリクエスト制御"""
        # 1. バックオフ期間チェック
        # 2. 使用量制限チェック
        # 3. 優先度による緩和
        # 4. 推奨待機時間計算
```

### 🔄 J-Quants統合ロードマップ

#### Phase 1: 基盤整備（完了）
- ✅ 統一データベース設計
- ✅ API制限管理システム
- ✅ 銘柄コード正規化

#### Phase 2: J-Quants統合（計画中）
```python
# 統合可能性: 95%
MAPPING_ANALYSIS = {
    'symbol': '完全一致（変換不要）',
    'financial_data': '既存テーブル拡張可能',
    'unique_data': '四半期財務・空売り比率・信用残高',
    'challenges': '単位統一の実装確認必要'
}
```

#### Phase 3: 高度分析機能
- 四半期決算トレンド分析
- 市場センチメント分析
- 機関投資家動向分析

## 📊 バージョン履歴

### v2.0.0 - 統一データベース（実装完了）
- 🏗️ 「両方の真実保持」データベース設計
- 🔥 **単位不一致問題完全解決**（SBI167.98% vs Yahoo0.1598）
- 📊 EnhancedCSVParser（32件データ正常処理）
- ⚡ 適応的API制限管理システム
- 🎯 銘柄コード統一（.T除去、小数点1桁）
- ✅ J-Quants統合準備完了（95%適合性）

### v0.3.0 - 統一データ処理
- 🎯 3段階警告システム（軽微/注意/重大）
- 📊 包括的異常値検出（ROE/時価総額/出来高）
- ✅ 実銘柄検証済み（積水ハウス他5銘柄）

### v0.2.2 - 重要バグ修正
- 🔥 配当利回り477%→4.77%修正
- 🛡️ 財務指標異常値検出強化

### 今後の展開
- **最高優先**: J-Quants API統合実装
- **高優先**: Streamlit UI v2.0対応
- **中優先**: 四半期決算分析機能
- **低優先**: 市場センチメント分析

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