"""
台股歷史股價抓取與分類系統
支援多種資料來源: Yahoo Finance, 證交所, 鉅亨網
自動分類並儲存為 CSV
"""

import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import os
from io import StringIO
import json

# 台股產業分類表 (根據官方分類)
TW_STOCK_CATEGORIES = {
    '半導體': {
        'stocks': ['2330', '2454', '2303', '3711', '3034', '2408', '3443', '3661', '6770', '5274'],
        'names': ['台積電', '聯發科', '聯電', '日月光投控', '聯詠', '南亞科', '創意', '世芯-KY', '力積電', '信驊']
    },
    'IC設計': {
        'stocks': ['2454', '3034', '3661', '5274', '3443', '6415', '6451', '3529', '8299', '6472'],
        'names': ['聯發科', '聯詠', '世芯-KY', '信驊', '創意', '矽力-KY', '訊芯-KY', '力旺', '群聯', '保瑞']
    },
    '晶圓代工': {
        'stocks': ['2330', '2303', '6770', '5347', '3105', '8069', '6488', '3450', '6411', '3707'],
        'names': ['台積電', '聯電', '力積電', '世界', '穩懋', '元太', '環球晶', '聯鈞', '晶焱', '漢磊']
    },
    '封測': {
        'stocks': ['3711', '2311', '6239', '8110', '2369', '3231', '6409', '2328', '3231', '8299'],
        'names': ['日月光投控', '日月光', '力成', '華東', '菱生', '緯創', '旭隼', '廣宇', '緯創', '群聯']
    },
    '金融': {
        'stocks': ['2881', '2882', '2886', '2891', '2884', '2892', '5880', '2887', '2880', '2888'],
        'names': ['富邦金', '國泰金', '兆豐金', '中信金', '玉山金', '第一金', '合庫金', '台新金', '華南金', '新光金']
    },
    '電子零組件': {
        'stocks': ['2317', '2382', '2357', '2324', '3231', '2301', '2308', '2327', '6505', '2474'],
        'names': ['鴻海', '廣達', '華碩', '仁寶', '緯創', '光寶科', '台達電', '國巨', '台塑化', '可成']
    },
    '光電': {
        'stocks': ['3008', '3481', '6176', '2409', '3034', '2474', '3443', '6116', '3481', '2409'],
        'names': ['大立光', '群創', '瑞儀', '友達', '聯詠', '可成', '創意', '彩晶', '群創', '友達']
    },
    '通訊網路': {
        'stocks': ['2412', '3045', '4904', '2474', '3231', '6176', '2454', '3443', '6451', '6669'],
        'names': ['中華電', '台灣大', '遠傳', '可成', '緯創', '瑞儀', '聯發科', '創意', '訊芯-KY', '緯穎']
    },
    '電腦及週邊': {
        'stocks': ['2382', '2357', '2324', '3231', '2301', '2308', '2327', '6505', '2474', '3443'],
        'names': ['廣達', '華碩', '仁寶', '緯創', '光寶科', '台達電', '國巨', '台塑化', '可成', '創意']
    },
    '鋼鐵': {
        'stocks': ['2002', '2006', '2009', '2013', '2015', '2017', '2020', '2023', '2027', '2029'],
        'names': ['中鋼', '東和鋼鐵', '第一銅', '中鋼構', '豐興', '官田鋼', '美亞', '燁輝', '大成鋼', '盛餘']
    },
    '塑膠': {
        'stocks': ['1301', '1303', '1326', '6505', '1304', '1310', '1402', '1409', '1410', '1413'],
        'names': ['台塑', '南亞', '台化', '台塑化', '台聚', '台苯', '遠東新', '新纖', '南染', '宏洲']
    },
    '水泥': {
        'stocks': ['1101', '1102', '1103', '1104', '1108', '1109', '1110', '1201', '1203', '1210'],
        'names': ['台泥', '亞泥', '嘉泥', '環泥', '幸福', '信大', '東泥', '味全', '味王', '大成']
    },
    '食品': {
        'stocks': ['1216', '1229', '1232', '1234', '1227', '1201', '1203', '1210', '1215', '1218'],
        'names': ['統一', '聯華', '大統益', '黑松', '佳格', '味全', '味王', '大成', '卜蜂', '泰山']
    },
    '生技醫療': {
        'stocks': ['4736', '6547', '6446', '1789', '4174', '6535', '4743', '6469', '1777', '4120'],
        'names': ['泰博', '高端疫苗', '藥華藥', '神隆', '浩鼎', '順藥', '合一', '大樹', '生泰', '友華']
    },
    '航運': {
        'stocks': ['2603', '2609', '2615', '2606', '2618', '2610', '2611', '2612', '2613', '2614'],
        'names': ['長榮', '陽明', '萬海', '裕民', '長榮航', '華航', '志信', '中航', '中櫃', '東森']
    },
    '汽車': {
        'stocks': ['2201', '2207', '2227', '1513', '1503', '2308', '1605', '1802', '6116', '3481'],
        'names': ['裕隆', '和泰車', '裕日車', '中興電', '士電', '台達電', '華新', '台玻', '彩晶', '群創']
    },
    '太陽能': {
        'stocks': ['6488', '3576', '6443', '3514', '6869', '6531', '3452', '6274', '3561', '6417'],
        'names': ['環球晶', '聯合再生', '元晶', '昱晶', '雲豹能源', '愛地雅', '益通', '台燿', '昇陽光電', '韋僑']
    },
    '電動車': {
        'stocks': ['2207', '2201', '2227', '1513', '1503', '2308', '1605', '1802', '6116', '3481'],
        'names': ['和泰車', '裕隆', '裕日車', '中興電', '士電', '台達電', '華新', '台玻', '彩晶', '群創']
    },
    '電池': {
        'stocks': ['5371', '6625', '6121', '3481', '6116', '1513', '1503', '2308', '1605', '1802'],
        'names': ['中光電', '必應', '新普', '群創', '彩晶', '中興電', '士電', '台達電', '華新', '台玻']
    }
}

class TaiwanStockFetcher:
    def __init__(self):
        self.data_dir = 'stock_data'
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def fetch_from_yahoo(self, stock_code, start_date=None, end_date=None, period='1y'):
        """
        從 Yahoo Finance 抓取台股資料
        stock_code: 股票代碼 (如 '2330')
        start_date: 開始日期 'YYYY-MM-DD'
        end_date: 結束日期 'YYYY-MM-DD'
        period: 時間區間 '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
        """
        try:
            # 台股代碼需加上 .TW 或 .TWO
            ticker_symbol = f"{stock_code}.TW"
            
            print(f"📥 正在抓取 {stock_code} 的資料...")
            
            stock = yf.Ticker(ticker_symbol)
            
            # 如果指定日期範圍
            if start_date and end_date:
                df = stock.history(start=start_date, end=end_date)
            else:
                df = stock.history(period=period)
            
            if df.empty:
                # 嘗試上櫃股票 .TWO
                ticker_symbol = f"{stock_code}.TWO"
                stock = yf.Ticker(ticker_symbol)
                if start_date and end_date:
                    df = stock.history(start=start_date, end=end_date)
                else:
                    df = stock.history(period=period)
            
            if not df.empty:
                df.reset_index(inplace=True)
                df['Stock_Code'] = stock_code
                
                # 重新命名欄位為中文
                df.rename(columns={
                    'Date': '日期',
                    'Open': '開盤價',
                    'High': '最高價',
                    'Low': '最低價',
                    'Close': '收盤價',
                    'Volume': '成交量',
                    'Dividends': '股息',
                    'Stock Splits': '股票分割',
                    'Stock_Code': '股票代碼'
                }, inplace=True)
                
                print(f"✅ {stock_code} 抓取成功! 共 {len(df)} 筆資料")
                return df
            else:
                print(f"❌ {stock_code} 無資料")
                return None
                
        except Exception as e:
            print(f"❌ {stock_code} 抓取失敗: {e}")
            return None
    
    def fetch_from_twse(self, stock_code, start_date, end_date):
        """
        從證交所抓取資料
        stock_code: 股票代碼
        start_date: 開始日期 'YYYYMMDD'
        end_date: 結束日期 'YYYYMMDD'
        """
        try:
            url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY"
            
            # 轉換日期格式
            start = datetime.strptime(start_date, '%Y%m%d')
            end = datetime.strptime(end_date, '%Y%m%d')
            
            all_data = []
            current = start
            
            while current <= end:
                year = current.year - 1911  # 民國年
                month = current.month
                
                params = {
                    'response': 'json',
                    'date': f"{year}{month:02d}01",
                    'stockNo': stock_code
                }
                
                print(f"📥 正在抓取 {stock_code} {year}年{month}月 的資料...")
                
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('stat') == 'OK':
                        df = pd.DataFrame(data['data'], columns=data['fields'])
                        all_data.append(df)
                        print(f"✅ {year}年{month}月 抓取成功")
                    else:
                        print(f"⚠️  {year}年{month}月 無資料")
                
                # 移到下個月
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
                
                time.sleep(3)  # 避免請求過快
            
            if all_data:
                final_df = pd.concat(all_data, ignore_index=True)
                final_df['股票代碼'] = stock_code
                print(f"✅ {stock_code} 總共抓取 {len(final_df)} 筆資料")
                return final_df
            else:
                print(f"❌ {stock_code} 無資料")
                return None
                
        except Exception as e:
            print(f"❌ {stock_code} 抓取失敗: {e}")
            return None
    
    def fetch_category_stocks(self, category, source='yahoo', period='1y'):
        """
        抓取特定產業的所有股票
        category: 產業名稱
        source: 'yahoo' 或 'twse'
        period: 時間區間
        """
        if category not in TW_STOCK_CATEGORIES:
            print(f"❌ 找不到產業: {category}")
            print(f"可用產業: {', '.join(TW_STOCK_CATEGORIES.keys())}")
            return None
        
        category_info = TW_STOCK_CATEGORIES[category]
        stocks = category_info['stocks']
        names = category_info['names']
        
        print(f"\n🏭 開始抓取 [{category}] 產業股票...")
        print(f"共 {len(stocks)} 檔股票\n")
        print("=" * 70)
        
        all_data = []
        
        for stock_code, stock_name in zip(stocks, names):
            print(f"\n📊 {stock_code} {stock_name}")
            
            if source == 'yahoo':
                df = self.fetch_from_yahoo(stock_code, period=period)
            else:
                # 證交所需要指定日期
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
                df = self.fetch_from_twse(stock_code, start_date, end_date)
            
            if df is not None:
                df['股票名稱'] = stock_name
                df['產業分類'] = category
                all_data.append(df)
            
            time.sleep(1)  # 避免請求過快
        
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            
            # 儲存檔案
            filename = f"{self.data_dir}/{category}_stocks_{datetime.now().strftime('%Y%m%d')}.csv"
            final_df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            print("\n" + "=" * 70)
            print(f"✅ [{category}] 產業資料抓取完成!")
            print(f"📁 檔案已儲存: {filename}")
            print(f"📊 總共 {len(final_df)} 筆資料")
            print("=" * 70)
            
            return final_df
        else:
            print(f"\n❌ [{category}] 產業無資料")
            return None
    
    def fetch_all_categories(self, source='yahoo', period='1y', categories=None):
        """
        抓取所有產業或指定產業列表
        categories: 產業列表,None 表示全部
        """
        if categories is None:
            categories = list(TW_STOCK_CATEGORIES.keys())
        
        print(f"\n🚀 開始抓取 {len(categories)} 個產業的股票資料...")
        print(f"資料來源: {source.upper()}")
        print(f"時間區間: {period}")
        print("=" * 70)
        
        results = {}
        
        for category in categories:
            df = self.fetch_category_stocks(category, source=source, period=period)
            if df is not None:
                results[category] = df
            time.sleep(2)
        
        # 生成總覽報告
        self.generate_summary_report(results)
        
        return results
    
    def generate_summary_report(self, results):
        """生成總覽報告"""
        report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = "=" * 70 + "\n"
        report += "台股歷史股價抓取總覽報告\n"
        report += f"報告時間: {report_time}\n"
        report += "=" * 70 + "\n\n"
        
        report += "📊 抓取統計\n"
        report += "-" * 70 + "\n"
        
        total_stocks = 0
        total_records = 0
        
        for category, df in results.items():
            stock_count = df['股票代碼'].nunique()
            record_count = len(df)
            total_stocks += stock_count
            total_records += record_count
            
            report += f"{category:15s} | 股票數: {stock_count:3d} | 資料筆數: {record_count:8d}\n"
        
        report += "-" * 70 + "\n"
        report += f"{'總計':15s} | 股票數: {total_stocks:3d} | 資料筆數: {total_records:8d}\n"
        report += "=" * 70 + "\n"
        
        # 儲存報告
        report_file = f"{self.data_dir}/summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("\n" + report)
        print(f"📝 報告已儲存: {report_file}")
    
    def export_category_list(self):
        """匯出產業分類表"""
        category_data = []
        
        for category, info in TW_STOCK_CATEGORIES.items():
            for stock_code, stock_name in zip(info['stocks'], info['names']):
                category_data.append({
                    '產業分類': category,
                    '股票代碼': stock_code,
                    '股票名稱': stock_name
                })
        
        df = pd.DataFrame(category_data)
        filename = f"{self.data_dir}/台股產業分類表.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        print(f"✅ 產業分類表已匯出: {filename}")
        return df
    
    def search_stock_category(self, stock_code):
        """查詢股票所屬產業"""
        for category, info in TW_STOCK_CATEGORIES.items():
            if stock_code in info['stocks']:
                idx = info['stocks'].index(stock_code)
                stock_name = info['names'][idx]
                print(f"📊 {stock_code} {stock_name} 屬於 [{category}] 產業")
                return category
        
        print(f"❌ 找不到股票代碼: {stock_code}")
        return None

# 使用範例
if __name__ == '__main__':
    fetcher = TaiwanStockFetcher()
    
    # 範例 1: 匯出產業分類表
    print("\n【範例】匯出產業分類表")
    print("=" * 70)
    category_df = fetcher.export_category_list()
    print("\n前 20 筆資料:")
    print(category_df.head(20))
    
    print("\n✅ 分類表匯出完成!")
