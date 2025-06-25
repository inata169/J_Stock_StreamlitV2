"""
投資戦略分析画面

統一プロセッサを経由した投資戦略分析結果をStreamlitで表示。
5つの投資戦略（ディフェンシブ・グロース・バリュー・配当・モメンタム）による
包括的な分析を提供。
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List
import logging
from datetime import datetime

# コアモジュールのインポート
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.multi_data_source import MultiDataSourceManager, DataFetchError, APIRateLimitError
from core.investment_strategies import InvestmentStrategyAnalyzer, RecommendationLevel
from core.chart_data_manager import ChartDataManager

# ログ設定
logger = logging.getLogger(__name__)


def initialize_strategy_page():
    """戦略分析ページの初期化"""
    if 'data_source_manager' not in st.session_state:
        st.session_state.data_source_manager = MultiDataSourceManager()
    
    if 'strategy_analyzer' not in st.session_state:
        st.session_state.strategy_analyzer = InvestmentStrategyAnalyzer()
    
    if 'chart_manager' not in st.session_state:
        st.session_state.chart_manager = ChartDataManager(st.session_state.data_source_manager)
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}


def render_strategy_analysis_header():
    """ヘッダー部分のレンダリング"""
    st.title("🎯 投資戦略分析")
    st.markdown("""
    **5つの投資戦略による包括的分析**
    - 📊 **ディフェンシブ戦略**: 低リスク・安定配当重視
    - 🚀 **グロース戦略**: 成長性重視
    - 💎 **バリュー戦略**: 割安性重視  
    - 💰 **配当戦略**: 配当収入重視
    - ⚡ **モメンタム戦略**: 市場の勢い重視
    
    ⚠️ **学習・研究専用ツール** - 投資判断は必ずご自身の責任で行ってください
    """)


def render_symbol_input_section():
    """銘柄入力セクション"""
    st.subheader("📋 分析対象銘柄の選択")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        symbol_input = st.text_input(
            "銘柄コードを入力",
            value="",
            placeholder="例: 1928.T (積水ハウス), 7203.T (トヨタ), AAPL (Apple)",
            help="日本株: 4桁コード.T、米国株: ティッカーシンボル"
        )
    
    with col2:
        analyze_button = st.button(
            "📊 分析実行",
            type="primary",
            use_container_width=True
        )
    
    # サンプル銘柄ボタン
    st.markdown("**クイック選択:**")
    col1, col2, col3, col4 = st.columns(4)
    
    sample_symbols = [
        ("1928.T", "積水ハウス"),
        ("7203.T", "トヨタ"),
        ("6758.T", "ソニー"),
        ("AAPL", "Apple")
    ]
    
    selected_sample = None
    for i, (symbol, name) in enumerate(sample_symbols):
        col = [col1, col2, col3, col4][i]
        if col.button(f"{name}\n{symbol}", key=f"sample_{i}"):
            selected_sample = symbol
    
    # 分析実行ロジック
    target_symbol = selected_sample or symbol_input
    
    if analyze_button or selected_sample:
        if target_symbol:
            execute_strategy_analysis(target_symbol)
        else:
            st.error("銘柄コードを入力してください")


def execute_strategy_analysis(symbol: str):
    """戦略分析の実行"""
    try:
        with st.spinner(f"📈 {symbol} を分析中..."):
            # データ取得
            data_source = st.session_state.data_source_manager
            strategy_analyzer = st.session_state.strategy_analyzer
            
            # 株式データ取得
            stock_data = data_source.get_stock_info(symbol)
            
            # 包括的戦略分析実行
            comprehensive_analysis = strategy_analyzer.get_comprehensive_analysis(stock_data)
            
            # 結果をセッションに保存
            st.session_state.analysis_results[symbol] = {
                'stock_data': stock_data,
                'analysis': comprehensive_analysis,
                'analyzed_at': datetime.now()
            }
            
            st.success(f"✅ {symbol} の分析が完了しました")
            
    except APIRateLimitError as e:
        st.error(f"🚫 API制限エラー: {str(e)}")
        st.info("しばらく時間をおいてから再試行してください")
        
    except DataFetchError as e:
        st.error(f"📡 データ取得エラー: {str(e)}")
        st.info("銘柄コードが正しいか確認してください")
        
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {str(e)}")
        logger.error(f"Strategy analysis error for {symbol}: {e}")


def render_analysis_results():
    """分析結果の表示"""
    if not st.session_state.analysis_results:
        st.info("👆 上記で銘柄を選択して分析を実行してください")
        return
    
    # 分析結果の選択
    available_symbols = list(st.session_state.analysis_results.keys())
    
    if len(available_symbols) == 1:
        selected_symbol = available_symbols[0]
    else:
        selected_symbol = st.selectbox(
            "表示する分析結果を選択",
            available_symbols,
            index=len(available_symbols) - 1  # 最新の結果を選択
        )
    
    if selected_symbol:
        display_analysis_for_symbol(selected_symbol)


def display_analysis_for_symbol(symbol: str):
    """特定銘柄の分析結果表示"""
    result_data = st.session_state.analysis_results[symbol]
    stock_data = result_data['stock_data']
    analysis = result_data['analysis']
    
    st.subheader(f"📊 {symbol} 分析結果")
    
    # 基本情報表示
    render_basic_info(stock_data)
    
    # 総合スコア表示
    render_overall_score(analysis)
    
    # 戦略別詳細結果
    render_strategy_details(analysis)
    
    # チャート表示
    render_strategy_charts(symbol, analysis)
    
    # データ品質情報
    render_data_quality_info(analysis)


def render_basic_info(stock_data):
    """基本情報の表示"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_price = stock_data.get('current_price')
        st.metric(
            "現在価格", 
            f"¥{float(current_price):,.0f}" if current_price else "N/A"
        )
    
    with col2:
        dividend_yield = stock_data.get('dividend_yield')
        st.metric(
            "配当利回り",
            f"{float(dividend_yield):.2f}%" if dividend_yield else "N/A"
        )
    
    with col3:
        pe_ratio = stock_data.get('pe_ratio')
        st.metric(
            "PER",
            f"{float(pe_ratio):.1f}倍" if pe_ratio else "N/A"
        )
    
    with col4:
        pb_ratio = stock_data.get('pb_ratio')
        st.metric(
            "PBR",
            f"{float(pb_ratio):.2f}倍" if pb_ratio else "N/A"
        )


def render_overall_score(analysis):
    """総合スコアの表示"""
    st.subheader("🎯 総合評価")
    
    col1, col2, col3 = st.columns([2, 2, 3])
    
    with col1:
        overall_score = analysis.get('overall_score', 0)
        st.metric(
            "総合スコア",
            f"{overall_score:.1f}点",
            delta=None
        )
    
    with col2:
        best_strategy = analysis.get('best_strategy', 'N/A')
        best_score = analysis.get('best_strategy_score', 0)
        st.metric(
            "最適戦略",
            best_strategy,
            delta=f"{best_score}点"
        )
    
    with col3:
        # スコア分布可視化
        score_data = []
        for strategy_name, result in analysis.get('strategy_results', {}).items():
            score_data.append({
                'strategy': strategy_name,
                'score': result['score_percentage']
            })
        
        if score_data:
            df = pd.DataFrame(score_data)
            st.bar_chart(df.set_index('strategy'))


def render_strategy_details(analysis):
    """戦略別詳細結果の表示"""
    st.subheader("📋 戦略別詳細分析")
    
    strategy_results = analysis.get('strategy_results', {})
    
    for strategy_name, result in strategy_results.items():
        with st.expander(f"{strategy_name} - {result['score_percentage']:.1f}点"):
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**✅ 満たした条件:**")
                for criteria in result['criteria_met']:
                    st.markdown(f"- {criteria}")
            
            with col2:
                st.markdown("**❌ 満たさなかった条件:**")
                for criteria in result['criteria_failed']:
                    st.markdown(f"- {criteria}")
            
            # 推奨レベルと信頼度
            recommendation = result['recommendation']
            confidence = result['confidence']
            
            col3, col4 = st.columns(2)
            with col3:
                st.metric("推奨レベル", recommendation)
            with col4:
                st.metric("信頼度", f"{confidence*100:.1f}%")


def render_strategy_charts(symbol: str, analysis: Dict[str, Any]):
    """戦略分析チャートの表示"""
    st.subheader("📈 視覚的分析")
    
    chart_manager = st.session_state.chart_manager
    
    # 戦略比較チャート
    strategy_chart = chart_manager.create_strategy_comparison_chart(analysis)
    st.plotly_chart(strategy_chart, use_container_width=True)
    
    # 財務指標レーダーチャート
    try:
        stock_data = st.session_state.analysis_results[symbol]['stock_data']
        radar_chart = chart_manager.create_financial_metrics_radar(symbol)
        st.plotly_chart(radar_chart, use_container_width=True)
    except Exception as e:
        logger.warning(f"Radar chart creation failed: {e}")
        st.warning("財務指標レーダーチャートの生成でエラーが発生しました")


def render_data_quality_info(analysis):
    """データ品質情報の表示"""
    data_quality = analysis.get('data_quality', {})
    
    with st.expander("🔍 データ品質情報"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            warnings_count = data_quality.get('warnings_count', 0)
            st.metric("警告数", warnings_count)
        
        with col2:
            critical_warnings = data_quality.get('critical_warnings', 0)
            st.metric("重要警告", critical_warnings)
        
        with col3:
            available_metrics = data_quality.get('available_metrics', 0)
            st.metric("利用可能指標", f"{available_metrics}/4")
        
        if warnings_count > 0:
            st.warning("⚠️ データに警告があります。分析結果は参考程度にお考えください。")


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
        page_title="投資戦略分析 - 日本株ウォッチドッグ",
        page_icon="🎯",
        layout="wide"
    )
    
    # 初期化
    initialize_strategy_page()
    
    # ヘッダー
    render_strategy_analysis_header()
    
    # サイドバー
    render_api_status_sidebar()
    
    # メインコンテンツ
    render_symbol_input_section()
    render_analysis_results()


if __name__ == "__main__":
    main()