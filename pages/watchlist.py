"""
監視リスト・欲しい銘柄管理画面

将来購入を検討している銘柄の追跡と分析機能を提供。
統一プロセッサを経由したリアルタイム監視と投資タイミング判定。
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import json

# コアモジュールのインポート
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.multi_data_source import MultiDataSourceManager, DataFetchError, APIRateLimitError
from core.investment_strategies import InvestmentStrategyAnalyzer, RecommendationLevel
from core.chart_data_manager import ChartDataManager
from core.financial_data_processor import WarningLevel

# ログ設定
logger = logging.getLogger(__name__)


def initialize_watchlist_page():
    """監視リストページの初期化"""
    if 'data_source_manager' not in st.session_state:
        st.session_state.data_source_manager = MultiDataSourceManager()
    
    if 'strategy_analyzer' not in st.session_state:
        st.session_state.strategy_analyzer = InvestmentStrategyAnalyzer()
    
    if 'chart_manager' not in st.session_state:
        st.session_state.chart_manager = ChartDataManager(st.session_state.data_source_manager)
    
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = []
    
    if 'watchlist_analysis' not in st.session_state:
        st.session_state.watchlist_analysis = {}


def render_watchlist_header():
    """ヘッダー部分のレンダリング"""
    st.title("👀 監視リスト・欲しい銘柄管理")
    st.markdown("""
    **将来の投資候補銘柄を効率的に追跡**
    - 📝 **銘柄追加・削除**: 興味のある銘柄を簡単管理
    - 📊 **リアルタイム監視**: 最新株価・財務指標の自動更新
    - 🎯 **投資タイミング判定**: 5つの戦略による購入推奨度評価
    - 📈 **比較分析**: 複数銘柄の横並び比較とランキング
    
    ⚠️ **学習・研究専用ツール** - 投資判断は必ずご自身の責任で行ってください
    """)


def render_watchlist_management():
    """監視リスト管理セクション"""
    st.subheader("📝 監視リスト管理")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        new_symbol = st.text_input(
            "銘柄コードを追加",
            value="",
            placeholder="例: 1928.T, 7203.T, AAPL",
            help="日本株: 4桁コード.T、米国株: ティッカーシンボル"
        )
    
    with col2:
        if st.button("➕ 追加", type="primary"):
            if new_symbol:
                add_to_watchlist(new_symbol.upper().strip())
            else:
                st.error("銘柄コードを入力してください")
    
    with col3:
        if st.button("🔄 全更新"):
            update_all_watchlist_data()
    
    # クイック追加ボタン
    st.markdown("**人気銘柄クイック追加:**")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    quick_add_symbols = [
        ("1928.T", "積水ハウス"),
        ("7203.T", "トヨタ"),
        ("6758.T", "ソニー"),
        ("AAPL", "Apple"),
        ("MSFT", "Microsoft")
    ]
    
    for i, (symbol, name) in enumerate(quick_add_symbols):
        col = [col1, col2, col3, col4, col5][i]
        if col.button(f"+ {name}", key=f"quick_add_{i}"):
            add_to_watchlist(symbol)


def add_to_watchlist(symbol: str):
    """監視リストに銘柄追加"""
    if symbol in st.session_state.watchlist:
        st.warning(f"⚠️ {symbol} は既に監視リストに含まれています")
        return
    
    try:
        # 銘柄データ取得で有効性確認
        data_source = st.session_state.data_source_manager
        stock_data = data_source.get_stock_info(symbol)
        
        # 監視リストに追加
        st.session_state.watchlist.append(symbol)
        
        # 追加時刻記録
        watchlist_item = {
            'symbol': symbol,
            'added_at': datetime.now(),
            'last_updated': datetime.now(),
            'stock_data': stock_data,
            'analysis': None,
            'notes': ""
        }
        
        st.session_state.watchlist_analysis[symbol] = watchlist_item
        st.success(f"✅ {symbol} を監視リストに追加しました")
        st.rerun()
        
    except (DataFetchError, APIRateLimitError) as e:
        st.error(f"❌ 銘柄追加エラー: {str(e)}")
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {str(e)}")
        logger.error(f"Watchlist add error for {symbol}: {e}")


def remove_from_watchlist(symbol: str):
    """監視リストから銘柄削除"""
    if symbol in st.session_state.watchlist:
        st.session_state.watchlist.remove(symbol)
        if symbol in st.session_state.watchlist_analysis:
            del st.session_state.watchlist_analysis[symbol]
        st.success(f"✅ {symbol} を監視リストから削除しました")
        st.rerun()


def update_all_watchlist_data():
    """全監視銘柄のデータ更新"""
    if not st.session_state.watchlist:
        st.info("監視リストが空です")
        return
    
    try:
        with st.spinner(f"📊 {len(st.session_state.watchlist)}銘柄のデータを更新中..."):
            data_source = st.session_state.data_source_manager
            strategy_analyzer = st.session_state.strategy_analyzer
            
            # 一括データ取得
            symbols = st.session_state.watchlist
            stocks_data = data_source.get_multiple_stocks(symbols, delay_between_requests=0.3)
            
            # 各銘柄の分析実行
            for symbol in symbols:
                if symbol in stocks_data:
                    stock_data = stocks_data[symbol]
                    
                    # 戦略分析実行
                    analysis = strategy_analyzer.get_comprehensive_analysis(stock_data)
                    
                    # 結果更新
                    if symbol in st.session_state.watchlist_analysis:
                        st.session_state.watchlist_analysis[symbol].update({
                            'stock_data': stock_data,
                            'analysis': analysis,
                            'last_updated': datetime.now()
                        })
            
            st.success(f"✅ {len(stocks_data)}銘柄のデータを更新しました")
            
    except Exception as e:
        st.error(f"❌ データ更新エラー: {str(e)}")
        logger.error(f"Watchlist update error: {e}")


def render_watchlist_overview():
    """監視リスト概要表示"""
    if not st.session_state.watchlist:
        st.info("👆 上記で監視したい銘柄を追加してください")
        return
    
    st.subheader("👀 監視中の銘柄")
    
    # 概要統計
    render_watchlist_statistics()
    
    # 銘柄リスト表示
    render_watchlist_table()
    
    # 投資タイミング分析
    render_investment_timing_analysis()


def render_watchlist_statistics():
    """監視リスト統計表示"""
    watchlist_data = st.session_state.watchlist_analysis
    
    # 統計計算
    total_symbols = len(st.session_state.watchlist)
    analyzed_symbols = len([item for item in watchlist_data.values() if item.get('analysis')])
    
    # 推奨レベル統計
    recommendations = {}
    for item in watchlist_data.values():
        if item.get('analysis'):
            best_strategy = item['analysis'].get('best_strategy', 'unknown')
            strategy_results = item['analysis'].get('strategy_results', {})
            if best_strategy in strategy_results:
                rec = strategy_results[best_strategy].get('recommendation', 'N/A')
                recommendations[rec] = recommendations.get(rec, 0) + 1
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("監視銘柄数", total_symbols)
    
    with col2:
        st.metric("分析完了", f"{analyzed_symbols}/{total_symbols}")
    
    with col3:
        buy_recommendations = recommendations.get('🟢 強い買い', 0) + recommendations.get('🔵 買い', 0)
        st.metric("買い推奨", f"{buy_recommendations}銘柄")
    
    with col4:
        avg_scores = []
        for item in watchlist_data.values():
            if item.get('analysis'):
                avg_scores.append(item['analysis'].get('overall_score', 0))
        avg_score = sum(avg_scores) / len(avg_scores) if avg_scores else 0
        st.metric("平均スコア", f"{avg_score:.1f}点")


def render_watchlist_table():
    """監視リスト詳細テーブル"""
    st.subheader("📊 詳細監視データ")
    
    watchlist_data = st.session_state.watchlist_analysis
    table_data = []
    
    for symbol in st.session_state.watchlist:
        item = watchlist_data.get(symbol, {})
        stock_data = item.get('stock_data', {})
        analysis = item.get('analysis', {})
        
        # 基本データ
        current_price = float(stock_data['current_price']) if stock_data.get('current_price') else None
        dividend_yield = float(stock_data['dividend_yield']) if stock_data.get('dividend_yield') else None
        pe_ratio = float(stock_data['pe_ratio']) if stock_data.get('pe_ratio') else None
        pb_ratio = float(stock_data['pb_ratio']) if stock_data.get('pb_ratio') else None
        
        # 分析データ
        overall_score = analysis.get('overall_score', 0) if analysis else 0
        best_strategy = analysis.get('best_strategy', 'N/A') if analysis else 'N/A'
        
        # 推奨レベル
        recommendation = 'N/A'
        if analysis and 'strategy_results' in analysis:
            strategy_results = analysis['strategy_results']
            if best_strategy in strategy_results:
                recommendation = strategy_results[best_strategy].get('recommendation', 'N/A')
        
        # 警告数
        warnings_count = len(stock_data.get('warnings', []))
        
        table_data.append({
            'symbol': symbol,
            'current_price': f"¥{current_price:,.0f}" if current_price else "N/A",
            'dividend_yield': f"{dividend_yield:.1f}%" if dividend_yield else "N/A",
            'pe_ratio': f"{pe_ratio:.1f}" if pe_ratio else "N/A",
            'pb_ratio': f"{pb_ratio:.2f}" if pb_ratio else "N/A",
            'overall_score': f"{overall_score:.1f}",
            'best_strategy': best_strategy,
            'recommendation': recommendation,
            'warnings': warnings_count,
            'last_updated': item.get('last_updated', datetime.now()).strftime('%H:%M:%S'),
            'actions': symbol  # 削除ボタン用
        })
    
    if table_data:
        df = pd.DataFrame(table_data)
        
        # カラム名変更
        column_names = {
            'symbol': '銘柄コード',
            'current_price': '現在価格',
            'dividend_yield': '配当利回り',
            'pe_ratio': 'PER',
            'pb_ratio': 'PBR',
            'overall_score': '総合スコア',
            'best_strategy': '最適戦略',
            'recommendation': '推奨レベル',
            'warnings': '警告数',
            'last_updated': '更新時刻',
            'actions': 'アクション'
        }
        
        display_df = df.rename(columns=column_names)
        
        # 削除ボタン付きで表示
        for i, row in display_df.iterrows():
            cols = st.columns([1, 1, 1, 1, 1, 1, 1.5, 1.5, 1, 1, 1])
            
            for j, (col_name, value) in enumerate(row.items()):
                if col_name == 'アクション':
                    with cols[j]:
                        if st.button(f"🗑️", key=f"delete_{value}", help=f"{value}を削除"):
                            remove_from_watchlist(value)
                else:
                    cols[j].write(value)
    else:
        st.info("監視リストが空です")


def render_investment_timing_analysis():
    """投資タイミング分析"""
    st.subheader("🎯 投資タイミング分析")
    
    watchlist_data = st.session_state.watchlist_analysis
    
    # 買い推奨銘柄の抽出
    buy_candidates = []
    for symbol, item in watchlist_data.items():
        analysis = item.get('analysis')
        if analysis and 'strategy_results' in analysis:
            best_strategy = analysis.get('best_strategy')
            if best_strategy and best_strategy in analysis['strategy_results']:
                result = analysis['strategy_results'][best_strategy]
                recommendation = result.get('recommendation', '')
                if '買い' in recommendation:
                    buy_candidates.append({
                        'symbol': symbol,
                        'score': analysis.get('overall_score', 0),
                        'strategy': best_strategy,
                        'recommendation': recommendation,
                        'confidence': result.get('confidence', 0),
                        'current_price': float(item['stock_data']['current_price']) if item.get('stock_data', {}).get('current_price') else 0
                    })
    
    if buy_candidates:
        # スコア順でソート
        buy_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        st.success("💰 **投資推奨銘柄**")
        
        for i, candidate in enumerate(buy_candidates[:5]):  # トップ5表示
            with st.expander(f"#{i+1} {candidate['symbol']} - {candidate['score']:.1f}点"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("推奨レベル", candidate['recommendation'])
                    st.metric("最適戦略", candidate['strategy'])
                
                with col2:
                    st.metric("信頼度", f"{candidate['confidence']*100:.1f}%")
                    st.metric("現在価格", f"¥{candidate['current_price']:,.0f}")
                
                with col3:
                    # 個別詳細分析ボタン
                    if st.button(f"📊 詳細分析", key=f"detail_{candidate['symbol']}"):
                        render_individual_analysis(candidate['symbol'])
    else:
        st.info("📊 現在買い推奨の銘柄はありません")
    
    # 注意銘柄の表示
    warning_symbols = []
    for symbol, item in watchlist_data.items():
        stock_data = item.get('stock_data', {})
        warnings = stock_data.get('warnings', [])
        critical_warnings = [w for w in warnings if w['level'] == WarningLevel.CRITICAL]
        if critical_warnings:
            warning_symbols.append(symbol)
    
    if warning_symbols:
        st.warning("⚠️ **データ要確認銘柄**")
        st.markdown(", ".join(warning_symbols))


def render_individual_analysis(symbol: str):
    """個別銘柄詳細分析"""
    if symbol not in st.session_state.watchlist_analysis:
        st.error(f"分析データが見つかりません: {symbol}")
        return
    
    item = st.session_state.watchlist_analysis[symbol]
    analysis = item.get('analysis')
    
    if not analysis:
        st.error(f"分析が未実行です: {symbol}")
        return
    
    st.subheader(f"📊 {symbol} 詳細分析")
    
    # 戦略別スコア表示
    strategy_results = analysis.get('strategy_results', {})
    
    cols = st.columns(len(strategy_results))
    for i, (strategy_name, result) in enumerate(strategy_results.items()):
        with cols[i]:
            st.metric(
                strategy_name,
                f"{result['score_percentage']:.1f}%",
                delta=result['recommendation']
            )
    
    # チャート表示
    try:
        chart_manager = st.session_state.chart_manager
        
        # 戦略比較チャート
        strategy_chart = chart_manager.create_strategy_comparison_chart(analysis)
        st.plotly_chart(strategy_chart, use_container_width=True)
        
        # 財務指標レーダーチャート
        radar_chart = chart_manager.create_financial_metrics_radar(symbol)
        st.plotly_chart(radar_chart, use_container_width=True)
        
    except Exception as e:
        st.error(f"チャート生成エラー: {e}")


def render_watchlist_comparison():
    """監視リスト比較分析"""
    if len(st.session_state.watchlist) < 2:
        return
    
    st.subheader("📈 監視銘柄比較")
    
    try:
        chart_manager = st.session_state.chart_manager
        
        # 配当利回り比較チャート
        dividend_chart = chart_manager.create_dividend_yield_chart(st.session_state.watchlist)
        st.plotly_chart(dividend_chart, use_container_width=True)
        
    except Exception as e:
        st.error(f"比較チャート生成エラー: {e}")


def render_watchlist_sidebar():
    """サイドバーの監視リスト機能"""
    with st.sidebar:
        st.subheader("👀 監視リスト管理")
        
        # エクスポート機能
        if st.session_state.watchlist:
            if st.button("📄 監視リストエクスポート"):
                export_watchlist()
            
            # インポート機能
            st.markdown("**監視リストインポート:**")
            uploaded_file = st.file_uploader(
                "JSON ファイル", 
                type=['json'],
                key="watchlist_import"
            )
            
            if uploaded_file:
                import_watchlist(uploaded_file)
        
        # 設定
        st.subheader("⚙️ 設定")
        
        auto_update = st.checkbox("自動更新", value=False, help="5分ごとに自動でデータ更新")
        
        if auto_update:
            st.info("⏰ 自動更新が有効です")


def export_watchlist():
    """監視リストのエクスポート"""
    try:
        export_data = {
            'watchlist': st.session_state.watchlist,
            'exported_at': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        st.download_button(
            label="📥 JSONファイルダウンロード",
            data=json_str,
            file_name=f"watchlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
    except Exception as e:
        st.error(f"エクスポートエラー: {e}")


def import_watchlist(uploaded_file):
    """監視リストのインポート"""
    try:
        content = uploaded_file.read()
        data = json.loads(content)
        
        if 'watchlist' in data:
            imported_symbols = data['watchlist']
            
            # 重複チェックして追加
            new_symbols = [s for s in imported_symbols if s not in st.session_state.watchlist]
            
            if new_symbols:
                st.session_state.watchlist.extend(new_symbols)
                st.success(f"✅ {len(new_symbols)}銘柄をインポートしました")
                st.rerun()
            else:
                st.info("インポートする新しい銘柄はありませんでした")
        else:
            st.error("無効なファイル形式です")
            
    except Exception as e:
        st.error(f"インポートエラー: {e}")


def main():
    """メイン関数"""
    # ページ設定
    st.set_page_config(
        page_title="監視リスト - 日本株ウォッチドッグ",
        page_icon="👀",
        layout="wide"
    )
    
    # 初期化
    initialize_watchlist_page()
    
    # ヘッダー
    render_watchlist_header()
    
    # サイドバー
    render_watchlist_sidebar()
    
    # メインコンテンツ
    render_watchlist_management()
    render_watchlist_overview()
    render_watchlist_comparison()


if __name__ == "__main__":
    main()