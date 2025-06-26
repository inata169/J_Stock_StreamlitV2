"""
ポートフォリオ管理画面

SBI証券・楽天証券のCSVファイル解析と投資アドバイス機能を提供。
統一プロセッサを経由したリアルタイム株価取得と損益計算。
"""

import streamlit as st
import pandas as pd
import io
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
from decimal import Decimal

# コアモジュールのインポート
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.csv_parser import UnifiedCSVParser

from core.multi_data_source import MultiDataSourceManager, DataFetchError, APIRateLimitError
from core.chart_data_manager import ChartDataManager
from core.financial_data_processor import WarningLevel

# ログ設定
logger = logging.getLogger(__name__)


def initialize_portfolio_page():
    """ポートフォリオページの初期化"""
    if 'data_source_manager' not in st.session_state:
        st.session_state.data_source_manager = MultiDataSourceManager()
    
    if 'chart_manager' not in st.session_state:
        st.session_state.chart_manager = ChartDataManager(st.session_state.data_source_manager)
    
    if 'portfolio_data' not in st.session_state:
        st.session_state.portfolio_data = pd.DataFrame()
    
    if 'csv_loaded' not in st.session_state:
        st.session_state.csv_loaded = False
    
    if 'investment_advice' not in st.session_state:
        st.session_state.investment_advice = {}


def render_portfolio_header():
    """ヘッダー部分のレンダリング"""
    st.title("📊 ポートフォリオ管理")
    st.markdown("""
    **CSV連携による高度なポートフォリオ分析**
    - 📁 **CSV対応**: SBI証券・楽天証券のポートフォリオCSV自動解析
    - 💹 **リアルタイム更新**: Yahoo Finance APIによる最新株価取得
    - 🎯 **投資アドバイス**: 利確15%・損切-8%ルールによる自動判定
    - 📈 **詳細分析**: 配当利回り・PER/PBR・セクター分析
    
    ⚠️ **学習・研究専用ツール** - 投資判断は必ずご自身の責任で行ってください
    """)


def render_csv_upload_section():
    """CSVアップロードセクション"""
    st.subheader("📁 ポートフォリオCSVファイル読み込み")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "CSVファイルを選択してください",
            type=['csv'],
            help="SBI証券・楽天証券のポートフォリオCSVファイルに対応",
            accept_multiple_files=False
        )
    
    with col2:
        st.markdown("**対応形式:**")
        st.markdown("- SBI証券 ポートフォリオ")
        st.markdown("- 楽天証券 保有商品")
        st.markdown("- カスタムCSV")
    
    if uploaded_file is not None:
        try:
            # ファイル読み込み（統一CSVパーサーを使用）
            with st.spinner("📊 CSVファイルを解析中..."):
                csv_parser = UnifiedCSVParser()
                df = csv_parser.parse_csv(uploaded_file.read(), uploaded_file.name)
                
                if not df.empty:
                    st.session_state.portfolio_data = df
                    st.session_state.csv_loaded = True
                    st.success(f"✅ CSVファイルを読み込みました ({len(df)}銘柄)")
                    
                    # 警告情報の表示
                    warnings_count = sum(len(row.get('warnings', [])) for _, row in df.iterrows() if 'warnings' in row)
                    if warnings_count > 0:
                        st.warning(f"⚠️ {warnings_count}件のデータ警告があります")
                    
                    # プレビュー表示
                    with st.expander("📋 読み込み内容プレビュー"):
                        display_df = df[['symbol', 'name', 'quantity', 'average_price']].copy()
                        st.dataframe(display_df.head(), use_container_width=True)
                else:
                    st.error("❌ CSVファイルの解析に失敗しました")
                    
        except Exception as e:
            st.error(f"❌ ファイル読み込みエラー: {str(e)}")
            logger.error(f"CSV upload error: {e}")
    
    # サンプルデータボタン
    if st.button("📋 サンプルデータで試す", help="デモ用のサンプルポートフォリオを読み込み"):
        st.session_state.portfolio_data = create_sample_portfolio()
        st.session_state.csv_loaded = True
        st.success("✅ サンプルポートフォリオを読み込みました")


def parse_csv_file(uploaded_file) -> pd.DataFrame:
    """CSVファイルの解析"""
    try:
        # 複数のエンコーディングを試行
        encodings = ['utf-8', 'shift_jis', 'cp932', 'utf-8-sig']
        
        df = None
        for encoding in encodings:
            try:
                uploaded_file.seek(0)
                content = uploaded_file.read().decode(encoding)
                # エラー処理を追加してCSVを読み込む
                df = pd.read_csv(io.StringIO(content), 
                                on_bad_lines='skip',  # 不正な行をスキップ
                                engine='python')      # より柔軟なパーサーを使用
                
                # デバッグ情報を出力
                logger.info(f"CSV successfully decoded with {encoding}")
                logger.info(f"Original columns: {df.columns.tolist()}")
                logger.info(f"Shape: {df.shape}")
                logger.info(f"First few rows:\n{df.head()}")
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("サポートされていないファイルエンコーディングです")
        
        # 空のDataFrameや無効なデータをスキップ
        if df is None or df.empty:
            raise ValueError("CSVファイルが空か、有効なデータが含まれていません")
        
        # ヘッダー行が含まれている可能性をチェック（楽天証券のケース）
        # 楽天証券のCSVは最初の数行にヘッダー情報があり、実際のデータは後ろにある
        if '保有商品詳細' in str(df.values) or '資産合計' in str(df.values):
            # 楽天証券形式の検出
            logger.info("楽天証券形式のCSVを検出")
            # データ行を探す
            data_start_idx = None
            for idx, row in df.iterrows():
                if any('銘柄コード' in str(cell) or '銘柄コード・ティッカー' in str(cell) for cell in row):
                    data_start_idx = idx
                    break
            
            if data_start_idx is not None:
                # ヘッダー行を新しいカラム名として設定
                df.columns = df.iloc[data_start_idx]
                df = df.iloc[data_start_idx + 1:].reset_index(drop=True)
                logger.info(f"楽天証券: データ開始行 {data_start_idx}, 新しいカラム: {df.columns.tolist()}")
        
        # カラム名の正規化
        df = normalize_csv_columns(df)
        logger.info(f"Normalized columns: {df.columns.tolist()}")
        
        # 必要なカラムの存在確認
        required_columns = ['symbol', 'quantity', 'average_price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.warning(f"⚠️ 一部のカラムが見つかりません: {missing_columns}")
            st.info("検出されたカラム: " + ", ".join(df.columns.tolist()[:10]))  # 最初の10カラムを表示
            st.info("必要なカラム: '銘柄コード'(SBI証券) または '銘柄コード・ティッカー'(楽天証券), '保有数量'/'保有株数', '取得単価'/'平均取得価額'")
            
            # より詳細なデバッグ情報
            with st.expander("詳細なデバッグ情報"):
                st.text("全カラム名:")
                st.text(str(df.columns.tolist()))
                st.text("\n最初の5行:")
                st.dataframe(df.head())
            
            raise KeyError(missing_columns)
        
        # データ型変換
        if 'quantity' in df.columns:
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        if 'average_price' in df.columns:
            df['average_price'] = pd.to_numeric(df['average_price'], errors='coerce')
        
        # 無効行の除去
        df = df.dropna(subset=['symbol'])
        
        # 銘柄コードの正規化（4桁の数字の場合は.Tを追加）
        df['symbol'] = df['symbol'].apply(lambda x: str(x) + '.T' if isinstance(x, (int, float)) or (isinstance(x, str) and x.isdigit() and len(x) == 4) else str(x))
        
        logger.info(f"Successfully parsed {len(df)} rows")
        return df
        
    except Exception as e:
        logger.error(f"CSV parsing error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        raise


def normalize_csv_columns(df: pd.DataFrame) -> pd.DataFrame:
    """CSVカラム名の正規化"""
    # SBI証券・楽天証券の一般的なカラム名マッピング
    column_mapping = {
        # SBI証券（SaveFile 5.csv形式）
        '銘柄コード': 'symbol',
        '銘柄': 'symbol', 
        '保有数量': 'quantity',
        '保有株数': 'quantity',  # SBI証券でも使用
        '数量': 'quantity',
        '平均取得価格': 'average_price',
        '取得価格': 'average_price',
        '取得単価': 'average_price',  # SBI証券で使用
        '評価額': 'market_value',
        '現在価格': 'current_price',
        '現在値': 'current_price',  # SBI証券でも使用
        '銘柄名称': 'name',  # SBI証券で使用
        
        # 楽天証券（assetbalance形式）
        '銘柄コード・ティッカー': 'symbol',  # 楽天証券特有
        'コード': 'symbol',
        '銘柄名': 'name',
        '平均取得価額': 'average_price',  # 楽天証券特有（価額）
        '平均取得単価': 'average_price',
        '評価金額': 'market_value',
        '時価評価額[円]': 'market_value',  # 楽天証券特有
        '［単位］': None,  # 不要なカラムは削除
        
        # 英語
        'Symbol': 'symbol',
        'Code': 'symbol',
        'Quantity': 'quantity',
        'Shares': 'quantity',
        'Average Price': 'average_price',
        'Cost Basis': 'average_price',
        'Market Value': 'market_value',
        'Current Price': 'current_price'
    }
    
    # カラム名を正規化
    df = df.rename(columns=column_mapping)
    
    # Noneにマップされたカラムを削除
    df = df.drop(columns=[col for col in df.columns if col is None], errors='ignore')
    
    return df


def create_sample_portfolio() -> pd.DataFrame:
    """サンプルポートフォリオの作成"""
    sample_data = [
        {'symbol': '1928.T', 'name': '積水ハウス', 'quantity': 100, 'average_price': 2100},
        {'symbol': '7203.T', 'name': 'トヨタ自動車', 'quantity': 50, 'average_price': 2000},
        {'symbol': '6758.T', 'name': 'ソニーグループ', 'quantity': 30, 'average_price': 12000},
        {'symbol': '8316.T', 'name': '三井住友フィナンシャル', 'quantity': 200, 'average_price': 4500},
        {'symbol': 'AAPL', 'name': 'Apple Inc.', 'quantity': 10, 'average_price': 180}
    ]
    
    return pd.DataFrame(sample_data)


def render_portfolio_overview():
    """ポートフォリオ概要表示"""
    if not st.session_state.csv_loaded:
        st.info("👆 上記でCSVファイルを読み込んでください")
        return
    
    portfolio_df = st.session_state.portfolio_data
    
    st.subheader("💼 ポートフォリオ概要")
    
    try:
        with st.spinner("📈 最新データを取得中..."):
            # リアルタイムデータ取得
            symbols = portfolio_df['symbol'].tolist()
            current_data = get_portfolio_realtime_data(symbols)
            
            # 損益計算
            portfolio_with_pnl = calculate_portfolio_pnl(portfolio_df, current_data)
            
            # サマリー表示
            render_portfolio_summary(portfolio_with_pnl)
            
            # 詳細テーブル
            render_portfolio_table(portfolio_with_pnl)
            
            # 投資アドバイス生成
            generate_investment_advice(portfolio_with_pnl)
            
    except Exception as e:
        st.error(f"❌ ポートフォリオ分析エラー: {str(e)}")
        logger.error(f"Portfolio analysis error: {e}")


def get_portfolio_realtime_data(symbols: List[str]) -> Dict[str, Any]:
    """ポートフォリオのリアルタイムデータ取得"""
    data_source = st.session_state.data_source_manager
    return data_source.get_multiple_stocks(symbols, delay_between_requests=0.5)


def calculate_portfolio_pnl(portfolio_df: pd.DataFrame, current_data: Dict[str, Any]) -> pd.DataFrame:
    """ポートフォリオ損益計算"""
    result_data = []
    
    for _, row in portfolio_df.iterrows():
        symbol = row['symbol']
        quantity = row.get('quantity', 0)
        average_price = row.get('average_price', 0)
        
        if symbol in current_data:
            stock_data = current_data[symbol]
            current_price = float(stock_data['current_price']) if stock_data.get('current_price') else average_price
            
            # 損益計算
            book_value = quantity * average_price
            market_value = quantity * current_price
            unrealized_pnl = market_value - book_value
            pnl_percentage = (unrealized_pnl / book_value * 100) if book_value > 0 else 0
            
            # アドバイス判定
            advice = determine_investment_advice(pnl_percentage)
            
            result_data.append({
                'symbol': symbol,
                'name': row.get('name', symbol),
                'quantity': quantity,
                'average_price': average_price,
                'current_price': current_price,
                'book_value': book_value,
                'market_value': market_value,
                'unrealized_pnl': unrealized_pnl,
                'pnl_percentage': pnl_percentage,
                'advice': advice,
                'dividend_yield': float(stock_data['dividend_yield']) if stock_data.get('dividend_yield') else None,
                'pe_ratio': float(stock_data['pe_ratio']) if stock_data.get('pe_ratio') else None,
                'warnings': len(stock_data.get('warnings', []))
            })
        else:
            # データ取得失敗時
            result_data.append({
                'symbol': symbol,
                'name': row.get('name', symbol),
                'quantity': quantity,
                'average_price': average_price,
                'current_price': average_price,  # フォールバック
                'book_value': quantity * average_price,
                'market_value': quantity * average_price,
                'unrealized_pnl': 0,
                'pnl_percentage': 0,
                'advice': '💭 データ取得失敗',
                'dividend_yield': None,
                'pe_ratio': None,
                'warnings': 1
            })
    
    return pd.DataFrame(result_data)


def determine_investment_advice(pnl_percentage: float) -> str:
    """投資アドバイスの判定"""
    if pnl_percentage >= 15:
        return "💰 利確検討"
    elif pnl_percentage <= -8:
        return "🛑 損切検討"
    elif pnl_percentage >= 10:
        return "📈 好調維持"
    elif pnl_percentage <= -5:
        return "⚠️ 注意監視"
    else:
        return "📊 継続保有"


def render_portfolio_summary(portfolio_df: pd.DataFrame):
    """ポートフォリオサマリー表示"""
    col1, col2, col3, col4 = st.columns(4)
    
    total_book_value = portfolio_df['book_value'].sum()
    total_market_value = portfolio_df['market_value'].sum()
    total_pnl = portfolio_df['unrealized_pnl'].sum()
    total_pnl_percentage = (total_pnl / total_book_value * 100) if total_book_value > 0 else 0
    
    with col1:
        st.metric(
            "総取得額",
            f"¥{total_book_value:,.0f}"
        )
    
    with col2:
        st.metric(
            "総評価額",
            f"¥{total_market_value:,.0f}"
        )
    
    with col3:
        st.metric(
            "含み損益",
            f"¥{total_pnl:,.0f}",
            delta=f"{total_pnl_percentage:+.1f}%"
        )
    
    with col4:
        # 銘柄数とアドバイス統計
        profit_count = len(portfolio_df[portfolio_df['pnl_percentage'] > 0])
        loss_count = len(portfolio_df[portfolio_df['pnl_percentage'] < 0])
        st.metric(
            "銘柄構成",
            f"{len(portfolio_df)}銘柄",
            delta=f"利益:{profit_count} 損失:{loss_count}"
        )


def render_portfolio_table(portfolio_df: pd.DataFrame):
    """ポートフォリオ詳細テーブル表示"""
    st.subheader("📋 保有銘柄詳細")
    
    # 表示用データフレーム作成
    display_df = portfolio_df.copy()
    
    # 数値フォーマット
    display_df['平均取得価格'] = display_df['average_price'].apply(lambda x: f"¥{x:,.0f}")
    display_df['現在価格'] = display_df['current_price'].apply(lambda x: f"¥{x:,.0f}")
    display_df['取得額'] = display_df['book_value'].apply(lambda x: f"¥{x:,.0f}")
    display_df['評価額'] = display_df['market_value'].apply(lambda x: f"¥{x:,.0f}")
    display_df['含み損益'] = display_df.apply(
        lambda row: f"¥{row['unrealized_pnl']:+,.0f} ({row['pnl_percentage']:+.1f}%)", axis=1
    )
    
    # 表示カラム選択
    display_columns = [
        'symbol', 'name', 'quantity', '平均取得価格', '現在価格', 
        '取得額', '評価額', '含み損益', 'advice', 'dividend_yield'
    ]
    
    # カラム名マッピング
    column_names = {
        'symbol': '銘柄コード',
        'name': '銘柄名',
        'quantity': '数量',
        'advice': 'アドバイス',
        'dividend_yield': '配当利回り(%)'
    }
    
    final_df = display_df[display_columns].rename(columns=column_names)
    
    # カラー設定付きでテーブル表示
    def color_pnl(val):
        if '利確' in str(val):
            return 'background-color: #d4edda; color: #155724'
        elif '損切' in str(val):
            return 'background-color: #f8d7da; color: #721c24'
        elif '好調' in str(val):
            return 'background-color: #cce5ff; color: #004080'
        elif '注意' in str(val):
            return 'background-color: #fff3cd; color: #856404'
        return ''
    
    styled_df = final_df.style.applymap(color_pnl, subset=['アドバイス'])
    st.dataframe(styled_df, use_container_width=True)


def generate_investment_advice(portfolio_df: pd.DataFrame):
    """投資アドバイス生成"""
    st.subheader("🎯 投資アドバイス")
    
    # アドバイス統計
    advice_counts = portfolio_df['advice'].value_counts()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 具体的なアドバイス
        profit_stocks = portfolio_df[portfolio_df['advice'] == '💰 利確検討']
        loss_stocks = portfolio_df[portfolio_df['advice'] == '🛑 損切検討']
        
        if not profit_stocks.empty:
            st.success("💰 **利確検討推奨銘柄**")
            for _, stock in profit_stocks.iterrows():
                st.markdown(f"- **{stock['symbol']}** ({stock['name']}): +{stock['pnl_percentage']:.1f}%")
        
        if not loss_stocks.empty:
            st.error("🛑 **損切検討推奨銘柄**")
            for _, stock in loss_stocks.iterrows():
                st.markdown(f"- **{stock['symbol']}** ({stock['name']}): {stock['pnl_percentage']:.1f}%")
        
        if profit_stocks.empty and loss_stocks.empty:
            st.info("📊 現在は売買推奨銘柄はありません。継続保有を推奨します。")
    
    with col2:
        # アドバイス分布
        if len(advice_counts) > 0:
            st.markdown("**アドバイス分布:**")
            for advice, count in advice_counts.items():
                st.markdown(f"- {advice}: {count}銘柄")


def render_portfolio_charts():
    """ポートフォリオチャート表示"""
    if not st.session_state.csv_loaded:
        return
    
    st.subheader("📈 ポートフォリオ可視化")
    
    portfolio_df = st.session_state.portfolio_data
    
    if not portfolio_df.empty:
        try:
            chart_manager = st.session_state.chart_manager
            
            # ポートフォリオ配分円グラフ
            portfolio_data = []
            for _, row in portfolio_df.iterrows():
                portfolio_data.append({
                    'symbol': row['symbol'],
                    'market_value': row.get('quantity', 0) * row.get('average_price', 0)
                })
            
            allocation_chart = chart_manager.create_portfolio_allocation_chart(portfolio_data)
            st.plotly_chart(allocation_chart, use_container_width=True)
            
        except Exception as e:
            st.error(f"チャート生成エラー: {e}")


def render_portfolio_sidebar():
    """サイドバーのポートフォリオ機能"""
    with st.sidebar:
        if st.session_state.csv_loaded:
            st.subheader("💼 ポートフォリオアクション")
            
            # データ更新
            if st.button("🔄 リアルタイム更新", use_container_width=True):
                st.rerun()
            
            # CSVエクスポート
            if st.button("📄 結果をCSVエクスポート", use_container_width=True):
                try:
                    portfolio_df = st.session_state.portfolio_data
                    csv = portfolio_df.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 CSVダウンロード",
                        data=csv,
                        file_name=f"portfolio_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"エクスポートエラー: {e}")
            
            # ポートフォリオクリア
            if st.button("🗑️ ポートフォリオクリア", use_container_width=True):
                st.session_state.portfolio_data = pd.DataFrame()
                st.session_state.csv_loaded = False
                st.success("ポートフォリオをクリアしました")
                st.rerun()


def main():
    """メイン関数"""
    # ページ設定
    st.set_page_config(
        page_title="ポートフォリオ管理 - 日本株ウォッチドッグ",
        page_icon="📊",
        layout="wide"
    )
    
    # 初期化
    initialize_portfolio_page()
    
    # ヘッダー
    render_portfolio_header()
    
    # サイドバー
    render_portfolio_sidebar()
    
    # メインコンテンツ
    render_csv_upload_section()
    render_portfolio_overview()
    render_portfolio_charts()


if __name__ == "__main__":
    main()