"""
CSV Parser Module
証券会社のCSVファイルを解析し、統一データ処理を行うモジュール
"""

import pandas as pd
import io
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from .financial_data_processor import FinancialDataProcessor

logger = logging.getLogger(__name__)


class UnifiedCSVParser:
    """統一CSVパーサー - 楽天証券・SBI証券のCSVを統一的に処理"""
    
    def __init__(self, financial_processor: Optional[FinancialDataProcessor] = None):
        """
        Args:
            financial_processor: 財務データプロセッサー（統一データ処理用）
        """
        self.financial_processor = financial_processor or FinancialDataProcessor()
        
        # カラムマッピング定義
        self.column_mappings = {
            # SBI証券（SaveFile形式）
            'sbi': {
                '銘柄コード': 'symbol',
                '銘柄名称': 'name',
                '保有株数': 'quantity',
                '保有数量': 'quantity',
                '取得単価': 'average_price',
                '平均取得価格': 'average_price',
                '現在値': 'current_price',
                '評価額': 'market_value',
                '評価損益': 'profit_loss'
            },
            # 楽天証券（assetbalance形式）
            'rakuten': {
                '銘柄コード・ティッカー': 'symbol',  # 旧形式
                '銘柄コード': 'symbol',  # 新形式
                '銘柄': 'name',
                '銘柄名': 'name',  # 新形式
                '保有数量': 'quantity',
                '保有数量［株］': 'quantity',  # 新形式
                '平均取得価額': 'average_price',
                '平均取得価額［円］': 'average_price',  # 新形式
                '現在値': 'current_price',
                '現在値［円］': 'current_price',  # 新形式
                '時価評価額[円]': 'market_value',
                '時価評価額［円］': 'market_value',  # 新形式
                '評価損益[円]': 'profit_loss',
                '評価損益［円］': 'profit_loss',  # 新形式
                '評価損益[％]': 'profit_loss_percent',
                '評価損益［％］': 'profit_loss_percent'  # 新形式
            },
            # 共通パターン
            'common': {
                'コード': 'symbol',
                '数量': 'quantity',
                '取得価格': 'average_price',
                '現在価格': 'current_price',
                'Symbol': 'symbol',
                'Quantity': 'quantity',
                'Average Price': 'average_price',
                'Current Price': 'current_price'
            }
        }
    
    def parse_csv(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """
        CSVファイルを解析して統一フォーマットのDataFrameを返す
        
        Args:
            file_content: CSVファイルの内容
            filename: ファイル名（形式判定用）
            
        Returns:
            pd.DataFrame: 統一フォーマットのポートフォリオデータ
        """
        # エンコーディング検出と読み込み
        df, encoding = self._read_csv_with_encoding(file_content)
        logger.info(f"CSV読み込み成功: {filename}, エンコーディング: {encoding}, 行数: {len(df)}")
        
        # CSV形式の自動判定
        csv_format = self._detect_csv_format(df, filename)
        logger.info(f"検出されたCSV形式: {csv_format}")
        
        # 形式に応じた処理
        if csv_format == 'rakuten':
            df = self._process_rakuten_csv(df)
        elif csv_format == 'sbi':
            df = self._process_sbi_csv(df)
        else:
            df = self._process_generic_csv(df)
        
        # カラム名の正規化
        df = self._normalize_columns(df, csv_format)
        
        # データ検証と正規化（統一プロセッサ経由）
        df = self._validate_and_normalize_data(df)
        
        # データソース情報の追加
        df['data_source'] = csv_format
        df['import_timestamp'] = datetime.now()
        
        return df
    
    def _read_csv_with_encoding(self, file_content: bytes) -> Tuple[pd.DataFrame, str]:
        """複数のエンコーディングを試してCSVを読み込む"""
        encodings = ['utf-8', 'shift_jis', 'cp932', 'utf-8-sig', 'iso-2022-jp']
        
        for encoding in encodings:
            try:
                content = file_content.decode(encoding)
                df = pd.read_csv(
                    io.StringIO(content),
                    on_bad_lines='skip',
                    engine='python',
                    quoting=1,  # QUOTE_ALL - 引用符を適切に処理
                    skipinitialspace=True,  # 先頭のスペースをスキップ
                    sep=None,  # 自動区切り文字検出
                    header=None  # ヘッダーを自動判定しない
                )
                return df, encoding
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        
        raise ValueError("サポートされていないファイルエンコーディングです")
    
    def _detect_csv_format(self, df: pd.DataFrame, filename: str) -> str:
        """CSV形式を自動判定"""
        # ファイル名から判定
        if 'assetbalance' in filename.lower():
            return 'rakuten'
        elif 'savefile' in filename.lower() or 'new_file' in filename.lower():
            return 'sbi'
        
        # 内容から判定 - 全データを文字列化して検索
        df_str = ' '.join([str(val) for val in df.values.flatten() if pd.notna(val)])
        df_str += ' ' + ' '.join([str(col) for col in df.columns if pd.notna(col)])
        
        logger.info(f"CSV内容検索文字列の最初の500文字: {df_str[:500]}")
        
        # 楽天証券パターン
        if any(pattern in df_str for pattern in [
            '保有商品詳細', '資産合計', '銘柄コード・ティッカー', 
            '■特定口座', '■NISA成長投資枠', '平均取得価額［円］'
        ]):
            return 'rakuten'
        
        # SBI証券パターン
        elif any(pattern in df_str for pattern in [
            '取得単価', '銘柄名称', '保有株数', '評価額合計', 
            '株式（特定預り）', '投資信託（金額/特定預り）'
        ]):
            return 'sbi'
        
        return 'generic'
    
    def _process_rakuten_csv(self, df: pd.DataFrame) -> pd.DataFrame:
        """楽天証券CSVの特殊処理"""
        logger.info(f"楽天証券CSV処理開始: 全{len(df)}行")
        
        # デバッグ: 全体の内容を確認
        logger.info(f"CSV全体の形状: {df.shape}")
        for idx in range(min(15, len(df))):
            row_values = [str(val) for val in df.iloc[idx].values if pd.notna(val)]
            logger.info(f"行 {idx}: {' | '.join(row_values[:8])}")  # 最初の8カラムのみ表示
        
        # 楽天証券のCSVは最初の数行にヘッダー情報があり、実際のデータは後ろにある
        data_start_idx = None
        
        for idx, row in df.iterrows():
            row_str = ' '.join(str(cell) for cell in row if pd.notna(cell))
            
            # ヘッダー行を検出（新形式に対応）
            # 楽天証券の新しい形式: 銘柄コード,銘柄名,保有数量［株］,執行中［株］,...
            if ('銘柄コード' in row_str and '銘柄名' in row_str and '保有数量' in row_str) or \
               ('銘柄コード' in row_str and '平均取得価額' in row_str) or \
               ('種別' in row_str and '銘柄コード・ティッカー' in row_str) or \
               ('銘柄コード・ティッカー' in row_str and '保有数量' in row_str):
                data_start_idx = idx
                logger.info(f"ヘッダー行を検出: 行 {idx}")
                logger.info(f"ヘッダー内容: {row_str[:200]}...")
                break
        
        if data_start_idx is not None:
            # ヘッダー行を新しいカラム名として設定
            new_columns = df.iloc[data_start_idx].fillna('').astype(str)
            logger.info(f"新しいカラム名: {new_columns.tolist()}")
            
            df.columns = new_columns
            df = df.iloc[data_start_idx + 1:].reset_index(drop=True)
            logger.info(f"ヘッダー設定後のデータ行数: {len(df)}")
            
            # 空の行を除去
            df = df.dropna(how='all')
            logger.info(f"空行除去後のデータ行数: {len(df)}")
            
            # 銘柄コードが有効な行のみを抽出
            symbol_column = None
            for col in df.columns:
                if '銘柄コード' in col:
                    symbol_column = col
                    break
            
            if symbol_column:
                original_len = len(df)
                # 銘柄コードが数字4桁のパターンを含む行のみ抽出
                df = df[df[symbol_column].notna() & 
                       df[symbol_column].astype(str).str.match(r'^"?\d{4}"?')]
                logger.info(f"有効な銘柄データのみ抽出: {original_len}行 → {len(df)}行")
                
                # 最初の数行をデバッグ表示
                if not df.empty:
                    logger.info(f"抽出されたデータの最初の行:\n{df.iloc[0].to_dict()}")
                    for i in range(min(3, len(df))):
                        logger.info(f"データ行 {i}: {df.iloc[i][symbol_column]} | {df.iloc[i].get('銘柄名', 'N/A')}")
            else:
                logger.warning("銘柄コードカラムが見つかりません")
                
            # 株式のみを抽出（種別列がある場合）
            if '種別' in df.columns:
                original_len = len(df)
                df = df[df['種別'].isin(['国内株式', '米国株式'])]
                logger.info(f"株式データのみ抽出: {original_len}行 → {len(df)}行")
                
        else:
            logger.error("楽天証券CSVでヘッダー行が見つかりませんでした")
            logger.error("検索したパターン:")
            logger.error("- '銘柄コード' + '銘柄名' + '保有数量'")
            logger.error("- '銘柄コード' + '平均取得価額'")
            logger.error("- '種別' + '銘柄コード・ティッカー'")
            logger.error("- '銘柄コード・ティッカー' + '保有数量'")
        
        return df
    
    def _process_sbi_csv(self, df: pd.DataFrame) -> pd.DataFrame:
        """SBI証券CSVの特殊処理"""
        logger.info(f"SBI証券CSV処理開始: 全{len(df)}行")
        
        # デバッグ: 最初の数行を確認
        logger.info(f"最初の5行:\n{df.head()}")
        
        # SBI証券のCSVで実際の銘柄データのヘッダー行を探す
        data_start_idx = None
        
        for idx, row in df.iterrows():
            row_str = ' '.join(str(cell) for cell in row if pd.notna(cell))
            logger.info(f"行 {idx}: {row_str[:100]}...")
            
            # 銘柄データのヘッダー行を検出
            if ('銘柄コード' in row_str and '銘柄名称' in row_str and '保有株数' in row_str) or \
               ('銘柄コード' in row_str and '保有数量' in row_str and '取得単価' in row_str):
                data_start_idx = idx
                logger.info(f"SBI証券ヘッダー行を検出: 行 {idx}")
                break
        
        if data_start_idx is not None:
            # ヘッダー行を新しいカラム名として設定
            new_columns = df.iloc[data_start_idx].fillna('').astype(str)
            logger.info(f"新しいカラム名: {new_columns.tolist()}")
            
            df.columns = new_columns
            df = df.iloc[data_start_idx + 1:].reset_index(drop=True)
            logger.info(f"データ行数: {len(df)}")
            
            # 銘柄コードが有効な行のみを抽出（数値または4桁の文字列）
            if '銘柄コード' in df.columns:
                original_len = len(df)
                # 銘柄コードが空でない、かつ数字を含む行のみ抽出
                df = df[df['銘柄コード'].notna() & 
                       df['銘柄コード'].astype(str).str.match(r'^[0-9]{4}.*$')]
                logger.info(f"有効な銘柄データのみ抽出: {original_len}行 → {len(df)}行")
            
            # データが見つかった場合の詳細ログ
            if not df.empty:
                logger.info(f"抽出されたデータの最初の行:\n{df.iloc[0].to_dict()}")
        else:
            logger.error("SBI証券CSVでヘッダー行が見つかりませんでした")
        
        return df
    
    def _process_generic_csv(self, df: pd.DataFrame) -> pd.DataFrame:
        """汎用CSV処理"""
        return df
    
    def _normalize_columns(self, df: pd.DataFrame, csv_format: str) -> pd.DataFrame:
        """カラム名を統一フォーマットに正規化"""
        # 形式別のマッピングを取得
        mapping = {}
        if csv_format in self.column_mappings:
            mapping.update(self.column_mappings[csv_format])
        mapping.update(self.column_mappings['common'])
        
        # カラム名を変換
        df = df.rename(columns=mapping)
        
        # 不要なカラムを削除
        required_columns = ['symbol', 'quantity', 'average_price']
        optional_columns = ['name', 'current_price', 'market_value', 'profit_loss']
        keep_columns = [col for col in required_columns + optional_columns if col in df.columns]
        
        df = df[keep_columns]
        
        return df
    
    def _validate_and_normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """データの検証と正規化（統一プロセッサ経由）"""
        logger.info(f"データ検証開始: {len(df)}行, カラム: {df.columns.tolist()}")
        
        validated_rows = []
        
        for idx, row in df.iterrows():
            try:
                logger.info(f"行 {idx} の処理: {row.to_dict()}")
                
                # 必要なカラムが存在するかチェック
                if 'symbol' not in row:
                    logger.error(f"行 {idx}: 'symbol'カラムが見つかりません。利用可能なカラム: {row.index.tolist()}")
                    continue
                if 'quantity' not in row:
                    logger.error(f"行 {idx}: 'quantity'カラムが見つかりません。利用可能なカラム: {row.index.tolist()}")
                    continue
                if 'average_price' not in row:
                    logger.error(f"行 {idx}: 'average_price'カラムが見つかりません。利用可能なカラム: {row.index.tolist()}")
                    continue
                
                # 基本的なデータ型変換（引用符を除去）
                symbol = str(row['symbol']).strip().strip('"\'')
                quantity = pd.to_numeric(str(row['quantity']).strip('"\''), errors='coerce')
                average_price = pd.to_numeric(str(row['average_price']).strip('"\''), errors='coerce')
                
                logger.info(f"行 {idx}: symbol={symbol}, quantity={quantity}, average_price={average_price}")
                
                # 無効なデータをスキップ
                if pd.isna(quantity) or pd.isna(average_price) or quantity <= 0 or average_price <= 0:
                    logger.warning(f"無効なデータをスキップ: symbol={symbol}, quantity={quantity}, average_price={average_price}")
                    continue
                
                # 銘柄コードの正規化（日本株の場合）
                if symbol.isdigit() and len(symbol) == 4:
                    symbol = symbol + '.T'
                    logger.info(f"銘柄コードを正規化: {row['symbol']} → {symbol}")
                
                # 統一プロセッサでポートフォリオデータを検証
                validated_data = self.financial_processor.validate_portfolio_data({
                    'symbol': symbol,
                    'quantity': quantity,
                    'average_price': average_price,
                    'name': row.get('name', ''),
                    'current_price': pd.to_numeric(row.get('current_price'), errors='coerce') if 'current_price' in row else None,
                    'market_value': pd.to_numeric(row.get('market_value'), errors='coerce') if 'market_value' in row else None
                })
                
                validated_rows.append(validated_data)
                logger.info(f"行 {idx}: 正常に検証完了")
                
            except KeyError as e:
                logger.error(f"行 {row.name if hasattr(row, 'name') else idx} の処理エラー: {e}")
                logger.error(f"行の内容: {row}")
                logger.error(f"利用可能なキー: {list(row.index) if hasattr(row, 'index') else 'N/A'}")
                continue
            except Exception as e:
                logger.error(f"行 {idx} の処理エラー: {e}")
                logger.error(f"行の内容: {row}")
                continue
        
        logger.info(f"データ検証完了: {len(validated_rows)}行が有効")
        return pd.DataFrame(validated_rows)