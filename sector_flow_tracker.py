"""
美股板塊資金流向 -> 台股族群對應系統 (優化版)
基於真實美股市場板塊分類,每日自動追蹤並對應到台股
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime, timedelta
import yfinance as yf
import os
import logging
from functools import wraps
import time

# Logging setup
os.makedirs('logs', exist_ok=True)
logger = logging.getLogger('sector_flow_tracker')
logger.setLevel(logging.INFO)
fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
fh = logging.FileHandler('logs/tracker.log', encoding='utf-8')
fh.setFormatter(fmt)
ch = logging.StreamHandler()
"""
美股板塊資金流向 -> 台股族群對應系統 (完整台股分類版)
基於台股官方產業分類,支援即時資料更新
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime, timedelta
import yfinance as yf
import os
import time
import pytz

# 美股核心板塊 ETF (11大板塊)
US_SECTOR_ETFS = {
    'XLK': '科技 Technology',
    'XLF': '金融 Financials', 
    'XLV': '醫療保健 Healthcare',
    'XLE': '能源 Energy',
    'XLI': '工業 Industrials',
    'XLP': '必需消費 Consumer Staples',
    'XLY': '非必需消費 Consumer Discretionary',
    'XLB': '原物料 Materials',
    'XLRE': '房地產 Real Estate',
    'XLU': '公用事業 Utilities',
    'XLC': '通訊服務 Communication Services'
}

# 細分板塊追蹤 (熱門主題 - 與官方台股分類對應)
US_THEME_ETFS = {
    'TAN': '太陽能 Solar Energy',
    'SOXX': '半導體 Semiconductors',
    'CLOU': '雲端運算 Cloud Computing',
    'CARZ': '電動車 EV',
    'LIT': '鋰電池 Lithium Battery'
}

# 美股板塊 -> 台股族群對應 (根據台股官方分類)
SECTOR_MAPPING = {
    'XLK': {
        'name': '科技',
        'tw_sectors': ['半導體', 'IC設計', '晶圓代工', '電腦及週邊', '光電', '通訊網路'],
        'tw_stocks': [
            '2330 台積電', '2454 聯發科', '2303 聯電', '3711 日月光投控', '3034 聯詠',
            '2408 南亞科', '2382 廣達', '2357 華碩', '3008 大立光', '6669 緯穎'
        ],
        'related_themes': ['SOXX', 'IGV', 'CLOU'],
        'industry_detail': 'IC設計、晶圓代工、封測、電腦製造、網通設備'
    },
    
    'XLF': {
        'name': '金融',
        'tw_sectors': ['金融'],
        'tw_stocks': [
            '2881 富邦金', '2882 國泰金', '2886 兆豐金', '2891 中信金', '2884 玉山金',
            '2892 第一金', '5880 合庫金', '2887 台新金', '2880 華南金', '2888 新光金'
        ],
        'related_themes': ['FINX'],
        'industry_detail': '金控、銀行、證券、保險經紀、資產管理'
    },
    
    'XLV': {
        'name': '醫療保健',
        'tw_sectors': ['生技醫療'],
        'tw_stocks': [
            '4736 泰博', '6547 高端疫苗', '6446 藥華藥', '1789 神隆', '4174 浩鼎',
            '6535 順藥', '4743 合一', '6469 大樹', '1777 生泰', '4120 友華'
        ],
        'related_themes': ['IHI'],
        'industry_detail': '西藥製劑、生技醫療、醫療器材、診斷設備、醫療服務'
    },
    
    'XLE': {
        'name': '能源',
        'tw_sectors': ['太陽能'],
        'tw_stocks': [
            '6488 環球晶', '3576 聯合再生', '6443 元晶', '3514 昱晶', '6869 雲豹能源',
            '6531 愛地雅', '3452 益通', '6274 台燿', '3561 昇陽光電', '6417 韋僑'
        ],
        'related_themes': ['TAN'],
        'industry_detail': '太陽能電池、太陽能模組、太陽能系統、綠能設備'
    },
    
    'XLI': {
        'name': '工業',
        'tw_sectors': ['航運'],
        'tw_stocks': [
            '2603 長榮', '2609 陽明', '2615 萬海', '2606 裕民', '2618 長榮航',
            '2610 華航', '2611 志信', '2612 中航', '2613 中櫃', '2614 東森'
        ],
        'related_themes': ['BOTZ'],
        'industry_detail': '海運、航空、運輸物流'
    },
    
    'XLP': {
        'name': '必需消費',
        'tw_sectors': ['食品'],
        'tw_stocks': [
            '1216 統一', '1229 聯華', '1232 大統益', '1234 黑松', '1227 佳格',
            '1201 味全', '1203 味王', '1210 大成', '1215 卜蜂', '1218 泰山'
        ],
        'related_themes': [],
        'industry_detail': '食品製造、飲品'
    },
    
    'XLY': {
        'name': '非必需消費',
        'tw_sectors': ['汽車', '電動車'],
        'tw_stocks': [
            '2201 裕隆', '2207 和泰車', '2227 裕日車', '1513 中興電', '1503 士電',
            '2308 台達電', '1605 華新', '1802 台玻', '6116 彩晶', '3481 群創'
        ],
        'related_themes': ['XRT', 'CARZ'],
        'industry_detail': '汽車製造、電動車'
    },
    
    'XLB': {
        'name': '原物料',
        'tw_sectors': ['鋼鐵', '塑膠', '水泥'],
        'tw_stocks': [
            '2002 中鋼', '2006 東和鋼鐵', '1301 台塑', '1303 南亞', '1326 台化',
            '1101 台泥', '1102 亞泥', '1304 台聚', '1310 台苯', '1402 遠東新'
        ],
        'related_themes': [],
        'industry_detail': '鋼鐵、化學原料、塑化、水泥'
    },
    
    'XLRE': {
        'name': '房地產',
        'tw_sectors': [],
        'tw_stocks': [],
        'related_themes': [],
        'industry_detail': '無直接對應台股產業'
    },
    
    'XLU': {
        'name': '公用事業',
        'tw_sectors': [],
        'tw_stocks': [],
        'related_themes': [],
        'industry_detail': '無直接對應台股產業'
    },
    
    'XLC': {
        'name': '通訊服務',
        'tw_sectors': ['通訊網路'],
        'tw_stocks': [
            '2412 中華電', '3045 台灣大', '4904 遠傳', '2454 聯發科', '3443 創意',
            '6451 訊芯-KY', '6669 緯穎', '2474 可成', '3231 緯創', '6176 瑞儀'
        ],
        'related_themes': [],
        'industry_detail': '電信服務、網路服務'
    },
    
    # 主題 ETF 對應
    'TAN': {
        'name': '太陽能',
        'tw_sectors': ['太陽能', '綠能', '太陽能電池', '太陽能系統運用', 'PV INVERTER'],
        'tw_stocks': [
            '6488 環球晶', '3576 聯合再生', '6443 元晶', '3514 昱晶', '6869 雲豹能源',
            '6531 愛地雅', '3452 益通', '6274 台燿', '3561 昇陽光電', '6417 韋僑'
        ],
        'related_themes': [],
        'industry_detail': '太陽能電池、太陽能模組、太陽能系統、綠能設備'
    },
    
    'SOXX': {
        'name': '半導體',
        'tw_sectors': ['半導體', 'IC設計', '晶圓代工'],
        'tw_stocks': [
            '2330 台積電', '2454 聯發科', '2303 聯電', '3711 日月光投控', '3034 聯詠',
            '2408 南亞科', '6770 力積電', '3443 創意', '3661 世芯-KY', '5274 信驊'
        ],
        'related_themes': [],
        'industry_detail': 'IC設計、晶圓代工、封裝測試'
    },
    
    'TAN': {
        'name': '太陽能',
        'tw_sectors': ['太陽能'],
        'tw_stocks': [
            '6488 環球晶', '3576 聯合再生', '6443 元晶', '3514 昱晶', '6869 雲豹能源',
            '6531 愛地雅', '3452 益通', '6274 台燿', '3561 昇陽光電', '6417 韋僑'
        ],
        'related_themes': [],
        'industry_detail': '太陽能電池、太陽能模組、太陽能系統'
    },
    
    'CLOU': {
        'name': '雲端運算',
        'tw_sectors': ['電子零組件', '通訊網路'],
        'tw_stocks': [
            '2317 鴻海', '2382 廣達', '2357 華碩', '2324 仁寶', '3231 緯創',
            '2301 光寶科', '2308 台達電', '6669 緯穎', '6451 訊芯-KY', '6561 是方'
        ],
        'related_themes': [],
        'industry_detail': '雲端伺服器、電腦製造、網通設備'
    },
    
    'CARZ': {
        'name': '電動車',
        'tw_sectors': ['汽車', '電動車'],
        'tw_stocks': [
            '2201 裕隆', '2207 和泰車', '2227 裕日車', '1513 中興電', '1503 士電',
            '2308 台達電', '1605 華新', '1802 台玻', '6116 彩晶', '3481 群創'
        ],
        'related_themes': [],
        'industry_detail': '電動車製造、車用電子'
    },
    
    'LIT': {
        'name': '鋰電池',
        'tw_sectors': ['電池'],
        'tw_stocks': [
            '5371 中光電', '6625 必應', '6121 新普', '3481 群創', '6116 彩晶',
            '1513 中興電', '1503 士電', '2308 台達電', '1605 華新', '1802 台玻'
        ],
        'related_themes': [],
        'industry_detail': '鋰電池、電池材料、儲能系統'
    }
}

class SectorFlowTracker:
    def __init__(self, include_themes=True, realtime=True):
        self.results = []
        self.include_themes = include_themes
        self.realtime = realtime
        self.us_tz = pytz.timezone('America/New_York')
        self.tw_tz = pytz.timezone('Asia/Taipei')
        
    def get_current_time_info(self):
        """獲取當前時間資訊"""
        now_utc = datetime.now(pytz.UTC)
        now_us = now_utc.astimezone(self.us_tz)
        now_tw = now_utc.astimezone(self.tw_tz)
        
        us_market_open = now_us.replace(hour=9, minute=30, second=0, microsecond=0)
        us_market_close = now_us.replace(hour=16, minute=0, second=0, microsecond=0)
        us_premarket_open = now_us.replace(hour=4, minute=0, second=0, microsecond=0)
        us_afterhours_close = now_us.replace(hour=20, minute=0, second=0, microsecond=0)
        
        if us_premarket_open <= now_us < us_market_open:
            market_status = '盤前交易'
            status_emoji = '🌅'
        elif us_market_open <= now_us < us_market_close:
            market_status = '盤中交易'
            status_emoji = '🔴'
        elif us_market_close <= now_us < us_afterhours_close:
            market_status = '盤後交易'
            status_emoji = '🌆'
        else:
            market_status = '休市'
            status_emoji = '💤'
        
        if now_us.weekday() >= 5:
            market_status = '週末休市'
            status_emoji = '🏖️'
        
        return {
            'us_time': now_us.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'tw_time': now_tw.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'market_status': market_status,
            'status_emoji': status_emoji,
            'is_trading': market_status == '盤中交易'
        }

    def fetch_realtime_data(self, ticker):
        """抓取即時資料"""
        try:
            stock = yf.Ticker(ticker)
            
            if self.realtime:
                hist = stock.history(period='1d', interval='1m')
                if len(hist) == 0:
                    hist = stock.history(period='5d', interval='1d')
            else:
                hist = stock.history(period='5d', interval='1d')
            
            info = stock.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose')
            
            if current_price is None and len(hist) > 0:
                current_price = hist['Close'].iloc[-1]
            
            if prev_close is None and len(hist) >= 2:
                prev_close = hist['Close'].iloc[-2]
            
            return {
                'hist': hist,
                'current_price': current_price,
                'prev_close': prev_close,
                'info': info
            }
        except Exception as e:
            print(f"⚠️  {ticker} 即時資料抓取失敗: {e}")
            return None

    def fetch_sector_data(self):
        """抓取美股板塊資料"""
        time_info = self.get_current_time_info()
        
        print("=" * 70)
        print(f"{time_info['status_emoji']} 美股市場狀態: {time_info['market_status']}")
        print(f"🇺🇸 美東時間: {time_info['us_time']}")
        print(f"🇹🇼 台灣時間: {time_info['tw_time']}")
        print("=" * 70)
        print("\n🔍 正在抓取即時板塊資料...\n")
        
        sector_data = []
        
        all_etfs = US_SECTOR_ETFS.copy()
        if self.include_themes:
            all_etfs.update(US_THEME_ETFS)
        
        for ticker, name in all_etfs.items():
            try:
                data = self.fetch_realtime_data(ticker)
                
                if data and data['current_price'] and data['prev_close']:
                    current_price = data['current_price']
                    prev_close = data['prev_close']
                    change_pct = ((current_price - prev_close) / prev_close) * 100
                    
                    hist = data['hist']
                    if len(hist) > 0:
                        latest_volume = hist['Volume'].iloc[-1]
                        avg_volume = hist['Volume'].mean()
                        volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 1
                    else:
                        latest_volume = data['info'].get('volume', 0)
                        volume_ratio = 1
                    
                    flow_strength = change_pct * volume_ratio
                    
                    sector_type = '核心板塊' if ticker in US_SECTOR_ETFS else '主題板塊'
                    last_update = datetime.now(self.tw_tz).strftime('%H:%M:%S')
                    
                    sector_data.append({
                        'ticker': ticker,
                        'name': name,
                        'type': sector_type,
                        'price': round(current_price, 2),
                        'prev_close': round(prev_close, 2),
                        'change_pct': round(change_pct, 2),
                        'volume': int(latest_volume),
                        'volume_ratio': round(volume_ratio, 2),
                        'flow_strength': round(flow_strength, 2),
                        'last_update': last_update,
                        'market_status': time_info['market_status']
                    })
                    
                    emoji = '🔥' if change_pct > 3 else '📈' if change_pct > 0 else '📉'
                    print(f"{emoji} {ticker:6s} ({name:25s}): {change_pct:+6.2f}% | ${current_price:8.2f} | 量能: {volume_ratio:.2f}x")
                
            except Exception as e:
                print(f"❌ {ticker} 抓取失敗: {e}")
        
        return sorted(sector_data, key=lambda x: x['flow_strength'], reverse=True)

    def map_to_taiwan_sectors(self, us_sectors):
        """對應到台股族群"""
        print("\n" + "="*70)
        print("📊 對應台股族群...")
        print("="*70 + "\n")
        
        mapped_results = []
        
        for sector in us_sectors:
            ticker = sector['ticker']
            if ticker in SECTOR_MAPPING:
                tw_info = SECTOR_MAPPING[ticker]
                
                result = {
                    'us_sector': sector['name'],
                    'us_ticker': ticker,
                    'sector_type': sector['type'],
                    'us_change': sector['change_pct'],
                    'current_price': sector['price'],
                    'prev_close': sector['prev_close'],
                    'flow_strength': sector['flow_strength'],
                    'volume_ratio': sector['volume_ratio'],
                    'tw_sectors': tw_info['tw_sectors'],
                    'tw_stocks': tw_info['tw_stocks'],
                    'industry_detail': tw_info.get('industry_detail', ''),
                    'related_themes': tw_info.get('related_themes', []),
                    'signal': self._generate_signal(sector['flow_strength']),
                    'strength_level': self._get_strength_level(sector['flow_strength']),
                    'last_update': sector['last_update'],
                    'market_status': sector['market_status']
                }
                
                mapped_results.append(result)
        
        return mapped_results

    def _generate_signal(self, flow_strength):
        """生成交易信號"""
        if flow_strength > 10:
            return '🔥🔥 爆量流入'
        elif flow_strength > 5:
            return '🔥 強勁流入'
        elif flow_strength > 2:
            return '📈 資金流入'
        elif flow_strength > -2:
            return '➡️ 持平'
        elif flow_strength > -5:
            return '📉 資金流出'
        elif flow_strength > -10:
            return '❄️ 大量流出'
        else:
            return '❄️❄️ 恐慌流出'

    def _get_strength_level(self, flow_strength):
        """獲取強度等級"""
        if flow_strength > 10:
            return 5
        elif flow_strength > 5:
            return 4
        elif flow_strength > 2:
            return 3
        elif flow_strength > -2:
            return 2
        else:
            return 1

    def generate_report(self, mapped_data):
        """生成報告"""
        time_info = self.get_current_time_info()
        report_time = datetime.now(self.tw_tz).strftime('%Y-%m-%d %H:%M:%S')
        
        report = "=" * 70 + "\n"
        report += f"{time_info['status_emoji']} 美股板塊資金流向 → 台股族群對應報告\n"
        report += f"報告時間: {report_time} (台灣時間)\n"
        report += f"美股狀態: {time_info['market_status']}\n"
        report += "=" * 70 + "\n\n"
        
        core_sectors = [d for d in mapped_data if d['sector_type'] == '核心板塊']
        theme_sectors = [d for d in mapped_data if d['sector_type'] == '主題板塊']
        
        report += "📊 統計摘要\n"
        report += "=" * 70 + "\n"
        report += f"核心板塊: {len(core_sectors)} 個 | 主題板塊: {len(theme_sectors)} 個\n"
        
        inflow_count = len([d for d in mapped_data if d['flow_strength'] > 2])
        outflow_count = len([d for d in mapped_data if d['flow_strength'] < -2])
        
        report += f"資金流入: {inflow_count} 個 | 資金流出: {outflow_count} 個\n"
        report += "=" * 70 + "\n"
        
        report += "\n\n🔥 【資金流入排名 TOP 5】\n"
        report += "=" * 70 + "\n"
        
        for i, data in enumerate(mapped_data[:5], 1):
            stars = '⭐' * data['strength_level']
            report += f"\n{i}. {data['signal']} {stars} | {data['us_sector']}\n"
            report += f"   類型: {data['sector_type']} | 更新: {data['last_update']}\n"
            report += f"   美股: {data['us_ticker']} | 價格: ${data['current_price']:.2f} ({data['us_change']:+.2f}%)\n"
            report += f"   資金強度: {data['flow_strength']:.2f} | 量能比: {data['volume_ratio']:.2f}x\n"
            report += f"\n   📍 台股對應產業: {', '.join(data['tw_sectors'][:3])}\n"
            report += f"   🏭 細分產業: {data['industry_detail']}\n"
            report += f"   💡 建議關注個股:\n"
            for j, stock in enumerate(data['tw_stocks'][:5], 1):
                report += f"      {j}. {stock}\n"
            
            if data['related_themes']:
                themes_str = ', '.join(data['related_themes'])
                report += f"   🔗 相關主題板塊: {themes_str}\n"
            
            report += "-" * 70 + "\n"
        
        report += "\n\n❄️ 【資金流出警示 BOTTOM 5】\n"
        report += "=" * 70 + "\n"
        
        for i, data in enumerate(mapped_data[-5:], 1):
            report += f"\n{i}. {data['signal']} | {data['us_sector']}\n"
            report += f"   類型: {data['sector_type']} | 更新: {data['last_update']}\n"
            report += f"   美股: {data['us_ticker']} | 價格: ${data['current_price']:.2f} ({data['us_change']:+.2f}%)\n"
            report += f"   資金強度: {data['flow_strength']:.2f}\n"
            report += f"   ⚠️  台股對應產業: {', '.join(data['tw_sectors'][:3])}\n"
            report += f"   ⚠️  建議觀望個股: {', '.join(data['tw_stocks'][:3])}\n"
            report += "-" * 70 + "\n"
        
        report += "\n\n💡 【投資建議】\n"
        report += "=" * 70 + "\n"
        
        if time_info['is_trading']:
            report += "🔴 美股盤中,資料為即時更新\n\n"
        else:
            report += f"💤 美股 {time_info['market_status']},資料為最近交易日\n\n"
        
        top_sector = mapped_data[0]
        report += f"✅ 強勢板塊: {top_sector['us_sector']} ({top_sector['us_change']:+.2f}%)\n"
        report += f"   台股對應: {', '.join(top_sector['tw_sectors'][:3])}\n"
        report += f"   細分產業: {top_sector['industry_detail']}\n"
        report += f"   操作策略: 順勢做多,優先關注 {top_sector['tw_stocks'][0]}, {top_sector['tw_stocks'][1]}\n\n"
        
        weak_sector = mapped_data[-1]
        report += f"⚠️  弱勢板塊: {weak_sector['us_sector']} ({weak_sector['us_change']:+.2f}%)\n"
        report += f"   台股對應: {', '.join(weak_sector['tw_sectors'][:3])}\n"
        report += f"   操作策略: 避開或等待反彈,觀望 {weak_sector['tw_stocks'][0]}, {weak_sector['tw_stocks'][1]}\n"
        
        report += "=" * 70 + "\n"
        
        return report

    def save_to_json(self, mapped_data, filename='sector_flow_data.json'):
        """儲存為 JSON"""
        time_info = self.get_current_time_info()

        output = {
            'update_time': datetime.now(self.tw_tz).isoformat(),
            'us_time': time_info['us_time'],
            'tw_time': time_info['tw_time'],
            'market_status': time_info['market_status'],
            'is_realtime': self.realtime,
            'data_count': len(mapped_data),
            'sectors': mapped_data,
            'summary': {
                'inflow_count': len([d for d in mapped_data if d['flow_strength'] > 2]),
                'outflow_count': len([d for d in mapped_data if d['flow_strength'] < -2]),
                'top_sector': mapped_data[0]['us_sector'] if mapped_data else None,
                'worst_sector': mapped_data[-1]['us_sector'] if mapped_data else None
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n💾 資料已儲存至 {filename}")

    def save_to_markdown(self, report, filename='README.md'):
        """儲存為 Markdown"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"📝 報告已儲存至 {filename}")

    def save_to_csv(self, mapped_data, filename='sector_flow_history.csv'):
        """儲存歷史記錄"""
        df = pd.DataFrame(mapped_data)
        df['date'] = datetime.now(self.tw_tz).strftime('%Y-%m-%d')
        df['time'] = datetime.now(self.tw_tz).strftime('%H:%M:%S')

        if os.path.exists(filename):
            existing_df = pd.read_csv(filename)
            df = pd.concat([existing_df, df], ignore_index=True)

        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"📊 歷史資料已更新至 {filename}")

    def run(self, continuous=False, interval=300):
        """執行完整流程"""
        print("🚀 開始執行美股板塊資金流向追蹤...\n")
        print("="*70)

        while True:
            try:
                us_sectors = self.fetch_sector_data()
                mapped_data = self.map_to_taiwan_sectors(us_sectors)
                report = self.generate_report(mapped_data)
                print(report)

                self.save_to_json(mapped_data)
                self.save_to_markdown(report)
                self.save_to_csv(mapped_data)

                print("\n✅ 執行完成！")
                print("="*70)

                if not continuous:
                    break

                print(f"\n⏰ {interval}秒後更新...")
                time.sleep(interval)
                print("\n" + "="*70)
                print("🔄 開始新一輪更新...")
                print("="*70 + "\n")

            except KeyboardInterrupt:
                print("\n\n⚠️  使用者中斷")
                break
            except Exception as e:
                print(f"\n❌ 錯誤: {e}")
                if continuous:
                    print(f"⏰ {interval}秒後重試...")
                    time.sleep(interval)
                else:
                    break

        return mapped_data if 'mapped_data' in locals() else []

if __name__ == '__main__':
    tracker = SectorFlowTracker(include_themes=True, realtime=True)
    tracker.run(continuous=False)
