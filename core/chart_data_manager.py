"""
チャート生成層 (ChartDataManager)

正規化済みデータを使用してPlotlyチャートを生成。
統一プロセッサ経由でのみデータ処理を行う。
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
import logging
from datetime import datetime, timedelta
import numpy as np

from .financial_data_processor import ProcessedData, WarningLevel
from .multi_data_source import MultiDataSourceManager

# ログ設定
logger = logging.getLogger(__name__)


class ChartDataManager:
    """
    チャート生成管理システム
    
    統一プロセッサ経由でのチャート用データ処理と
    Plotlyを使用した金融チャートの生成を担当。
    """
    
    def __init__(self, data_source_manager: MultiDataSourceManager):
        """
        初期化
        
        Args:
            data_source_manager: データソース管理インスタンス
        """
        self.data_source = data_source_manager
        self.chart_themes = {
            'default': {
                'template': 'plotly_white',
                'color_sequence': ['#FF6B35', '#004E89', '#00A6A6', '#7209B7', '#F2CC85'],
                'background_color': '#FFFFFF',
                'grid_color': '#E8E8E8'
            },
            'dark': {
                'template': 'plotly_dark', 
                'color_sequence': ['#FF6B35', '#66D9EF', '#A6E22E', '#F92672', '#FD971F'],
                'background_color': '#2F2F2F',
                'grid_color': '#404040'
            }
        }
    
    def create_dividend_yield_chart(
        self, 
        symbols: List[str], 
        theme: str = 'default'
    ) -> go.Figure:
        """
        配当利回り比較チャート作成
        
        Args:
            symbols: 銘柄コードリスト
            theme: チャートテーマ
            
        Returns:
            go.Figure: Plotlyチャート
        """
        try:
            # 複数銘柄データ取得
            stocks_data = self.data_source.get_multiple_stocks(symbols)
            
            if not stocks_data:
                return self._create_empty_chart("データなし", theme)
            
            # チャートデータ準備
            chart_data = []
            for symbol, data in stocks_data.items():
                dividend_yield = data.get('dividend_yield')
                if dividend_yield:
                    chart_data.append({
                        'symbol': symbol,
                        'dividend_yield': float(dividend_yield),
                        'has_warnings': len(data['warnings']) > 0,
                        'critical_warnings': len([w for w in data['warnings'] 
                                                if w['level'] == WarningLevel.CRITICAL])
                    })
            
            if not chart_data:
                return self._create_empty_chart("配当データなし", theme)
            
            # DataFrame作成
            df = pd.DataFrame(chart_data)
            
            # 横棒グラフ作成
            fig = go.Figure()
            
            theme_config = self.chart_themes[theme]
            
            # 通常データ
            normal_data = df[df['critical_warnings'] == 0]
            if not normal_data.empty:
                fig.add_trace(go.Bar(
                    y=normal_data['symbol'],
                    x=normal_data['dividend_yield'],
                    orientation='h',
                    name='配当利回り',
                    marker_color=theme_config['color_sequence'][0],
                    hovertemplate='%{y}<br>配当利回り: %{x:.2f}%<extra></extra>'
                ))
            
            # 警告ありデータ
            warning_data = df[df['critical_warnings'] > 0]
            if not warning_data.empty:
                fig.add_trace(go.Bar(
                    y=warning_data['symbol'],
                    x=warning_data['dividend_yield'],
                    orientation='h',
                    name='配当利回り（要注意）',
                    marker_color=theme_config['color_sequence'][3],
                    hovertemplate='%{y}<br>配当利回り: %{x:.2f}%<br>⚠️ データ要確認<extra></extra>'
                ))
            
            # レイアウト設定
            fig.update_layout(
                title='配当利回り比較',
                xaxis_title='配当利回り (%)',
                yaxis_title='銘柄コード',
                template=theme_config['template'],
                height=max(400, len(chart_data) * 50),
                showlegend=True,
                plot_bgcolor=theme_config['background_color']
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Dividend yield chart creation failed: {e}")
            return self._create_error_chart(f"エラー: {str(e)}", theme)
    
    def create_financial_metrics_radar(
        self, 
        symbol: str, 
        theme: str = 'default'
    ) -> go.Figure:
        """
        財務指標レーダーチャート作成
        
        Args:
            symbol: 銘柄コード
            theme: チャートテーマ
            
        Returns:
            go.Figure: レーダーチャート
        """
        try:
            stock_data = self.data_source.get_stock_info(symbol)
            
            # データの有効性チェック
            if not stock_data or not isinstance(stock_data, dict):
                logger.warning(f"Invalid stock data for {symbol}: {type(stock_data)}")
                return self._create_empty_chart(f"{symbol}: データ取得失敗", theme)
            
            # メトリクス正規化（0-100スケール）
            metrics = self._normalize_metrics_for_radar(stock_data)
            
            if not metrics:
                return self._create_empty_chart(f"{symbol}: メトリクスデータなし", theme)
            
            theme_config = self.chart_themes[theme]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=list(metrics.values()),
                theta=list(metrics.keys()),
                fill='toself',
                fillcolor=f'rgba{tuple(list(int(theme_config["color_sequence"][0][1:], 16)[i:i+2], 16) for i in (0, 2, 4)) + [0.3]}',
                line_color=theme_config['color_sequence'][0],
                name=symbol,
                hovertemplate='%{theta}<br>スコア: %{r:.1f}<extra></extra>'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )
                ),
                title=f'{symbol} 財務指標レーダーチャート',
                template=theme_config['template'],
                height=500
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Radar chart creation failed for {symbol}: {e}")
            return self._create_error_chart(f"エラー: {str(e)}", theme)
    
    def create_dividend_history_chart(
        self, 
        symbol: str, 
        period: str = "5y",
        theme: str = 'default'
    ) -> go.Figure:
        """
        配当履歴チャート作成
        
        Args:
            symbol: 銘柄コード
            period: 取得期間
            theme: チャートテーマ
            
        Returns:
            go.Figure: 配当履歴チャート
        """
        try:
            dividend_data = self.data_source.get_dividend_history(symbol, period)
            
            if not dividend_data or not dividend_data.get('dividends'):
                return self._create_empty_chart("配当履歴なし", theme)
            
            # 配当データをDataFrameに変換
            dividends_dict = dividend_data['dividends']
            dates = list(dividends_dict.keys())
            amounts = list(dividends_dict.values())
            
            df = pd.DataFrame({
                'date': pd.to_datetime(dates),
                'amount': amounts
            }).sort_values('date')
            
            theme_config = self.chart_themes[theme]
            
            fig = go.Figure()
            
            # 配当金額の棒グラフ
            fig.add_trace(go.Bar(
                x=df['date'],
                y=df['amount'],
                name='配当金額',
                marker_color=theme_config['color_sequence'][1],
                hovertemplate='日付: %{x}<br>配当: ¥%{y:.2f}<extra></extra>'
            ))
            
            # トレンドライン追加
            if len(df) > 2:
                z = np.polyfit(range(len(df)), df['amount'], 1)
                p = np.poly1d(z)
                
                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=p(range(len(df))),
                    mode='lines',
                    name='トレンド',
                    line=dict(color=theme_config['color_sequence'][3], dash='dash'),
                    hovertemplate='トレンド: ¥%{y:.2f}<extra></extra>'
                ))
            
            fig.update_layout(
                title=f'{symbol} 配当履歴 ({period})',
                xaxis_title='日付',
                yaxis_title='配当金額 (円)',
                template=theme_config['template'],
                height=400,
                hovermode='x unified'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Dividend history chart creation failed for {symbol}: {e}")
            return self._create_error_chart(f"エラー: {str(e)}", theme)
    
    def create_strategy_comparison_chart(
        self, 
        strategy_results: Dict[str, Any], 
        theme: str = 'default'
    ) -> go.Figure:
        """
        投資戦略比較チャート作成
        
        Args:
            strategy_results: 戦略分析結果
            theme: チャートテーマ
            
        Returns:
            go.Figure: 戦略比較チャート
        """
        try:
            if not strategy_results or 'strategy_results' not in strategy_results:
                return self._create_empty_chart("戦略データなし", theme)
            
            # 戦略データ準備
            strategies = []
            scores = []
            confidences = []
            
            for strategy_name, result in strategy_results['strategy_results'].items():
                strategies.append(strategy_name)
                scores.append(result['score_percentage'])
                confidences.append(result['confidence'] * 100)
            
            theme_config = self.chart_themes[theme]
            
            # サブプロット作成
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('戦略スコア', '信頼度'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # スコア棒グラフ
            fig.add_trace(
                go.Bar(
                    x=strategies,
                    y=scores,
                    name='スコア',
                    marker_color=theme_config['color_sequence'][0],
                    hovertemplate='%{x}<br>スコア: %{y:.1f}%<extra></extra>'
                ),
                row=1, col=1
            )
            
            # 信頼度棒グラフ
            fig.add_trace(
                go.Bar(
                    x=strategies,
                    y=confidences,
                    name='信頼度',
                    marker_color=theme_config['color_sequence'][2],
                    hovertemplate='%{x}<br>信頼度: %{y:.1f}%<extra></extra>'
                ),
                row=1, col=2
            )
            
            fig.update_layout(
                title=f'{strategy_results["symbol"]} 投資戦略比較',
                template=theme_config['template'],
                height=500,
                showlegend=False
            )
            
            # Y軸範囲設定
            fig.update_yaxes(range=[0, 100], row=1, col=1)
            fig.update_yaxes(range=[0, 100], row=1, col=2)
            
            return fig
            
        except Exception as e:
            logger.error(f"Strategy comparison chart creation failed: {e}")
            return self._create_error_chart(f"エラー: {str(e)}", theme)
    
    def create_portfolio_allocation_chart(
        self, 
        portfolio_data: List[Dict[str, Any]], 
        theme: str = 'default'
    ) -> go.Figure:
        """
        ポートフォリオ配分円グラフ作成
        
        Args:
            portfolio_data: ポートフォリオデータリスト
            theme: チャートテーマ
            
        Returns:
            go.Figure: 円グラフ
        """
        try:
            if not portfolio_data:
                return self._create_empty_chart("ポートフォリオデータなし", theme)
            
            # データ準備
            symbols = []
            values = []
            
            for stock in portfolio_data:
                symbols.append(stock.get('symbol', '不明'))
                values.append(float(stock.get('market_value', 0)))
            
            theme_config = self.chart_themes[theme]
            
            fig = go.Figure(data=[go.Pie(
                labels=symbols,
                values=values,
                hole=.3,
                marker_colors=theme_config['color_sequence'],
                hovertemplate='%{label}<br>評価額: ¥%{value:,.0f}<br>割合: %{percent}<extra></extra>'
            )])
            
            fig.update_layout(
                title='ポートフォリオ配分',
                template=theme_config['template'],
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.01
                )
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Portfolio allocation chart creation failed: {e}")
            return self._create_error_chart(f"エラー: {str(e)}", theme)
    
    def _normalize_metrics_for_radar(self, data: ProcessedData) -> Dict[str, float]:
        """レーダーチャート用メトリクス正規化"""
        metrics = {}
        
        # データの型チェック
        if not isinstance(data, dict):
            logger.error(f"Invalid data type for radar normalization: {type(data)}")
            return metrics
        
        # 配当利回り (0-10% → 0-100)
        if data.get('dividend_yield') is not None:
            try:
                # Decimalオブジェクトも含めて数値変換
                dividend_yield = float(str(data['dividend_yield']))
                metrics['配当利回り'] = min(dividend_yield * 10, 100)
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to process dividend_yield: {e}, value: {data.get('dividend_yield')}")
        
        # PER (逆数で評価、低いほど良い: 5-30 → 100-0)
        if data.get('pe_ratio') is not None:
            try:
                # Decimalオブジェクトも含めて数値変換
                pe_ratio = float(str(data['pe_ratio']))
                if 5 <= pe_ratio <= 30:
                    metrics['PER評価'] = max(0, 100 - ((pe_ratio - 5) * 4))
                elif pe_ratio < 5:
                    metrics['PER評価'] = 100
                else:
                    metrics['PER評価'] = 0
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to process pe_ratio: {e}, value: {data.get('pe_ratio')}")
        
        # PBR (逆数で評価、低いほど良い: 0.5-3.0 → 100-0)
        if data.get('pb_ratio') is not None:
            try:
                # Decimalオブジェクトも含めて数値変換
                pb_ratio = float(str(data['pb_ratio']))
                if 0.5 <= pb_ratio <= 3.0:
                    metrics['PBR評価'] = max(0, 100 - ((pb_ratio - 0.5) * 40))
                elif pb_ratio < 0.5:
                    metrics['PBR評価'] = 100
                else:
                    metrics['PBR評価'] = 0
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to process pb_ratio: {e}, value: {data.get('pb_ratio')}")
        
        # ROE (0-30% → 0-100)
        if data.get('roe') is not None:
            try:
                # Decimalオブジェクトも含めて数値変換
                roe = float(str(data['roe']))
                metrics['ROE'] = min(max(0, roe * 3.33), 100)
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to process roe: {e}, value: {data.get('roe')}")
        
        return metrics
    
    def _create_empty_chart(self, message: str, theme: str) -> go.Figure:
        """空のチャート作成"""
        theme_config = self.chart_themes[theme]
        
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            font=dict(size=16)
        )
        
        fig.update_layout(
            title="データなし",
            template=theme_config['template'],
            height=400,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        
        return fig
    
    def _create_error_chart(self, error_message: str, theme: str) -> go.Figure:
        """エラーチャート作成"""
        theme_config = self.chart_themes[theme]
        
        fig = go.Figure()
        fig.add_annotation(
            text=f"⚠️ {error_message}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            font=dict(size=16, color='red')
        )
        
        fig.update_layout(
            title="チャート生成エラー",
            template=theme_config['template'],
            height=400,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        
        return fig
    
    def get_chart_config(self, chart_type: str) -> Dict[str, Any]:
        """チャート設定の取得"""
        configs = {
            'dividend_yield': {
                'title': '配当利回り比較',
                'description': '複数銘柄の配当利回りを横棒グラフで比較',
                'data_requirements': ['dividend_yield'],
                'recommended_symbols': 5
            },
            'financial_radar': {
                'title': '財務指標レーダーチャート',
                'description': '単一銘柄の財務指標を総合評価',
                'data_requirements': ['dividend_yield', 'pe_ratio', 'pb_ratio', 'roe'],
                'recommended_symbols': 1
            },
            'dividend_history': {
                'title': '配当履歴',
                'description': '配当の推移と傾向を時系列で表示',
                'data_requirements': ['dividend_history'],
                'recommended_symbols': 1
            },
            'strategy_comparison': {
                'title': '投資戦略比較',
                'description': '複数の投資戦略による評価結果を比較',
                'data_requirements': ['strategy_analysis'],
                'recommended_symbols': 1
            },
            'portfolio_allocation': {
                'title': 'ポートフォリオ配分',
                'description': '投資配分を円グラフで可視化',
                'data_requirements': ['portfolio_data'],
                'recommended_symbols': 'multiple'
            }
        }
        
        return configs.get(chart_type, {})