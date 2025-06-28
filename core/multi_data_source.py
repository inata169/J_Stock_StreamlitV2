"""
データ取得層 (MultiDataSourceManager)

外部APIからの生データ取得を担当。取得した生データは即座に
FinancialDataProcessorに渡して正規化する。
"""

import yfinance as yf
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
from requests.exceptions import RequestException, Timeout

from .financial_data_processor import FinancialDataProcessor, ProcessedData
from .symbol_utils import SymbolNormalizer

# ログ設定
logger = logging.getLogger(__name__)


class DataFetchError(Exception):
    """データ取得エラー"""
    pass


class APIRateLimitError(Exception):
    """API制限エラー"""
    pass


class MultiDataSourceManager:
    """
    マルチデータソース管理システム
    
    外部APIからの生データ取得のみを担当。
    取得したデータは即座にFinancialDataProcessorで正規化する。
    """
    
    def __init__(self, enable_cache: bool = True):
        """
        初期化
        
        Args:
            enable_cache: キャッシュ機能の有効化
        """
        self.financial_processor = FinancialDataProcessor()
        self.enable_cache = enable_cache
        self.request_history = []  # API制限管理用
        self.cache = {}  # 簡易キャッシュ
        self.cache_ttl = 900  # 15分間キャッシュ
        
        # API制限設定
        self.api_limits = {
            'yahoo_finance': {
                'requests_per_hour': 100,
                'requests_per_minute': 5,
                'timeout': 30
            }
        }
    
    def get_stock_info(self, symbol: str, force_refresh: bool = False) -> ProcessedData:
        """
        株式情報の取得
        
        Args:
            symbol: 銘柄コード（例: "1234.T", "AAPL"）
            force_refresh: キャッシュを無視して強制更新
            
        Returns:
            ProcessedData: 正規化済み株式データ
            
        Raises:
            DataFetchError: データ取得失敗
            APIRateLimitError: API制限エラー
        """
        # キャッシュチェック
        if not force_refresh and self.enable_cache:
            cached_data = self._get_cached_data(symbol)
            if cached_data:
                logger.info(f"Using cached data for {symbol}")
                return cached_data
        
        # API制限チェック
        self._check_rate_limits()
        
        try:
            # Yahoo Finance APIから生データ取得
            raw_data = self._fetch_yahoo_data(symbol)
            
            # 統一プロセッサで即座に正規化
            normalized_data = self.financial_processor.process_financial_data(raw_data)
            
            # キャッシュに保存
            if self.enable_cache:
                self._cache_data(symbol, normalized_data)
            
            # リクエスト履歴記録
            self._record_request()
            
            logger.info(f"Successfully fetched and processed data for {symbol}")
            return normalized_data
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            raise DataFetchError(f"データ取得失敗: {symbol} - {str(e)}")
    
    def get_multiple_stocks(
        self, 
        symbols: List[str], 
        max_retries: int = 3,
        delay_between_requests: float = 1.0
    ) -> Dict[str, ProcessedData]:
        """
        複数銘柄の一括取得
        
        Args:
            symbols: 銘柄コードのリスト
            max_retries: 最大リトライ回数
            delay_between_requests: リクエスト間隔（秒）
            
        Returns:
            Dict[str, ProcessedData]: 銘柄コードとデータのマッピング
        """
        results = {}
        failed_symbols = []
        
        for i, symbol in enumerate(symbols):
            try:
                # API制限を考慮したリクエスト間隔
                if i > 0 and delay_between_requests > 0:
                    time.sleep(delay_between_requests)
                
                results[symbol] = self.get_stock_info(symbol)
                
            except (DataFetchError, APIRateLimitError) as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
                failed_symbols.append(symbol)
                
                # API制限エラーの場合は長めの待機
                if isinstance(e, APIRateLimitError):
                    logger.info("API rate limit hit, waiting 60 seconds...")
                    time.sleep(60)
        
        # 失敗した銘柄のリトライ
        if failed_symbols and max_retries > 0:
            logger.info(f"Retrying {len(failed_symbols)} failed symbols...")
            time.sleep(5)  # 少し待ってからリトライ
            
            retry_results = self.get_multiple_stocks(
                failed_symbols, 
                max_retries - 1, 
                delay_between_requests * 2  # 間隔を倍にして負荷軽減
            )
            results.update(retry_results)
        
        logger.info(f"Successfully fetched {len(results)}/{len(symbols)} symbols")
        return results
    
    def _fetch_yahoo_data(self, symbol: str) -> Dict[str, Any]:
        """
        Yahoo Finance APIからの生データ取得
        
        Args:
            symbol: 銘柄コード
            
        Returns:
            Dict[str, Any]: 生データ
        """
        try:
            # 日本株の場合は.T形式に変換
            if SymbolNormalizer.validate_japanese_stock(symbol):
                yahoo_symbol = SymbolNormalizer.to_yahoo_format(symbol)
                logger.info(f"Converting symbol: {symbol} → {yahoo_symbol}")
            else:
                yahoo_symbol = symbol
            
            # タイムアウト設定でTickerオブジェクト作成
            ticker = yf.Ticker(yahoo_symbol)
            
            # infoデータ取得（タイムアウト付き）
            info = ticker.info
            
            if not info or 'symbol' not in info:
                raise DataFetchError(f"No data available for symbol: {symbol}")
            
            # 必要な生データのみ抽出
            raw_data = {
                'symbol': symbol,
                'dividendYield': info.get('dividendYield'),
                'trailingPE': info.get('trailingPE'),
                'priceToBook': info.get('priceToBook'),
                'currentPrice': info.get('currentPrice') or info.get('regularMarketPrice'),
                'marketCap': info.get('marketCap'),
                'sharesOutstanding': info.get('sharesOutstanding'),
                'returnOnEquity': info.get('returnOnEquity'),
                'longName': info.get('longName', ''),
                'currency': info.get('currency', 'JPY'),
                'exchange': info.get('exchange', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'fetched_at': datetime.now().isoformat()
            }
            
            return raw_data
            
        except RequestException as e:
            logger.error(f"Network error fetching {symbol}: {e}")
            raise DataFetchError(f"ネットワークエラー: {symbol}")
            
        except Timeout as e:
            logger.error(f"Timeout error fetching {symbol}: {e}")
            raise DataFetchError(f"タイムアウトエラー: {symbol}")
            
        except Exception as e:
            logger.error(f"Unexpected error fetching {symbol}: {e}")
            raise DataFetchError(f"予期しないエラー: {symbol}")
    
    def get_dividend_history(self, symbol: str, period: str = "5y") -> Optional[Dict[str, Any]]:
        """
        配当履歴の取得
        
        Args:
            symbol: 銘柄コード
            period: 取得期間（"1y", "2y", "5y", "10y", "max"）
            
        Returns:
            Optional[Dict[str, Any]]: 配当履歴データ
        """
        try:
            # 日本株の場合は.T形式に変換
            if SymbolNormalizer.validate_japanese_stock(symbol):
                yahoo_symbol = SymbolNormalizer.to_yahoo_format(symbol)
            else:
                yahoo_symbol = symbol
                
            ticker = yf.Ticker(yahoo_symbol)
            dividends = ticker.dividends
            
            if dividends.empty:
                logger.info(f"No dividend history for {symbol}")
                return None
            
            # 期間でフィルタリング
            if period != "max":
                years = int(period.replace("y", ""))
                start_date = datetime.now() - timedelta(days=years * 365)
                dividends = dividends[dividends.index >= start_date]
            
            return {
                'symbol': symbol,
                'dividends': dividends.to_dict(),
                'period': period,
                'total_dividends': len(dividends),
                'latest_dividend': float(dividends.iloc[-1]) if not dividends.empty else 0,
                'fetched_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching dividend history for {symbol}: {e}")
            return None
    
    def get_price_history(
        self, 
        symbol: str, 
        period: str = "1y",
        interval: str = "1d"
    ) -> Optional[Dict[str, Any]]:
        """
        株価履歴の取得
        
        Args:
            symbol: 銘柄コード
            period: 取得期間
            interval: データ間隔
            
        Returns:
            Optional[Dict[str, Any]]: 株価履歴データ
        """
        try:
            # 日本株の場合は.T形式に変換
            if SymbolNormalizer.validate_japanese_stock(symbol):
                yahoo_symbol = SymbolNormalizer.to_yahoo_format(symbol)
            else:
                yahoo_symbol = symbol
                
            ticker = yf.Ticker(yahoo_symbol)
            history = ticker.history(period=period, interval=interval)
            
            if history.empty:
                logger.warning(f"No price history for {symbol}")
                return None
            
            return {
                'symbol': symbol,
                'history': history.to_dict('records'),
                'period': period,
                'interval': interval,
                'data_points': len(history),
                'fetched_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching price history for {symbol}: {e}")
            return None
    
    def _check_rate_limits(self) -> None:
        """API制限チェック"""
        current_time = datetime.now()
        
        # 過去1時間のリクエスト数チェック
        hour_ago = current_time - timedelta(hours=1)
        recent_requests = [
            req for req in self.request_history 
            if req > hour_ago
        ]
        
        if len(recent_requests) >= self.api_limits['yahoo_finance']['requests_per_hour']:
            raise APIRateLimitError("1時間あたりのAPI制限に達しました")
        
        # 過去1分間のリクエスト数チェック
        minute_ago = current_time - timedelta(minutes=1)
        recent_minute_requests = [
            req for req in self.request_history 
            if req > minute_ago
        ]
        
        if len(recent_minute_requests) >= self.api_limits['yahoo_finance']['requests_per_minute']:
            raise APIRateLimitError("1分間あたりのAPI制限に達しました")
    
    def _record_request(self) -> None:
        """リクエスト履歴の記録"""
        self.request_history.append(datetime.now())
        
        # 古い履歴の削除（メモリ節約）
        cutoff_time = datetime.now() - timedelta(hours=2)
        self.request_history = [
            req for req in self.request_history 
            if req > cutoff_time
        ]
    
    def _get_cached_data(self, symbol: str) -> Optional[ProcessedData]:
        """キャッシュからデータ取得"""
        if symbol not in self.cache:
            return None
        
        cached_item = self.cache[symbol]
        cache_time = cached_item['cached_at']
        
        # キャッシュの有効期限チェック
        if datetime.now() - cache_time > timedelta(seconds=self.cache_ttl):
            del self.cache[symbol]
            return None
        
        return cached_item['data']
    
    def _cache_data(self, symbol: str, data: ProcessedData) -> None:
        """データをキャッシュに保存"""
        self.cache[symbol] = {
            'data': data,
            'cached_at': datetime.now()
        }
        
        # キャッシュサイズ制限（100件まで）
        if len(self.cache) > 100:
            # 古いアイテムを削除
            oldest_symbol = min(
                self.cache.keys(),
                key=lambda k: self.cache[k]['cached_at']
            )
            del self.cache[oldest_symbol]
    
    def clear_cache(self) -> None:
        """キャッシュクリア"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_api_usage_stats(self) -> Dict[str, Any]:
        """API使用統計の取得"""
        current_time = datetime.now()
        hour_ago = current_time - timedelta(hours=1)
        minute_ago = current_time - timedelta(minutes=1)
        
        requests_last_hour = len([
            req for req in self.request_history 
            if req > hour_ago
        ])
        
        requests_last_minute = len([
            req for req in self.request_history 
            if req > minute_ago
        ])
        
        return {
            'requests_last_hour': requests_last_hour,
            'requests_last_minute': requests_last_minute,
            'hourly_limit': self.api_limits['yahoo_finance']['requests_per_hour'],
            'minute_limit': self.api_limits['yahoo_finance']['requests_per_minute'],
            'hourly_remaining': self.api_limits['yahoo_finance']['requests_per_hour'] - requests_last_hour,
            'cache_size': len(self.cache),
            'cache_enabled': self.enable_cache
        }