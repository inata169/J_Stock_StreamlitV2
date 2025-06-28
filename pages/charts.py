"""
配当チャート画面 v2.0.0

統一データベースアーキテクチャ対応版
- DatabaseManager: チャートデータキャッシュ（任意機能）
- 統一プロセッサ経由の配当データを使用したインタラクティブチャート
- Plotlyを使用した高度な可視化機能を提供
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging
from datetime import datetime

# v2.0.0 新アーキテクチャモジュール
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.database_manager import DatabaseManager
from core.multi_data_source import MultiDataSourceManager, DataFetchError, APIRateLimitError
from core.chart_data_manager import ChartDataManager
from core.financial_data_processor import WarningLevel

# ログ設定
logger = logging.getLogger(__name__)


def initialize_charts_page():
    """チャートページの初期化（v2.0.0対応）"""
    # v2.0.0: データベースマネージャー追加（キャッシュ機能用）
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    if 'data_source_manager' not in st.session_state:
        st.session_state.data_source_manager = MultiDataSourceManager()
    
    if 'chart_manager' not in st.session_state:
        st.session_state.chart_manager = ChartDataManager(st.session_state.data_source_manager)
    
    if 'chart_data_cache' not in st.session_state:
        st.session_state.chart_data_cache = {}
    
    if 'selected_symbols' not in st.session_state:
        st.session_state.selected_symbols = []


def render_charts_header():
    """ヘッダー部分のレンダリング（v2.0.0）"""
    st.title("📈 金融チャート分析 v2.0.0")
    st.markdown("""
    **統一データベースアーキテクチャ対応版**
    - 💾 **データベースキャッシュ**: 高速チャート生成（任意機能）
    - 📊 **配当利回り比較**: 複数銘柄の配当利回りを横並び比較
    - 📈 **配当履歴**: 時系列での配当推移とトレンド分析
    - 🎯 **財務指標レーダー**: 多角的な財務健全性評価
    - 🔄 **リアルタイムデータ**: Yahoo Finance APIによる最新データ
    
    ⚠️ **学習・研究専用ツール** - データは参考程度にお考えください
    """)


def render_chart_type_selection():
    """チャートタイプ選択セクション"""
    st.subheader("📋 チャート種類の選択")
    
    chart_types = {
        'dividend_yield': {
            'name': '📊 配当利回り比較',
            'description': '複数銘柄の配当利回りを横棒グラフで比較',
            'max_symbols': 8
        },
        'dividend_history': {
            'name': '📈 配当履歴',
            'description': '単一銘柄の配当の時系列推移',
            'max_symbols': 1
        },
        'financial_radar': {
            'name': '🎯 財務指標レーダー',
            'description': '財務指標の総合評価（PER・PBR・ROE・配当利回り）',
            'max_symbols': 1
        }
    }
    
    # チャートタイプ選択
    selected_chart_type = st.radio(
        "チャートタイプを選択してください:",
        options=list(chart_types.keys()),
        format_func=lambda x: chart_types[x]['name'],
        horizontal=True
    )
    
    # 選択されたチャートの説明
    chart_info = chart_types[selected_chart_type]
    st.info(f"**{chart_info['name']}**: {chart_info['description']}")
    
    return selected_chart_type, chart_info


def render_symbol_selection(chart_info: Dict[str, Any]):
    """銘柄選択セクション"""
    st.subheader("🏢 銘柄選択")
    
    max_symbols = chart_info['max_symbols']
    
    if max_symbols == 1:
        # 単一銘柄選択
        col1, col2 = st.columns([3, 1])
        
        with col1:
            single_symbol = st.text_input(
                "銘柄コードを入力",
                value="",
                placeholder="例: 1928, 7203, AAPL",
                help="日本株: 4桁コード（.T不要）、米国株: ティッカーシンボル"
            )
        
        with col2:
            if st.button("📊 チャート生成", type="primary"):
                if single_symbol:
                    st.session_state.selected_symbols = [single_symbol.upper()]
                else:
                    st.error("銘柄コードを入力してください")
    
    else:
        # 複数銘柄選択
        col1, col2 = st.columns([3, 1])
        
        with col1:
            symbols_input = st.text_area(
                f"銘柄コード（最大{max_symbols}銘柄）",
                value="",
                placeholder="例:\n1928\n7203\n6758\nAAPL",
                help=f"1行に1銘柄ずつ入力。日本株は4桁数字（.T不要）。最大{max_symbols}銘柄まで",
                height=150
            )
        
        with col2:
            st.markdown("**サンプル銘柄:**")
            sample_sets = {
                "日本高配当株": ["1928.T", "8316.T", "8411.T", "9434.T"],
                "日本大型株": ["7203.T", "6758.T", "9984.T", "4502.T"],
                "米国テック株": ["AAPL", "MSFT", "GOOGL", "TSLA"]
            }
            
            for set_name, symbols in sample_sets.items():
                if st.button(set_name, key=f"sample_{set_name}"):
                    st.session_state.selected_symbols = symbols[:max_symbols]
            
            if st.button("📊 チャート生成", type="primary"):
                if symbols_input.strip():
                    symbols = [s.strip().upper() for s in symbols_input.split('\n') if s.strip()]
                    symbols = symbols[:max_symbols]  # 制限適用
                    st.session_state.selected_symbols = symbols
                else:
                    st.error("銘柄コードを入力してください")
    
    # 追加オプション（配当履歴の場合）
    period = "5y"  # デフォルト
    if chart_info['max_symbols'] == 1:
        st.subheader("⚙️ 表示オプション")
        period = st.selectbox(
            "表示期間",
            options=["1y", "2y", "5y", "10y", "max"],
            index=2,  # 5yをデフォルト
            format_func=lambda x: {
                "1y": "1年", "2y": "2年", "5y": "5年", 
                "10y": "10年", "max": "全期間"
            }[x]
        )
    
    return period


def render_chart_display(chart_type: str, period: str = "5y"):
    """チャート表示セクション"""
    if not st.session_state.selected_symbols:
        st.info("👆 上記で銘柄を選択してチャートを生成してください")
        return
    
    symbols = st.session_state.selected_symbols
    
    try:
        with st.spinner(f"📊 チャートを生成中... ({len(symbols)}銘柄)"):
            chart_manager = st.session_state.chart_manager
            
            if chart_type == 'dividend_yield':
                fig = chart_manager.create_dividend_yield_chart(symbols)
                st.subheader(f"📊 配当利回り比較 ({len(symbols)}銘柄)")
                
            elif chart_type == 'dividend_history':
                symbol = symbols[0]
                fig = chart_manager.create_dividend_history_chart(symbol, period)
                st.subheader(f"📈 {symbol} 配当履歴 ({period})")
                
            elif chart_type == 'financial_radar':
                symbol = symbols[0]
                fig = chart_manager.create_financial_metrics_radar(symbol)
                st.subheader(f"🎯 {symbol} 財務指標レーダー")
            
            # チャート表示
            st.plotly_chart(fig, use_container_width=True)
            
            # 詳細データ表示
            render_detailed_data(chart_type, symbols)
            
    except APIRateLimitError as e:
        st.error(f"🚫 API制限エラー: {str(e)}")
        st.info("しばらく時間をおいてから再試行してください")
        
    except DataFetchError as e:
        st.error(f"📡 データ取得エラー: {str(e)}")
        st.info("銘柄コードが正しいか確認してください")
        
    except Exception as e:
        st.error(f"❌ チャート生成エラー: {str(e)}")
        logger.error(f"Chart generation error: {e}")


def render_detailed_data(chart_type: str, symbols: List[str]):
    """詳細データ表示"""
    with st.expander("📊 詳細データ表示"):
        
        if chart_type == 'dividend_yield':
            render_dividend_yield_table(symbols)
        
        elif chart_type == 'dividend_history':
            render_dividend_history_table(symbols[0])
        
        elif chart_type == 'financial_radar':
            render_financial_metrics_table(symbols[0])


def render_dividend_yield_table(symbols: List[str]):
    """配当利回りテーブル表示"""
    try:
        data_source = st.session_state.data_source_manager
        stocks_data = data_source.get_multiple_stocks(symbols)
        
        table_data = []
        for symbol, data in stocks_data.items():
            dividend_yield = data.get('dividend_yield')
            current_price = data.get('current_price')
            pe_ratio = data.get('pe_ratio')
            pb_ratio = data.get('pb_ratio')
            
            # 警告情報
            warnings = data.get('warnings', [])
            critical_warnings = [w for w in warnings if w['level'] == WarningLevel.CRITICAL]
            
            table_data.append({
                '銘柄コード': symbol,
                '配当利回り (%)': float(dividend_yield) if dividend_yield else None,
                '株価 (円)': float(current_price) if current_price else None,
                'PER (倍)': float(pe_ratio) if pe_ratio else None,
                'PBR (倍)': float(pb_ratio) if pb_ratio else None,
                '警告': len(critical_warnings),
                'データ更新': data.get('processed_at', datetime.now()).strftime('%H:%M:%S')
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"テーブル生成エラー: {e}")


def render_dividend_history_table(symbol: str):
    """配当履歴テーブル表示"""
    try:
        data_source = st.session_state.data_source_manager
        dividend_data = data_source.get_dividend_history(symbol)
        
        if dividend_data and dividend_data.get('dividends'):
            dividends_dict = dividend_data['dividends']
            df = pd.DataFrame([
                {'日付': date, '配当金額 (円)': amount}
                for date, amount in dividends_dict.items()
            ])
            df['日付'] = pd.to_datetime(df['日付'])
            df = df.sort_values('日付', ascending=False)
            
            st.dataframe(df, use_container_width=True)
            
            # 統計情報
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("配当回数", len(df))
            with col2:
                st.metric("平均配当額", f"¥{df['配当金額 (円)'].mean():.2f}")
            with col3:
                st.metric("最新配当", f"¥{df['配当金額 (円)'].iloc[0]:.2f}")
        else:
            st.warning("配当履歴データがありません")
            
    except Exception as e:
        st.error(f"配当履歴テーブル生成エラー: {e}")


def render_financial_metrics_table(symbol: str):
    """財務指標テーブル表示"""
    try:
        data_source = st.session_state.data_source_manager
        stock_data = data_source.get_stock_info(symbol)
        
        metrics_data = [
            {'指標': '配当利回り (%)', '値': float(stock_data['dividend_yield']) if stock_data.get('dividend_yield') else None},
            {'指標': 'PER (倍)', '値': float(stock_data['pe_ratio']) if stock_data.get('pe_ratio') else None},
            {'指標': 'PBR (倍)', '値': float(stock_data['pb_ratio']) if stock_data.get('pb_ratio') else None},
            {'指標': 'ROE (%)', '値': float(stock_data['roe']) if stock_data.get('roe') else None},
            {'指標': '現在価格 (円)', '値': float(stock_data['current_price']) if stock_data.get('current_price') else None},
        ]
        
        df = pd.DataFrame(metrics_data)
        st.dataframe(df, use_container_width=True)
        
        # 警告情報
        warnings = stock_data.get('warnings', [])
        if warnings:
            st.subheader("⚠️ データ警告")
            for warning in warnings:
                level_color = {
                    WarningLevel.CRITICAL: "error",
                    WarningLevel.WARNING: "warning", 
                    WarningLevel.MINOR: "info"
                }
                
                getattr(st, level_color[warning['level']])(
                    f"{warning['level'].value} {warning['field']}: {warning['message']}"
                )
        
    except Exception as e:
        st.error(f"財務指標テーブル生成エラー: {e}")


def render_chart_export_options():
    """チャートエクスポートオプション"""
    with st.sidebar:
        st.subheader("💾 エクスポート")
        
        if st.session_state.selected_symbols:
            symbols_text = ", ".join(st.session_state.selected_symbols)
            
            # データダウンロード
            if st.button("📄 データをCSVダウンロード"):
                try:
                    data_source = st.session_state.data_source_manager
                    stocks_data = data_source.get_multiple_stocks(st.session_state.selected_symbols)
                    
                    export_data = []
                    for symbol, data in stocks_data.items():
                        export_data.append({
                            'symbol': symbol,
                            'dividend_yield': float(data['dividend_yield']) if data.get('dividend_yield') else None,
                            'pe_ratio': float(data['pe_ratio']) if data.get('pe_ratio') else None,
                            'pb_ratio': float(data['pb_ratio']) if data.get('pb_ratio') else None,
                            'current_price': float(data['current_price']) if data.get('current_price') else None,
                            'processed_at': data.get('processed_at', datetime.now()).isoformat()
                        })
                    
                    df = pd.DataFrame(export_data)
                    csv = df.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 CSVファイルをダウンロード",
                        data=csv,
                        file_name=f"stock_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                except Exception as e:
                    st.error(f"エクスポートエラー: {e}")


def render_api_status_sidebar():
    """サイドバーのAPI状況表示"""
    with st.sidebar:
        st.subheader("📊 API使用状況")
        
        if 'data_source_manager' in st.session_state:
            usage_stats = st.session_state.data_source_manager.get_api_usage_stats()
            
            # 使用量表示
            hourly_progress = usage_stats['requests_last_hour'] / usage_stats['hourly_limit']
            st.progress(hourly_progress, text=f"時間制限: {usage_stats['requests_last_hour']}/{usage_stats['hourly_limit']}")
            
            minute_progress = usage_stats['requests_last_minute'] / usage_stats['minute_limit']
            st.progress(minute_progress, text=f"分制限: {usage_stats['requests_last_minute']}/{usage_stats['minute_limit']}")
            
            # キャッシュ状況
            st.metric("キャッシュサイズ", usage_stats['cache_size'])
            
            # キャッシュクリアボタン
            if st.button("🧹 キャッシュクリア"):
                st.session_state.data_source_manager.clear_cache()
                st.success("キャッシュをクリアしました")
                st.rerun()


def main():
    """メイン関数"""
    # ページ設定
    st.set_page_config(
        page_title="金融チャート - 日本株ウォッチドッグ",
        page_icon="📈",
        layout="wide"
    )
    
    # 初期化
    initialize_charts_page()
    
    # ヘッダー
    render_charts_header()
    
    # サイドバー
    render_api_status_sidebar()
    render_chart_export_options()
    
    # メインコンテンツ
    chart_type, chart_info = render_chart_type_selection()
    period = render_symbol_selection(chart_info)
    render_chart_display(chart_type, period)


if __name__ == "__main__":
    main()