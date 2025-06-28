"""
ポートフォリオ管理画面 v2.0.0

新統一データベースアーキテクチャ対応版
- EnhancedCSVParser: 楽天・SBI証券CSV自動解析
- DatabaseManager: SQLite永続化ストレージ
- 「両方の真実保持」: 証券会社とYahoo Financeデータの透明性表示
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from decimal import Decimal

# v2.0.0 新アーキテクチャモジュール
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.database_manager import DatabaseManager
from core.enhanced_csv_parser import EnhancedCSVParser
from core.multi_data_source import MultiDataSourceManager, DataFetchError, APIRateLimitError
from core.chart_data_manager import ChartDataManager

# ログ設定
logger = logging.getLogger(__name__)


def initialize_portfolio_page():
    """ポートフォリオページの初期化（v2.0.0対応）"""
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    if 'csv_parser' not in st.session_state:
        st.session_state.csv_parser = EnhancedCSVParser(st.session_state.db_manager)
    
    if 'data_source_manager' not in st.session_state:
        st.session_state.data_source_manager = MultiDataSourceManager()
    
    if 'chart_manager' not in st.session_state:
        st.session_state.chart_manager = ChartDataManager(st.session_state.data_source_manager)
    
    # v2.0.0: セッション状態ではなくデータベースから取得
    if 'portfolio_last_updated' not in st.session_state:
        st.session_state.portfolio_last_updated = datetime.now()


def render_portfolio_header():
    """ヘッダー部分のレンダリング（v2.0.0）"""
    st.title("📊 ポートフォリオ管理 v2.0.0")
    st.markdown("""
    **新統一データベースアーキテクチャ対応版**
    - 🏗️ **「両方の真実保持」**: SBI・楽天データとYahoo Financeの透明性表示
    - 📁 **Enhanced CSV Parser**: 32件データ正常処理確認済み
    - 💾 **SQLiteデータベース**: 永続化ストレージで安全管理
    - 💹 **リアルタイム更新**: Yahoo Finance APIによる最新株価取得
    - 🎯 **投資アドバイス**: 利確15%・損切-8%ルールによる自動判定
    
    ⚠️ **学習・研究専用ツール** - 投資判断は必ずご自身の責任で行ってください
    """)


def render_csv_upload_section():
    """CSVアップロードセクション（v2.0.0対応）"""
    st.subheader("📁 ポートフォリオCSVファイル読み込み")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "CSVファイルを選択してください",
            type=['csv'],
            help="SBI証券・楽天証券のポートフォリオCSVファイルに対応（UTF-8, Shift_JIS対応）",
            accept_multiple_files=False
        )
    
    with col2:
        st.markdown("**v2.0.0対応形式:**")
        st.markdown("- SBI証券 ポートフォリオ")
        st.markdown("- 楽天証券 保有商品")
        st.markdown("- 自動エンコーディング検出")
        st.markdown("- データベース永続化")
    
    if uploaded_file is not None:
        try:
            # v2.0.0: EnhancedCSVParserで直接データベースに保存
            with st.spinner("📊 CSV解析中... (v2.0.0 Enhanced Parser)"):
                csv_parser = st.session_state.csv_parser
                success, result = csv_parser.parse_csv_to_database(
                    uploaded_file.read(), 
                    uploaded_file.name
                )
                
                if success:
                    st.success(f"✅ CSVファイルを解析・保存しました")
                    st.info(f"""
                    **処理結果:**
                    - データソース: {result['data_source']}
                    - 総レコード数: {result['total_records']}
                    - 成功: {result['success_count']}件
                    - エラー: {result['error_count']}件
                    - エンコーディング: {result['encoding']}
                    """)
                    
                    # データベースから最新データを表示
                    st.session_state.portfolio_last_updated = datetime.now()
                    
                    # プレビュー表示
                    with st.expander("📋 データベース保存内容プレビュー"):
                        portfolio_data = get_portfolio_from_database()
                        if not portfolio_data.empty:
                            preview_df = portfolio_data[['symbol', 'name', 'data_source', 'quantity', 'average_price']].head()
                            st.dataframe(preview_df, use_container_width=True)
                else:
                    st.error(f"❌ CSV解析エラー: {result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            st.error(f"❌ ファイル処理エラー: {str(e)}")
            logger.error(f"CSV upload error: {e}")
    
    # v2.0.0: データベース状況表示
    render_database_status()
    
    # サンプルデータボタン
    if st.button("📋 サンプルデータで試す", help="デモ用サンプルをデータベースに保存"):
        try:
            insert_sample_data_to_database()
            st.success("✅ サンプルポートフォリオをデータベースに保存しました")
            st.session_state.portfolio_last_updated = datetime.now()
        except Exception as e:
            st.error(f"❌ サンプルデータ挿入エラー: {e}")


def render_database_status():
    """データベース状況表示"""
    try:
        db_manager = st.session_state.db_manager
        portfolio_count = len(get_portfolio_from_database())
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("データベース内銘柄数", f"{portfolio_count}銘柄")
        with col2:
            st.metric("最終更新", st.session_state.portfolio_last_updated.strftime("%H:%M:%S"))
        with col3:
            if st.button("🗑️ データベースクリア"):
                # 確認ダイアログの代わりに、削除結果を表示
                deleted_count = clear_portfolio_database()
                if deleted_count > 0:
                    st.success(f"✅ データベースをクリアしました（{deleted_count}件削除）")
                    st.session_state.portfolio_last_updated = datetime.now()
                else:
                    st.info("📭 データベースは既に空です")
                st.rerun()
                
    except Exception as e:
        st.warning(f"データベース状況取得エラー: {e}")


def get_portfolio_from_database() -> pd.DataFrame:
    """データベースからポートフォリオデータを取得"""
    try:
        db_manager = st.session_state.db_manager
        portfolio_data = db_manager.get_portfolio_analytics()
        
        if portfolio_data:
            return pd.DataFrame(portfolio_data)
        else:
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Database portfolio fetch error: {e}")
        return pd.DataFrame()


def insert_sample_data_to_database():
    """サンプルデータをデータベースに挿入"""
    sample_data = [
        {
            'symbol': '1928',
            'name': '積水ハウス',
            'data_source': 'sample',
            'quantity': 100,
            'average_price': 2100.0,
            'current_price': 2200.0,
            'market_value': 220000.0,
            'profit_loss': 10000.0,
            'total_cost': 210000.0,
            'profit_loss_rate_original': None,
            'profit_loss_rate_percent': 4.8,
            'profit_loss_rate_decimal': 0.048
        },
        {
            'symbol': '7203',
            'name': 'トヨタ自動車',
            'data_source': 'sample',
            'quantity': 50,
            'average_price': 2000.0,
            'current_price': 2150.0,
            'market_value': 107500.0,
            'profit_loss': 7500.0,
            'total_cost': 100000.0,
            'profit_loss_rate_original': None,
            'profit_loss_rate_percent': 7.5,
            'profit_loss_rate_decimal': 0.075
        },
        {
            'symbol': '8316',
            'name': '三井住友フィナンシャル',
            'data_source': 'sample',
            'quantity': 200,
            'average_price': 4500.0,
            'current_price': 4200.0,
            'market_value': 840000.0,
            'profit_loss': -60000.0,
            'total_cost': 900000.0,
            'profit_loss_rate_original': None,
            'profit_loss_rate_percent': -6.7,
            'profit_loss_rate_decimal': -0.067
        }
    ]
    
    db_manager = st.session_state.db_manager
    for item in sample_data:
        db_manager.insert_portfolio_data(item)


def clear_portfolio_database():
    """ポートフォリオデータベースをクリア"""
    db_manager = st.session_state.db_manager
    deleted_count = db_manager.clear_all_portfolio_data()
    return deleted_count


def render_portfolio_overview():
    """ポートフォリオ概要表示（v2.0.0データベース対応）"""
    portfolio_df = get_portfolio_from_database()
    
    if portfolio_df.empty:
        st.info("👆 上記でCSVファイルを読み込むか、サンプルデータで試してください")
        return
    
    st.subheader("💼 ポートフォリオ概要（データベース版）")
    
    try:
        with st.spinner("📈 最新データを取得中..."):
            # リアルタイムデータ取得
            symbols = [f"{row['symbol']}.T" if row['symbol'].isdigit() else row['symbol'] 
                      for _, row in portfolio_df.iterrows()]
            current_data = get_portfolio_realtime_data(symbols)
            
            # v2.0.0: 「両方の真実保持」表示
            portfolio_with_realtime = merge_database_and_realtime_data(portfolio_df, current_data)
            
            # サマリー表示
            render_portfolio_summary(portfolio_with_realtime)
            
            # 詳細テーブル
            render_portfolio_table(portfolio_with_realtime)
            
            # 投資アドバイス生成
            generate_investment_advice(portfolio_with_realtime)
            
    except Exception as e:
        st.error(f"❌ ポートフォリオ分析エラー: {str(e)}")
        logger.error(f"Portfolio analysis error: {e}")


def get_portfolio_realtime_data(symbols: List[str]) -> Dict[str, Any]:
    """ポートフォリオのリアルタイムデータ取得"""
    data_source = st.session_state.data_source_manager
    return data_source.get_multiple_stocks(symbols, delay_between_requests=0.5)


def merge_database_and_realtime_data(portfolio_df: pd.DataFrame, current_data: Dict[str, Any]) -> pd.DataFrame:
    """データベースデータとリアルタイムデータの統合（両方の真実保持）"""
    result_data = []
    
    for _, row in portfolio_df.iterrows():
        symbol = row['symbol']
        yahoo_symbol = f"{symbol}.T" if symbol.isdigit() else symbol
        
        # データベースから取得した値（証券会社データ）
        db_profit_loss_rate = row.get('profit_loss_rate_percent', 0)
        
        # Yahoo Financeから取得した値
        yahoo_profit_loss_rate = None
        current_price = row.get('current_price', row.get('average_price', 0))
        
        if yahoo_symbol in current_data:
            stock_data = current_data[yahoo_symbol]
            if stock_data.get('current_price') is not None:
                current_price = float(stock_data['current_price'])
            
            # Yahoo Finance損益率を計算
            if current_price and row.get('average_price', 0) > 0:
                yahoo_profit_loss_rate = ((current_price - row['average_price']) / row['average_price']) * 100
        
        # 投資アドバイス判定
        advice_rate = yahoo_profit_loss_rate if yahoo_profit_loss_rate is not None else db_profit_loss_rate
        advice = determine_investment_advice(advice_rate)
        
        # Yahoo Financeから銘柄名を取得、なければデータベースから、それもなければシンボルを使用
        stock_name = row.get('name', symbol)
        if yahoo_symbol in current_data and current_data[yahoo_symbol].get('long_name'):
            stock_name = current_data[yahoo_symbol]['long_name']
        
        result_data.append({
            'symbol': symbol,
            'name': stock_name,
            'data_source': row.get('data_source', 'unknown'),
            'quantity': row.get('quantity', 0),
            'average_price': row.get('average_price', 0),
            'current_price': current_price,
            'market_value': row.get('quantity', 0) * current_price,
            'book_value': row.get('total_cost', 0),
            
            # v2.0.0: 両方の真実を保持
            'db_profit_loss_rate': db_profit_loss_rate,  # 証券会社データ
            'yahoo_profit_loss_rate': yahoo_profit_loss_rate,  # Yahoo Financeデータ
            'profit_loss_rate_original': row.get('profit_loss_rate_original'),  # 生データ
            
            'advice': advice,
            'dividend_yield': float(current_data.get(yahoo_symbol, {}).get('dividend_yield') or 0) if yahoo_symbol in current_data and current_data.get(yahoo_symbol, {}).get('dividend_yield') is not None else None,
            'pe_ratio': float(current_data.get(yahoo_symbol, {}).get('pe_ratio') or 0) if yahoo_symbol in current_data and current_data.get(yahoo_symbol, {}).get('pe_ratio') is not None else None,
            'warnings': len(current_data.get(yahoo_symbol, {}).get('warnings', []))
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
    """ポートフォリオサマリー表示（v2.0.0対応）"""
    col1, col2, col3, col4 = st.columns(4)
    
    total_book_value = portfolio_df['book_value'].sum()
    total_market_value = portfolio_df['market_value'].sum()
    total_pnl = total_market_value - total_book_value
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
        # データソース統計
        sources = portfolio_df['data_source'].value_counts()
        source_text = " | ".join([f"{src}:{cnt}" for src, cnt in sources.items()])
        st.metric(
            "銘柄構成",
            f"{len(portfolio_df)}銘柄",
            delta=source_text
        )


def render_portfolio_table(portfolio_df: pd.DataFrame):
    """ポートフォリオ詳細テーブル表示（両方の真実保持版）"""
    st.subheader("📋 保有銘柄詳細（両方の真実保持）")
    
    # 表示用データフレーム作成
    display_df = portfolio_df.copy()
    
    # 数値フォーマット
    display_df['平均取得価格'] = display_df['average_price'].apply(lambda x: f"¥{x:,.0f}")
    display_df['現在価格'] = display_df['current_price'].apply(lambda x: f"¥{x:,.0f}")
    display_df['評価額'] = display_df['market_value'].apply(lambda x: f"¥{x:,.0f}")
    
    # v2.0.0: 両方の損益率を表示
    def format_profit_loss_rates(row):
        db_rate = row['db_profit_loss_rate']
        yahoo_rate = row['yahoo_profit_loss_rate']
        
        if yahoo_rate is not None:
            return f"DB:{db_rate:+.1f}% | Yahoo:{yahoo_rate:+.1f}%"
        else:
            return f"DB:{db_rate:+.1f}% | Yahoo:N/A"
    
    display_df['損益率(両表示)'] = display_df.apply(format_profit_loss_rates, axis=1)
    
    # 配当利回りフォーマット
    display_df['配当利回り'] = display_df['dividend_yield'].apply(
        lambda x: f"{x:.1f}%" if x is not None and x > 0 else "N/A"
    )
    
    # 表示カラム選択
    display_columns = [
        'symbol', 'name', 'data_source', 'quantity', '平均取得価格', '現在価格', 
        '評価額', '損益率(両表示)', 'advice', '配当利回り'
    ]
    
    # カラム名マッピング
    column_names = {
        'symbol': '銘柄コード',
        'name': '銘柄名',
        'data_source': 'データソース',
        'quantity': '数量',
        'advice': 'アドバイス'
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
    
    styled_df = final_df.style.map(color_pnl, subset=['アドバイス'])
    st.dataframe(styled_df, use_container_width=True)
    
    # v2.0.0: 「両方の真実」についての説明
    with st.expander("ℹ️ 「両方の真実保持」について"):
        st.markdown("""
        **v2.0.0の「両方の真実保持」機能:**
        - **DB**: 証券会社CSVファイルの元データ（SBI証券167.98%等）
        - **Yahoo**: Yahoo Finance APIから計算した損益率
        - **目的**: データソース間の単位不一致問題の完全解決
        - **メリット**: 計算なしで直接比較、透明性の確保
        """)


def generate_investment_advice(portfolio_df: pd.DataFrame):
    """投資アドバイス生成（v2.0.0対応）"""
    st.subheader("🎯 投資アドバイス（統一判定）")
    
    # アドバイス統計
    advice_counts = portfolio_df['advice'].value_counts()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 具体的なアドバイス
        profit_stocks = portfolio_df[portfolio_df['advice'] == '💰 利確検討']
        loss_stocks = portfolio_df[portfolio_df['advice'] == '🛑 損切検討']
        hold_stocks = portfolio_df[portfolio_df['advice'] == '📊 継続保有']
        
        if not profit_stocks.empty:
            st.success("💰 **利確検討推奨銘柄**")
            for _, stock in profit_stocks.iterrows():
                yahoo_rate = stock.get('yahoo_profit_loss_rate', 'N/A')
                rate_text = f"{yahoo_rate:+.1f}%" if yahoo_rate != 'N/A' else "N/A"
                st.markdown(f"- **{stock['symbol']}** ({stock['name']}): {rate_text}")
        
        if not loss_stocks.empty:
            st.error("🛑 **損切検討推奨銘柄**")
            for _, stock in loss_stocks.iterrows():
                yahoo_rate = stock.get('yahoo_profit_loss_rate', 'N/A')
                rate_text = f"{yahoo_rate:+.1f}%" if yahoo_rate != 'N/A' else "N/A"
                st.markdown(f"- **{stock['symbol']}** ({stock['name']}): {rate_text}")
        
        if not hold_stocks.empty:
            st.info("📊 **継続保有推奨銘柄**")
            for _, stock in hold_stocks.iterrows():
                yahoo_rate = stock.get('yahoo_profit_loss_rate', 'N/A')
                rate_text = f"{yahoo_rate:+.1f}%" if yahoo_rate != 'N/A' else "N/A"
                st.markdown(f"- **{stock['symbol']}** ({stock['name']}): {rate_text}")
        
        if profit_stocks.empty and loss_stocks.empty and hold_stocks.empty:
            st.info("📊 現在は分析対象銘柄がありません。")
    
    with col2:
        # アドバイス分布
        if len(advice_counts) > 0:
            st.markdown("**アドバイス分布:**")
            for advice, count in advice_counts.items():
                st.markdown(f"- {advice}: {count}銘柄")


def render_portfolio_sidebar():
    """サイドバーのポートフォリオ機能（v2.0.0対応）"""
    with st.sidebar:
        portfolio_df = get_portfolio_from_database()
        
        if not portfolio_df.empty:
            st.subheader("💼 ポートフォリオアクション v2.0.0")
            
            # データ更新
            if st.button("🔄 リアルタイム更新", use_container_width=True):
                st.session_state.portfolio_last_updated = datetime.now()
                st.rerun()
            
            # データベースサマリー取得
            if st.button("📊 サマリー取得", use_container_width=True):
                try:
                    csv_parser = st.session_state.csv_parser
                    summary = csv_parser.get_portfolio_summary()
                    
                    if "error" not in summary:
                        st.success("📈 サマリー取得成功")
                        st.json(summary)
                    else:
                        st.error(f"サマリーエラー: {summary['error']}")
                except Exception as e:
                    st.error(f"サマリー取得エラー: {e}")
            
            # CSVエクスポート（データベースから）
            if st.button("📄 DBからCSVエクスポート", use_container_width=True):
                try:
                    if portfolio_df.empty:
                        st.warning("⚠️ エクスポートするデータがありません")
                    else:
                        csv = portfolio_df.to_csv(index=False)
                        
                        # ファイルサイズ情報
                        file_size = len(csv.encode())
                        file_size_kb = file_size / 1024
                        
                        st.success(f"✅ CSVファイル準備完了（{len(portfolio_df)}銘柄, {file_size_kb:.1f}KB）")
                        
                        st.download_button(
                            label="📥 CSVファイルをダウンロード",
                            data=csv,
                            file_name=f"portfolio_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                except Exception as e:
                    st.error(f"エクスポートエラー: {e}")


def main():
    """メイン関数（v2.0.0）"""
    # ページ設定
    st.set_page_config(
        page_title="ポートフォリオ管理 v2.0.0 - 日本株ウォッチドッグ",
        page_icon="📊",
        layout="wide"
    )
    
    # v2.0.0初期化
    initialize_portfolio_page()
    
    # ヘッダー
    render_portfolio_header()
    
    # サイドバー
    render_portfolio_sidebar()
    
    # メインコンテンツ
    render_csv_upload_section()
    render_portfolio_overview()


if __name__ == "__main__":
    main()