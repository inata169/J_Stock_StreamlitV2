"""
Enhanced CSV Parser Module
新スキーマ対応・両方の真実保持版CSVパーサー
"""

import csv
import io
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# pandas問題を回避するため、テスト時は単純なCSV処理を使用
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️  pandas利用不可 - 単純なCSV処理を使用")

try:
    from .database_manager import DatabaseManager
    from .symbol_utils import SymbolNormalizer, DecimalFormatter
except ImportError:
    from database_manager import DatabaseManager
    from symbol_utils import SymbolNormalizer, DecimalFormatter

logger = logging.getLogger(__name__)


class EnhancedCSVParser:
    """新スキーマ対応統一CSVパーサー"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Args:
            db_manager: データベースマネージャー
        """
        self.db_manager = db_manager or DatabaseManager()
        self.symbol_normalizer = SymbolNormalizer()
        self.decimal_formatter = DecimalFormatter()
        
        # 証券会社別フィールドマッピング
        self.field_mappings = {
            'sbi': {
                'symbol_fields': ['銘柄（コード）', '銘柄コード'],
                'name_fields': ['銘柄名称', '銘柄名'],
                'quantity_fields': ['数量', '保有数量', '保有株数'],
                'average_price_fields': ['取得単価', '平均取得価格'],
                'current_price_fields': ['現在値'],
                'market_value_fields': ['評価額'],
                'profit_loss_fields': ['損益', '評価損益'],
                'profit_loss_percent_fields': ['損益（％）', '損益率'],
            },
            'rakuten': {
                'symbol_fields': ['銘柄コード', '銘柄コード・ティッカー'],
                'name_fields': ['銘柄名', '銘柄'],
                'quantity_fields': ['保有数量［株］', '保有数量'],
                'average_price_fields': ['平均取得価額［円］', '平均取得価額'],
                'current_price_fields': ['現在値［円］', '現在値'],
                'market_value_fields': ['時価評価額［円］', '時価評価額[円]'],
                'profit_loss_fields': ['評価損益［円］', '評価損益[円]'],
                'total_cost_fields': ['取得総額［円］'],
            }
        }
    
    def parse_csv_to_database(self, file_content: bytes, filename: str, 
                             data_source: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        CSVファイルを解析して直接データベースに保存
        
        Args:
            file_content: CSVファイルの内容
            filename: ファイル名
            data_source: データソース（自動判定可能）
            
        Returns:
            Tuple[成功フラグ, 処理結果]
        """
        try:
            # CSV読み込み
            lines, encoding = self._read_csv_with_encoding(file_content)
            logger.info(f"CSV読み込み: {filename}, エンコーディング: {encoding}, 行数: {len(lines)}")
            
            # データソース自動判定
            if data_source is None:
                data_source = self._detect_data_source(lines, filename)
            
            logger.info(f"検出されたデータソース: {data_source}")
            
            # データ抽出と正規化
            portfolio_data = self._extract_portfolio_data(lines, data_source)
            
            if not portfolio_data:
                return False, {"error": "有効なポートフォリオデータが見つかりません"}
            
            # データベースに保存
            success_count = 0
            error_count = 0
            
            for item in portfolio_data:
                if self.db_manager.insert_portfolio_data(item):
                    success_count += 1
                else:
                    error_count += 1
            
            result = {
                "data_source": data_source,
                "total_records": len(portfolio_data),
                "success_count": success_count,
                "error_count": error_count,
                "encoding": encoding
            }
            
            logger.info(f"CSV処理完了: {success_count}件成功, {error_count}件失敗")
            return success_count > 0, result
            
        except Exception as e:
            logger.error(f"CSV処理エラー: {e}")
            return False, {"error": str(e)}
    
    def _read_csv_with_encoding(self, file_content: bytes) -> Tuple[List[List[str]], str]:
        """複数エンコーディングでCSV読み込み（pandas不使用版）"""
        encodings = ['utf-8', 'shift_jis', 'cp932', 'utf-8-sig']
        
        for encoding in encodings:
            try:
                content = file_content.decode(encoding)
                
                # CSV読み込み（標準ライブラリ使用）
                lines = []
                reader = csv.reader(io.StringIO(content))
                for row in reader:
                    lines.append(row)
                
                logger.debug(f"エンコーディング {encoding} で読み込み成功: {len(lines)}行")
                return lines, encoding
                
            except UnicodeDecodeError as e:
                logger.debug(f"エンコーディング {encoding} で失敗: {e}")
                continue
        
        raise ValueError("サポートされていないファイルエンコーディングです")
    
    def _detect_data_source(self, lines: List[List[str]], filename: str) -> str:
        """データソース（証券会社）の自動判定"""
        # ファイル名から判定
        filename_lower = filename.lower()
        if 'assetbalance' in filename_lower:
            return 'rakuten'
        elif 'savefile' in filename_lower or 'new_file' in filename_lower:
            return 'sbi'
        
        # 内容から判定
        content_str = ' '.join([' '.join(row) for row in lines])
        
        # 楽天証券の特徴的なパターン
        if any(pattern in content_str for pattern in [
            '保有商品詳細', '■特定口座', '■NISA成長投資枠', 
            '平均取得価額［円］', '時価評価額［円］'
        ]):
            return 'rakuten'
        
        # SBI証券の特徴的なパターン
        elif any(pattern in content_str for pattern in [
            'ポートフォリオ一覧', '銘柄（コード）', '取得単価', '損益（％）'
        ]):
            return 'sbi'
        
        return 'unknown'
    
    def _extract_portfolio_data(self, lines: List[List[str]], data_source: str) -> List[Dict[str, Any]]:
        """ポートフォリオデータを抽出・正規化"""
        if data_source == 'rakuten':
            return self._extract_rakuten_data(lines)
        elif data_source == 'sbi':
            return self._extract_sbi_data(lines)
        else:
            logger.warning(f"未対応のデータソース: {data_source}")
            return []
    
    def _extract_sbi_data(self, lines: List[List[str]]) -> List[Dict[str, Any]]:
        """SBI証券データの抽出"""
        portfolio_data = []
        
        # ヘッダー行を探す
        header_row_idx = None
        for idx, row in enumerate(lines):
            row_str = ' '.join(str(cell) for cell in row)
            if '銘柄（コード）' in row_str and '数量' in row_str:
                header_row_idx = idx
                break
        
        if header_row_idx is None:
            logger.error("SBI証券のヘッダー行が見つかりません")
            return []
        
        # ヘッダーを取得
        headers = [str(cell).strip() for cell in lines[header_row_idx]]
        
        # データ行を処理
        for idx in range(header_row_idx + 1, len(lines)):
            row = lines[idx]
            if not row or all(not cell.strip() for cell in row):
                continue
            
            # 行データを辞書に変換
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(headers) and headers[i]:
                    row_dict[headers[i]] = value
            
            # 銘柄データを抽出
            item = self._extract_stock_item(row_dict, 'sbi')
            if item:
                portfolio_data.append(item)
        
        return portfolio_data
    
    def _extract_rakuten_data(self, lines: List[List[str]]) -> List[Dict[str, Any]]:
        """楽天証券データの抽出"""
        portfolio_data = []
        
        # 複数のセクション（特定口座、NISA等）を処理
        for idx, row in enumerate(lines):
            row_str = ' '.join(str(cell) for cell in row)
            
            # ヘッダー行を検出
            if '銘柄コード' in row_str and '保有数量［株］' in row_str:
                headers = [str(cell).strip().strip('\"') for cell in row]
                
                # このセクションのデータを抽出
                section_data = self._extract_rakuten_section(lines, idx, headers)
                portfolio_data.extend(section_data)
        
        return portfolio_data
    
    def _extract_rakuten_section(self, lines: List[List[str]], header_idx: int, 
                                headers: List[str]) -> List[Dict[str, Any]]:
        """楽天証券の特定セクションからデータを抽出"""
        section_data = []
        
        # データ行の範囲を特定
        data_start = header_idx + 1
        data_end = len(lines)
        
        for idx in range(data_start, data_end):
            row = lines[idx]
            row_str = ' '.join(str(cell) for cell in row)
            
            # セクション終了の判定
            if ('合計' in row_str and '口座合計' in row_str) or '■' in row_str:
                break
            
            # 空行スキップ
            if not row or all(not cell.strip() for cell in row):
                continue
            
            # 行データを辞書に変換
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(headers) and headers[i]:
                    row_dict[headers[i]] = str(value).strip().strip('\"')
            
            # 銘柄データを抽出
            item = self._extract_stock_item(row_dict, 'rakuten')
            if item:
                section_data.append(item)
        
        return section_data
    
    def _extract_stock_item(self, row_dict: Dict[str, Any], data_source: str) -> Optional[Dict[str, Any]]:
        """個別銘柄データを抽出・正規化"""
        try:
            # 銘柄コードと銘柄名を抽出
            symbol, name = self.symbol_normalizer.extract_symbols_from_csv_row(row_dict)
            
            if not symbol:
                return None
            
            # 基本データ抽出
            mappings = self.field_mappings.get(data_source, {})
            
            # 数値データの抽出とフォーマット
            quantity = self._extract_numeric_value(row_dict, mappings.get('quantity_fields', []))
            average_price = self._extract_numeric_value(row_dict, mappings.get('average_price_fields', []))
            current_price = self._extract_numeric_value(row_dict, mappings.get('current_price_fields', []))
            market_value = self._extract_numeric_value(row_dict, mappings.get('market_value_fields', []))
            profit_loss = self._extract_numeric_value(row_dict, mappings.get('profit_loss_fields', []))
            
            # 損益率の処理（両方の真実を保持）
            profit_loss_percent_original = self._extract_numeric_value(
                row_dict, mappings.get('profit_loss_percent_fields', [])
            )
            
            # SBI証券の損益率は%値、楽天証券は計算
            if data_source == 'sbi' and profit_loss_percent_original is not None:
                # SBI: 167.98% → percent=167.9, decimal=1.679
                profit_loss_rate_percent = self.decimal_formatter.format_percentage(profit_loss_percent_original)
                profit_loss_rate_decimal = round(profit_loss_percent_original / 100.0, 4)
            elif data_source == 'rakuten' and average_price and current_price:
                # 楽天: 計算で損益率を算出
                rate_decimal = (current_price - average_price) / average_price
                profit_loss_rate_percent = self.decimal_formatter.format_percentage(rate_decimal * 100)
                profit_loss_rate_decimal = round(rate_decimal, 4)
                profit_loss_percent_original = None  # 楽天証券にはない
            else:
                profit_loss_rate_percent = None
                profit_loss_rate_decimal = None
            
            # 取得総額の計算（楽天証券から取得または計算）
            total_cost = self._extract_numeric_value(row_dict, mappings.get('total_cost_fields', []))
            if total_cost is None and quantity and average_price:
                total_cost = self.decimal_formatter.format_price(quantity * average_price)
            
            # データ構造の構築
            item = {
                'symbol': symbol,
                'name': name,
                'data_source': data_source,
                'quantity': int(quantity) if quantity else 0,
                'average_price': self.decimal_formatter.format_price(average_price),
                'current_price': self.decimal_formatter.format_price(current_price),
                'market_value': self.decimal_formatter.format_price(market_value),
                'profit_loss': self.decimal_formatter.format_price(profit_loss),
                'total_cost': total_cost,
                'profit_loss_rate_original': profit_loss_percent_original,
                'profit_loss_rate_percent': profit_loss_rate_percent,
                'profit_loss_rate_decimal': profit_loss_rate_decimal
            }
            
            logger.debug(f"銘柄データ抽出: {symbol} ({data_source}) - 損益率: {profit_loss_rate_percent}%")
            return item
            
        except Exception as e:
            logger.error(f"銘柄データ抽出エラー: {e}")
            return None
    
    def _extract_numeric_value(self, row_dict: Dict[str, Any], field_candidates: List[str]) -> Optional[float]:
        """数値フィールドを抽出"""
        for field in field_candidates:
            if field in row_dict and row_dict[field]:
                value_str = str(row_dict[field]).strip().replace(',', '').replace('+', '')
                try:
                    return float(value_str)
                except ValueError:
                    continue
        return None
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """ポートフォリオサマリーを取得"""
        try:
            analytics = self.db_manager.get_portfolio_analytics()
            
            if not analytics:
                return {"error": "ポートフォリオデータが見つかりません"}
            
            # サマリー計算
            total_market_value = sum(item.get('market_value', 0) or 0 for item in analytics)
            total_profit_loss = sum(item.get('profit_loss', 0) or 0 for item in analytics)
            
            summary = {
                "total_holdings": len(analytics),
                "total_market_value": total_market_value,
                "total_profit_loss": total_profit_loss,
                "profit_loss_rate": (total_profit_loss / (total_market_value - total_profit_loss) * 100) 
                                   if (total_market_value - total_profit_loss) > 0 else 0,
                "data_sources": list(set(item.get('data_source') for item in analytics if item.get('data_source'))),
                "last_updated": max((item.get('last_updated', '') for item in analytics), default='')
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"ポートフォリオサマリー取得エラー: {e}")
            return {"error": str(e)}


# 便利関数
def parse_csv_file(file_path: str, data_source: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
    """CSVファイルを解析してデータベースに保存"""
    parser = EnhancedCSVParser()
    
    with open(file_path, 'rb') as f:
        content = f.read()
    
    return parser.parse_csv_to_database(content, file_path, data_source)


if __name__ == "__main__":
    # テスト実行
    print("=== 新CSVパーサーテスト ===")
    
    parser = EnhancedCSVParser(DatabaseManager("test_enhanced_parser.db"))
    
    # 既存のテストファイルでテスト
    test_files = [
        "../assetbalance(JP)_20250626_193110.csv",
        "../New_file 2.csv"
    ]
    
    for file_path in test_files:
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            success, result = parser.parse_csv_to_database(content, file_path)
            
            if success:
                print(f"✅ {file_path}: {result['success_count']}件処理成功")
                print(f"   データソース: {result['data_source']}")
            else:
                print(f"❌ {file_path}: 処理失敗 - {result.get('error', 'Unknown error')}")
                
        except FileNotFoundError:
            print(f"⚠️  ファイルが見つかりません: {file_path}")
    
    # サマリー表示
    summary = parser.get_portfolio_summary()
    if "error" not in summary:
        print(f"\n📊 ポートフォリオサマリー:")
        print(f"   総銘柄数: {summary['total_holdings']}")
        print(f"   総評価額: ¥{summary['total_market_value']:,.0f}")
        print(f"   総損益: ¥{summary['total_profit_loss']:,.0f}")
        print(f"   損益率: {summary['profit_loss_rate']:.1f}%")