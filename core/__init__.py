"""
Core Package

統一データ処理アーキテクチャの中核モジュール群
全ての金融データ処理は必ずこのパッケージを経由する
"""

# バージョン情報
__version__ = "0.3.0"
__author__ = "日本株ウォッチドッグ開発チーム"

# 中核モジュールのインポート
from .financial_data_processor import FinancialDataProcessor, ProcessedData, WarningLevel
from .multi_data_source import MultiDataSourceManager
from .investment_strategies import InvestmentStrategyAnalyzer, RecommendationLevel
from .chart_data_manager import ChartDataManager

# パッケージ情報
__all__ = [
    # 統一データ処理層
    'FinancialDataProcessor',
    'ProcessedData', 
    'WarningLevel',
    
    # データ取得層
    'MultiDataSourceManager',
    
    # 戦略分析層
    'InvestmentStrategyAnalyzer',
    'RecommendationLevel',
    
    # チャート生成層
    'ChartDataManager'
]

# アーキテクチャ原則の明示
ARCHITECTURE_PRINCIPLES = """
🏗️ 統一データ処理アーキテクチャ原則:

1. 単一通過点原則
   全ての金融データは FinancialDataProcessor のみを経由

2. 生データ直接アクセス禁止  
   Yahoo Finance等の生データを直接使用してはならない

3. 統一キー使用義務
   dividend_yield, pe_ratio, pb_ratio, roe の統一キーを使用

4. 異常値自動検出・修正
   配当利回り70% → 7% 等の単位エラーを自動修正

5. 3段階警告システム
   🟡軽微 → 🟠注意 → 🔴重大 の段階的警告
"""

def get_architecture_info():
    """アーキテクチャ情報の取得"""
    return {
        'version': __version__,
        'principles': ARCHITECTURE_PRINCIPLES,
        'core_modules': __all__,
        'data_flow': 'Raw Data → FinancialDataProcessor → Normalized Data → Business Logic'
    }