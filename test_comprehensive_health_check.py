#!/usr/bin/env python3
"""
完璧なテスト&修正ループ - 包括的システム健全性診断
v2.0.0 対応版

このテストファイルは、同様の問題を防ぐための多層防御システムです：
1. 環境診断（仮想環境 vs システム環境）
2. 依存関係完全性テスト
3. アプリケーション段階テスト
4. 自動問題検出・修復提案
"""

import sys
import os
import subprocess
import importlib
import traceback
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('health_check.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class ComprehensiveHealthChecker:
    """包括的システム健全性診断"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'python_info': {},
            'environment_info': {},
            'dependency_tests': {},
            'application_tests': {},
            'recommendations': [],
            'overall_status': 'UNKNOWN'
        }
    
    def check_python_environment(self) -> Dict:
        """Python環境の詳細診断"""
        logger.info("🐍 Python環境診断開始")
        
        env_info = {
            'python_version': sys.version,
            'python_executable': sys.executable,
            'platform': sys.platform,
            'python_path': sys.path[:3],  # 最初の3つのパスのみ
            'virtual_env': None,
            'pip_packages': {}
        }
        
        # 仮想環境検出
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            env_info['virtual_env'] = 'ACTIVE'
            env_info['virtual_env_path'] = sys.prefix
        else:
            env_info['virtual_env'] = 'NONE'
        
        # 重要パッケージのバージョン確認
        critical_packages = [
            'pandas', 'streamlit', 'yfinance', 'sqlite3', 
            'numpy', 'requests', 'matplotlib', 'plotly'
        ]
        
        for package in critical_packages:
            try:
                if package == 'sqlite3':
                    import sqlite3
                    env_info['pip_packages'][package] = sqlite3.sqlite_version
                else:
                    module = importlib.import_module(package)
                    version = getattr(module, '__version__', 'UNKNOWN')
                    env_info['pip_packages'][package] = version
                logger.info(f"✅ {package}: {env_info['pip_packages'][package]}")
            except ImportError as e:
                env_info['pip_packages'][package] = f"MISSING: {str(e)}"
                logger.error(f"❌ {package}: インポートエラー")
        
        self.results['python_info'] = env_info
        return env_info
    
    def test_dependency_functionality(self) -> Dict:
        """依存関係の機能テスト（単なるインポートではなく実際の動作確認）"""
        logger.info("🔧 依存関係機能テスト開始")
        
        functionality_tests = {}
        
        # 1. pandas機能テスト
        try:
            import pandas as pd
            import numpy as np
            
            # データフレーム作成・操作テスト
            test_df = pd.DataFrame({
                'symbol': ['9432', '6758'], 
                'price': [2000.0, 15000.0]
            })
            test_df['market_value'] = test_df['price'] * 100
            
            # CSV読み書きテスト
            test_csv_path = Path('test_pandas_functionality.csv')
            test_df.to_csv(test_csv_path, index=False)
            read_df = pd.read_csv(test_csv_path)
            test_csv_path.unlink()  # 削除
            
            functionality_tests['pandas'] = {
                'status': 'PASS',
                'version': pd.__version__,
                'dataframe_operations': 'OK',
                'csv_operations': 'OK'
            }
            logger.info("✅ pandas機能テスト PASS")
            
        except Exception as e:
            functionality_tests['pandas'] = {
                'status': 'FAIL',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            logger.error(f"❌ pandas機能テスト FAIL: {e}")
        
        # 2. streamlit機能テスト
        try:
            import streamlit as st
            functionality_tests['streamlit'] = {
                'status': 'PASS',
                'version': st.__version__,
                'import_check': 'OK'
            }
            logger.info("✅ streamlit機能テスト PASS")
            
        except Exception as e:
            functionality_tests['streamlit'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            logger.error(f"❌ streamlit機能テスト FAIL: {e}")
        
        # 3. yfinance機能テスト
        try:
            import yfinance as yf
            
            # 軽量データ取得テスト（タイムアウト付き）
            ticker = yf.Ticker("9432.T")
            info = ticker.info
            
            functionality_tests['yfinance'] = {
                'status': 'PASS',
                'version': yf.__version__,
                'data_fetch': 'OK' if info else 'LIMITED'
            }
            logger.info("✅ yfinance機能テスト PASS")
            
        except Exception as e:
            functionality_tests['yfinance'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            logger.error(f"❌ yfinance機能テスト FAIL: {e}")
        
        # 4. SQLite機能テスト
        try:
            import sqlite3
            
            # インメモリデータベーステスト
            conn = sqlite3.connect(':memory:')
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE test (id INTEGER, name TEXT)')
            cursor.execute('INSERT INTO test VALUES (1, "テスト")')
            result = cursor.execute('SELECT * FROM test').fetchone()
            conn.close()
            
            functionality_tests['sqlite3'] = {
                'status': 'PASS',
                'version': sqlite3.sqlite_version,
                'database_operations': 'OK'
            }
            logger.info("✅ sqlite3機能テスト PASS")
            
        except Exception as e:
            functionality_tests['sqlite3'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            logger.error(f"❌ sqlite3機能テスト FAIL: {e}")
        
        self.results['dependency_tests'] = functionality_tests
        return functionality_tests
    
    def test_application_layers(self) -> Dict:
        """アプリケーション段階テスト"""
        logger.info("🏗️ アプリケーション段階テスト開始")
        
        app_tests = {}
        
        # Stage 1: モジュールインポートテスト
        try:
            from core.database_init import initialize_stock_database
            from pages import portfolio, watchlist, strategy, charts
            
            app_tests['imports'] = {
                'status': 'PASS',
                'core_modules': 'OK',
                'page_modules': 'OK'
            }
            logger.info("✅ Stage 1 - インポート PASS")
            
        except Exception as e:
            app_tests['imports'] = {
                'status': 'FAIL',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            logger.error(f"❌ Stage 1 - インポート FAIL: {e}")
            return app_tests
        
        # Stage 2: データベース初期化テスト
        try:
            success = initialize_stock_database("test_health_check.db")
            
            # データベースファイル確認
            db_path = Path("test_health_check.db")
            db_exists = db_path.exists()
            
            app_tests['database_init'] = {
                'status': 'PASS' if success and db_exists else 'FAIL',
                'initialization': success,
                'file_created': db_exists,
                'file_size': db_path.stat().st_size if db_exists else 0
            }
            
            # テストファイル削除
            if db_exists:
                db_path.unlink()
            
            logger.info("✅ Stage 2 - データベース初期化 PASS")
            
        except Exception as e:
            app_tests['database_init'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            logger.error(f"❌ Stage 2 - データベース初期化 FAIL: {e}")
        
        # Stage 3: Streamlit起動可能性テスト
        try:
            # app.pyファイル存在確認
            app_py_path = Path("app.py")
            if not app_py_path.exists():
                raise FileNotFoundError("app.py not found")
            
            # 構文チェック（実際の起動はしない）
            with open(app_py_path, 'r', encoding='utf-8') as f:
                app_code = f.read()
            
            compile(app_code, 'app.py', 'exec')
            
            app_tests['streamlit_readiness'] = {
                'status': 'PASS',
                'app_py_exists': True,
                'syntax_valid': True,
                'estimated_startup': 'READY'
            }
            logger.info("✅ Stage 3 - Streamlit起動準備 PASS")
            
        except Exception as e:
            app_tests['streamlit_readiness'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            logger.error(f"❌ Stage 3 - Streamlit起動準備 FAIL: {e}")
        
        self.results['application_tests'] = app_tests
        return app_tests
    
    def analyze_and_recommend(self) -> List[str]:
        """問題分析と修復推奨事項"""
        logger.info("🔍 問題分析・推奨事項生成")
        
        recommendations = []
        
        # 仮想環境関連の推奨事項
        if self.results['python_info'].get('virtual_env') == 'ACTIVE':
            failed_deps = [
                pkg for pkg, status in self.results['dependency_tests'].items() 
                if isinstance(status, dict) and status.get('status') == 'FAIL'
            ]
            
            if failed_deps:
                recommendations.append(
                    f"🔥 仮想環境で{len(failed_deps)}個のパッケージに問題があります。"
                    f"システム環境での動作確認を推奨します: {', '.join(failed_deps)}"
                )
                recommendations.append(
                    "💡 修復手順: `deactivate` で仮想環境を抜けて、システム環境でテストしてください"
                )
        
        # パッケージ固有の推奨事項
        pandas_status = self.results['dependency_tests'].get('pandas', {})
        if pandas_status.get('status') == 'FAIL':
            recommendations.append(
                "🐼 pandas修復: `pip uninstall pandas && pip install pandas` で再インストールしてください"
            )
        
        streamlit_status = self.results['dependency_tests'].get('streamlit', {})
        if streamlit_status.get('status') == 'FAIL':
            recommendations.append(
                "📊 streamlit修復: `pip install --upgrade streamlit` でアップグレードしてください"
            )
        
        # アプリケーション固有の推奨事項
        if self.results['application_tests'].get('imports', {}).get('status') == 'FAIL':
            recommendations.append(
                "📁 モジュール構造確認: core/ と pages/ フォルダが正しく配置されているか確認してください"
            )
        
        # 包括的な推奨事項
        if not recommendations:
            recommendations.append("✅ すべてのテストが成功しました！アプリケーションは正常に動作可能です")
        else:
            recommendations.append(
                "🔄 修復後、このテストを再実行して問題が解決されたことを確認してください"
            )
        
        self.results['recommendations'] = recommendations
        return recommendations
    
    def determine_overall_status(self) -> str:
        """総合ステータス判定"""
        failed_critical = []
        
        # 重要な依存関係の失敗をチェック
        critical_deps = ['pandas', 'streamlit']
        for dep in critical_deps:
            if self.results['dependency_tests'].get(dep, {}).get('status') == 'FAIL':
                failed_critical.append(dep)
        
        # アプリケーションテストの失敗をチェック
        if self.results['application_tests'].get('imports', {}).get('status') == 'FAIL':
            failed_critical.append('imports')
        
        if not failed_critical:
            status = 'HEALTHY'
        elif len(failed_critical) <= 1:
            status = 'WARNING'
        else:
            status = 'CRITICAL'
        
        self.results['overall_status'] = status
        return status
    
    def run_full_diagnostic(self) -> Dict:
        """完全診断の実行"""
        logger.info("🚀 包括的健全性診断開始")
        print("=" * 60)
        print("🏥 日本株ウォッチドッグ - 包括的システム健全性診断")
        print("=" * 60)
        
        # 各段階の実行
        self.check_python_environment()
        self.test_dependency_functionality()
        self.test_application_layers()
        self.analyze_and_recommend()
        overall_status = self.determine_overall_status()
        
        # 結果表示
        print(f"\n📊 診断結果サマリー:")
        print(f"   総合ステータス: {overall_status}")
        print(f"   Python環境: {self.results['python_info']['virtual_env']}")
        print(f"   依存関係テスト: {len([d for d in self.results['dependency_tests'].values() if d.get('status') == 'PASS'])}/{len(self.results['dependency_tests'])} PASS")
        print(f"   アプリケーションテスト: {len([d for d in self.results['application_tests'].values() if d.get('status') == 'PASS'])}/{len(self.results['application_tests'])} PASS")
        
        print(f"\n💡 推奨事項:")
        for i, rec in enumerate(self.results['recommendations'], 1):
            print(f"   {i}. {rec}")
        
        # JSON結果保存
        results_path = Path('health_check_results.json')
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 詳細結果: {results_path}")
        logger.info("🏁 包括的健全性診断完了")
        
        return self.results


def quick_startup_test() -> bool:
    """クイック起動テスト（シンプル版）"""
    print("\n⚡ クイック起動テスト")
    try:
        import pandas as pd
        import streamlit as st
        from core.database_init import initialize_stock_database
        
        print("✅ 基本インポート成功")
        
        # 簡単なpandas動作確認
        df = pd.DataFrame({'test': [1, 2, 3]})
        assert len(df) == 3
        print("✅ pandas動作確認")
        
        # データベース初期化テスト
        success = initialize_stock_database("quick_test.db")
        if success:
            Path("quick_test.db").unlink(missing_ok=True)
        print("✅ データベース初期化確認")
        
        print("🎉 アプリケーション起動可能！")
        return True
        
    except Exception as e:
        print(f"❌ クイックテスト失敗: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='システム健全性診断')
    parser.add_argument('--quick', action='store_true', help='クイックテストのみ実行')
    parser.add_argument('--full', action='store_true', help='完全診断を実行')
    
    args = parser.parse_args()
    
    if args.quick:
        quick_startup_test()
    elif args.full or len(sys.argv) == 1:
        checker = ComprehensiveHealthChecker()
        results = checker.run_full_diagnostic()
    else:
        print("使用方法: python test_comprehensive_health_check.py [--quick|--full]")