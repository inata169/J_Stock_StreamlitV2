"""
API Rate Limit Manager Module
適応的API制限管理システム
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import deque
from enum import Enum

try:
    from .database_manager import DatabaseManager
except ImportError:
    from database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class Priority(Enum):
    """リクエスト優先度"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class APIRequest:
    """APIリクエスト情報"""
    api_name: str
    symbol: str
    request_type: str
    priority: Priority
    timestamp: datetime
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class APILimitConfig:
    """API制限設定"""
    requests_per_hour: int
    requests_per_minute: int = None
    burst_limit: int = None
    backoff_enabled: bool = True
    base_delay: float = 1.0
    max_delay: float = 300.0


class AdaptiveAPIManager:
    """適応的API制限管理クラス"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Args:
            db_manager: データベースマネージャー
        """
        self.db_manager = db_manager or DatabaseManager()
        
        # デフォルトAPI制限設定
        self.api_configs = {
            'yahoo_finance': APILimitConfig(
                requests_per_hour=100,
                requests_per_minute=10,
                burst_limit=5,
                backoff_enabled=True
            ),
            'j_quants': APILimitConfig(
                requests_per_hour=500,
                requests_per_minute=30,
                burst_limit=10,
                backoff_enabled=True
            )
        }
        
        # リクエスト履歴（メモリキャッシュ）
        self.request_history = {}  # api_name -> deque of timestamps
        self.request_queues = {}   # api_name -> priority queue
        self.backoff_until = {}    # api_name -> datetime
        
        # 設定読み込み
        self._load_settings()
        
        # 履歴初期化
        for api_name in self.api_configs.keys():
            self.request_history[api_name] = deque()
            self.request_queues[api_name] = {priority: deque() for priority in Priority}
            self.backoff_until[api_name] = datetime.now()
    
    def _load_settings(self):
        """データベースから設定を読み込み"""
        try:
            settings = self.db_manager.get_setting('api_limits')
            if settings:
                for api_name, config in settings.items():
                    if api_name in self.api_configs and isinstance(config, dict):
                        # 設定を更新
                        current_config = self.api_configs[api_name]
                        current_config.requests_per_hour = config.get('requests', current_config.requests_per_hour)
                        if 'backoff_enabled' in config:
                            current_config.backoff_enabled = config['backoff_enabled']
                
                logger.info("API制限設定をデータベースから読み込み")
        except Exception as e:
            logger.warning(f"設定読み込みエラー: {e}")
    
    def can_make_request(self, api_name: str, priority: Priority = Priority.NORMAL) -> Tuple[bool, float]:
        """
        リクエスト可能かチェック
        
        Args:
            api_name: API名
            priority: リクエスト優先度
            
        Returns:
            Tuple[可能フラグ, 推奨待機時間（秒）]
        """
        if api_name not in self.api_configs:
            logger.warning(f"未知のAPI: {api_name}")
            return True, 0.0
        
        config = self.api_configs[api_name]
        now = datetime.now()
        
        # バックオフ期間中かチェック
        if now < self.backoff_until[api_name]:
            remaining = (self.backoff_until[api_name] - now).total_seconds()
            logger.debug(f"{api_name}: バックオフ期間中（残り{remaining:.1f}秒）")
            return False, remaining
        
        # 過去の履歴をクリーンアップ
        self._cleanup_history(api_name)
        
        # 現在の使用量を計算
        hour_count = self._count_requests_in_window(api_name, 3600)  # 1時間
        minute_count = self._count_requests_in_window(api_name, 60)  # 1分
        
        # 制限チェック
        hour_limit_ok = hour_count < config.requests_per_hour
        minute_limit_ok = (config.requests_per_minute is None or 
                          minute_count < config.requests_per_minute)
        
        # 優先度による制限緩和
        if priority == Priority.CRITICAL:
            # 緊急時は制限を緩和
            hour_limit_ok = hour_count < config.requests_per_hour * 1.2
        elif priority == Priority.HIGH:
            # 高優先度は少し緩和
            hour_limit_ok = hour_count < config.requests_per_hour * 1.1
        
        if hour_limit_ok and minute_limit_ok:
            return True, 0.0
        
        # 推奨待機時間を計算
        if not minute_limit_ok and config.requests_per_minute:
            wait_time = 60.0 / config.requests_per_minute
        else:
            wait_time = 3600.0 / config.requests_per_hour
        
        # 優先度による待機時間調整
        if priority == Priority.HIGH:
            wait_time *= 0.5
        elif priority == Priority.LOW:
            wait_time *= 2.0
        
        return False, wait_time
    
    def request_api_slot(self, api_name: str, symbol: str, request_type: str,
                        priority: Priority = Priority.NORMAL) -> bool:
        """
        APIスロットをリクエスト
        
        Args:
            api_name: API名
            symbol: 銘柄コード
            request_type: リクエスト種別
            priority: 優先度
            
        Returns:
            bool: 即座に実行可能ならTrue
        """
        can_request, wait_time = self.can_make_request(api_name, priority)
        
        if can_request:
            # 即座に実行可能
            self._record_request(api_name, symbol, request_type)
            return True
        else:
            # キューに追加
            request = APIRequest(
                api_name=api_name,
                symbol=symbol,
                request_type=request_type,
                priority=priority,
                timestamp=datetime.now()
            )
            
            self.request_queues[api_name][priority].append(request)
            logger.debug(f"{api_name}: リクエストをキューに追加 ({symbol}, 優先度: {priority.name})")
            return False
    
    def get_next_request(self, api_name: str) -> Optional[APIRequest]:
        """
        次に実行すべきリクエストを取得
        
        Args:
            api_name: API名
            
        Returns:
            APIRequest: 実行可能なリクエスト（なければNone）
        """
        if api_name not in self.request_queues:
            return None
        
        # 優先度順にチェック
        for priority in [Priority.CRITICAL, Priority.HIGH, Priority.NORMAL, Priority.LOW]:
            queue = self.request_queues[api_name][priority]
            
            while queue:
                request = queue.popleft()
                
                # リクエストが古すぎる場合はスキップ
                age = datetime.now() - request.timestamp
                if age > timedelta(hours=1):
                    logger.debug(f"古いリクエストをスキップ: {request.symbol}")
                    continue
                
                # 実行可能かチェック
                can_request, _ = self.can_make_request(api_name, request.priority)
                if can_request:
                    self._record_request(api_name, request.symbol, request.request_type)
                    return request
                else:
                    # まだ実行できない場合はキューに戻す
                    queue.appendleft(request)
                    return None
        
        return None
    
    def record_api_response(self, api_name: str, symbol: str, response_status: int,
                           processing_time_ms: int, error_message: str = None):
        """
        APIレスポンスを記録
        
        Args:
            api_name: API名
            symbol: 銘柄コード
            response_status: HTTPステータス
            processing_time_ms: 処理時間（ミリ秒）
            error_message: エラーメッセージ
        """
        # データベースにログ
        self.db_manager.log_api_usage(
            api_name=api_name,
            response_status=response_status,
            symbol=symbol,
            processing_time_ms=processing_time_ms
        )
        
        # エラーハンドリング
        if response_status == 429:  # Too Many Requests
            self._handle_rate_limit_exceeded(api_name)
        elif response_status >= 500:  # Server Error
            self._handle_server_error(api_name)
        elif response_status == 403:  # Forbidden
            self._handle_forbidden_error(api_name)
        
        logger.debug(f"API応答記録: {api_name} {symbol} - {response_status} ({processing_time_ms}ms)")
    
    def _record_request(self, api_name: str, symbol: str, request_type: str):
        """リクエスト実行を記録"""
        now = datetime.now()
        self.request_history[api_name].append(now)
        
        logger.debug(f"APIリクエスト実行: {api_name} {symbol} ({request_type})")
    
    def _cleanup_history(self, api_name: str):
        """古いリクエスト履歴をクリーンアップ"""
        cutoff = datetime.now() - timedelta(hours=1)
        history = self.request_history[api_name]
        
        while history and history[0] < cutoff:
            history.popleft()
    
    def _count_requests_in_window(self, api_name: str, window_seconds: int) -> int:
        """指定時間窓内のリクエスト数を計算"""
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        history = self.request_history[api_name]
        
        count = 0
        for timestamp in reversed(history):
            if timestamp >= cutoff:
                count += 1
            else:
                break
        
        return count
    
    def _handle_rate_limit_exceeded(self, api_name: str):
        """レート制限超過時の処理"""
        config = self.api_configs[api_name]
        
        if config.backoff_enabled:
            # 指数バックオフ
            current_delay = getattr(self, f'_{api_name}_delay', config.base_delay)
            new_delay = min(current_delay * 2, config.max_delay)
            setattr(self, f'_{api_name}_delay', new_delay)
            
            self.backoff_until[api_name] = datetime.now() + timedelta(seconds=new_delay)
            
            logger.warning(f"{api_name}: レート制限超過 - {new_delay:.1f}秒バックオフ")
        
        # 制限を一時的に厳しくする
        config.requests_per_hour = int(config.requests_per_hour * 0.8)
        logger.info(f"{api_name}: 制限を一時的に削減 ({config.requests_per_hour}/時間)")
    
    def _handle_server_error(self, api_name: str):
        """サーバーエラー時の処理"""
        # 短時間のバックオフ
        self.backoff_until[api_name] = datetime.now() + timedelta(seconds=30)
        logger.warning(f"{api_name}: サーバーエラー - 30秒バックオフ")
    
    def _handle_forbidden_error(self, api_name: str):
        """認証エラー時の処理"""
        # 長時間のバックオフ
        self.backoff_until[api_name] = datetime.now() + timedelta(minutes=30)
        logger.error(f"{api_name}: 認証エラー - 30分バックオフ")
    
    def get_api_status(self) -> Dict[str, Any]:
        """API使用状況を取得"""
        status = {}
        
        for api_name, config in self.api_configs.items():
            hour_count = self._count_requests_in_window(api_name, 3600)
            minute_count = self._count_requests_in_window(api_name, 60)
            
            queue_counts = {
                priority.name: len(self.request_queues[api_name][priority])
                for priority in Priority
            }
            
            backoff_remaining = max(0, (self.backoff_until[api_name] - datetime.now()).total_seconds())
            
            status[api_name] = {
                'requests_last_hour': hour_count,
                'requests_last_minute': minute_count,
                'hourly_limit': config.requests_per_hour,
                'minute_limit': config.requests_per_minute,
                'usage_percentage': (hour_count / config.requests_per_hour) * 100,
                'backoff_remaining': backoff_remaining,
                'queued_requests': queue_counts,
                'total_queued': sum(queue_counts.values())
            }
        
        return status
    
    def update_api_config(self, api_name: str, new_limits: Dict[str, Any]):
        """API制限設定を更新"""
        if api_name in self.api_configs:
            config = self.api_configs[api_name]
            
            if 'requests_per_hour' in new_limits:
                config.requests_per_hour = new_limits['requests_per_hour']
            if 'requests_per_minute' in new_limits:
                config.requests_per_minute = new_limits['requests_per_minute']
            if 'backoff_enabled' in new_limits:
                config.backoff_enabled = new_limits['backoff_enabled']
            
            # データベースに保存
            settings = self.db_manager.get_setting('api_limits') or {}
            settings[api_name] = {
                'requests': config.requests_per_hour,
                'backoff_enabled': config.backoff_enabled
            }
            self.db_manager.update_setting('api_limits', settings)
            
            logger.info(f"{api_name}: 制限設定更新 ({config.requests_per_hour}/時間)")


class UpdateStrategy:
    """更新戦略管理クラス"""
    
    STRATEGIES = {
        'conservative': {
            'interval_seconds': 3600,      # 1時間
            'batch_size': 10,
            'priority': Priority.LOW,
            'description': '控えめ更新（1時間毎、10銘柄ずつ）'
        },
        'normal': {
            'interval_seconds': 1800,      # 30分
            'batch_size': 20,
            'priority': Priority.NORMAL,
            'description': '標準更新（30分毎、20銘柄ずつ）'
        },
        'aggressive': {
            'interval_seconds': 900,       # 15分
            'batch_size': 50,
            'priority': Priority.HIGH,
            'description': '積極更新（15分毎、50銘柄ずつ）'
        },
        'realtime': {
            'interval_seconds': 300,       # 5分
            'batch_size': 100,
            'priority': Priority.HIGH,
            'description': 'リアルタイム更新（5分毎、100銘柄ずつ）'
        }
    }
    
    @classmethod
    def get_strategy(cls, strategy_name: str) -> Dict[str, Any]:
        """更新戦略を取得"""
        return cls.STRATEGIES.get(strategy_name, cls.STRATEGIES['normal'])
    
    @classmethod
    def list_strategies(cls) -> Dict[str, str]:
        """利用可能な戦略一覧を取得"""
        return {name: config['description'] for name, config in cls.STRATEGIES.items()}


# 便利関数
def get_api_manager(db_path: str = "stock_watchdog.db") -> AdaptiveAPIManager:
    """APIマネージャーのインスタンスを取得"""
    db_manager = DatabaseManager(db_path)
    return AdaptiveAPIManager(db_manager)


if __name__ == "__main__":
    # テスト実行
    print("=== API制限管理システムテスト ===")
    
    manager = AdaptiveAPIManager(DatabaseManager("test_api_manager.db"))
    
    # 制限チェックテスト
    print("\n🔍 制限チェックテスト:")
    for priority in [Priority.LOW, Priority.NORMAL, Priority.HIGH, Priority.CRITICAL]:
        can_request, wait_time = manager.can_make_request('yahoo_finance', priority)
        print(f"   {priority.name}: 可能={can_request}, 待機時間={wait_time:.1f}秒")
    
    # リクエスト実行テスト
    print("\n⚡ リクエスト実行テスト:")
    symbols = ['9432', '1928', '8316']
    for symbol in symbols:
        success = manager.request_api_slot('yahoo_finance', symbol, 'stock_info', Priority.NORMAL)
        print(f"   {symbol}: 即座実行={success}")
    
    # ステータス確認
    print("\n📊 API使用状況:")
    status = manager.get_api_status()
    for api_name, info in status.items():
        print(f"   {api_name}:")
        print(f"     使用率: {info['usage_percentage']:.1f}%")
        print(f"     キュー: {info['total_queued']}件")
        
    # 更新戦略一覧
    print("\n🎯 利用可能な更新戦略:")
    strategies = UpdateStrategy.list_strategies()
    for name, description in strategies.items():
        print(f"   {name}: {description}")
    
    print("\n✅ テスト完了")