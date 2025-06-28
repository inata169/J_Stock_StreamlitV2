#!/usr/bin/env python3
"""
完全自動テストスイート実行スクリプト
手動操作なしでアプリケーションの全機能をテスト
"""

import subprocess
import sys
import time
import logging
from datetime import datetime
import json
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FullTestSuite:
    """完全テストスイート"""
    
    def __init__(self):
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests_run': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0
            }
        }
    
    def run_test(self, name, command, timeout=60):
        """個別テストの実行"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 テスト実行: {name}")
        logger.info('='*60)
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            elapsed_time = time.time() - start_time
            
            test_result = {
                'name': name,
                'command': command,
                'elapsed_time': elapsed_time,
                'return_code': result.returncode,
                'stdout': result.stdout[-1000:],  # 最後の1000文字
                'stderr': result.stderr[-1000:] if result.stderr else None
            }
            
            if result.returncode == 0:
                logger.info(f"✅ 成功 ({elapsed_time:.2f}秒)")
                test_result['status'] = 'PASS'
                self.test_results['summary']['passed'] += 1
            else:
                logger.error(f"❌ 失敗 (リターンコード: {result.returncode})")
                test_result['status'] = 'FAIL'
                self.test_results['summary']['failed'] += 1
                if result.stderr:
                    logger.error(f"エラー出力: {result.stderr[:200]}...")
            
            self.test_results['tests_run'].append(test_result)
            self.test_results['summary']['total'] += 1
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏱️ タイムアウト ({timeout}秒)")
            self.test_results['tests_run'].append({
                'name': name,
                'command': command,
                'status': 'TIMEOUT',
                'elapsed_time': timeout
            })
            self.test_results['summary']['errors'] += 1
            self.test_results['summary']['total'] += 1
            
        except Exception as e:
            logger.error(f"💥 エラー: {e}")
            self.test_results['tests_run'].append({
                'name': name,
                'command': command,
                'status': 'ERROR',
                'error': str(e)
            })
            self.test_results['summary']['errors'] += 1
            self.test_results['summary']['total'] += 1
    
    def run_all_tests(self):
        """全テストの実行"""
        logger.info("🚀 完全テストスイート開始")
        logger.info(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 環境チェック
        self.run_test(
            "環境チェック",
            f"{sys.executable} test_comprehensive_health_check.py --quick",
            timeout=30
        )
        
        # 2. インポートテスト
        self.run_test(
            "モジュールインポート",
            f"{sys.executable} -c \"import app; import pandas; import streamlit; print('All imports OK')\"",
            timeout=10
        )
        
        # 3. データベース初期化テスト
        self.run_test(
            "データベース初期化",
            f"{sys.executable} -c \"from core.database_init import init_database; init_database('test_suite.db'); print('DB initialized')\"",
            timeout=30
        )
        
        # 4. CSVパーサーテスト
        self.run_test(
            "CSVパーサー",
            f"{sys.executable} -c \"from core.csv_parser import UnifiedCSVParser; parser = UnifiedCSVParser(); print('CSV parser OK')\"",
            timeout=10
        )
        
        # 5. 財務データプロセッサーテスト
        self.run_test(
            "財務データプロセッサー",
            f"{sys.executable} -c \"from core.financial_data_processor import FinancialDataProcessor; processor = FinancialDataProcessor(); print('Processor OK')\"",
            timeout=10
        )
        
        # 6. アプリケーション起動テスト（バックグラウンド）
        logger.info("\n📱 アプリケーション起動テスト...")
        app_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8503"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        time.sleep(10)  # アプリ起動待機
        
        # アプリが起動しているか確認
        try:
            import requests
            response = requests.get("http://localhost:8503", timeout=5)
            if response.status_code == 200:
                logger.info("✅ アプリケーション起動成功")
                self.test_results['summary']['passed'] += 1
            else:
                logger.error(f"❌ アプリケーション起動失敗 (ステータス: {response.status_code})")
                self.test_results['summary']['failed'] += 1
        except Exception as e:
            logger.error(f"❌ アプリケーション接続失敗: {e}")
            self.test_results['summary']['failed'] += 1
        finally:
            self.test_results['summary']['total'] += 1
        
        # 7. アプリケーション状態監視
        self.run_test(
            "アプリケーション状態監視",
            f"{sys.executable} monitor_app_state.py",
            timeout=30
        )
        
        # アプリケーションを終了
        app_process.terminate()
        time.sleep(2)
        
        # 8. メモリ使用量チェック
        self.run_test(
            "メモリ使用量",
            f"{sys.executable} -c \"import psutil; print(f'Memory: {{psutil.Process().memory_info().rss / 1024 / 1024:.2f}} MB')\"",
            timeout=10
        )
        
        # 9. ログファイル分析
        self.check_log_files()
        
        # 10. 最終レポート生成
        self.generate_final_report()
    
    def check_log_files(self):
        """ログファイルの分析"""
        logger.info("\n📋 ログファイル分析...")
        
        log_analysis = {
            'errors': 0,
            'warnings': 0,
            'critical': 0
        }
        
        log_files = ['app.log', 'automated_test.log']
        
        for log_file in log_files:
            if Path(log_file).exists():
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    log_analysis['errors'] += content.count('ERROR')
                    log_analysis['warnings'] += content.count('WARNING')
                    log_analysis['critical'] += content.count('CRITICAL')
        
        self.test_results['log_analysis'] = log_analysis
        
        logger.info(f"  - エラー: {log_analysis['errors']}件")
        logger.info(f"  - 警告: {log_analysis['warnings']}件")
        logger.info(f"  - 重大: {log_analysis['critical']}件")
    
    def generate_final_report(self):
        """最終レポートの生成"""
        logger.info("\n" + "="*60)
        logger.info("📊 テストスイート最終レポート")
        logger.info("="*60)
        
        summary = self.test_results['summary']
        
        # 成功率の計算
        success_rate = (summary['passed'] / summary['total'] * 100) if summary['total'] > 0 else 0
        
        logger.info(f"\n総テスト数: {summary['total']}")
        logger.info(f"✅ 成功: {summary['passed']}")
        logger.info(f"❌ 失敗: {summary['failed']}")
        logger.info(f"⚠️ エラー: {summary['errors']}")
        logger.info(f"📈 成功率: {success_rate:.1f}%")
        
        # ログ分析結果
        if 'log_analysis' in self.test_results:
            log_stats = self.test_results['log_analysis']
            logger.info(f"\nログ分析:")
            logger.info(f"  - エラーログ: {log_stats['errors']}件")
            logger.info(f"  - 警告ログ: {log_stats['warnings']}件")
        
        # 評価
        logger.info("\n🎯 総合評価:")
        if success_rate >= 90 and self.test_results.get('log_analysis', {}).get('errors', 0) == 0:
            logger.info("  ⭐ 優秀 - アプリケーションは安定して動作しています")
        elif success_rate >= 70:
            logger.info("  ✅ 良好 - 軽微な問題がありますが、基本機能は動作しています")
        elif success_rate >= 50:
            logger.info("  ⚠️ 要改善 - 複数の問題があります")
        else:
            logger.info("  ❌ 重大 - 深刻な問題があります")
        
        # 推奨事項
        logger.info("\n💡 推奨事項:")
        
        if summary['failed'] > 0:
            logger.info("  1. 失敗したテストの詳細を確認してください")
            
            # 失敗したテストをリスト
            failed_tests = [t['name'] for t in self.test_results['tests_run'] if t.get('status') == 'FAIL']
            if failed_tests:
                logger.info(f"     失敗: {', '.join(failed_tests)}")
        
        if self.test_results.get('log_analysis', {}).get('errors', 0) > 0:
            logger.info("  2. エラーログを確認して原因を特定してください")
        
        if summary['errors'] > 0:
            logger.info("  3. タイムアウトやシステムエラーが発生しています")
        
        # レポート保存
        report_file = f"full_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📄 詳細レポート保存: {report_file}")
        
        # サマリーテキストファイルも作成
        summary_file = f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"テストスイート実行結果\n")
            f.write(f"実行日時: {self.test_results['timestamp']}\n")
            f.write(f"成功率: {success_rate:.1f}%\n")
            f.write(f"総テスト: {summary['total']}, 成功: {summary['passed']}, 失敗: {summary['failed']}\n")
            
            if failed_tests:
                f.write(f"\n失敗したテスト:\n")
                for test in failed_tests:
                    f.write(f"  - {test}\n")
        
        logger.info(f"📄 サマリー保存: {summary_file}")
        
        return success_rate >= 70  # 70%以上で成功とする


if __name__ == "__main__":
    # psutilのインストール確認
    try:
        import psutil
    except ImportError:
        logger.warning("psutilがインストールされていません。メモリ使用量テストはスキップされます。")
        logger.info("インストール: pip install psutil")
    
    # requestsのインストール確認
    try:
        import requests
    except ImportError:
        logger.error("requestsがインストールされていません。")
        logger.info("インストール: pip install requests")
        sys.exit(1)
    
    # テストスイート実行
    suite = FullTestSuite()
    success = suite.run_all_tests()
    
    # 終了コード
    sys.exit(0 if success else 1)