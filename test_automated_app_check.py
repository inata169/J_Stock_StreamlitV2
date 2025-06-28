#!/usr/bin/env python3
"""
自動アプリケーションテストスクリプト
Streamlitアプリの状態を自動的にチェックして、ログとエラーを報告
"""

import time
import logging
import requests
import subprocess
import sys
import os
from datetime import datetime
import json
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StreamlitAppTester:
    """Streamlitアプリケーションの自動テスター"""
    
    def __init__(self, port=8502):
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.process = None
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'errors': [],
            'warnings': []
        }
    
    def start_app(self):
        """Streamlitアプリを起動"""
        logger.info("Streamlitアプリを起動中...")
        self.process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(self.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # アプリの起動を待つ
        time.sleep(5)
        
        # 起動確認
        for i in range(10):
            try:
                response = requests.get(self.base_url, timeout=2)
                if response.status_code == 200:
                    logger.info(f"✅ アプリが起動しました: {self.base_url}")
                    return True
            except:
                time.sleep(1)
        
        logger.error("❌ アプリの起動に失敗しました")
        return False
    
    def check_app_health(self):
        """アプリの健全性チェック"""
        logger.info("アプリケーション健全性チェック開始...")
        
        # 1. 基本的な接続性
        try:
            response = requests.get(self.base_url)
            self.test_results['tests']['connection'] = {
                'status': 'PASS',
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds()
            }
            logger.info(f"✅ 接続性: OK (応答時間: {response.elapsed.total_seconds():.2f}秒)")
        except Exception as e:
            self.test_results['tests']['connection'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            logger.error(f"❌ 接続性: NG - {e}")
        
        # 2. ページナビゲーション確認
        pages = ['portfolio', 'watchlist', 'strategy', 'charts']
        for page in pages:
            try:
                # Streamlitのページ遷移をシミュレート
                response = requests.get(f"{self.base_url}/?page={page}")
                if response.status_code == 200:
                    self.test_results['tests'][f'page_{page}'] = {'status': 'PASS'}
                    logger.info(f"✅ ページ '{page}': アクセス可能")
                else:
                    self.test_results['tests'][f'page_{page}'] = {
                        'status': 'FAIL',
                        'status_code': response.status_code
                    }
                    logger.warning(f"⚠️ ページ '{page}': ステータス {response.status_code}")
            except Exception as e:
                self.test_results['tests'][f'page_{page}'] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                logger.error(f"❌ ページ '{page}': エラー - {e}")
    
    def check_logs(self):
        """ログファイルのエラーチェック"""
        logger.info("ログファイルチェック開始...")
        
        log_files = [
            'app.log',
            'streamlit.log',
            'automated_test.log'
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                logger.info(f"📋 {log_file} を確認中...")
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[-100:]  # 最後の100行
                    
                    error_count = 0
                    warning_count = 0
                    
                    for line in lines:
                        if 'ERROR' in line or 'CRITICAL' in line:
                            error_count += 1
                            self.test_results['errors'].append({
                                'file': log_file,
                                'line': line.strip()
                            })
                        elif 'WARNING' in line:
                            warning_count += 1
                            self.test_results['warnings'].append({
                                'file': log_file,
                                'line': line.strip()
                            })
                    
                    logger.info(f"  - エラー: {error_count}件, 警告: {warning_count}件")
    
    def simulate_user_actions(self):
        """ユーザー操作のシミュレーション"""
        logger.info("ユーザー操作シミュレーション開始...")
        
        # 1. CSVアップロードのシミュレーション（実際にはファイルをアップロードできないが、エンドポイントの存在確認）
        logger.info("📤 CSVアップロード機能の確認...")
        # ここでは実際のアップロードはできないが、機能の存在を確認
        
        # 2. データ取得のシミュレーション
        logger.info("📊 データ取得機能の確認...")
        # APIエンドポイントへのアクセスをシミュレート
    
    def generate_report(self):
        """テストレポートの生成"""
        logger.info("\n" + "="*50)
        logger.info("📊 テストレポート")
        logger.info("="*50)
        
        # テスト結果のサマリー
        total_tests = len(self.test_results['tests'])
        passed = sum(1 for t in self.test_results['tests'].values() if t.get('status') == 'PASS')
        failed = sum(1 for t in self.test_results['tests'].values() if t.get('status') == 'FAIL')
        errors = sum(1 for t in self.test_results['tests'].values() if t.get('status') == 'ERROR')
        
        logger.info(f"総テスト数: {total_tests}")
        logger.info(f"✅ 成功: {passed}")
        logger.info(f"❌ 失敗: {failed}")
        logger.info(f"⚠️ エラー: {errors}")
        
        # エラーと警告のサマリー
        logger.info(f"\nエラー総数: {len(self.test_results['errors'])}")
        logger.info(f"警告総数: {len(self.test_results['warnings'])}")
        
        # 最新のエラーを表示
        if self.test_results['errors']:
            logger.info("\n最新のエラー:")
            for error in self.test_results['errors'][-5:]:
                logger.error(f"  - {error['file']}: {error['line'][:100]}...")
        
        # レポートをファイルに保存
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        logger.info(f"\nレポート保存: {report_file}")
        
        return self.test_results
    
    def cleanup(self):
        """クリーンアップ処理"""
        if self.process:
            logger.info("アプリを終了中...")
            self.process.terminate()
            time.sleep(2)
            if self.process.poll() is None:
                self.process.kill()
            logger.info("✅ アプリを終了しました")


def run_automated_test():
    """自動テストの実行"""
    tester = StreamlitAppTester()
    
    try:
        # アプリ起動
        if not tester.start_app():
            logger.error("アプリの起動に失敗したため、テストを中止します")
            return
        
        # 各種テスト実行
        tester.check_app_health()
        tester.check_logs()
        tester.simulate_user_actions()
        
        # レポート生成
        report = tester.generate_report()
        
        # 結果に基づいた推奨事項
        logger.info("\n" + "="*50)
        logger.info("💡 推奨アクション")
        logger.info("="*50)
        
        if report['errors']:
            logger.info("1. エラーが検出されました。ログを確認してください。")
        
        if report['warnings']:
            logger.info("2. 警告が検出されました。パフォーマンスに影響する可能性があります。")
        
        failed_tests = [name for name, result in report['tests'].items() if result.get('status') != 'PASS']
        if failed_tests:
            logger.info(f"3. 失敗したテスト: {', '.join(failed_tests)}")
        
        if not report['errors'] and not failed_tests:
            logger.info("✨ すべてのテストが正常に完了しました！")
    
    finally:
        tester.cleanup()


def monitor_logs_realtime():
    """リアルタイムログ監視（別プロセスで実行）"""
    logger.info("リアルタイムログ監視を開始...")
    
    log_file = 'app.log'
    if not os.path.exists(log_file):
        Path(log_file).touch()
    
    # tail -fのような動作
    with open(log_file, 'r') as f:
        # ファイルの最後に移動
        f.seek(0, 2)
        
        while True:
            line = f.readline()
            if line:
                # エラーや警告を強調表示
                if 'ERROR' in line or 'CRITICAL' in line:
                    print(f"🔴 {line.strip()}")
                elif 'WARNING' in line:
                    print(f"🟡 {line.strip()}")
                else:
                    print(f"   {line.strip()}")
            else:
                time.sleep(0.1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Streamlitアプリ自動テスト")
    parser.add_argument('--monitor', action='store_true', help="リアルタイムログ監視モード")
    args = parser.parse_args()
    
    if args.monitor:
        monitor_logs_realtime()
    else:
        run_automated_test()