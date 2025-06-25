"""
Pages Package

Streamlit UI層のパッケージ初期化ファイル
各ページモジュールをインポート可能にする
"""

# バージョン情報
__version__ = "0.3.0"
__author__ = "日本株ウォッチドッグ開発チーム"

# ページモジュールの明示的なインポート
from . import strategy
from . import charts
from . import portfolio
from . import watchlist

# パッケージ情報
__all__ = [
    'strategy',
    'charts', 
    'portfolio',
    'watchlist'
]