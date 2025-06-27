#!/usr/bin/env python3
"""
Yahoo Finance API データ分析スクリプト
"""
import json

# Yahoo Finance APIで取得可能な全フィールド（ドキュメントベース）
YAHOO_FINANCE_FIELDS = {
    "基本情報": {
        "symbol": "銘柄コード",
        "longName": "企業名（長）",
        "shortName": "企業名（短）",
        "currency": "通貨",
        "exchange": "取引所",
        "quoteType": "証券タイプ",
        "marketState": "市場状態",
        "gmtOffSetMilliseconds": "GMTオフセット",
        "uuid": "UUID",
        "messageBoardId": "メッセージボードID",
        "market": "市場"
    },
    
    "株価データ": {
        "currentPrice": "現在価格",
        "regularMarketPrice": "通常市場価格",
        "previousClose": "前日終値",
        "open": "始値",
        "dayLow": "日中安値",
        "dayHigh": "日中高値",
        "regularMarketDayLow": "通常市場日中安値",
        "regularMarketDayHigh": "通常市場日中高値",
        "fiftyTwoWeekLow": "52週安値",
        "fiftyTwoWeekHigh": "52週高値",
        "fiftyDayAverage": "50日移動平均",
        "twoHundredDayAverage": "200日移動平均",
        "bid": "買い気配",
        "ask": "売り気配",
        "bidSize": "買い気配数量",
        "askSize": "売り気配数量"
    },
    
    "出来高データ": {
        "volume": "出来高",
        "regularMarketVolume": "通常市場出来高",
        "averageVolume": "平均出来高",
        "averageVolume10days": "10日間平均出来高",
        "averageDailyVolume10Day": "10日間平均日次出来高",
        "sharesShort": "空売り株数",
        "sharesShortPriorMonth": "前月空売り株数",
        "shortRatio": "空売り比率",
        "shortPercentOfFloat": "浮動株に対する空売り比率"
    },
    
    "時価総額・企業価値": {
        "marketCap": "時価総額",
        "enterpriseValue": "企業価値",
        "sharesOutstanding": "発行済株式数",
        "floatShares": "浮動株式数",
        "impliedSharesOutstanding": "推定発行済株式数"
    },
    
    "財務指標（バリュエーション）": {
        "trailingPE": "実績PER",
        "forwardPE": "予想PER",
        "priceToBook": "PBR（株価純資産倍率）",
        "priceToSalesTrailing12Months": "PSR（株価売上高倍率）",
        "enterpriseToRevenue": "EV/売上高",
        "enterpriseToEbitda": "EV/EBITDA",
        "pegRatio": "PEGレシオ"
    },
    
    "配当データ": {
        "dividendYield": "配当利回り",
        "dividendRate": "年間配当額",
        "exDividendDate": "配当落ち日",
        "payoutRatio": "配当性向",
        "fiveYearAvgDividendYield": "5年平均配当利回り",
        "trailingAnnualDividendYield": "実績年間配当利回り",
        "trailingAnnualDividendRate": "実績年間配当額",
        "lastDividendValue": "直近配当額",
        "lastDividendDate": "直近配当日"
    },
    
    "収益性指標": {
        "returnOnEquity": "ROE（自己資本利益率）",
        "returnOnAssets": "ROA（総資産利益率）",
        "profitMargins": "純利益率",
        "operatingMargins": "営業利益率",
        "grossMargins": "売上総利益率",
        "ebitdaMargins": "EBITDAマージン"
    },
    
    "成長性指標": {
        "earningsGrowth": "利益成長率",
        "revenueGrowth": "売上成長率",
        "earningsQuarterlyGrowth": "四半期利益成長率",
        "revenueQuarterlyGrowth": "四半期売上成長率"
    },
    
    "財務健全性": {
        "debtToEquity": "負債自己資本比率",
        "quickRatio": "当座比率",
        "currentRatio": "流動比率",
        "totalCash": "現金総額",
        "totalCashPerShare": "1株当たり現金",
        "totalDebt": "総負債",
        "totalRevenue": "総売上高",
        "revenuePerShare": "1株当たり売上高",
        "ebitda": "EBITDA",
        "freeCashflow": "フリーキャッシュフロー",
        "operatingCashflow": "営業キャッシュフロー"
    },
    
    "1株当たりデータ": {
        "bookValue": "1株当たり純資産",
        "earningsPerShare": "EPS（1株当たり利益）",
        "revenue": "売上高",
        "totalCashPerShare": "1株当たり現金",
        "netIncomeToCommon": "普通株主に帰属する純利益"
    },
    
    "企業情報": {
        "sector": "セクター",
        "industry": "業界",
        "fullTimeEmployees": "正社員数",
        "companyOfficers": "役員情報",
        "website": "ウェブサイト",
        "address1": "住所1",
        "address2": "住所2",
        "city": "市区町村",
        "state": "都道府県",
        "zip": "郵便番号",
        "country": "国",
        "phone": "電話番号",
        "fax": "FAX番号",
        "longBusinessSummary": "事業概要"
    },
    
    "アナリスト情報": {
        "recommendationKey": "推奨評価",
        "recommendationMean": "推奨評価平均",
        "numberOfAnalystOpinions": "アナリスト数",
        "targetHighPrice": "目標株価上限",
        "targetLowPrice": "目標株価下限",
        "targetMeanPrice": "目標株価平均",
        "targetMedianPrice": "目標株価中央値"
    },
    
    "その他の技術的指標": {
        "beta": "ベータ値",
        "beta3Year": "3年ベータ値",
        "morningStarRiskRating": "モーニングスターリスク評価",
        "priceHint": "価格ヒント",
        "maxAge": "データ年齢"
    }
}

# 取得可能な履歴データタイプ
HISTORICAL_DATA_TYPES = {
    "price_history": {
        "method": "ticker.history()",
        "fields": ["Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"],
        "periods": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
        "intervals": ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
    },
    
    "dividends": {
        "method": "ticker.dividends",
        "description": "配当履歴データ",
        "returns": "pandas.Series with dates and dividend amounts"
    },
    
    "splits": {
        "method": "ticker.splits",
        "description": "株式分割履歴",
        "returns": "pandas.Series with dates and split ratios"
    },
    
    "actions": {
        "method": "ticker.actions",
        "description": "配当と株式分割の履歴",
        "returns": "pandas.DataFrame with dividends and stock splits"
    },
    
    "financials": {
        "method": "ticker.financials",
        "description": "年次財務諸表",
        "returns": "pandas.DataFrame with income statement data"
    },
    
    "quarterly_financials": {
        "method": "ticker.quarterly_financials",
        "description": "四半期財務諸表",
        "returns": "pandas.DataFrame with quarterly income statement data"
    },
    
    "balance_sheet": {
        "method": "ticker.balance_sheet",
        "description": "年次貸借対照表",
        "returns": "pandas.DataFrame with balance sheet data"
    },
    
    "quarterly_balance_sheet": {
        "method": "ticker.quarterly_balance_sheet",
        "description": "四半期貸借対照表",
        "returns": "pandas.DataFrame with quarterly balance sheet data"
    },
    
    "cashflow": {
        "method": "ticker.cashflow",
        "description": "年次キャッシュフロー計算書",
        "returns": "pandas.DataFrame with cash flow data"
    },
    
    "quarterly_cashflow": {
        "method": "ticker.quarterly_cashflow",
        "description": "四半期キャッシュフロー計算書",
        "returns": "pandas.DataFrame with quarterly cash flow data"
    },
    
    "recommendations": {
        "method": "ticker.recommendations",
        "description": "アナリスト推奨履歴",
        "returns": "pandas.DataFrame with analyst recommendations"
    },
    
    "institutional_holders": {
        "method": "ticker.institutional_holders",
        "description": "機関投資家保有情報",
        "returns": "pandas.DataFrame with institutional ownership data"
    },
    
    "major_holders": {
        "method": "ticker.major_holders",
        "description": "主要株主情報",
        "returns": "pandas.DataFrame with major shareholders data"
    }
}

# 分析結果を出力
print("=== Yahoo Finance API 完全データ分析 ===\n")

print("1. ticker.info で取得可能なフィールド数:")
total_fields = sum(len(fields) for fields in YAHOO_FINANCE_FIELDS.values())
print(f"   合計: {total_fields} フィールド\n")

print("2. カテゴリ別フィールド詳細:")
for category, fields in YAHOO_FINANCE_FIELDS.items():
    print(f"\n   【{category}】 ({len(fields)}項目)")
    for field, description in fields.items():
        print(f"      - {field}: {description}")

print("\n3. 取得可能な履歴データタイプ:")
for data_type, info in HISTORICAL_DATA_TYPES.items():
    print(f"\n   【{data_type}】")
    print(f"      メソッド: {info['method']}")
    if 'description' in info:
        print(f"      説明: {info['description']}")
    if 'fields' in info:
        print(f"      フィールド: {', '.join(info['fields'])}")
    if 'periods' in info:
        print(f"      期間: {', '.join(info['periods'])}")
    if 'returns' in info:
        print(f"      戻り値: {info['returns']}")

print("\n=== 分析完了 ===")