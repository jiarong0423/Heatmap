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

# 細分板塊追蹤 (熱門主題)
US_THEME_ETFS = {
    'TAN': '太陽能 Solar Energy',
    'SOXX': '半導體 Semiconductors',
    'IGV': '應用軟件 Software',
    'IHI': '醫療設備 Medical Devices',
    'XRT': '零售 Retail',
    'ARKK': '創新科技 Innovation',
    'BOTZ': '機器人與AI Robotics & AI',
    'FINX': '金融科技 FinTech',
    'CLOU': '雲端運算 Cloud Computing',
    'HACK': '網路安全 Cybersecurity'
}

# 美股板塊 -> 台股族群對應 (更新版)
SECTOR_MAPPING = {
    'XLK': {
        'name': '科技',
        'tw_sectors': ['半導體', 'IC設計', '電腦及週邊設備', '電子零組件', '光電'],
        'tw_stocks': ['2330 台積電', '2454 聯發科', '2317 鴻海', '2303 聯電', '3711 日月光投控'],
        'related_themes': ['SOXX', 'IGV', 'CLOU']
    },
    'XLF': {
        'name': '金融',
        'tw_sectors': ['金控', '銀行', '證券', '保險'],
        'tw_stocks': ['2881 富邦金', '2882 國泰金', '2886 兆豐金', '2891 中信金', '2884 玉山金'],
        'related_themes': ['FINX']
    },
    'XLV': {
        'name': '醫療保健',
        'tw_sectors': ['生技醫療', '醫療器材'],
        'tw_stocks': ['4736 泰博', '6547 高端疫苗', '6446 藥華藥', '1789 神隆', '4174 浩鼎'],
        'related_themes': ['IHI']
    },
    'XLE': {
        'name': '能源',
        'tw_sectors': ['油電燃氣', '綠能環保', '太陽能'],
        'tw_stocks': ['6505 台塑化', '1326 台化', '3481 群創', '6488 環球晶', '3576 聯合再生'],
        'related_themes': ['TAN']
    },
    'XLI': {
        'name': '工業',
        'tw_sectors': ['航運', '塑膠', '水泥', '機械', '電機'],
        'tw_stocks': ['2603 長榮', '2609 陽明', '2615 萬海', '1101 台泥', '2207 和泰車'],
        'related_themes': ['BOTZ']
    },
    'XLP': {
        'name': '必需消費',
        'tw_sectors': ['食品', '貿易百貨', '觀光餐飲'],
        'tw_stocks': ['1301 台塑', '1216 統一', '2912 統一超', '2105 正新', '1227 佳格'],
        'related_themes': []
    },
    'XLY': {
        'name': '非必需消費',
        'tw_sectors': ['汽車', '紡織', '電商零售', '百貨'],
        'tw_stocks': ['2201 裕隆', '2207 和泰車', '2371 大同', '2915 潤泰全', '2845 遠東銀'],
        'related_themes': ['XRT']
    },
    'XLB': {
        'name': '原物料',
        'tw_sectors': ['鋼鐵', '化學', '塑膠', '水泥'],
        'tw_stocks': ['2002 中鋼', '1303 南亞', '1326 台化', '6505 台塑化', '1101 台泥'],
        'related_themes': []
    },
    'XLRE': {
        'name': '房地產',
        'tw_sectors': ['營建', '不動產', 'REITs'],
        'tw_stocks': ['2501 國建', '2515 中工', '5522 遠雄', '2542 興富發', '9945 潤泰新'],
        'related_themes': []
    },
    'XLU': {
        'name': '公用事業',
        'tw_sectors': ['電信', '電力', '天然氣'],
        'tw_stocks': ['3045 台灣大', '4904 遠傳', '2412 中華電', '9802 鈺齊-KY'],
        'related_themes': []
    },
    'XLC': {
        'name': '通訊服務',
        'tw_sectors': ['電信', '媒體', '網路服務'],
        'tw_stocks': ['2412 中華電', '3045 台灣大', '4904 遠傳', '2498 宏達電', '3008 大立光'],
        'related_themes': []
    },
    # 主題 ETF 對應
    'TAN': {
        'name': '太陽能',
        'tw_sectors': ['太陽能', '綠能', '電池'],
        'tw_stocks': ['6488 環球晶', '3576 聯合再生', '6443 元晶', '3514 昱晶', '6869 雲豹能源'],
        'related_themes': []
    },
    'SOXX': {
        'name': '半導體',
        'tw_sectors': ['半導體', 'IC設計', '晶圓代工', '封測'],
        'tw_stocks': ['2330 台積電', '2454 聯發科', '2303 聯電', '3711 日月光投控', '3034 聯詠'],
        'related_themes': []
    },
    'IGV': {
        'name': '應用軟件',
        'tw_sectors': ['軟體', '資訊服務', '雲端'],
        'tw_stocks': ['6488 環球晶', '3293 鈊象', '6263 普萊德', '6462 神盾', '3293 鈊象'],
        'related_themes': []
    },
    'IHI': {
        'name': '醫療設備',
        'tw_sectors': ['醫療器材', '生技醫療'],
        'tw_stocks': ['4736 泰博', '4743 合一', '6547 高端疫苗', '6446 藥華藥', '4174 浩鼎'],
        'related_themes': []
    },
    'XRT': {
        'name': '零售',
        'tw_sectors': ['百貨', '電商', '零售通路'],
        'tw_stocks': ['2912 統一超', '2915 潤泰全', '2845 遠東銀', '2888 新光金', '9945 潤泰新'],
        'related_themes': []
    }
}

class SectorFlowTracker:
    def __init__(self, include_themes=True):
        self.results = []
        self.include_themes = include_themes
        
    def fetch_sector_data(self):
        """抓取美股板塊資料"""
        print("🔍 正在抓取美股板塊資料...\n")
        sector_data = []
        
        # 合併主要板塊和主題 ETF
        all_etfs = US_SECTOR_ETFS.copy()
        if self.include_themes:
            all_etfs.update(US_THEME_ETFS)
        
        for ticker, name in all_etfs.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period='5d')
                
                if len(hist) >= 2:
                    latest_close = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
                    change_pct = ((latest_close - prev_close) / prev_close) * 100
                    volume = hist['Volume'].iloc[-1]
                    avg_volume = hist['Volume'].mean()
                    volume_ratio = volume / avg_volume
                    
                    # 計算資金流向強度
                    flow_strength = change_pct * volume_ratio
                    
                    # 判斷板塊類型
                    sector_type = '核心板塊' if ticker in US_SECTOR_ETFS else '主題板塊'
                    
                    sector_data.append({
                        'ticker': ticker,
                        'name': name,
                        'type': sector_type,
                        'price': round(latest_close, 2),
                        'change_pct': round(change_pct, 2),
                        'volume': int(volume),
                        'volume_ratio': round(volume_ratio, 2),
                        'flow_strength': round(flow_strength, 2)
                    })
                    
                    emoji = '🔥' if change_pct > 3 else '📈' if change_pct > 0 else '📉'
                    print(f"{emoji} {ticker:6s} ({name:20s}): {change_pct:+6.2f}% | 量能: {volume_ratio:.2f}x")
                
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
                    'flow_strength': sector['flow_strength'],
                    'volume_ratio': sector['volume_ratio'],
                    'tw_sectors': tw_info['tw_sectors'],
                    'tw_stocks': tw_info['tw_stocks'],
                    'related_themes': tw_info.get('related_themes', []),
                    'signal': self._generate_signal(sector['flow_strength']),
                    'strength_level': self._get_strength_level(sector['flow_strength'])
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
        """獲取強度等級 (1-5)"""
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
        report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════╗
║              美股板塊資金流向 → 台股族群對應報告                      ║
║              報告時間: {report_time}                        ║
╚══════════════════════════════════════════════════════════════════════╝

"""
        
        # 分類統計
        core_sectors = [d for d in mapped_data if d['sector_type'] == '核心板塊']
        theme_sectors = [d for d in mapped_data if d['sector_type'] == '主題板塊']
        
        report += f"\n📊 統計摘要\n"
        report += "=" * 70 + "\n"
        report += f"核心板塊: {len(core_sectors)} 個 | 主題板塊: {len(theme_sectors)} 個\n"
        
        inflow_count = len([d for d in mapped_data if d['flow_strength'] > 2])
        outflow_count = len([d for d in mapped_data if d['flow_strength'] < -2])
        
        report += f"資金流入: {inflow_count} 個 | 資金流出: {outflow_count} 個\n"
        report += "=" * 70 + "\n"
        
        # TOP 5 資金流入
        report += "\n\n🔥 【資金流入排名 TOP 5】\n"
        report += "=" * 70 + "\n"
        
        for i, data in enumerate(mapped_data[:5], 1):
            stars = '⭐' * data['strength_level']
            report += f"\n{i}. {data['signal']} {stars} | {data['us_sector']}\n"
            report += f"   類型: {data['sector_type']}\n"
            report += f"   美股: {data['us_ticker']} ({data['us_change']:+.2f}%)\n"
            report += f"   資金強度: {data['flow_strength']:.2f} | 量能比: {data['volume_ratio']:.2f}x\n"
            report += f"\n   📍 對應台股族群: {', '.join(data['tw_sectors'])}\n"
            report += f"   💡 建議關注個股: {', '.join(data['tw_stocks'][:3])}\n"
            
            if data['related_themes']:
                themes_str = ', '.join(data['related_themes'])
                report += f"   🔗 相關主題: {themes_str}\n"
            
            report += "-" * 70 + "\n"
        
        # BOTTOM 5 資金流出
        report += "\n\n❄️ 【資金流出警示 BOTTOM 5】\n"
        report += "=" * 70 + "\n"
        
        for i, data in enumerate(mapped_data[-5:], 1):
            report += f"\n{i}. {data['signal']} | {data['us_sector']}\n"
            report += f"   類型: {data['sector_type']}\n"
            report += f"   美股: {data['us_ticker']} ({data['us_change']:+.2f}%)\n"
            report += f"   資金強度: {data['flow_strength']:.2f}\n"
            report += f"   ⚠️  對應台股族群: {', '.join(data['tw_sectors'])}\n"
            report += f"   ⚠️  建議觀望個股: {', '.join(data['tw_stocks'][:3])}\n"
            report += "-" * 70 + "\n"
        
        # 投資建議
        report += "\n\n💡 【投資建議】\n"
        report += "=" * 70 + "\n"
        
        top_sector = mapped_data[0]
        report += f"✅ 強勢板塊: {top_sector['us_sector']} ({top_sector['us_change']:+.2f}%)\n"
        report += f"   台股對應: {', '.join(top_sector['tw_sectors'])}\n"
        report += f"   操作策略: 順勢做多,關注 {', '.join(top_sector['tw_stocks'][:2])}\n\n"
        
        weak_sector = mapped_data[-1]
        report += f"⚠️  弱勢板塊: {weak_sector['us_sector']} ({weak_sector['us_change']:+.2f}%)\n"
        report += f"   台股對應: {', '.join(weak_sector['tw_sectors'])}\n"
        report += f"   操作策略: 避開或等待反彈,觀望 {', '.join(weak_sector['tw_stocks'][:2])}\n"
        
        report += "=" * 70 + "\n"
        
        return report
    
    def save_to_json(self, mapped_data, filename='sector_flow_data.json'):
        """儲存為 JSON"""
        output = {
            'update_time': datetime.now().isoformat(),
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
        """儲存歷史記錄為 CSV"""
        df = pd.DataFrame(mapped_data)
        df['date'] = datetime.now().strftime('%Y-%m-%d')
        
        # 如果檔案存在,追加資料
        if os.path.exists(filename):
            existing_df = pd.read_csv(filename)
            df = pd.concat([existing_df, df], ignore_index=True)
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"📊 歷史資料已更新至 {filename}")
    
    def run(self):
        """執行完整流程"""
        print("🚀 開始執行美股板塊資金流向追蹤...\n")
        print("="*70)
        
        # 1. 抓取美股板塊資料
        us_sectors = self.fetch_sector_data()
        
        # 2. 對應台股族群
        mapped_data = self.map_to_taiwan_sectors(us_sectors)
        
        # 3. 生成報告
        report = self.generate_report(mapped_data)
        print(report)
        
        # 4. 儲存資料
        self.save_to_json(mapped_data)
        self.save_to_markdown(report)
        self.save_to_csv(mapped_data)
        
        print("\n✅ 執行完成！")
        print("="*70)
        
        return mapped_data

if __name__ == '__main__':
    # include_themes=True 會包含主題 ETF (如太陽能、半導體等)
    tracker = SectorFlowTracker(include_themes=True)
    tracker.run()
