"""
統一データ処理層 (FinancialDataProcessor)

全ての金融データの正規化・検証・異常値検出を担当する中核モジュール。
他のモジュールによる生データ直接アクセスを禁止し、データ整合性を保証する。
"""

from typing import TypedDict, Optional, List, Any, Dict
from decimal import Decimal, InvalidOperation
from enum import Enum
import logging
from datetime import datetime

# ログ設定
logger = logging.getLogger(__name__)


class WarningLevel(Enum):
    """警告レベルの定義"""
    MINOR = "🟡"
    WARNING = "🟠"
    CRITICAL = "🔴"


class DataWarning(TypedDict):
    """データ警告の型定義"""
    level: WarningLevel
    field: str
    message: str
    original_value: Any
    corrected_value: Any


class ProcessedData(TypedDict):
    """正規化済みデータの型定義"""
    symbol: str
    dividend_yield: Optional[Decimal]
    pe_ratio: Optional[Decimal]
    pb_ratio: Optional[Decimal]
    current_price: Optional[Decimal]
    market_cap: Optional[Decimal]
    shares_outstanding: Optional[Decimal]
    roe: Optional[Decimal]
    warnings: List[DataWarning]
    processed_at: datetime


class FinancialDataProcessor:
    """
    統一データ処理システム
    
    全ての金融データの正規化・検証・異常値検出を担当。
    データ整合性の絶対保証のため、全データは必ずここを経由する。
    """
    
    def __init__(self):
        """初期化"""
        self.validation_rules = {
            'dividend_yield': {'min': 0, 'max': 50, 'unit_error_threshold': 50},
            'pe_ratio': {'min': 0, 'max': 1000},
            'pb_ratio': {'min': 0, 'max': 50},
            'current_price': {'min': 1, 'max': 1000000},
            'roe': {'min': -100, 'max': 100}
        }
    
    def process_financial_data(self, raw_data: Dict[str, Any]) -> ProcessedData:
        """
        金融データの統一処理
        
        Args:
            raw_data: Yahoo Finance等から取得した生データ
            
        Returns:
            ProcessedData: 正規化・検証済みデータ
        """
        warnings = []
        
        # 基本情報
        symbol = str(raw_data.get('symbol', ''))
        
        # 配当利回りの処理
        dividend_yield = self._process_dividend_yield(
            raw_data.get('dividendYield'), warnings
        )
        
        # PER処理
        pe_ratio = self._process_pe_ratio(
            raw_data.get('trailingPE'), warnings
        )
        
        # PBR処理
        pb_ratio = self._process_pb_ratio(
            raw_data.get('priceToBook'), warnings
        )
        
        # 株価処理
        current_price = self._process_current_price(
            raw_data.get('currentPrice') or raw_data.get('regularMarketPrice'),
            warnings
        )
        
        # 時価総額処理
        market_cap = self._process_market_cap(
            raw_data.get('marketCap'), warnings
        )
        
        # 発行済株式数処理
        shares_outstanding = self._process_shares_outstanding(
            raw_data.get('sharesOutstanding'), warnings
        )
        
        # ROE処理
        roe = self._process_roe(
            raw_data.get('returnOnEquity'), warnings
        )
        
        # 整合性チェック
        self._validate_data_consistency(
            current_price, market_cap, shares_outstanding, warnings
        )
        
        # 結果作成
        result: ProcessedData = {
            'symbol': symbol,
            'dividend_yield': dividend_yield,
            'pe_ratio': pe_ratio,
            'pb_ratio': pb_ratio,
            'current_price': current_price,
            'market_cap': market_cap,
            'shares_outstanding': shares_outstanding,
            'roe': roe,
            'warnings': warnings,
            'processed_at': datetime.now()
        }
        
        # ログ記録
        self._log_processing_result(result)
        
        return result
    
    def _process_dividend_yield(self, value: Any, warnings: List[DataWarning]) -> Optional[Decimal]:
        """配当利回りの処理"""
        if value is None or value == 0:
            return None
        
        try:
            dividend_yield = Decimal(str(value))
            
            # Yahoo Finance APIは配当利回りを小数形式で返す（0.045 = 4.5%）
            # 1以下の値の場合は百分率に変換
            if 0 < dividend_yield <= 1:
                dividend_yield = dividend_yield * 100
                logger.info(f"Dividend yield converted from decimal to percentage: {value} → {dividend_yield}%")
            
            # 異常値チェック（50%以上は単位エラーの可能性）
            if dividend_yield > 50:
                corrected_value = dividend_yield / 100
                warnings.append({
                    'level': WarningLevel.CRITICAL,
                    'field': 'dividend_yield',
                    'message': f"配当利回り異常値検出: {dividend_yield}% → {corrected_value}%に修正",
                    'original_value': dividend_yield,
                    'corrected_value': corrected_value
                })
                return corrected_value
            
            # 合理的範囲チェック
            if dividend_yield < 0:
                warnings.append({
                    'level': WarningLevel.WARNING,
                    'field': 'dividend_yield',
                    'message': f"配当利回り負の値: {dividend_yield}% → Noneに変換",
                    'original_value': dividend_yield,
                    'corrected_value': None
                })
                return None
            
            return dividend_yield
            
        except (InvalidOperation, ValueError) as e:
            warnings.append({
                'level': WarningLevel.WARNING,
                'field': 'dividend_yield',
                'message': f"配当利回り変換エラー: {value}",
                'original_value': value,
                'corrected_value': None
            })
            return None
    
    def _process_pe_ratio(self, value: Any, warnings: List[DataWarning]) -> Optional[Decimal]:
        """PER処理"""
        if value is None:
            return None
        
        try:
            pe_ratio = Decimal(str(value))
            
            # 負の値チェック
            if pe_ratio < 0:
                warnings.append({
                    'level': WarningLevel.WARNING,
                    'field': 'pe_ratio',
                    'message': f"PER負の値: {pe_ratio} → Noneに変換",
                    'original_value': pe_ratio,
                    'corrected_value': None
                })
                return None
            
            # 異常に高い値チェック
            if pe_ratio > 1000:
                warnings.append({
                    'level': WarningLevel.WARNING,
                    'field': 'pe_ratio',
                    'message': f"PER異常高値: {pe_ratio} → 要確認",
                    'original_value': pe_ratio,
                    'corrected_value': pe_ratio
                })
            
            return pe_ratio
            
        except (InvalidOperation, ValueError):
            warnings.append({
                'level': WarningLevel.WARNING,
                'field': 'pe_ratio',
                'message': f"PER変換エラー: {value}",
                'original_value': value,
                'corrected_value': None
            })
            return None
    
    def _process_pb_ratio(self, value: Any, warnings: List[DataWarning]) -> Optional[Decimal]:
        """PBR処理"""
        if value is None:
            return None
        
        try:
            pb_ratio = Decimal(str(value))
            
            # 負の値チェック
            if pb_ratio < 0:
                warnings.append({
                    'level': WarningLevel.WARNING,
                    'field': 'pb_ratio',
                    'message': f"PBR負の値: {pb_ratio} → Noneに変換",
                    'original_value': pb_ratio,
                    'corrected_value': None
                })
                return None
            
            # 異常に高い値チェック
            if pb_ratio > 50:
                warnings.append({
                    'level': WarningLevel.WARNING,
                    'field': 'pb_ratio',
                    'message': f"PBR異常高値: {pb_ratio} → 要確認",
                    'original_value': pb_ratio,
                    'corrected_value': pb_ratio
                })
            
            return pb_ratio
            
        except (InvalidOperation, ValueError):
            warnings.append({
                'level': WarningLevel.WARNING,
                'field': 'pb_ratio',
                'message': f"PBR変換エラー: {value}",
                'original_value': value,
                'corrected_value': None
            })
            return None
    
    def _process_current_price(self, value: Any, warnings: List[DataWarning]) -> Optional[Decimal]:
        """株価処理"""
        if value is None:
            return None
        
        try:
            price = Decimal(str(value))
            
            # 株価ゼロ以下チェック
            if price <= 0:
                warnings.append({
                    'level': WarningLevel.CRITICAL,
                    'field': 'current_price',
                    'message': f"株価異常値: {price} → 要確認",
                    'original_value': price,
                    'corrected_value': None
                })
                return None
            
            return price
            
        except (InvalidOperation, ValueError):
            warnings.append({
                'level': WarningLevel.WARNING,
                'field': 'current_price',
                'message': f"株価変換エラー: {value}",
                'original_value': value,
                'corrected_value': None
            })
            return None
    
    def _process_market_cap(self, value: Any, warnings: List[DataWarning]) -> Optional[Decimal]:
        """時価総額処理"""
        if value is None:
            return None
        
        try:
            market_cap = Decimal(str(value))
            
            if market_cap <= 0:
                warnings.append({
                    'level': WarningLevel.WARNING,
                    'field': 'market_cap',
                    'message': f"時価総額異常値: {market_cap}",
                    'original_value': market_cap,
                    'corrected_value': None
                })
                return None
            
            return market_cap
            
        except (InvalidOperation, ValueError):
            warnings.append({
                'level': WarningLevel.WARNING,
                'field': 'market_cap',
                'message': f"時価総額変換エラー: {value}",
                'original_value': value,
                'corrected_value': None
            })
            return None
    
    def _process_shares_outstanding(self, value: Any, warnings: List[DataWarning]) -> Optional[Decimal]:
        """発行済株式数処理"""
        if value is None:
            return None
        
        try:
            shares = Decimal(str(value))
            
            if shares <= 0:
                warnings.append({
                    'level': WarningLevel.WARNING,
                    'field': 'shares_outstanding',
                    'message': f"発行済株式数異常値: {shares}",
                    'original_value': shares,
                    'corrected_value': None
                })
                return None
            
            return shares
            
        except (InvalidOperation, ValueError):
            warnings.append({
                'level': WarningLevel.WARNING,
                'field': 'shares_outstanding',
                'message': f"発行済株式数変換エラー: {value}",
                'original_value': value,
                'corrected_value': None
            })
            return None
    
    def _process_roe(self, value: Any, warnings: List[DataWarning]) -> Optional[Decimal]:
        """ROE処理"""
        if value is None:
            return None
        
        try:
            roe = Decimal(str(value))
            
            # Yahoo Finance APIはROEを小数形式で返す場合がある（0.15 = 15%）
            # 1以下の値の場合は百分率に変換
            if -1 <= roe <= 1 and roe != 0:
                roe = roe * 100
                logger.info(f"ROE converted from decimal to percentage: {value} → {roe}%")
            
            # ROEの異常値チェック
            if roe > 100 or roe < -100:
                warnings.append({
                    'level': WarningLevel.WARNING,
                    'field': 'roe',
                    'message': f"ROE異常値: {roe}% → 要確認",
                    'original_value': value,
                    'corrected_value': roe
                })
            
            return roe
            
        except (InvalidOperation, ValueError):
            warnings.append({
                'level': WarningLevel.WARNING,
                'field': 'roe',
                'message': f"ROE変換エラー: {value}",
                'original_value': value,
                'corrected_value': None
            })
            return None
    
    def _validate_data_consistency(
        self, 
        current_price: Optional[Decimal], 
        market_cap: Optional[Decimal], 
        shares_outstanding: Optional[Decimal],
        warnings: List[DataWarning]
    ) -> None:
        """データ整合性チェック"""
        
        # 時価総額 = 株価 × 発行済株式数の整合性チェック
        if all([current_price, market_cap, shares_outstanding]):
            calculated_market_cap = current_price * shares_outstanding
            
            # 10%以上の差異があれば警告
            if abs(calculated_market_cap - market_cap) / market_cap > 0.1:
                warnings.append({
                    'level': WarningLevel.WARNING,
                    'field': 'market_cap_consistency',
                    'message': f"時価総額整合性エラー: 計算値{calculated_market_cap} vs 取得値{market_cap}",
                    'original_value': market_cap,
                    'corrected_value': calculated_market_cap
                })
    
    def _log_processing_result(self, result: ProcessedData) -> None:
        """処理結果のログ記録"""
        critical_warnings = [w for w in result['warnings'] if w['level'] == WarningLevel.CRITICAL]
        warning_warnings = [w for w in result['warnings'] if w['level'] == WarningLevel.WARNING]
        
        if critical_warnings:
            logger.error(f"Critical warnings for {result['symbol']}: {len(critical_warnings)} issues")
        elif warning_warnings:
            logger.warning(f"Warnings for {result['symbol']}: {len(warning_warnings)} issues")
        else:
            logger.info(f"Successfully processed {result['symbol']} with no warnings")
    
    def get_summary_stats(self, processed_data_list: List[ProcessedData]) -> Dict[str, Any]:
        """処理統計の取得"""
        total_symbols = len(processed_data_list)
        symbols_with_warnings = len([d for d in processed_data_list if d['warnings']])
        total_warnings = sum(len(d['warnings']) for d in processed_data_list)
        
        return {
            'total_symbols': total_symbols,
            'symbols_with_warnings': symbols_with_warnings,
            'total_warnings': total_warnings,
            'warning_rate': symbols_with_warnings / total_symbols if total_symbols > 0 else 0
        }
    
    def validate_portfolio_data(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ポートフォリオデータ（CSV由来）の検証と正規化
        
        Args:
            portfolio_data: CSVから読み込んだポートフォリオデータ
            
        Returns:
            Dict[str, Any]: 検証・正規化済みのポートフォリオデータ
        """
        warnings = []
        
        # 銘柄コード
        symbol = str(portfolio_data.get('symbol', '')).strip()
        
        # 保有数量の検証
        quantity = float(portfolio_data.get('quantity', 0))
        if quantity <= 0:
            warnings.append({
                'level': WarningLevel.CRITICAL,
                'field': 'quantity',
                'message': f"無効な保有数量: {quantity}",
                'original_value': quantity,
                'corrected_value': None
            })
            quantity = 0
        elif quantity > 1000000:  # 100万株以上は異常値の可能性
            warnings.append({
                'level': WarningLevel.WARNING,
                'field': 'quantity',
                'message': f"非常に大きな保有数量: {quantity:,.0f}株",
                'original_value': quantity,
                'corrected_value': quantity
            })
        
        # 平均取得価格の検証
        average_price = float(portfolio_data.get('average_price', 0))
        if average_price <= 0:
            warnings.append({
                'level': WarningLevel.CRITICAL,
                'field': 'average_price',
                'message': f"無効な平均取得価格: {average_price}",
                'original_value': average_price,
                'corrected_value': None
            })
            average_price = 0
        elif average_price > 1000000:  # 100万円以上は異常値の可能性
            warnings.append({
                'level': WarningLevel.WARNING,
                'field': 'average_price',
                'message': f"非常に高い平均取得価格: ¥{average_price:,.0f}",
                'original_value': average_price,
                'corrected_value': average_price
            })
        
        # 現在価格の検証（オプション）
        current_price = portfolio_data.get('current_price')
        if current_price is not None:
            current_price = float(current_price)
            if current_price <= 0:
                warnings.append({
                    'level': WarningLevel.WARNING,
                    'field': 'current_price',
                    'message': f"無効な現在価格: {current_price}",
                    'original_value': current_price,
                    'corrected_value': None
                })
                current_price = None
        
        # 評価額の整合性チェック（オプション）
        market_value = portfolio_data.get('market_value')
        if market_value is not None and current_price is not None and quantity > 0:
            market_value = float(market_value)
            expected_value = current_price * quantity
            
            # 10%以上の乖離は警告
            if abs(market_value - expected_value) / expected_value > 0.1:
                warnings.append({
                    'level': WarningLevel.WARNING,
                    'field': 'market_value',
                    'message': f"評価額の不整合: 記載 ¥{market_value:,.0f} vs 計算値 ¥{expected_value:,.0f}",
                    'original_value': market_value,
                    'corrected_value': expected_value
                })
        
        # 検証済みデータを返す
        return {
            'symbol': symbol,
            'name': portfolio_data.get('name', ''),
            'quantity': quantity,
            'average_price': average_price,
            'current_price': current_price,
            'market_value': market_value,
            'warnings': warnings,
            'data_source': 'csv',
            'processed_at': datetime.now()
        }