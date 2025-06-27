# CLAUDE.md

日本株ウォッチドッグ - 株式市場学習ツール Web版（投資アドバイスは行いません）

## 🚨 重要：プロジェクト方針

**このツールは学習・研究専用です**
- ✅ メイン投資: インデックス投資(オルカン等) 90-95%
- 🧪 このツール: 市場理解のための学習 0%実投資
- 投資判断は必ずご自身の責任で行ってください

## プロジェクト概要

日本株式市場のデータ分析・学習ツール（Streamlit Web版）。Yahoo Finance APIを使用した株価情報取得、ポートフォリオ管理、投資戦略分析、配当分析機能を提供。デスクトップ版からの主要機能移植。

## 開発環境

- **開発**: WSL Ubuntu (/mnt/c/Users/inata/Documents/ClaudeCode/J_Stock_Streamlit)  
- **本番**: Streamlit Cloud 対応予定
- **ローカル**: Windows/Mac/Linux対応

## 基本コマンド

```bash
# 環境セットアップ
git clone https://github.com/inata169/J_Stock_Streamlit.git
cd J_Stock_Streamlit

# 仮想環境（推奨）
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 依存関係インストール
pip install -r requirements.txt

# アプリ起動
streamlit run app.py

# ブラウザアクセス
# http://localhost:8501
```

## 🏗️ 統一データ処理アーキテクチャ（v0.3.0）

### 設計思想：データ整合性の絶対保証

**核心原則**: 複数の計算式による不整合を防ぐため、全ての金融データは単一の統一処理システム（FinancialDataProcessor）のみを経由する

```
🚨 重要: 生データの直接使用は厳禁
外部API → FinancialDataProcessor → 正規化データ → 各機能モジュール
```

### 📊 統一データフロー設計

#### レイヤー構成
```
┌─────────────────────────────────────────────────────────┐
│                    UI層 (pages/)                        │
│  ├─ strategy.py (戦略分析)                               │
│  ├─ charts.py (チャート生成)                             │
│  └─ portfolio.py (ポートフォリオ)                        │
└─────────────────┬───────────────────────────────────────┘
                 │ 必ず統一プロセッサ経由
┌─────────────────▼───────────────────────────────────────┐
│              ビジネスロジック層 (core/)                   │
│  ├─ investment_strategies.py                           │
│  ├─ chart_data_manager.py                              │
│  └─ portfolio_manager.py                               │
└─────────────────┬───────────────────────────────────────┘
                 │ 統一正規化処理
┌─────────────────▼───────────────────────────────────────┐
│         統一データ処理層 (必須通過点)                      │
│  financial_data_processor.py                           │
│  ├─ 異常値検出 (配当14k円→24円等)                        │
│  ├─ 単位統一 (70%→7%等)                                 │
│  └─ 欠損値処理 (null→None等)                             │
└─────────────────┬───────────────────────────────────────┘
                 │ 生データ取得のみ
┌─────────────────▼───────────────────────────────────────┐
│              データ取得層 (core/)                        │
│  multi_data_source.py                                  │
│  ├─ Yahoo Finance API                                  │
│  └─ J Quants API                                       │
└─────────────────────────────────────────────────────────┘
```

### 🔧 コアモジュール詳細仕様

#### 1. FinancialDataProcessor（統一データ処理層）
**場所**: `core/financial_data_processor.py`  
**役割**: 全ての金融データの正規化・検証・異常値検出

```python
# ✅ 正しい使用例
processor = FinancialDataProcessor()
normalized_data = processor.process_financial_data(raw_yahoo_data)
dividend_yield = normalized_data.dividend_yield  # 必ず検証済み

# ❌ 禁止パターン
dividend_yield = raw_yahoo_data.get('dividendYield')  # 生データ直接使用
```

**重要責務**:
- ✅ **異常値自動修正**: 配当利回り70% → 7%（単位エラー修正）
- ✅ **範囲検証**: PER<0 → None、配当>1000円 → 修正
- ✅ **警告分類**: 🟡軽微→🟠注意→🔴重大の3段階
- ⚠️ **制約**: 他モジュールによる生データ直接アクセス禁止

**実装例**:
```python
class FinancialDataProcessor:
    def process_financial_data(self, raw_data: dict) -> ProcessedData:
        warnings = []
        
        # 配当利回り正規化
        dividend_yield = raw_data.get('dividendYield', 0)
        if dividend_yield > 50:  # 50%以上は異常値
            warnings.append(Warning(
                level=WarningLevel.CRITICAL,
                message=f"配当利回り異常値: {dividend_yield}% → {dividend_yield/100}%に修正"
            ))
            dividend_yield = dividend_yield / 100
        
        # PER正規化
        pe_ratio = raw_data.get('trailingPE')
        if pe_ratio and pe_ratio < 0:
            warnings.append(Warning(
                level=WarningLevel.WARNING,
                message=f"PER負の値: {pe_ratio} → Noneに変換"
            ))
            pe_ratio = None
        
        return ProcessedData(
            dividend_yield=dividend_yield,
            pe_ratio=pe_ratio,
            warnings=warnings
        )
```

#### 2. MultiDataSourceManager（データ取得層）
**場所**: `core/multi_data_source.py`  
**役割**: 外部APIからの生データ取得のみ

```python
# ✅ 正しい実装
def get_stock_info(self, symbol):
    raw_data = self._fetch_yahoo_data(symbol)  # 生データ取得
    normalized = self.financial_processor.process_financial_data(raw_data)  # 即座に正規化
    return normalized

# ❌ 禁止パターン
def get_stock_info(self, symbol):
    raw_data = self._fetch_yahoo_data(symbol)
    # 独自計算や検証は禁止
    dividend_yield = raw_data.get('dividendYield') * 100  
    return raw_data
```

**Yahoo Finance API対応**:
```python
def _fetch_yahoo_data(self, symbol: str) -> dict:
    """Yahoo Finance APIからの生データ取得"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 必要な生データのみ抽出
        raw_data = {
            'symbol': symbol,
            'dividendYield': info.get('dividendYield'),
            'trailingPE': info.get('trailingPE'),
            'priceToBook': info.get('priceToBook'),
            'currentPrice': info.get('currentPrice') or info.get('regularMarketPrice'),
            'marketCap': info.get('marketCap'),
            'sharesOutstanding': info.get('sharesOutstanding')
        }
        
        return raw_data
        
    except Exception as e:
        logger.error(f"Yahoo Finance API error for {symbol}: {e}")
        raise DataFetchError(f"データ取得失敗: {symbol}")
```

#### 3. InvestmentStrategyAnalyzer（戦略分析層）
**場所**: `core/investment_strategies.py`  
**役割**: 正規化済みデータでの戦略分析のみ

**統一キー仕様**:
```python
# ✅ 必須使用キー（全モジュール共通）
normalized_data = {
    "dividend_yield": 4.5,    # パーセント形式（4.5%）
    "pe_ratio": 12.3,         # 倍率
    "pb_ratio": 0.95,         # 倍率  
    "current_price": 3456.0   # 円
}

# ❌ 禁止キー（旧システム）
legacy_data = {
    "pbr": 0.95,             # pb_ratioを使用すること
    "price": 3456.0,         # current_priceを使用すること
    "pe": 12.3               # pe_ratioを使用すること
}
```

**戦略分析実装例**:
```python
class InvestmentStrategyAnalyzer:
    def analyze_defensive_strategy(self, data: ProcessedData) -> StrategyResult:
        """ディフェンシブ株戦略の分析"""
        score = 0
        criteria_met = []
        
        # 配当利回りチェック（3%以上で加点）
        if data.dividend_yield and data.dividend_yield >= 3.0:
            score += 30
            criteria_met.append(f"高配当: {data.dividend_yield:.1f}%")
        
        # PERチェック（15倍以下で加点）
        if data.pe_ratio and data.pe_ratio <= 15:
            score += 25
            criteria_met.append(f"割安PER: {data.pe_ratio:.1f}倍")
        
        # PBRチェック（1倍以下で加点）
        if data.pb_ratio and data.pb_ratio <= 1.0:
            score += 25
            criteria_met.append(f"割安PBR: {data.pb_ratio:.2f}倍")
        
        return StrategyResult(
            strategy_name="ディフェンシブ株戦略",
            score=score,
            max_score=100,
            criteria_met=criteria_met,
            recommendation=self._generate_recommendation(score)
        )
```

#### 4. ChartDataManager（チャート生成層）
**場所**: `core/chart_data_manager.py`  
**役割**: 統一プロセッサ経由でのチャート用データ処理

**配当データ処理仕様**:
```python
# ✅ 正しい配当処理フロー
def create_dividend_chart(self, symbols):
    for symbol in symbols:
        # 1. 生データ取得
        raw_dividends = ticker.dividends
        
        # 2. 空の場合は代替計算
        if raw_dividends.empty:
            dividend_yield = info.get('dividendYield')
            annual_dividend = (dividend_yield / 100) * current_price
        
        # 3. 統一プロセッサで検証
        if 1 <= annual_dividend <= 1000:  # 合理的範囲
            validated_dividends.append(annual_dividend)
        else:
            corrected = annual_dividend / 100  # 単位エラー修正
```

**Plotlyチャート生成例**:
```python
def generate_dividend_comparison_chart(self, stock_data_list: List[ProcessedData]) -> go.Figure:
    """配当比較チャートの生成"""
    fig = go.Figure()
    
    for data in stock_data_list:
        if data.dividend_history:
            fig.add_trace(go.Scatter(
                x=data.dividend_history.index,
                y=data.dividend_history.values,
                mode='lines+markers',
                name=data.symbol,
                hovertemplate='%{x}<br>配当: ¥%{y:.0f}<extra></extra>'
            ))
    
    fig.update_layout(
        title="配当推移比較",
        xaxis_title="年度",
        yaxis_title="年間配当額（円）",
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    return fig
```

### ⚠️ 設計違反パターンと対策

#### 違反パターン1: 複数計算式の混在
```python
# ❌ 危険: 2つの計算式が存在
def calc_dividend_yield_a(dividend, price):
    return (dividend / price) * 100

def calc_dividend_yield_b(dividend_yield_raw):
    return dividend_yield_raw / 100

# 結果: 同じ銘柄で4.5%と450%の表示

# ✅ 解決: 統一プロセッサのみ使用
processor = FinancialDataProcessor()
normalized = processor.process_financial_data(raw_data)
yield = normalized.dividend_yield  # 唯一の正解値
```

#### 違反パターン2: 生データの直接使用
```python
# ❌ 危険: Yahoo Finance生データ直接使用
info = ticker.info
dividend_yield = info.get('dividendYield')  # 70.0（異常値の可能性）
chart_y_axis = dividend_yield * price       # 14,000円表示

# ✅ 解決: 統一プロセッサ経由
processor = FinancialDataProcessor()
normalized = processor.process_financial_data(info)
dividend_yield = normalized.dividend_yield  # 7.0（修正済み）
```

#### 違反パターン3: データキーの不統一
```python
# ❌ 危険: モジュールごとに異なるキー
# strategy.py
analysis_data = {"pbr": 1.2, "per": 15.0}

# chart.py  
chart_data = {"pb_ratio": 1.2, "pe_ratio": 15.0}

# 結果: データが見つからず0点表示

# ✅ 解決: 統一キー使用
unified_data = {
    "pb_ratio": 1.2,    # 全モジュール共通
    "pe_ratio": 15.0    # 全モジュール共通
}
```

### 🚨 データ整合性チェックシステム

#### 開発時必須チェックリスト

**新機能追加時**:
- [ ] `FinancialDataProcessor.process_financial_data()`を使用しているか？
- [ ] 統一キー（`dividend_yield`, `pe_ratio`, `pb_ratio`）を使用しているか？
- [ ] 独自の財務計算コードを書いていないか？
- [ ] 生データ（`info.get('dividendYield')`等）を直接使用していないか？

**バグ修正時**:
- [ ] 同じ計算を行う関数が複数存在していないか？
- [ ] 異常値（配当14k円、利回り70%等）が表示されていないか？
- [ ] エラーログで「データなし」「0点」が頻出していないか？

**リファクタリング時**:
- [ ] 全てのデータフローが統一アーキテクチャ図に準拠しているか？
- [ ] 各モジュールの責務分離が明確か？
- [ ] テストケースで異常値検出が正常動作しているか？

### 📋 モジュール間依存関係マップ

```
pages/strategy.py
│
├─→ core/investment_strategies.py
│   └─→ core/financial_data_processor.py ★
│
├─→ core/multi_data_source.py  
│   └─→ core/financial_data_processor.py ★
│
└─→ core/chart_data_manager.py
    └─→ core/financial_data_processor.py ★

★ = 必須依存（統一処理層）
```

**重要制約**:
- `financial_data_processor.py`は他モジュールに依存してはならない
- UI層(`pages/`)は統一プロセッサに直接依存してはならない
- 全ての金融計算は統一プロセッサ内でのみ実行

### 📁 詳細ファイル構造

```
J_Stock_Streamlit/
├── app.py                           # Streamlitメインエントリ
├── pages/                           # UI層（統一プロセッサ間接使用）
│   ├── strategy.py                  # 戦略分析画面
│   ├── charts.py                    # 配当チャート画面  
│   ├── portfolio.py                 # ポートフォリオ管理
│   └── watchlist.py                 # 監視リスト管理
├── core/                            # ビジネスロジック層
│   ├── financial_data_processor.py  # ★統一データ処理（依存なし）
│   ├── multi_data_source.py         # データ取得→統一プロセッサ
│   ├── investment_strategies.py     # 戦略分析→統一プロセッサ
│   ├── chart_data_manager.py        # チャート→統一プロセッサ
│   ├── portfolio_manager.py         # ポートフォリオ→統一プロセッサ
│   ├── csv_parser.py               # CSV解析（SBI・楽天）
│   ├── api_cache.py                # APIキャッシュ管理
│   └── data_source_selector.py     # データソース選択
├── cache/                          # APIキャッシュファイル
├── requirements.txt                # 依存ライブラリ
├── streamlit_config.toml          # Streamlit設定
└── CLAUDE.md                      # 開発仕様書（本ファイル）
```

### 🔄 典型的なデータ処理フロー例

#### 投資戦略分析の完全フロー
```
1. ユーザー操作: pages/strategy.py で分析実行
   ↓
2. 銘柄データ取得: MultiDataSourceManager.get_stock_info(symbol)
   ├─ Yahoo Finance API → 生データ取得
   └─ raw_data = {"dividendYield": 70.0, "trailingPE": 12.5, ...}
   ↓
3. 統一正規化処理: FinancialDataProcessor.process_financial_data(raw_data)
   ├─ 異常値検出: dividendYield=70.0 → 異常（>50%）
   ├─ 自動修正: 70.0 → 7.0 (単位エラー修正)
   └─ normalized_data = {"dividend_yield": 7.0, "pe_ratio": 12.5, ...}
   ↓
4. 戦略ルール適用: InvestmentStrategyAnalyzer.analyze_stock(normalized_data)
   ├─ ディフェンシブ戦略: 配当7.0% ≥ 3.0% → ✅
   ├─ PER判定: 12.5 ≤ 15.0 → ✅  
   └─ 総合スコア: 85点
   ↓
5. UI表示: pages/strategy.py で結果表示
```

#### 配当チャート生成の完全フロー
```
1. ユーザー操作: pages/charts.py で配当チャート要求
   ↓
2. 配当履歴取得: ChartDataManager.get_dividend_history(symbol)
   ├─ ticker.dividends → 空データ
   └─ 代替手段: 配当利回り×株価 → 年間配当額計算
   ↓
3. 統一検証処理: FinancialDataProcessor検証ルール適用
   ├─ 年間配当2,404円 → 異常（>1000円）
   ├─ 自動修正: 2,404 → 24.04 (100で除算)
   └─ validated_dividend = 24.04円
   ↓
4. チャート描画: Plotlyで正規化済み配当データを表示
   └─ Y軸: 24円（現実的な値）
```

### 💡 将来の拡張指針

#### 新機能追加時の設計原則
1. **統一プロセッサ原則**: 全ての金融計算は`FinancialDataProcessor`内で実装
2. **単一責任原則**: 各モジュールは明確に分離された責務のみ
3. **依存逆転原則**: UI層は統一プロセッサに直接依存せず、ビジネスロジック層経由

#### 作り直し判断基準
以下の症状が3つ以上該当する場合、アーキテクチャ再設計を検討：
- [ ] 同じ財務計算が複数箇所に存在
- [ ] 異常値（14k円配当等）が頻繁に表示
- [ ] 戦略分析が頻繁に0点表示
- [ ] モジュール間でデータキーが不統一
- [ ] 統一プロセッサをバイパスする処理が存在

#### 緊急時の対処法
```bash
# 統一プロセッサのバイパスを検出
grep -r "dividendYield\|trailingPE\|priceToBook" --include="*.py" .
grep -r "info\.get\|ticker\.info" --include="*.py" .

# 複数の計算式を検出  
grep -r "dividend.*yield.*=" --include="*.py" .
grep -r "\* 100\|/ 100" --include="*.py" .
```

## 📱 Streamlit Web UI 詳細仕様

### 🎨 画面構成・レイアウト設計

#### メインナビゲーション構造
```
app.py (メインエントリポイント)
├── サイドバー固定ナビゲーション
│   ├── 📊 ポートフォリオ管理 (portfolio.py)
│   ├── 👀 監視リスト (watchlist.py)  
│   ├── 🎯 投資戦略分析 (strategy.py)
│   ├── 📈 配当チャート (charts.py)
│   └── 🔧 API設定・状況 (api_status.py)
└── メインコンテンツエリア
    ├── ページヘッダー (タイトル・説明)
    ├── 機能別UI (各ページ固有)
    ├── データ表示エリア
    └── フッター・バージョン情報
```

#### レスポンシブデザイン仕様
```python
# 画面幅対応設定
st.set_page_config(
    page_title="日本株ウォッチドッグ",
    page_icon="📊",
    layout="wide",           # ワイドレイアウト（推奨）
    initial_sidebar_state="expanded"  # サイドバー展開
)

# 3カラムレイアウト（推奨パターン）
col1, col2, col3 = st.columns([1, 2, 1])  # 左:中央:右 = 1:2:1
col1, col2, col3 = st.columns([3, 1, 3])  # 均等3分割

# タブレット・スマートフォン対応
with st.container():
    # モバイル時は縦スタック、デスクトップ時は横並び
    if st.session_state.get('mobile_view', False):
        # 縦スタック表示
    else:
        # 横並び表示
```

### 🔧 Streamlit セッション管理詳細

#### st.session_state 設計仕様
```python
# セッション状態の標準化設計
st.session_state = {
    # === コアデータ ===
    'portfolio_data': pd.DataFrame,          # ポートフォリオCSVデータ
    'watchlist': List[Dict],                 # 監視リスト
    'csv_loaded': bool,                      # CSV読み込み状態
    'data_source_manager': MultiDataSourceManager,  # データソースマネージャー
    
    # === UI状態管理 ===
    'current_page': str,                     # 現在のページ
    'last_update_time': datetime,            # 最終更新時刻
    'api_error_count': int,                  # APIエラー回数
    'cache_status': Dict[str, Any],          # キャッシュ状況
    
    # === 分析結果キャッシュ ===
    'investment_advice': Dict[str, Any],     # 投資アドバイス結果
    'strategy_analysis_results': Dict,       # 戦略分析結果  
    'chart_data_cache': Dict[str, Any],      # チャートデータキャッシュ
    
    # === ユーザー設定 ===
    'show_debug_info': bool,                 # デバッグ情報表示
    'preferred_currency': str,               # 通貨設定（JPY固定）
    'chart_theme': str,                      # チャートテーマ
    'api_timeout': int,                      # APIタイムアウト設定
}
```

#### セッション初期化パターン
```python
def initialize_session_state():
    """セッション状態の安全な初期化"""
    defaults = {
        'portfolio_data': pd.DataFrame(),
        'watchlist': [],
        'csv_loaded': False,
        'current_page': 'portfolio',
        'last_update_time': datetime.now(),
        'api_error_count': 0
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
```

### 📊 UI コンポーネント標準仕様

#### 1. データ表示コンポーネント

**メトリクス表示（推奨パターン）**
```python
# 3列メトリクス（標準）
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="総評価額", 
        value="¥1,234,567", 
        delta="¥56,789 (+4.8%)",
        delta_color="normal"
    )
```

**データテーブル表示（大量データ対応）**
```python
# パフォーマンス最適化されたテーブル
st.dataframe(
    data=portfolio_df,
    use_container_width=True,    # 幅自動調整
    hide_index=True,             # インデックス非表示
    height=400,                  # スクロール対応
    column_config={              # 列設定
        "評価額": st.column_config.NumberColumn(
            "評価額", format="¥%d"
        ),
        "変動率": st.column_config.ProgressColumn(
            "変動率", min_value=-100, max_value=100
        )
    }
)
```

#### 2. 入力コンポーネント

**ファイルアップロード（CSV対応）**
```python
uploaded_file = st.file_uploader(
    "CSVファイルを選択",
    type=['csv'],
    help="SBI証券・楽天証券のポートフォリオCSVに対応",
    accept_multiple_files=False,
    key="portfolio_csv_upload"
)

# プログレスバー表示
if uploaded_file:
    progress_bar = st.progress(0)
    for i in range(100):
        progress_bar.progress(i + 1)
        time.sleep(0.01)
```

**銘柄選択UI（マルチセレクト）**
```python
# 動的オプション生成
available_stocks = get_available_stocks()
selected_stocks = st.multiselect(
    "分析対象銘柄を選択",
    options=available_stocks,
    default=available_stocks[:3],  # デフォルト3銘柄
    help="APIトークン制限のため、3銘柄以下推奨",
    key="stock_selection"
)
```

#### 3. チャート・可視化コンポーネント

**Plotly統合チャート**
```python
# インタラクティブチャート（推奨）
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df['date'],
    y=df['price'],
    mode='lines+markers',
    name='株価',
    hovertemplate='日付: %{x}<br>株価: ¥%{y:,.0f}<extra></extra>'
))

fig.update_layout(
    title="株価推移チャート",
    xaxis_title="日付",
    yaxis_title="株価（円）",
    hovermode='x unified',
    template='plotly_white',    # 統一テーマ
    showlegend=True,
    height=500                  # 固定高さ
)

st.plotly_chart(fig, use_container_width=True)
```

**エラー・警告表示パターン**
```python
# 段階的アラート表示
if critical_errors:
    st.error("🔴 重大なデータエラーが検出されました")
    with st.expander("詳細エラー情報"):
        for error in critical_errors:
            st.text(error)

elif warnings:
    st.warning("🟠 データに注意点があります")
    
elif minor_issues:
    st.info("🟡 軽微な問題が検出されました")
    
else:
    st.success("✅ データ検証完了")
```

### 🔄 ページ間ナビゲーション・状態管理

#### ページ切り替え処理
```python
def handle_page_navigation():
    """ページ切り替え時の状態管理"""
    
    # 前ページの状態保存
    if 'current_page' in st.session_state:
        previous_page = st.session_state.current_page
        # ページ固有データの保存処理
        save_page_state(previous_page)
    
    # 新ページの状態復元
    current_page = st.session_state.get('current_page', 'portfolio')
    restore_page_state(current_page)
    
    # ページ間データ連携
    sync_cross_page_data()
```

#### データ永続化戦略
```python
# 一時的データ（セッション内のみ）
st.session_state.temp_analysis_results = analysis_data

# 半永続的データ（ブラウザキャッシュ活用）
@st.cache_data(ttl=3600)  # 1時間キャッシュ
def get_market_data(symbol):
    return fetch_stock_data(symbol)

# 設定データ（ローカルストレージ活用）
def save_user_preferences(preferences):
    # ブラウザのlocalStorageに保存
    st.components.v1.html(f"""
    <script>
        localStorage.setItem('user_prefs', '{json.dumps(preferences)}');
    </script>
    """, height=0)
```

### 🎛️ サイドバー詳細設計

#### 固定サイドバー構成
```python
def render_sidebar():
    """統一サイドバーレンダリング"""
    
    with st.sidebar:
        # === ヘッダー部分 ===
        st.title("📊 日本株ウォッチドッグ")
        st.caption("v0.3.0 - 統一データ処理対応")
        
        # === ナビゲーションメニュー ===
        page = st.radio(
            "メニュー",
            options=["📊 ポートフォリオ", "👀 監視リスト", "🎯 戦略分析", "📈 チャート", "🔧 設定"],
            key="navigation_radio"
        )
        
        st.divider()
        
        # === 現在の状況表示 ===
        st.subheader("📈 現在の状況")
        
        # データソース状況
        data_source_status = get_data_source_status()
        st.metric("データソース", data_source_status['name'], 
                 delta=data_source_status['status'])
        
        # API制限状況
        api_usage = get_api_usage_status()
        st.progress(api_usage['used'] / api_usage['limit'])
        st.caption(f"API使用量: {api_usage['used']}/{api_usage['limit']}")
        
        # === クイックアクション ===
        st.subheader("⚡ クイックアクション")
        
        if st.button("🔄 データ更新", use_container_width=True):
            refresh_all_data()
            
        if st.button("📊 全銘柄分析", use_container_width=True):
            run_full_analysis()
            
        # === フッター情報 ===
        st.divider()
        st.caption("⚠️ 学習・研究専用ツール")
        st.caption("投資判断は自己責任で")
        
        # === デバッグ情報（開発時） ===
        if st.session_state.get('show_debug_info', False):
            with st.expander("🔧 デバッグ情報"):
                st.json(st.session_state)
```

### 🚀 パフォーマンス最適化

#### キャッシュ戦略
```python
# === データキャッシュ階層 ===

# レベル1: セッションキャッシュ（最速）
@st.cache_data(ttl=300)  # 5分
def get_stock_price_cached(symbol):
    return fetch_stock_price(symbol)

# レベル2: メモリキャッシュ（高速）  
@st.cache_data(ttl=900)  # 15分
def get_financial_data_cached(symbol):
    return fetch_financial_data(symbol)

# レベル3: ディスクキャッシュ（API制限対応）
@st.cache_data(ttl=3600, persist="disk")  # 1時間、ディスク保存
def get_historical_data_cached(symbol, years):
    return fetch_historical_data(symbol, years)

# キャッシュクリア戦略
def clear_selective_cache():
    """選択的キャッシュクリア"""
    if st.button("💨 価格データクリア"):
        get_stock_price_cached.clear()
    
    if st.button("🧹 全キャッシュクリア"):
        st.cache_data.clear()
```

#### 大量データ処理最適化
```python
def optimize_large_dataset_display():
    """大量データ表示最適化"""
    
    # データ分割表示
    data_size = len(portfolio_df)
    page_size = 50
    
    if data_size > page_size:
        # ページネーション実装
        pages = (data_size + page_size - 1) // page_size
        page_number = st.selectbox("ページ", range(1, pages + 1))
        
        start_idx = (page_number - 1) * page_size
        end_idx = min(start_idx + page_size, data_size)
        
        display_data = portfolio_df.iloc[start_idx:end_idx]
    else:
        display_data = portfolio_df
    
    # 仮想化テーブル（大量データ対応）
    st.dataframe(
        display_data,
        use_container_width=True,
        height=min(400, len(display_data) * 35 + 100)  # 動的高さ
    )
```

### 🔒 セキュリティ・プライバシー対応

#### データ保護設計
```python
def implement_data_protection():
    """データ保護機能実装"""
    
    # === 一時ファイル自動削除 ===
    @atexit.register
    def cleanup_temp_files():
        temp_dir = tempfile.gettempdir()
        for file in glob.glob(os.path.join(temp_dir, "streamlit_*")):
            try:
                os.remove(file)
            except:
                pass
    
    # === セッション情報の暗号化 ===
    def encrypt_session_data(data):
        key = os.environ.get('SESSION_ENCRYPTION_KEY', 'default_key')
        # 簡易暗号化（本番環境では強化必要）
        return base64.b64encode(str(data).encode()).decode()
    
    # === API制限保護 ===
    def rate_limit_protection():
        current_time = time.time()
        request_history = st.session_state.get('api_requests', [])
        
        # 過去1時間のリクエスト数チェック
        recent_requests = [req for req in request_history 
                          if current_time - req < 3600]
        
        if len(recent_requests) > 100:  # 1時間100リクエスト制限
            st.error("⚠️ API制限に達しました。1時間後に再試行してください。")
            return False
        
        return True
```

## 🔧 実装ガイドライン

### 品質向上の改善提案

#### 1. エラーバウンダリー実装
```python
from contextlib import contextmanager
import logging

@contextmanager
def error_boundary(operation_name: str):
    """エラー境界コンテキストマネージャー"""
    try:
        yield
    except DataFetchError as e:
        logger.error(f"{operation_name}: データ取得エラー - {e}")
        st.error(f"データ取得エラー: {e}")
        # 自動リカバリー：キャッシュデータ使用
        if cached_data := get_cached_data(operation_name):
            st.info("キャッシュデータを使用します")
            return cached_data
    except ValidationError as e:
        logger.error(f"{operation_name}: 検証エラー - {e}")
        st.warning(f"データ検証エラー: {e}")
    except Exception as e:
        logger.error(f"{operation_name}: 予期しないエラー - {e}")
        st.error(f"処理エラーが発生しました")
        # エラー詳細をデバッグモードで表示
        if st.session_state.get('show_debug_info', False):
            st.exception(e)
```

#### 2. プログレッシブエンハンスメント
```python
def render_chart_with_fallback(data: pd.DataFrame):
    """段階的機能拡張によるチャート表示"""
    
    # 高機能チャート（Plotly）が利用可能な場合
    if advanced_features_available():
        try:
            fig = create_interactive_plotly_chart(data)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.warning(f"Plotlyチャート生成失敗: {e}")
            # フォールバック：基本チャート
            render_basic_chart(data)
    else:
        # 基本チャート（matplotlib）
        render_basic_chart(data)

def render_basic_chart(data: pd.DataFrame):
    """基本的なチャート表示（フォールバック）"""
    st.line_chart(data)
```

#### 3. 型安全性の強化
```python
from typing import TypedDict, Optional, List
from decimal import Decimal
from enum import Enum

class WarningLevel(Enum):
    MINOR = "🟡"
    WARNING = "🟠"
    CRITICAL = "🔴"

class NormalizedStockData(TypedDict):
    symbol: str
    dividend_yield: Optional[Decimal]
    pe_ratio: Optional[Decimal]
    pb_ratio: Optional[Decimal]
    current_price: Decimal
    warnings: List['DataWarning']

class DataWarning(TypedDict):
    level: WarningLevel
    field: str
    message: str
    original_value: Any
    corrected_value: Any

def process_with_type_safety(raw_data: dict) -> NormalizedStockData:
    """型安全なデータ処理"""
    result: NormalizedStockData = {
        'symbol': str(raw_data.get('symbol', '')),
        'dividend_yield': None,
        'pe_ratio': None,
        'pb_ratio': None,
        'current_price': Decimal('0'),
        'warnings': []
    }
    
    # 型安全な変換処理
    if div_yield := raw_data.get('dividendYield'):
        try:
            result['dividend_yield'] = Decimal(str(div_yield))
        except (ValueError, TypeError):
            result['warnings'].append({
                'level': WarningLevel.WARNING,
                'field': 'dividend_yield',
                'message': '配当利回り変換エラー',
                'original_value': div_yield,
                'corrected_value': None
            })
    
    return result
```

#### 4. 監視・アラート機能
```python
import asyncio
from datetime import datetime, timedelta

class MarketAnomalyDetector:
    """市場異常検知システム"""
    
    def __init__(self):
        self.alert_threshold = {
            'price_change': 0.1,  # 10%以上の価格変動
            'volume_spike': 3.0,  # 通常の3倍以上の出来高
            'dividend_cut': 0.5   # 配当50%以上カット
        }
    
    async def monitor_portfolio(self, portfolio: List[str]):
        """ポートフォリオの異常監視"""
        while True:
            anomalies = []
            
            for symbol in portfolio:
                if anomaly := await self.check_anomaly(symbol):
                    anomalies.append(anomaly)
            
            if anomalies:
                await self.send_alerts(anomalies)
            
            # 5分間隔でチェック
            await asyncio.sleep(300)
    
    async def check_anomaly(self, symbol: str) -> Optional[dict]:
        """個別銘柄の異常チェック"""
        try:
            current_data = await self.fetch_current_data(symbol)
            historical_data = await self.fetch_historical_data(symbol)
            
            # 価格変動チェック
            price_change = abs(
                (current_data['price'] - historical_data['price']) / 
                historical_data['price']
            )
            
            if price_change > self.alert_threshold['price_change']:
                return {
                    'symbol': symbol,
                    'type': 'price_anomaly',
                    'severity': 'high' if price_change > 0.2 else 'medium',
                    'message': f"{symbol}: {price_change:.1%}の価格変動検出"
                }
            
        except Exception as e:
            logger.error(f"異常検知エラー {symbol}: {e}")
        
        return None
    
    async def send_alerts(self, anomalies: List[dict]):
        """アラート送信"""
        # Slack通知（実装例）
        for anomaly in anomalies:
            if anomaly['severity'] == 'high':
                await send_slack_notification(
                    f"🚨 {anomaly['message']}"
                )
        
        # UI表示
        st.session_state['market_alerts'] = anomalies
```

#### 5. A/Bテスト基盤
```python
import hashlib
from typing import Dict, Any

class FeatureFlagManager:
    """機能フラグによる段階的リリース管理"""
    
    def __init__(self):
        self.feature_configs = {
            'new_chart_engine': {
                'rollout_percentage': 20,
                'description': '新しいチャートエンジン'
            },
            'ai_analysis': {
                'rollout_percentage': 5,
                'description': 'AI投資分析機能'
            },
            'real_time_alerts': {
                'rollout_percentage': 50,
                'description': 'リアルタイムアラート'
            }
        }
    
    def is_feature_enabled(self, feature_name: str, user_id: str) -> bool:
        """機能フラグの有効判定"""
        if feature_name not in self.feature_configs:
            return False
        
        config = self.feature_configs[feature_name]
        rollout_percentage = config['rollout_percentage']
        
        # ユーザーIDと機能名のハッシュで決定的な割り当て
        hash_input = f"{feature_name}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        user_bucket = hash_value % 100
        
        return user_bucket < rollout_percentage
    
    def get_variant(self, experiment_name: str, user_id: str) -> str:
        """A/Bテストのバリアント取得"""
        variants = {
            'chart_layout': ['control', 'variant_a', 'variant_b'],
            'portfolio_view': ['table', 'card', 'hybrid']
        }
        
        if experiment_name not in variants:
            return 'control'
        
        options = variants[experiment_name]
        hash_input = f"{experiment_name}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        return options[hash_value % len(options)]

# 使用例
feature_flags = FeatureFlagManager()
user_id = st.session_state.get('user_id', 'anonymous')

if feature_flags.is_feature_enabled('new_chart_engine', user_id):
    # 新しいチャートエンジンを使用
    render_advanced_charts()
else:
    # 従来のチャートエンジン
    render_legacy_charts()

# A/Bテスト
layout_variant = feature_flags.get_variant('portfolio_view', user_id)
if layout_variant == 'card':
    render_card_layout()
elif layout_variant == 'hybrid':
    render_hybrid_layout()
else:
    render_table_layout()
```

### 🧪 テスト戦略

#### 単体テスト
```python
import pytest
from unittest.mock import Mock, patch

class TestFinancialDataProcessor:
    """FinancialDataProcessorの単体テスト"""
    
    def test_dividend_yield_normalization(self):
        """配当利回り正規化テスト"""
        processor = FinancialDataProcessor()
        
        # 異常値ケース（70%）
        raw_data = {'dividendYield': 70.0}
        result = processor.process_financial_data(raw_data)
        
        assert result.dividend_yield == 7.0
        assert len(result.warnings) == 1
        assert result.warnings[0].level == WarningLevel.CRITICAL
    
    def test_negative_per_handling(self):
        """負のPER処理テスト"""
        processor = FinancialDataProcessor()
        
        raw_data = {'trailingPE': -15.5}
        result = processor.process_financial_data(raw_data)
        
        assert result.pe_ratio is None
        assert any(w.field == 'pe_ratio' for w in result.warnings)
    
    @patch('yfinance.Ticker')
    def test_api_error_handling(self, mock_ticker):
        """APIエラーハンドリングテスト"""
        mock_ticker.side_effect = Exception("Network error")
        
        manager = MultiDataSourceManager()
        
        with pytest.raises(DataFetchError):
            manager.get_stock_info("1234.T")
```

#### 統合テスト
```python
class TestDataFlowIntegration:
    """データフロー統合テスト"""
    
    def test_end_to_end_strategy_analysis(self):
        """戦略分析の完全フローテスト"""
        # 1. モックデータ準備
        mock_raw_data = {
            'symbol': '1234.T',
            'dividendYield': 4.5,  # 正常値
            'trailingPE': 12.0,
            'priceToBook': 0.8,
            'currentPrice': 1500
        }
        
        # 2. データ処理
        processor = FinancialDataProcessor()
        normalized = processor.process_financial_data(mock_raw_data)
        
        # 3. 戦略分析
        analyzer = InvestmentStrategyAnalyzer()
        result = analyzer.analyze_defensive_strategy(normalized)
        
        # 4. 検証
        assert result.score >= 70  # 高得点期待
        assert "高配当" in str(result.criteria_met)
        assert len(normalized.warnings) == 0  # 警告なし
```

### 📊 実運用・モニタリング

#### パフォーマンス監視実装
```python
import time
from functools import wraps

def performance_monitor(operation_name: str):
    """パフォーマンス監視デコレータ"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # パフォーマンス記録
                record_performance(
                    operation=operation_name,
                    duration=execution_time,
                    status='success'
                )
                
                # 遅い処理の警告
                if execution_time > 5.0:
                    st.warning(
                        f"⚠️ {operation_name}に"
                        f"{execution_time:.1f}秒かかりました"
                    )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                record_performance(
                    operation=operation_name,
                    duration=execution_time,
                    status='error',
                    error=str(e)
                )
                raise
        
        return wrapper
    return decorator

@performance_monitor("株価データ取得")
def fetch_stock_prices(symbols: List[str]) -> pd.DataFrame:
    """株価データ取得（監視付き）"""
    # 実装
    pass
```

#### エラー追跡システム
```python
import logging
import traceback
from datetime import datetime

class ErrorTracker:
    """エラー追跡・分析システム"""
    
    def __init__(self):
        self.error_history = []
        self.setup_logging()
    
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('app.log', encoding='utf-8'),
                # 本番環境ではCloudWatchやSentryへ送信
            ]
        )
    
    def track_error(self, error: Exception, context: dict = None):
        """エラー追跡"""
        error_info = {
            'timestamp': datetime.now(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'session_id': st.session_state.get('session_id'),
            'user_action': st.session_state.get('last_action')
        }
        
        self.error_history.append(error_info)
        logging.error(f"エラー発生: {error_info}")
        
        # エラー頻度分析
        self.analyze_error_patterns()
    
    def analyze_error_patterns(self):
        """エラーパターン分析"""
        if len(self.error_history) < 10:
            return
        
        # 直近のエラーを分析
        recent_errors = self.error_history[-10:]
        error_types = [e['error_type'] for e in recent_errors]
        
        # 同じエラーが頻発している場合
        if error_types.count(error_types[0]) > 5:
            st.error(
                f"⚠️ システムエラーが頻発しています。"
                f"サポートにお問い合わせください。"
            )
            # 管理者に通知
            self.notify_admin(error_types[0])
```

## 重要な実装ノート

### セキュリティ
- API認証情報なし（Yahoo Finance APIは無料・認証不要）
- 一時ファイルの適切な削除
- セッションデータの適切な管理

### データソース
- **Yahoo Finance API**: 株価・配当・財務データ（primary）
- **無料制限**: 1日約2000リクエスト
- **データ精度**: 99%程度

### Web版特有の考慮事項
- **セッション管理**: ブラウザ閉じると消失
- **ファイルアップロード**: 一時ファイル処理
- **API制限**: 複数ユーザーでの制限共有

## 開発ガイドライン

### 環境管理
- **仮想環境**: venv 使用推奨
- **依存関係**: requirements.txt で管理
- **Python**: 3.8+ 対応

### コーディング規約
- **文字エンコーディング**: UTF-8内部処理、CSV I/O時のみ変換
- **エラーハンドリング**: API制限・ネットワークエラーへの対応
- **セッション管理**: st.session_state の適切な利用
- **一時ファイル**: 適切な作成・削除

### パフォーマンス
- **API制限**: レート制限内での利用
- **キャッシュ**: 同一銘柄の重複取得回避
- **並列処理**: 複数銘柄の効率的取得

## トラブルシューティング

### よくある問題

1. **Streamlit起動エラー**:
   ```bash
   pip install --upgrade streamlit
   streamlit --version
   ```

2. **Yahoo Finance API エラー**:
   - ネットワーク接続確認
   - API制限チェック（1日2000リクエスト）
   - 銘柄コード形式確認（日本株: 4桁+.T、米国株: ティッカー）

3. **CSV読み込みエラー**:
   - ファイル形式確認（SBI・楽天証券対応）
   - エンコーディング確認（Shift-JIS、UTF-8、cp932）
   - ファイルサイズ確認（200MB制限）

4. **ブラウザ表示エラー**:
   ```bash
   # キャッシュクリア
   streamlit cache clear
   
   # ポート変更
   streamlit run app.py --server.port 8502
   ```

## 最新バージョン (v0.3.0)

### 主要機能（デスクトップ版移植）
- ✅ SBI・楽天証券CSV解析（完全互換）
- ✅ 投資アドバイス機能（利確15%・損切-8%）
- ✅ 監視リスト・欲しい銘柄管理
- ✅ 戦略分析（実データ連携・Yahoo Finance API）
- ✅ 配当チャート（4種類・期間選択）

### Web版独自機能
- ✅ ブラウザ完結（インストール不要）
- ✅ レスポンシブデザイン
- ✅ リアルタイム株価取得
- ✅ インタラクティブチャート（Plotly）

### v0.3.0 包括的ロバストネス向上
- 🎯 **段階的警告システム**: 🟡軽微→🟠注意→🔴重大の3段階警告
- 📊 **ROE異常値検出**: >100%、<-100%の範囲チェック
- 🏢 **時価総額整合性**: 株価×発行済株式数の整合性検証
- 📈 **出来高異常検出**: 回転率分析、取引停止検出
- 🛡️ **投資判断信頼性**: データエラー・市場異常の事前検出
- ✅ **実銘柄検証**: 積水ハウス他5銘柄で正常動作確認

### v0.2.2 重要修正（継承）
- 🔥 **配当利回り計算バグ修正**: 477% → 4.77%（積水ハウス1928で確認）
- 🛡️ **財務指標異常値検出**: 配当利回り≥100%、PER<0/>1000、PBR<0/>50、株価≤0
- 🔧 **Yahoo Finance API対応**: dividendYieldは既にパーセント形式
- ✅ **投資判断ロジック強化**: 損切・利確判断の根拠データ品質向上

### 方針継承（デスクトップ版）
**投資システム → 学習ツール**
- 投資推奨機能は学習目的のみ
- 教育的コンテンツの強化
- リスク警告の明確化

## 開発優先度

### 🔥 高優先（v0.1.0）
- 配当チャート実データ完全連携
- エラーハンドリング強化
- API制限対応改善

### ⚡ 中優先（v0.2.0）
- キャッシュ機能（重複API回避）
- J Quants API連携
- バッチ処理（高速化）

### 🚀 低優先（v1.0.0+）
- ユーザー認証・データ保存
- カスタム戦略作成
- 高度な統計分析

## デプロイメント

### ローカル実行
```bash
streamlit run app.py
```

### Streamlit Cloud（将来）
- GitHub連携
- 自動デプロイ
- 無料ホスティング

---

## 🎯 プロジェクト哲学（デスクトップ版継承）

- **オルカン投資**: 合理的最適解
- **このツール**: 学習プロセス・知的好奇心の探求
- **目標**: 技術・金融・分析スキルの習得

**Web版の付加価値**:
- **アクセシビリティ**: どこでも・誰でも利用可能
- **リアルタイム性**: 最新データでの学習体験
- **インタラクティブ性**: 直感的なデータ探索

### 開発者向けメモ
- デスクトップ版との機能互換性維持
- Web版独自の価値創造
- 学習ツールとしての教育効果最大化