"""
日本株ウォッチドッグ - 株式市場学習ツール Web版

メインアプリケーション・ナビゲーションハブ
統一データ処理アーキテクチャに基づくStreamlit Webアプリケーション
"""

import streamlit as st
import logging
from datetime import datetime
import sys
import os

# v2.0.0データベース初期化
from core.database_init import initialize_stock_database

# ページのインポート
from pages import strategy, charts, portfolio, watchlist
from core.multi_data_source import MultiDataSourceManager

# 設定のインポート
import config
from version import get_full_version_string

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def configure_page():
    """ページ基本設定"""
    st.set_page_config(
        page_title="日本株ウォッチドッグ - 株式学習ツール",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/inata169/J_Stock_StreamlitV2',
            'Report a bug': 'https://github.com/inata169/J_Stock_StreamlitV2/issues',
            'About': f"""
            # 日本株ウォッチドッグ {get_full_version_string()}
            
            株式市場学習・研究専用ツール（新統一データベース版）
            
            **v2.1.0 新機能:**
            - 🎛️ API制限リアルタイム監視・調整機能
            - ⚙️ config.py + .env 設定管理システム
            - 📚 仮想環境対応インストール手順
            - 📂 データ保存場所の詳細ドキュメント
            - 🏷️ MITライセンス対応
            
            **v2.0.0 新機能:**
            - 🏗️ 「両方の真実保持」データベース設計
            - 📊 EnhancedCSVParser（32件データ正常処理）
            - 💾 SQLite永続化ストレージ
            - ⚡ 適応的API制限管理システム
            - 🎯 統一銘柄コード（9432.T→9432）
            - ✅ J-Quants統合準備完了（95%適合性）
            
            **データソース:**
            - SBI・楽天証券CSV（自動エンコーディング検出）
            - Yahoo Finance API（リアルタイム株価・財務指標）
            - J-Quants API対応（Phase 2予定）
            
            **重要:** このツールは学習・研究専用です。
            投資判断は必ずご自身の責任で行ってください。
            """
        }
    )


def initialize_session_state():
    """セッション状態の初期化（v2.0.0対応）"""
    # v2.0.0: データベース初期化（初回のみ）
    if 'database_initialized' not in st.session_state:
        try:
            success = initialize_stock_database()
            st.session_state.database_initialized = success
            if success:
                logger.info("Database initialized successfully")
            else:
                logger.error("Database initialization failed")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            st.session_state.database_initialized = False
    
    # アプリケーション状態
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'portfolio'
    
    if 'app_started_at' not in st.session_state:
        st.session_state.app_started_at = datetime.now()
    
    if 'page_visit_count' not in st.session_state:
        st.session_state.page_visit_count = {}
    
    # UI設定
    if 'show_debug_info' not in st.session_state:
        st.session_state.show_debug_info = False
    
    if 'theme' not in st.session_state:
        st.session_state.theme = 'default'
    
    # データ管理
    if 'last_update_time' not in st.session_state:
        st.session_state.last_update_time = datetime.now()
    
    if 'api_error_count' not in st.session_state:
        st.session_state.api_error_count = 0
    
    # データソースマネージャー
    if 'data_source_manager' not in st.session_state:
        manager = MultiDataSourceManager()
        # config.pyから設定を適用
        yahoo_limits = config.API_RATE_LIMITS['yahoo_finance']
        manager.api_limits['yahoo_finance']['requests_per_hour'] = yahoo_limits['requests_per_hour']
        manager.api_limits['yahoo_finance']['requests_per_minute'] = yahoo_limits['requests_per_minute']
        st.session_state.data_source_manager = manager
    
    # API制限設定（config.pyから読み込み）
    if 'api_rate_limits' not in st.session_state:
        yahoo_limits = config.API_RATE_LIMITS['yahoo_finance']
        st.session_state.api_rate_limits = {
            'requests_per_hour': yahoo_limits['requests_per_hour'],
            'requests_per_minute': yahoo_limits['requests_per_minute']
        }


def render_sidebar_navigation():
    """サイドバーナビゲーション"""
    with st.sidebar:
        # アプリケーションヘッダー
        st.title("📊 日本株ウォッチドッグ")
        st.caption(get_full_version_string())
        
        st.markdown("---")
        
        # メインナビゲーション
        st.subheader("📋 メニュー")
        
        pages = {
            'portfolio': {
                'name': '📊 ポートフォリオ管理',
                'description': 'CSV連携・投資アドバイス'
            },
            'watchlist': {
                'name': '👀 監視リスト',
                'description': '欲しい銘柄追跡・分析'
            },
            'strategy': {
                'name': '🎯 投資戦略分析',
                'description': '5戦略による総合評価'
            },
            'charts': {
                'name': '📈 金融チャート',
                'description': '配当・財務可視化'
            }
        }
        
        # ページ選択
        for page_key, page_info in pages.items():
            if st.button(
                page_info['name'],
                key=f"nav_{page_key}",
                use_container_width=True,
                help=page_info['description']
            ):
                st.session_state.current_page = page_key
                # 訪問回数カウント
                if page_key not in st.session_state.page_visit_count:
                    st.session_state.page_visit_count[page_key] = 0
                st.session_state.page_visit_count[page_key] += 1
                st.rerun()
        
        st.markdown("---")
        
        # アプリケーション情報
        render_app_status_sidebar()
        
        # 重要警告
        render_important_notice()


def render_app_status_sidebar():
    """アプリケーション状況サイドバー"""
    st.subheader("📊 アプリ状況")
    
    # 稼働時間
    uptime = datetime.now() - st.session_state.app_started_at
    hours, remainder = divmod(uptime.total_seconds(), 3600)
    minutes, _ = divmod(remainder, 60)
    st.metric("稼働時間", f"{int(hours):02d}:{int(minutes):02d}")
    
    # 現在のページ
    current_page_name = {
        'portfolio': 'ポートフォリオ管理',
        'watchlist': '監視リスト',
        'strategy': '投資戦略分析',
        'charts': '金融チャート'
    }.get(st.session_state.current_page, '不明')
    
    st.metric("現在のページ", current_page_name)
    
    # API使用状況
    render_api_usage_stats()
    
    # セッション管理
    with st.expander("🔧 セッション管理"):
        if st.button("🔄 セッションリセット", use_container_width=True):
            # 重要なデータ以外をクリア
            keys_to_keep = ['app_started_at', 'current_page']
            keys_to_remove = [key for key in st.session_state.keys() if key not in keys_to_keep]
            
            for key in keys_to_remove:
                del st.session_state[key]
            
            st.success("セッションをリセットしました")
            st.rerun()
        
        # デバッグ情報表示切り替え
        st.session_state.show_debug_info = st.checkbox(
            "デバッグ情報表示",
            value=st.session_state.show_debug_info
        )


def render_api_usage_stats():
    """API使用状況の表示と設定"""
    st.markdown("---")
    st.subheader("🌐 API使用状況")
    
    # 現在の使用状況を取得
    if hasattr(st.session_state, 'data_source_manager'):
        stats = st.session_state.data_source_manager.get_api_usage_stats()
        
        # 使用状況の表示
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "過去1時間",
                f"{stats['requests_last_hour']}/{stats['hourly_limit']}",
                delta=f"{stats['hourly_remaining']}残"
            )
        with col2:
            st.metric(
                "過去1分",
                f"{stats['requests_last_minute']}/{stats['minute_limit']}",
                delta=None
            )
        
        # プログレスバー
        hourly_usage = stats['requests_last_hour'] / stats['hourly_limit']
        st.progress(hourly_usage, text=f"時間制限: {hourly_usage * 100:.1f}%")
    
    # API制限設定
    with st.expander("⚙️ API制限設定"):
        st.info("APIレート制限を調整できます。デフォルト値は控えめに設定されています。")
        
        # 時間あたりの制限
        new_hourly_limit = st.slider(
            "1時間あたりのリクエスト数",
            min_value=50,
            max_value=500,
            value=st.session_state.api_rate_limits['requests_per_hour'],
            step=10,
            help="Yahoo Finance APIの1時間あたりの最大リクエスト数"
        )
        
        # 分あたりの制限
        new_minute_limit = st.slider(
            "1分あたりのリクエスト数",
            min_value=5,
            max_value=30,
            value=st.session_state.api_rate_limits['requests_per_minute'],
            step=1,
            help="Yahoo Finance APIの1分あたりの最大リクエスト数"
        )
        
        # 設定の適用
        if st.button("設定を適用", use_container_width=True):
            # セッション状態を更新
            st.session_state.api_rate_limits['requests_per_hour'] = new_hourly_limit
            st.session_state.api_rate_limits['requests_per_minute'] = new_minute_limit
            
            # データソースマネージャーに適用
            if hasattr(st.session_state, 'data_source_manager'):
                st.session_state.data_source_manager.api_limits['yahoo_finance']['requests_per_hour'] = new_hourly_limit
                st.session_state.data_source_manager.api_limits['yahoo_finance']['requests_per_minute'] = new_minute_limit
            
            st.success("API制限設定を更新しました")
            st.rerun()
        
        # 推奨設定
        st.caption("""
        **推奨設定:**
        - 通常使用: 100/時間、10/分
        - 高頻度使用: 200/時間、20/分
        - 最大性能: 300/時間、30/分
        
        ※Yahoo Finance APIの実際の制限に注意してください
        """)


def render_important_notice():
    """重要な注意事項"""
    st.markdown("---")
    st.subheader("⚠️ 重要事項")
    
    st.warning("""
    **学習・研究専用ツール**
    
    このアプリケーションは教育目的のみです：
    - 📚 株式市場の理解促進
    - 🧮 投資戦略の学習支援
    - 📊 データ分析スキル向上
    
    **投資判断は必ずご自身の責任で**
    """)
    
    # 推奨投資方針
    with st.expander("💡 推奨投資方針"):
        st.markdown("""
        **メイン投資（90-95%）:**
        - インデックス投資（オルカン等）
        - 長期・分散・積立
        
        **このツール（0%実投資）:**
        - 市場理解の学習ツールとして活用
        - 投資スキル向上の練習として利用
        """)


def render_debug_info():
    """デバッグ情報表示（開発者向け）"""
    if not st.session_state.show_debug_info:
        return
    
    with st.expander("🔧 デバッグ情報（開発者向け）"):
        debug_info = {
            'session_state_keys': list(st.session_state.keys()),
            'current_page': st.session_state.current_page,
            'page_visits': st.session_state.page_visit_count,
            'uptime_seconds': (datetime.now() - st.session_state.app_started_at).total_seconds(),
            'api_error_count': st.session_state.api_error_count,
            'last_update': st.session_state.last_update_time.isoformat(),
            
            # v2.0.0: データベース状況
            'database_initialized': st.session_state.get('database_initialized', False),
            'app_version': get_full_version_string()
        }
        st.json(debug_info)


def render_main_content():
    """メインコンテンツのレンダリング"""
    current_page = st.session_state.current_page
    
    try:
        # ページルーティング
        if current_page == 'portfolio':
            portfolio.main()
        elif current_page == 'watchlist':
            watchlist.main()
        elif current_page == 'strategy':
            strategy.main()
        elif current_page == 'charts':
            charts.main()
        else:
            st.error(f"未知のページ: {current_page}")
            st.session_state.current_page = 'portfolio'
            st.rerun()
    
    except Exception as e:
        logger.error(f"Page rendering error for {current_page}: {e}")
        st.error(f"ページの読み込みでエラーが発生しました: {str(e)}")
        
        # エラー詳細（デバッグモード時のみ）
        if st.session_state.show_debug_info:
            st.exception(e)
        
        # エラーリカバリ
        if st.button("🔄 ページを再読み込み"):
            st.rerun()


def render_footer():
    """フッター情報"""
    st.markdown("---")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"""
        **日本株ウォッチドッグ {get_full_version_string()}** | 
        統一データベースアーキテクチャ | 
        学習・研究専用ツール
        """)
    
    with col2:
        st.markdown("**データソース:** Yahoo Finance API")
    
    with col3:
        st.markdown(f"**最終更新:** {st.session_state.last_update_time.strftime('%H:%M:%S')}")


def main():
    """メイン関数"""
    try:
        # ページ設定
        configure_page()
        
        # セッション初期化
        initialize_session_state()
        
        # サイドバーナビゲーション
        render_sidebar_navigation()
        
        # メインコンテンツ
        render_main_content()
        
        # デバッグ情報（本番環境では無効化）
        # render_debug_info()
        
        # フッター
        render_footer()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error("アプリケーションでエラーが発生しました")
        
        if st.session_state.get('show_debug_info', False):
            st.exception(e)


if __name__ == "__main__":
    main()