"""
日本株ウォッチドッグ - バージョン情報

このファイルでアプリケーション全体のバージョンを管理します。
"""

__version__ = "2.1.0"
__version_name__ = "統一データベース＋API制限設定版"

# バージョン履歴
VERSION_HISTORY = {
    "2.1.0": {
        "name": "統一データベース＋API制限設定版",
        "date": "2024-12-29",
        "features": [
            "🎛️ API制限リアルタイム監視・調整機能",
            "⚙️ config.py + .env 設定管理システム",
            "📚 仮想環境対応インストール手順",
            "📂 データ保存場所の詳細ドキュメント",
            "🏷️ MITライセンス対応",
            "📋 GitHub公開準備完了"
        ]
    },
    "2.0.0": {
        "name": "統一データベース版",
        "date": "2024-12-25",
        "features": [
            "🏗️ 「両方の真実保持」データベース設計",
            "📊 EnhancedCSVParser（32件データ正常処理）",
            "💾 SQLite永続化ストレージ",
            "⚡ 適応的API制限管理システム",
            "🎯 統一銘柄コード（9432.T→9432）",
            "✅ J-Quants統合準備完了（95%適合性）"
        ]
    },
    "0.3.0": {
        "name": "統一データ処理版",
        "date": "2024-12-20",
        "features": [
            "🎯 3段階警告システム（軽微/注意/重大）",
            "📊 包括的異常値検出（ROE/時価総額/出来高）",
            "✅ 実銘柄検証済み（積水ハウス他5銘柄）"
        ]
    }
}

def get_version_info():
    """バージョン情報を辞書形式で取得"""
    return {
        'version': __version__,
        'version_name': __version_name__,
        'full_name': f"v{__version__} - {__version_name__}",
        'history': VERSION_HISTORY
    }

def get_current_version():
    """現在のバージョン文字列を取得"""
    return f"v{__version__}"

def get_full_version_string():
    """完全なバージョン文字列を取得"""
    return f"v{__version__} - {__version_name__}"