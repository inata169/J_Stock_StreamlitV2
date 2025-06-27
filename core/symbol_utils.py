"""
Symbol Utils Module
銘柄コード正規化・変換ユーティリティ
"""

import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class SymbolNormalizer:
    """銘柄コード正規化クラス"""
    
    # 日本株銘柄コードのパターン
    JAPANESE_STOCK_PATTERN = re.compile(r'^[0-9]{4}$')
    
    # 各種フォーマットの変換ルール
    NORMALIZATION_RULES = [
        (r'^"([^"]+)"$', r'\1'),           # 引用符除去 "9432" → 9432
        (r'^(\d{4})\.T$', r'\1'),          # .T除去 9432.T → 9432
        (r'^(\d{4})\s.*$', r'\1'),         # スペース以降除去 "9432 NTT" → 9432
        (r'^\s*(\d{4})\s*$', r'\1'),       # 前後空白除去
    ]
    
    @classmethod
    def normalize(cls, symbol: str) -> Optional[str]:
        """
        銘柄コードを統一形式（4桁数字）に正規化
        
        Args:
            symbol: 元の銘柄コード（様々な形式）
            
        Returns:
            str: 正規化された銘柄コード（4桁）またはNone
            
        Examples:
            normalize("9432.T") → "9432"
            normalize('"1928"') → "1928"  
            normalize("8316 三井住友") → "8316"
            normalize("invalid") → None
        """
        if not symbol or not isinstance(symbol, str):
            logger.warning(f"無効な銘柄コード: {symbol}")
            return None
            
        cleaned_symbol = symbol.strip()
        
        # 各正規化ルールを適用
        for pattern, replacement in cls.NORMALIZATION_RULES:
            match = re.match(pattern, cleaned_symbol)
            if match:
                cleaned_symbol = re.sub(pattern, replacement, cleaned_symbol)
                break
        
        # 日本株銘柄コードの形式チェック
        if cls.JAPANESE_STOCK_PATTERN.match(cleaned_symbol):
            logger.debug(f"銘柄コード正規化: {symbol} → {cleaned_symbol}")
            return cleaned_symbol
        else:
            logger.warning(f"無効な日本株銘柄コード: {symbol} → {cleaned_symbol}")
            return None
    
    @classmethod
    def to_yahoo_format(cls, symbol: str) -> str:
        """
        統一形式からYahoo Finance形式に変換
        
        Args:
            symbol: 統一形式の銘柄コード（4桁）
            
        Returns:
            str: Yahoo Finance形式（.T付き）
            
        Examples:
            to_yahoo_format("9432") → "9432.T"
        """
        normalized = cls.normalize(symbol)
        if normalized:
            return f"{normalized}.T"
        else:
            raise ValueError(f"無効な銘柄コード: {symbol}")
    
    @classmethod
    def validate_japanese_stock(cls, symbol: str) -> bool:
        """
        日本株銘柄コードかどうか検証
        
        Args:
            symbol: 銘柄コード
            
        Returns:
            bool: 日本株の場合True
        """
        normalized = cls.normalize(symbol)
        return normalized is not None
    
    @classmethod
    def extract_symbols_from_csv_row(cls, row_data: dict) -> Tuple[Optional[str], str]:
        """
        CSV行データから銘柄コードを抽出・正規化
        
        Args:
            row_data: CSV行のデータ（辞書形式）
            
        Returns:
            Tuple[銘柄コード, 銘柄名]
        """
        # 銘柄コードの候補フィールド
        symbol_fields = [
            'symbol', '銘柄コード', '銘柄（コード）', 
            '銘柄コード・ティッカー', 'Symbol'
        ]
        
        # 銘柄名の候補フィールド
        name_fields = [
            'name', '銘柄名', '銘柄', '銘柄名称', '企業名'
        ]
        
        # 銘柄コードを抽出
        symbol = None
        for field in symbol_fields:
            if field in row_data and row_data[field]:
                symbol = cls.normalize(str(row_data[field]))
                if symbol:
                    break
        
        # 銘柄名を抽出
        name = ""
        for field in name_fields:
            if field in row_data and row_data[field]:
                name = str(row_data[field]).strip()
                break
        
        return symbol, name


class DecimalFormatter:
    """小数点桁数統一フォーマッター"""
    
    @staticmethod
    def format_price(value: float, decimals: int = 1) -> float:
        """
        価格を指定桁数に丸める
        
        Args:
            value: 元の価格
            decimals: 小数点以下桁数（デフォルト: 1）
            
        Returns:
            float: 丸められた価格
        """
        if value is None:
            return None
        return round(float(value), decimals)
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 1) -> float:
        """
        パーセント値を指定桁数に丸める
        
        Args:
            value: 元のパーセント値
            decimals: 小数点以下桁数（デフォルト: 1）
            
        Returns:
            float: 丸められたパーセント値
        """
        if value is None:
            return None
        return round(float(value), decimals)


# 便利関数
def normalize_symbol(symbol: str) -> Optional[str]:
    """銘柄コード正規化のショートカット関数"""
    return SymbolNormalizer.normalize(symbol)


def to_yahoo_symbol(symbol: str) -> str:
    """Yahoo Finance形式変換のショートカット関数"""
    return SymbolNormalizer.to_yahoo_format(symbol)


def format_decimal(value: float, decimals: int = 1) -> float:
    """小数点フォーマットのショートカット関数"""
    return DecimalFormatter.format_price(value, decimals)


# テスト用関数
def test_symbol_normalization():
    """銘柄コード正規化のテスト"""
    test_cases = [
        ('"9432"', '9432'),
        ('9432.T', '9432'),
        ('8316 三井住友', '8316'),
        ('  1928  ', '1928'),
        ('invalid', None),
        ('123', None),  # 3桁は無効
        ('12345', None),  # 5桁は無効
    ]
    
    print("=== 銘柄コード正規化テスト ===")
    for input_symbol, expected in test_cases:
        result = normalize_symbol(input_symbol)
        status = "✅" if result == expected else "❌"
        result_str = str(result) if result is not None else "None"
        expected_str = str(expected) if expected is not None else "None"
        print(f"{status} {input_symbol:15} → {result_str:10} (期待値: {expected_str})")
    
    # Yahoo Finance形式変換テスト
    print("\n=== Yahoo Finance形式変換テスト ===")
    test_symbols = ['9432', '1928', '8316']
    for symbol in test_symbols:
        yahoo_format = to_yahoo_symbol(symbol)
        print(f"✅ {symbol} → {yahoo_format}")


if __name__ == "__main__":
    test_symbol_normalization()