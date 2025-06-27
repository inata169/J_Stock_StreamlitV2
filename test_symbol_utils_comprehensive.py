#!/usr/bin/env python3
"""
SymbolUtils包括的テスト v2.0.0
銘柄コード正規化・変換ユーティリティの徹底テスト
"""

import os
import sys
import logging
from typing import Tuple, Optional, List

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# パス設定
sys.path.append(os.path.dirname(__file__))
sys.path.append('core')


class TestSymbolUtils:
    """SymbolUtilsの包括的テストクラス"""
    
    def __init__(self):
        try:
            from core.symbol_utils import SymbolNormalizer, DecimalFormatter
            self.SymbolNormalizer = SymbolNormalizer
            self.DecimalFormatter = DecimalFormatter
            print("✅ SymbolUtilsモジュール読み込み成功")
        except ImportError as e:
            print(f"❌ SymbolUtilsモジュール読み込み失敗: {e}")
            raise
    
    def test_symbol_normalization_basic(self):
        """基本的な銘柄コード正規化テスト"""
        print("\n=== 基本的な銘柄コード正規化テスト ===")
        
        test_cases = [
            # (入力, 期待される出力, テストケース名)
            ('9432.T', '9432', '.T除去'),
            ('"9432"', '9432', '二重引用符除去'),
            ("'9432'", '9432', '単一引用符除去'),
            ('  9432  ', '9432', '前後空白除去'),
            ('9432', '9432', 'そのまま'),
            ('1928.T', '1928', '.T除去（別銘柄）'),
            ('8316 三井住友', '8316', 'スペース以降除去'),
        ]
        
        all_passed = True
        for input_symbol, expected, test_name in test_cases:
            result = self.SymbolNormalizer.normalize(input_symbol)
            if result == expected:
                print(f"✅ {test_name}: {input_symbol:15} → {result}")
            else:
                print(f"❌ {test_name}: {input_symbol:15} → {result} (期待値: {expected})")
                all_passed = False
        
        return all_passed
    
    def test_symbol_normalization_edge_cases(self):
        """エッジケースの銘柄コード正規化テスト"""
        print("\n=== エッジケースの銘柄コード正規化テスト ===")
        
        edge_cases = [
            # (入力, 期待される出力, テストケース名)
            ('', None, '空文字列'),
            (None, None, 'None値'),
            ('123', None, '3桁数字（無効）'),
            ('12345', None, '5桁数字（無効）'),
            ('AAPL', None, 'アルファベット（日本株以外）'),
            ('9432.', '9432', '.のみ'),
            ('"', None, '引用符のみ'),
            ('  ', None, '空白のみ'),
            ('0000', '0000', 'ゼロパディング'),
            ('9999', '9999', '最大値'),
        ]
        
        all_passed = True
        for input_symbol, expected, test_name in edge_cases:
            try:
                result = self.SymbolNormalizer.normalize(input_symbol)
                if result == expected:
                    print(f"✅ {test_name}: {str(input_symbol):15} → {str(result)}")
                else:
                    print(f"❌ {test_name}: {str(input_symbol):15} → {str(result)} (期待値: {str(expected)})")
                    all_passed = False
            except Exception as e:
                print(f"❌ {test_name}: {str(input_symbol):15} → エラー: {e}")
                all_passed = False
        
        return all_passed
    
    def test_yahoo_format_conversion(self):
        """Yahoo Finance形式変換テスト"""
        print("\n=== Yahoo Finance形式変換テスト ===")
        
        test_cases = [
            ('9432', '9432.T'),
            ('1928', '1928.T'),
            ('8316', '8316.T'),
            ('7203', '7203.T'),
        ]
        
        all_passed = True
        for input_symbol, expected in test_cases:
            try:
                result = self.SymbolNormalizer.to_yahoo_format(input_symbol)
                if result == expected:
                    print(f"✅ Yahoo形式変換: {input_symbol} → {result}")
                else:
                    print(f"❌ Yahoo形式変換: {input_symbol} → {result} (期待値: {expected})")
                    all_passed = False
            except Exception as e:
                print(f"❌ Yahoo形式変換エラー: {input_symbol} → {e}")
                all_passed = False
        
        # 無効な銘柄コードでのエラーテスト
        try:
            result = self.SymbolNormalizer.to_yahoo_format('invalid')
            print(f"❌ 無効銘柄エラーテスト失敗: エラーが発生しなかった → {result}")
            all_passed = False
        except ValueError:
            print("✅ 無効銘柄エラーテスト成功: 適切にValueErrorが発生")
        except Exception as e:
            print(f"❌ 無効銘柄エラーテスト失敗: 予期しないエラー → {e}")
            all_passed = False
        
        return all_passed
    
    def test_japanese_stock_validation(self):
        """日本株銘柄コード検証テスト"""
        print("\n=== 日本株銘柄コード検証テスト ===")
        
        test_cases = [
            ('9432', True, '有効な日本株'),
            ('1928.T', True, '有効な日本株（.T付き）'),
            ('"7203"', True, '有効な日本株（引用符付き）'),
            ('AAPL', False, '米国株'),
            ('123', False, '3桁（無効）'),
            ('12345', False, '5桁（無効）'),
            ('', False, '空文字列'),
            ('invalid', False, '無効文字列'),
        ]
        
        all_passed = True
        for input_symbol, expected, test_name in test_cases:
            result = self.SymbolNormalizer.validate_japanese_stock(input_symbol)
            if result == expected:
                print(f"✅ {test_name}: {input_symbol:10} → {result}")
            else:
                print(f"❌ {test_name}: {input_symbol:10} → {result} (期待値: {expected})")
                all_passed = False
        
        return all_passed
    
    def test_csv_row_extraction(self):
        """CSV行からの銘柄抽出テスト"""
        print("\n=== CSV行からの銘柄抽出テスト ===")
        
        test_cases = [
            # SBI証券形式
            {
                'data': {
                    '銘柄（コード）': '1928',
                    '銘柄名称': '積水ハウス'
                },
                'expected_symbol': '1928',
                'expected_name': '積水ハウス',
                'test_name': 'SBI証券形式'
            },
            # 楽天証券形式
            {
                'data': {
                    '銘柄コード': '7203.T',
                    '銘柄名': 'トヨタ自動車'
                },
                'expected_symbol': '7203',
                'expected_name': 'トヨタ自動車',
                'test_name': '楽天証券形式'
            },
            # 引用符付き
            {
                'data': {
                    'symbol': '"9432"',
                    'name': 'NTT'
                },
                'expected_symbol': '9432',
                'expected_name': 'NTT',
                'test_name': '引用符付き'
            },
            # 銘柄名なし
            {
                'data': {
                    '銘柄コード': '8316'
                },
                'expected_symbol': '8316',
                'expected_name': '',
                'test_name': '銘柄名なし'
            },
            # 無効なデータ
            {
                'data': {
                    'other_field': 'value'
                },
                'expected_symbol': None,
                'expected_name': '',
                'test_name': '銘柄コードなし'
            },
        ]
        
        all_passed = True
        for case in test_cases:
            symbol, name = self.SymbolNormalizer.extract_symbols_from_csv_row(case['data'])
            
            symbol_ok = symbol == case['expected_symbol']
            name_ok = name == case['expected_name']
            
            if symbol_ok and name_ok:
                print(f"✅ {case['test_name']}: {symbol}, {name}")
            else:
                print(f"❌ {case['test_name']}: {symbol}, {name} (期待値: {case['expected_symbol']}, {case['expected_name']})")
                all_passed = False
        
        return all_passed
    
    def test_decimal_formatting(self):
        """小数点フォーマットテスト"""
        print("\n=== 小数点フォーマットテスト ===")
        
        formatter = self.DecimalFormatter()
        
        # 価格フォーマットテスト
        price_tests = [
            (2100.0, 2100.0, '整数価格'),
            (2100.123, 2100.1, '小数点価格（1桁丸め）'),
            (2100.167, 2100.2, '小数点価格（繰り上げ）'),
            (None, None, 'None値'),
        ]
        
        all_passed = True
        print("📊 価格フォーマットテスト:")
        for input_value, expected, test_name in price_tests:
            result = formatter.format_price(input_value)
            if result == expected:
                print(f"✅ {test_name}: {input_value} → {result}")
            else:
                print(f"❌ {test_name}: {input_value} → {result} (期待値: {expected})")
                all_passed = False
        
        # パーセンテージフォーマットテスト
        percentage_tests = [
            (4.76, 4.8, '通常パーセンテージ'),
            (167.98, 167.9, '高パーセンテージ'),
            (0.1234, 0.1, '小パーセンテージ'),
            (None, None, 'None値'),
        ]
        
        print("\n📈 パーセンテージフォーマットテスト:")
        for input_value, expected, test_name in percentage_tests:
            result = formatter.format_percentage(input_value)
            if result == expected:
                print(f"✅ {test_name}: {input_value}% → {result}%")
            else:
                print(f"❌ {test_name}: {input_value}% → {result}% (期待値: {expected}%)")
                all_passed = False
        
        return all_passed
    
    def test_performance_and_stress(self):
        """パフォーマンス・ストレステスト"""
        print("\n=== パフォーマンス・ストレステスト ===")
        
        import time
        
        # 大量データでの正規化パフォーマンステスト
        test_symbols = ['9432.T', '"1928"', '  7203  ', '8316 名前'] * 1000  # 4000件
        
        start_time = time.time()
        success_count = 0
        
        for symbol in test_symbols:
            result = self.SymbolNormalizer.normalize(symbol)
            if result:
                success_count += 1
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        if processing_time < 1.0 and success_count == 4000:
            print(f"✅ パフォーマンステスト成功: {len(test_symbols)}件を{processing_time:.3f}秒で処理")
            print(f"   成功率: {success_count/len(test_symbols)*100:.1f}%")
        else:
            print(f"❌ パフォーマンステスト失敗: {processing_time:.3f}秒, 成功{success_count}件")
            return False
        
        # メモリ効率テスト（同じ結果が返されることを確認）
        test_symbol = '9432.T'
        results = [self.SymbolNormalizer.normalize(test_symbol) for _ in range(1000)]
        
        if all(result == '9432' for result in results):
            print("✅ メモリ効率テスト成功: 一貫した結果")
        else:
            print("❌ メモリ効率テスト失敗: 結果が一貫していない")
            return False
        
        return True
    
    def test_convenience_functions(self):
        """便利関数テスト"""
        print("\n=== 便利関数テスト ===")
        
        try:
            from core.symbol_utils import normalize_symbol, to_yahoo_symbol, format_decimal
            
            # 便利関数の動作確認
            test_cases = [
                (normalize_symbol('9432.T'), '9432', 'normalize_symbol'),
                (to_yahoo_symbol('9432'), '9432.T', 'to_yahoo_symbol'),
                (format_decimal(123.456), 123.5, 'format_decimal'),
            ]
            
            all_passed = True
            for result, expected, func_name in test_cases:
                if result == expected:
                    print(f"✅ {func_name}: {result}")
                else:
                    print(f"❌ {func_name}: {result} (期待値: {expected})")
                    all_passed = False
            
            return all_passed
            
        except ImportError as e:
            print(f"❌ 便利関数インポートエラー: {e}")
            return False
    
    def run_all_tests(self):
        """全テスト実行"""
        print("🧪 SymbolUtils包括的テスト開始")
        print("=" * 50)
        
        test_methods = [
            ("基本的な銘柄コード正規化", self.test_symbol_normalization_basic),
            ("エッジケースの正規化", self.test_symbol_normalization_edge_cases),
            ("Yahoo Finance形式変換", self.test_yahoo_format_conversion),
            ("日本株銘柄コード検証", self.test_japanese_stock_validation),
            ("CSV行からの銘柄抽出", self.test_csv_row_extraction),
            ("小数点フォーマット", self.test_decimal_formatting),
            ("パフォーマンス・ストレス", self.test_performance_and_stress),
            ("便利関数", self.test_convenience_functions),
        ]
        
        results = []
        for test_name, test_method in test_methods:
            try:
                result = test_method()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} テスト実行エラー: {e}")
                results.append((test_name, False))
        
        # 結果サマリー
        print("\n" + "=" * 50)
        print("📊 SymbolUtils包括的テスト結果サマリー")
        print("=" * 50)
        
        passed = 0
        failed = 0
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print(f"\n合計: {passed + failed}テスト")
        print(f"成功: {passed}")
        print(f"失敗: {failed}")
        
        return failed == 0


def main():
    """メイン関数"""
    try:
        tester = TestSymbolUtils()
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ テスト初期化エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()