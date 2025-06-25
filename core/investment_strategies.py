"""
戦略分析層 (InvestmentStrategyAnalyzer)

正規化済みデータでの投資戦略分析を担当。
統一キーを使用し、複数の投資戦略による評価を行う。
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
from enum import Enum
import logging
from datetime import datetime

from .financial_data_processor import ProcessedData, WarningLevel

# ログ設定
logger = logging.getLogger(__name__)


class RecommendationLevel(Enum):
    """推奨レベル"""
    STRONG_BUY = "🟢 強い買い"
    BUY = "🔵 買い"
    HOLD = "🟡 保有"
    SELL = "🟠 売り"
    STRONG_SELL = "🔴 強い売り"
    INSUFFICIENT_DATA = "⚪ データ不足"


class StrategyResult:
    """戦略分析結果"""
    
    def __init__(
        self,
        strategy_name: str,
        score: int,
        max_score: int,
        criteria_met: List[str],
        criteria_failed: List[str],
        recommendation: RecommendationLevel,
        confidence: float,
        analysis_details: Dict[str, Any]
    ):
        self.strategy_name = strategy_name
        self.score = score
        self.max_score = max_score
        self.criteria_met = criteria_met
        self.criteria_failed = criteria_failed
        self.recommendation = recommendation
        self.confidence = confidence
        self.analysis_details = analysis_details
        self.analyzed_at = datetime.now()
    
    @property
    def score_percentage(self) -> float:
        """スコア割合"""
        return (self.score / self.max_score) * 100 if self.max_score > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で結果を返す"""
        return {
            'strategy_name': self.strategy_name,
            'score': self.score,
            'max_score': self.max_score,
            'score_percentage': self.score_percentage,
            'criteria_met': self.criteria_met,
            'criteria_failed': self.criteria_failed,
            'recommendation': self.recommendation.value,
            'confidence': self.confidence,
            'analysis_details': self.analysis_details,
            'analyzed_at': self.analyzed_at.isoformat()
        }


class InvestmentStrategyAnalyzer:
    """
    投資戦略分析システム
    
    正規化済みデータを使用して複数の投資戦略による分析を実行。
    統一キーを使用してデータ整合性を保証。
    """
    
    def __init__(self):
        """初期化"""
        self.strategies = {
            'defensive': self.analyze_defensive_strategy,
            'growth': self.analyze_growth_strategy,
            'value': self.analyze_value_strategy,
            'dividend': self.analyze_dividend_strategy,
            'momentum': self.analyze_momentum_strategy
        }
    
    def analyze_all_strategies(self, data: ProcessedData) -> Dict[str, StrategyResult]:
        """
        全戦略による分析
        
        Args:
            data: 正規化済み株式データ
            
        Returns:
            Dict[str, StrategyResult]: 戦略名と分析結果のマッピング
        """
        results = {}
        
        for strategy_name, strategy_func in self.strategies.items():
            try:
                results[strategy_name] = strategy_func(data)
                logger.debug(f"Successfully analyzed {strategy_name} for {data['symbol']}")
            except Exception as e:
                logger.error(f"Error analyzing {strategy_name} for {data['symbol']}: {e}")
                results[strategy_name] = self._create_error_result(strategy_name, str(e))
        
        return results
    
    def analyze_defensive_strategy(self, data: ProcessedData) -> StrategyResult:
        """
        ディフェンシブ株戦略の分析
        
        低リスク・安定配当を重視する保守的な投資戦略
        """
        score = 0
        max_score = 100
        criteria_met = []
        criteria_failed = []
        analysis_details = {}
        
        # 配当利回りチェック（30点満点）
        dividend_yield = data.get('dividend_yield')
        if dividend_yield:
            if dividend_yield >= Decimal('4.0'):
                score += 30
                criteria_met.append(f"高配当: {dividend_yield:.1f}%")
            elif dividend_yield >= Decimal('3.0'):
                score += 20
                criteria_met.append(f"適度な配当: {dividend_yield:.1f}%")
            elif dividend_yield >= Decimal('2.0'):
                score += 10
                criteria_met.append(f"低配当: {dividend_yield:.1f}%")
            else:
                criteria_failed.append(f"配当利回り低い: {dividend_yield:.1f}%")
        else:
            criteria_failed.append("配当利回りデータなし")
        
        analysis_details['dividend_yield'] = float(dividend_yield) if dividend_yield else None
        
        # PERチェック（25点満点）
        pe_ratio = data.get('pe_ratio')
        if pe_ratio:
            if pe_ratio <= Decimal('12'):
                score += 25
                criteria_met.append(f"割安PER: {pe_ratio:.1f}倍")
            elif pe_ratio <= Decimal('15'):
                score += 15
                criteria_met.append(f"適正PER: {pe_ratio:.1f}倍")
            elif pe_ratio <= Decimal('20'):
                score += 5
                criteria_met.append(f"やや高PER: {pe_ratio:.1f}倍")
            else:
                criteria_failed.append(f"PER高すぎ: {pe_ratio:.1f}倍")
        else:
            criteria_failed.append("PERデータなし")
        
        analysis_details['pe_ratio'] = float(pe_ratio) if pe_ratio else None
        
        # PBRチェック（25点満点）
        pb_ratio = data.get('pb_ratio')
        if pb_ratio:
            if pb_ratio <= Decimal('0.8'):
                score += 25
                criteria_met.append(f"割安PBR: {pb_ratio:.2f}倍")
            elif pb_ratio <= Decimal('1.0'):
                score += 20
                criteria_met.append(f"適正PBR: {pb_ratio:.2f}倍")
            elif pb_ratio <= Decimal('1.5'):
                score += 10
                criteria_met.append(f"やや高PBR: {pb_ratio:.2f}倍")
            else:
                criteria_failed.append(f"PBR高すぎ: {pb_ratio:.2f}倍")
        else:
            criteria_failed.append("PBRデータなし")
        
        analysis_details['pb_ratio'] = float(pb_ratio) if pb_ratio else None
        
        # ROEチェック（20点満点）
        roe = data.get('roe')
        if roe:
            if roe >= Decimal('10'):
                score += 20
                criteria_met.append(f"高ROE: {roe:.1f}%")
            elif roe >= Decimal('5'):
                score += 10
                criteria_met.append(f"適度なROE: {roe:.1f}%")
            else:
                criteria_failed.append(f"ROE低い: {roe:.1f}%")
        else:
            criteria_failed.append("ROEデータなし")
        
        analysis_details['roe'] = float(roe) if roe else None
        
        # 推奨レベルと信頼度の決定
        recommendation, confidence = self._determine_recommendation(score, max_score, data)
        
        return StrategyResult(
            strategy_name="ディフェンシブ株戦略",
            score=score,
            max_score=max_score,
            criteria_met=criteria_met,
            criteria_failed=criteria_failed,
            recommendation=recommendation,
            confidence=confidence,
            analysis_details=analysis_details
        )
    
    def analyze_growth_strategy(self, data: ProcessedData) -> StrategyResult:
        """
        グロース株戦略の分析
        
        成長性を重視する積極的な投資戦略
        """
        score = 0
        max_score = 100
        criteria_met = []
        criteria_failed = []
        analysis_details = {}
        
        # ROEチェック（40点満点）
        roe = data.get('roe')
        if roe:
            if roe >= Decimal('20'):
                score += 40
                criteria_met.append(f"非常に高いROE: {roe:.1f}%")
            elif roe >= Decimal('15'):
                score += 30
                criteria_met.append(f"高ROE: {roe:.1f}%")
            elif roe >= Decimal('10'):
                score += 15
                criteria_met.append(f"適度なROE: {roe:.1f}%")
            else:
                criteria_failed.append(f"ROE低い: {roe:.1f}%")
        else:
            criteria_failed.append("ROEデータなし")
        
        analysis_details['roe'] = float(roe) if roe else None
        
        # PERチェック（30点満点）- グロース株は高PERを許容
        pe_ratio = data.get('pe_ratio')
        if pe_ratio:
            if Decimal('15') <= pe_ratio <= Decimal('25'):
                score += 30
                criteria_met.append(f"成長株適正PER: {pe_ratio:.1f}倍")
            elif Decimal('25') < pe_ratio <= Decimal('35'):
                score += 20
                criteria_met.append(f"やや高PER: {pe_ratio:.1f}倍")
            elif pe_ratio <= Decimal('15'):
                score += 15
                criteria_met.append(f"割安PER: {pe_ratio:.1f}倍")
            else:
                criteria_failed.append(f"PER高すぎ: {pe_ratio:.1f}倍")
        else:
            criteria_failed.append("PERデータなし")
        
        analysis_details['pe_ratio'] = float(pe_ratio) if pe_ratio else None
        
        # PBRチェック（20点満点）
        pb_ratio = data.get('pb_ratio')
        if pb_ratio:
            if pb_ratio <= Decimal('3.0'):
                score += 20
                criteria_met.append(f"適正PBR: {pb_ratio:.2f}倍")
            elif pb_ratio <= Decimal('5.0'):
                score += 10
                criteria_met.append(f"やや高PBR: {pb_ratio:.2f}倍")
            else:
                criteria_failed.append(f"PBR高すぎ: {pb_ratio:.2f}倍")
        else:
            criteria_failed.append("PBRデータなし")
        
        analysis_details['pb_ratio'] = float(pb_ratio) if pb_ratio else None
        
        # 配当利回りチェック（10点満点）- グロース株は配当より成長重視
        dividend_yield = data.get('dividend_yield')
        if dividend_yield:
            if dividend_yield <= Decimal('2.0'):
                score += 10
                criteria_met.append(f"成長重視型配当: {dividend_yield:.1f}%")
            elif dividend_yield <= Decimal('4.0'):
                score += 5
                criteria_met.append(f"適度な配当: {dividend_yield:.1f}%")
            else:
                criteria_failed.append(f"配当過多（成長阻害）: {dividend_yield:.1f}%")
        else:
            criteria_met.append("配当なし（成長重視）")
            score += 5
        
        analysis_details['dividend_yield'] = float(dividend_yield) if dividend_yield else None
        
        recommendation, confidence = self._determine_recommendation(score, max_score, data)
        
        return StrategyResult(
            strategy_name="グロース株戦略",
            score=score,
            max_score=max_score,
            criteria_met=criteria_met,
            criteria_failed=criteria_failed,
            recommendation=recommendation,
            confidence=confidence,
            analysis_details=analysis_details
        )
    
    def analyze_value_strategy(self, data: ProcessedData) -> StrategyResult:
        """
        バリュー株戦略の分析
        
        割安性を重視する価値投資戦略
        """
        score = 0
        max_score = 100
        criteria_met = []
        criteria_failed = []
        analysis_details = {}
        
        # PERチェック（40点満点）
        pe_ratio = data.get('pe_ratio')
        if pe_ratio:
            if pe_ratio <= Decimal('10'):
                score += 40
                criteria_met.append(f"非常に割安PER: {pe_ratio:.1f}倍")
            elif pe_ratio <= Decimal('12'):
                score += 30
                criteria_met.append(f"割安PER: {pe_ratio:.1f}倍")
            elif pe_ratio <= Decimal('15'):
                score += 15
                criteria_met.append(f"適正PER: {pe_ratio:.1f}倍")
            else:
                criteria_failed.append(f"PER高い: {pe_ratio:.1f}倍")
        else:
            criteria_failed.append("PERデータなし")
        
        analysis_details['pe_ratio'] = float(pe_ratio) if pe_ratio else None
        
        # PBRチェック（35点満点）
        pb_ratio = data.get('pb_ratio')
        if pb_ratio:
            if pb_ratio <= Decimal('0.8'):
                score += 35
                criteria_met.append(f"非常に割安PBR: {pb_ratio:.2f}倍")
            elif pb_ratio <= Decimal('1.0'):
                score += 25
                criteria_met.append(f"割安PBR: {pb_ratio:.2f}倍")
            elif pb_ratio <= Decimal('1.2'):
                score += 10
                criteria_met.append(f"適正PBR: {pb_ratio:.2f}倍")
            else:
                criteria_failed.append(f"PBR高い: {pb_ratio:.2f}倍")
        else:
            criteria_failed.append("PBRデータなし")
        
        analysis_details['pb_ratio'] = float(pb_ratio) if pb_ratio else None
        
        # ROEチェック（15点満点）
        roe = data.get('roe')
        if roe:
            if roe >= Decimal('8'):
                score += 15
                criteria_met.append(f"健全なROE: {roe:.1f}%")
            elif roe >= Decimal('5'):
                score += 10
                criteria_met.append(f"適度なROE: {roe:.1f}%")
            else:
                criteria_failed.append(f"ROE低い: {roe:.1f}%")
        else:
            criteria_failed.append("ROEデータなし")
        
        analysis_details['roe'] = float(roe) if roe else None
        
        # 配当利回りチェック（10点満点）
        dividend_yield = data.get('dividend_yield')
        if dividend_yield and dividend_yield > Decimal('2.0'):
            score += 10
            criteria_met.append(f"配当あり: {dividend_yield:.1f}%")
        elif dividend_yield:
            score += 5
            criteria_met.append(f"低配当: {dividend_yield:.1f}%")
        else:
            criteria_failed.append("配当なし")
        
        analysis_details['dividend_yield'] = float(dividend_yield) if dividend_yield else None
        
        recommendation, confidence = self._determine_recommendation(score, max_score, data)
        
        return StrategyResult(
            strategy_name="バリュー株戦略",
            score=score,
            max_score=max_score,
            criteria_met=criteria_met,
            criteria_failed=criteria_failed,
            recommendation=recommendation,
            confidence=confidence,
            analysis_details=analysis_details
        )
    
    def analyze_dividend_strategy(self, data: ProcessedData) -> StrategyResult:
        """
        配当株戦略の分析
        
        配当収入を重視するインカムゲイン戦略
        """
        score = 0
        max_score = 100
        criteria_met = []
        criteria_failed = []
        analysis_details = {}
        
        # 配当利回りチェック（50点満点）
        dividend_yield = data.get('dividend_yield')
        if dividend_yield:
            if dividend_yield >= Decimal('5.0'):
                score += 50
                criteria_met.append(f"高配当: {dividend_yield:.1f}%")
            elif dividend_yield >= Decimal('4.0'):
                score += 40
                criteria_met.append(f"良好な配当: {dividend_yield:.1f}%")
            elif dividend_yield >= Decimal('3.0'):
                score += 25
                criteria_met.append(f"適度な配当: {dividend_yield:.1f}%")
            elif dividend_yield >= Decimal('2.0'):
                score += 10
                criteria_met.append(f"低配当: {dividend_yield:.1f}%")
            else:
                criteria_failed.append(f"配当極小: {dividend_yield:.1f}%")
        else:
            criteria_failed.append("配当なし")
        
        analysis_details['dividend_yield'] = float(dividend_yield) if dividend_yield else None
        
        # ROEチェック（25点満点）- 配当の持続性
        roe = data.get('roe')
        if roe:
            if roe >= Decimal('10'):
                score += 25
                criteria_met.append(f"配当継続性良好ROE: {roe:.1f}%")
            elif roe >= Decimal('6'):
                score += 15
                criteria_met.append(f"適度なROE: {roe:.1f}%")
            else:
                criteria_failed.append(f"配当継続性懸念ROE: {roe:.1f}%")
        else:
            criteria_failed.append("ROEデータなし")
        
        analysis_details['roe'] = float(roe) if roe else None
        
        # PERチェック（15点満点）- 安定性重視
        pe_ratio = data.get('pe_ratio')
        if pe_ratio:
            if pe_ratio <= Decimal('15'):
                score += 15
                criteria_met.append(f"安定PER: {pe_ratio:.1f}倍")
            elif pe_ratio <= Decimal('20'):
                score += 10
                criteria_met.append(f"適正PER: {pe_ratio:.1f}倍")
            else:
                criteria_failed.append(f"PER高い: {pe_ratio:.1f}倍")
        else:
            criteria_failed.append("PERデータなし")
        
        analysis_details['pe_ratio'] = float(pe_ratio) if pe_ratio else None
        
        # PBRチェック（10点満点）
        pb_ratio = data.get('pb_ratio')
        if pb_ratio and pb_ratio <= Decimal('2.0'):
            score += 10
            criteria_met.append(f"適正PBR: {pb_ratio:.2f}倍")
        elif pb_ratio:
            score += 5
            criteria_met.append(f"やや高PBR: {pb_ratio:.2f}倍")
        else:
            criteria_failed.append("PBRデータなし")
        
        analysis_details['pb_ratio'] = float(pb_ratio) if pb_ratio else None
        
        recommendation, confidence = self._determine_recommendation(score, max_score, data)
        
        return StrategyResult(
            strategy_name="配当株戦略",
            score=score,
            max_score=max_score,
            criteria_met=criteria_met,
            criteria_failed=criteria_failed,
            recommendation=recommendation,
            confidence=confidence,
            analysis_details=analysis_details
        )
    
    def analyze_momentum_strategy(self, data: ProcessedData) -> StrategyResult:
        """
        モメンタム戦略の分析
        
        価格動向と市場の勢いを重視する戦略
        """
        # 注意: この戦略は価格履歴データが必要だが、
        # 現在のProcessedDataには含まれていないため、
        # 利用可能なデータで簡易分析を実行
        
        score = 0
        max_score = 100
        criteria_met = []
        criteria_failed = []
        analysis_details = {}
        
        # ROEによる企業の勢い評価（30点満点）
        roe = data.get('roe')
        if roe:
            if roe >= Decimal('15'):
                score += 30
                criteria_met.append(f"高成長ROE: {roe:.1f}%")
            elif roe >= Decimal('10'):
                score += 20
                criteria_met.append(f"成長ROE: {roe:.1f}%")
            else:
                criteria_failed.append(f"ROE低い: {roe:.1f}%")
        else:
            criteria_failed.append("ROEデータなし")
        
        analysis_details['roe'] = float(roe) if roe else None
        
        # PERによる市場期待度評価（25点満点）
        pe_ratio = data.get('pe_ratio')
        if pe_ratio:
            if Decimal('20') <= pe_ratio <= Decimal('30'):
                score += 25
                criteria_met.append(f"高期待PER: {pe_ratio:.1f}倍")
            elif Decimal('15') <= pe_ratio < Decimal('20'):
                score += 15
                criteria_met.append(f"適度な期待PER: {pe_ratio:.1f}倍")
            elif pe_ratio < Decimal('15'):
                score += 5
                criteria_met.append(f"低期待PER: {pe_ratio:.1f}倍")
            else:
                criteria_failed.append(f"PER過大評価: {pe_ratio:.1f}倍")
        else:
            criteria_failed.append("PERデータなし")
        
        analysis_details['pe_ratio'] = float(pe_ratio) if pe_ratio else None
        
        # 時価総額による流動性評価（20点満点）
        market_cap = data.get('market_cap')
        if market_cap:
            # 1兆円以上: 大型株
            if market_cap >= Decimal('1000000000000'):
                score += 15
                criteria_met.append("大型株（高流動性）")
            # 1000億円以上: 中型株
            elif market_cap >= Decimal('100000000000'):
                score += 20
                criteria_met.append("中型株（適度な流動性）")
            # 100億円以上: 小型株
            elif market_cap >= Decimal('10000000000'):
                score += 10
                criteria_met.append("小型株（変動性大）")
            else:
                criteria_failed.append("超小型株（流動性リスク）")
        else:
            criteria_failed.append("時価総額データなし")
        
        analysis_details['market_cap'] = float(market_cap) if market_cap else None
        
        # 配当による安定性減点（25点満点）
        dividend_yield = data.get('dividend_yield')
        if dividend_yield:
            if dividend_yield <= Decimal('2.0'):
                score += 25
                criteria_met.append(f"成長重視型: {dividend_yield:.1f}%")
            elif dividend_yield <= Decimal('4.0'):
                score += 15
                criteria_met.append(f"バランス型: {dividend_yield:.1f}%")
            else:
                score += 5
                criteria_failed.append(f"配当重視型: {dividend_yield:.1f}%")
        else:
            score += 20
            criteria_met.append("配当なし（成長重視）")
        
        analysis_details['dividend_yield'] = float(dividend_yield) if dividend_yield else None
        
        # 注意事項を追加
        criteria_failed.append("注意: 価格履歴データによる詳細分析が必要")
        
        recommendation, confidence = self._determine_recommendation(score, max_score, data)
        # モメンタム戦略は価格データが不十分なため信頼度を下げる
        confidence *= 0.7
        
        return StrategyResult(
            strategy_name="モメンタム戦略",
            score=score,
            max_score=max_score,
            criteria_met=criteria_met,
            criteria_failed=criteria_failed,
            recommendation=recommendation,
            confidence=confidence,
            analysis_details=analysis_details
        )
    
    def _determine_recommendation(
        self, 
        score: int, 
        max_score: int, 
        data: ProcessedData
    ) -> tuple[RecommendationLevel, float]:
        """推奨レベルと信頼度の決定"""
        
        # データ品質による信頼度調整
        available_data_count = sum(1 for key in ['dividend_yield', 'pe_ratio', 'pb_ratio', 'roe'] 
                                 if data.get(key) is not None)
        confidence = available_data_count / 4.0  # 最大4つのデータ
        
        # 警告による信頼度調整
        critical_warnings = [w for w in data['warnings'] if w['level'] == WarningLevel.CRITICAL]
        if critical_warnings:
            confidence *= 0.7
        
        score_percentage = (score / max_score) * 100
        
        if score_percentage >= 80 and confidence >= 0.8:
            return RecommendationLevel.STRONG_BUY, confidence
        elif score_percentage >= 70 and confidence >= 0.6:
            return RecommendationLevel.BUY, confidence
        elif score_percentage >= 50:
            return RecommendationLevel.HOLD, confidence
        elif score_percentage >= 30:
            return RecommendationLevel.SELL, confidence
        elif confidence < 0.5:
            return RecommendationLevel.INSUFFICIENT_DATA, confidence
        else:
            return RecommendationLevel.STRONG_SELL, confidence
    
    def _create_error_result(self, strategy_name: str, error_message: str) -> StrategyResult:
        """エラー結果の作成"""
        return StrategyResult(
            strategy_name=strategy_name,
            score=0,
            max_score=100,
            criteria_met=[],
            criteria_failed=[f"分析エラー: {error_message}"],
            recommendation=RecommendationLevel.INSUFFICIENT_DATA,
            confidence=0.0,
            analysis_details={'error': error_message}
        )
    
    def get_comprehensive_analysis(self, data: ProcessedData) -> Dict[str, Any]:
        """包括的分析の実行"""
        
        # 全戦略分析
        strategy_results = self.analyze_all_strategies(data)
        
        # 総合スコア計算
        valid_scores = [result.score for result in strategy_results.values() 
                       if result.recommendation != RecommendationLevel.INSUFFICIENT_DATA]
        
        overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
        
        # 最も適合する戦略
        best_strategy = max(strategy_results.items(), 
                          key=lambda x: x[1].score if x[1].recommendation != RecommendationLevel.INSUFFICIENT_DATA else -1)
        
        return {
            'symbol': data['symbol'],
            'overall_score': overall_score,
            'best_strategy': best_strategy[0],
            'best_strategy_score': best_strategy[1].score,
            'strategy_results': {name: result.to_dict() for name, result in strategy_results.items()},
            'data_quality': {
                'warnings_count': len(data['warnings']),
                'critical_warnings': len([w for w in data['warnings'] if w['level'] == WarningLevel.CRITICAL]),
                'available_metrics': sum(1 for key in ['dividend_yield', 'pe_ratio', 'pb_ratio', 'roe'] 
                                       if data.get(key) is not None)
            },
            'analysis_timestamp': datetime.now().isoformat()
        }