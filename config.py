"""
アプリケーション設定ファイル

環境変数またはこのファイルで設定を管理します。
環境変数が設定されている場合は、環境変数の値が優先されます。
"""

import os
from typing import Dict, Any

# API制限設定
API_RATE_LIMITS = {
    'yahoo_finance': {
        'requests_per_hour': int(os.getenv('YAHOO_API_HOURLY_LIMIT', '100')),
        'requests_per_minute': int(os.getenv('YAHOO_API_MINUTE_LIMIT', '10')),
        'timeout': int(os.getenv('YAHOO_API_TIMEOUT', '30'))
    },
    'j_quants': {
        'requests_per_hour': int(os.getenv('JQUANTS_API_HOURLY_LIMIT', '500')),
        'requests_per_minute': int(os.getenv('JQUANTS_API_MINUTE_LIMIT', '30')),
        'timeout': int(os.getenv('JQUANTS_API_TIMEOUT', '30'))
    }
}

# キャッシュ設定
CACHE_CONFIG = {
    'enable_cache': os.getenv('ENABLE_CACHE', 'true').lower() == 'true',
    'cache_ttl': int(os.getenv('CACHE_TTL', '900')),  # 15分
    'max_cache_size': int(os.getenv('MAX_CACHE_SIZE', '100'))
}

# データベース設定
DATABASE_CONFIG = {
    'db_path': os.getenv('DATABASE_PATH', 'data/stock_portfolio.db'),
    'echo': os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
}

# アプリケーション設定
APP_CONFIG = {
    'debug_mode': os.getenv('DEBUG_MODE', 'false').lower() == 'true',
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    'theme': os.getenv('APP_THEME', 'default')
}

# 推奨API制限プリセット
API_RATE_PRESETS = {
    'conservative': {
        'name': '控えめ',
        'requests_per_hour': 100,
        'requests_per_minute': 5,
        'description': 'APIエラーを最小限に抑える安全な設定'
    },
    'normal': {
        'name': '通常',
        'requests_per_hour': 200,
        'requests_per_minute': 10,
        'description': 'バランスの取れた標準的な設定'
    },
    'aggressive': {
        'name': '高頻度',
        'requests_per_hour': 300,
        'requests_per_minute': 20,
        'description': '大量のデータ取得に適した設定'
    },
    'maximum': {
        'name': '最大性能',
        'requests_per_hour': 500,
        'requests_per_minute': 30,
        'description': '最高のパフォーマンス（エラーリスクあり）'
    }
}

def get_config() -> Dict[str, Any]:
    """
    全設定を辞書形式で取得
    
    Returns:
        Dict[str, Any]: 設定辞書
    """
    return {
        'api_rate_limits': API_RATE_LIMITS,
        'cache': CACHE_CONFIG,
        'database': DATABASE_CONFIG,
        'app': APP_CONFIG,
        'presets': API_RATE_PRESETS
    }

def update_api_limits(source: str, requests_per_hour: int, requests_per_minute: int) -> None:
    """
    API制限を動的に更新
    
    Args:
        source: データソース名（'yahoo_finance' or 'j_quants'）
        requests_per_hour: 1時間あたりのリクエスト数
        requests_per_minute: 1分あたりのリクエスト数
    """
    if source in API_RATE_LIMITS:
        API_RATE_LIMITS[source]['requests_per_hour'] = requests_per_hour
        API_RATE_LIMITS[source]['requests_per_minute'] = requests_per_minute