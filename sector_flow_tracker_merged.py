#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股板塊資金流向 → 台股族群對應系統 (合併版)
Sector Flow Tracker: US sectors + Taiwan group mapping
版本: 2.5 (Merged Edition)

特色：
✓ 保留 11 大美股板塊完整信息
✓ 整合台股族群對應（不只有台股）
✓ 多格式輸出 (JSON + CSV + Markdown)
✓ GitHub Actions 自動化支持
"""

import yfinance as yf
import pandas as pd
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================================
# 配置和數據定義
# ============================================================================

# 美股 11 大板塊 ETF
US_SECTOR_ETFS = {
    'XLK': {'en': 'Technology', 'zh': '科技'},
    'XLF': {'en': 'Financials', 'zh': '金融'},
    'XLV': {'en': 'Healthcare', 'zh': '醫療保健'},
    'XLE': {'en': 'Energy', 'zh': '能源'},
    'XLI': {'en': 'Industrials', 'zh': '工業'},
    'XLP': {'en': 'Consumer Staples', 'zh': '必需消費'},
    'XLY': {'en': 'Consumer Discretionary', 'zh': '非必需消費'},
    'XLB': {'en': 'Materials', 'zh': '原物料'},
    'XLRE': {'en': 'Real Estate', 'zh': '房地產'},
    'XLU': {'en': 'Utilities', 'zh': '公用事業'},
    'XLC': {'en': 'Communication Services', 'zh': '通訊服務'},
}

# 美股板塊 → 台股族群對應表
SECTOR_MAPPING = {
    'XLK': {
        'name_zh': '科技',
        'tw_groups': ['半導體', 'IC設計', '電腦及週邊設備', '電子零組件', '光電']
    },
    'XLF': {
        'name_zh': '金融',
        'tw_groups': ['金控', '銀行', '證券', '保險']
    },
    'XLV': {
        'name_zh': '醫療保健',
        'tw_groups': ['生技醫療', '醫療器材']
    },
    'XLE': {
        'name_zh': '能源',
        'tw_groups': ['油電燃氣', '綠能環保']
    },
    'XLI': {
        'name_zh': '工業',
        'tw_groups': ['航運', '塑膠', '水泥', '機械']
    },
    'XLP': {
        'name_zh': '必需消費',
        'tw_groups': ['食品', '貿易百貨', '觀光']
    },
    'XLY': {
        'name_zh': '非必需消費',
        'tw_groups': ['汽車', '紡織', '電商零售']
    },
    'XLB': {
        'name_zh': '原物料',
        'tw_groups': ['鋼鐵', '化學', '塑膠']
    },
    'XLRE': {
        'name_zh': '房地產',
        'tw_groups': ['營建', '不動產']
    },
    'XLU': {
        'name_zh': '公用事業',
        'tw_groups': ['電信', '電力']
    },
    'XLC': {
        'name_zh': '通訊服務',
        'tw_groups': ['電信', '媒體']
    }
}


# ============================================================================
# 核心追蹤類
# ============================================================================

class SectorFlowTracker:
    """美股板塊資金流向追蹤器 (合併版)"""
    
    def __init__(self):
        # 使用台北時區作為時間基準（不在初始化時鎖定時間）
        self.tz = ZoneInfo('Asia/Taipei')
        self.timestamp = None
        self.results = []
        self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)

    def get_timestamp(self) -> str:
        """即時抓取電腦時間（台北時區）並回傳格式化字串。"""
        return datetime.now(self.tz).strftime('%Y-%m-%d %H:%M:%S %Z')
    
    def fetch_sector_data(self) -> List[Dict]:
        """抓取美股板塊實時數據"""
        print("🔍 正在抓取美股板塊資料...")
        print("=" * 80)
        
        sector_data = []
        
        for ticker, info in US_SECTOR_ETFS.items():
            try:
                # 獲取 ETF 數據
                etf = yf.Ticker(ticker)
                hist = etf.history(period='1d')
                
                if len(hist) > 0:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = hist['Open'].iloc[0]
                    change = current_price - prev_close
                    change_pct = (change / prev_close) * 100 if prev_close > 0 else 0
                    
                    # 計算量能比（與平均比較，簡化版為 1.0）
                    volume_ratio = 1.0
                    
                    # 計算資金流向強度 = 漲幅% × 量能比
                    flow_strength = change_pct * volume_ratio
                    
                    # 生成信號
                    signal = self._generate_signal(flow_strength)
                    
                    data = {
                        'us_ticker': ticker,
                        'us_sector': f"{info['zh']} {info['en']}",
                        'us_price': round(current_price, 2),
                        'us_change': round(change_pct, 2),
                        'volume_ratio': round(volume_ratio, 2),
                        'flow_strength': round(flow_strength, 2),
                        'signal': signal
                    }
                    
                    sector_data.append(data)
                    print(f"✅ {ticker:6s} | {info['zh']:10s} {info['en']:25s} | {change_pct:+7.2f}% | 量能: {volume_ratio:.2f}x")
                
            except Exception as e:
                print(f"⚠️  {ticker:6s} | 抓取失敗: {str(e)}")
        
        print("=" * 80)
        return sorted(sector_data, key=lambda x: x['flow_strength'], reverse=True)
    
    def _generate_signal(self, flow_strength: float) -> str:
        """生成交易信號"""
        if flow_strength > 5:
            return '🔥 強勁流入'
        elif flow_strength > 2:
            return '📈 資金流入'
        elif flow_strength > -2:
            return '➡️ 持平'
        elif flow_strength > -5:
            return '📉 資金流出'
        else:
            return '❄️ 大量流出'
    
    def map_to_taiwan_groups(self, us_sectors: List[Dict]) -> List[Dict]:
        """對應台股族群"""
        print("\n📊 對應台股族群...")
        print("=" * 80)
        
        mapped_results = []
        
        for sector in us_sectors:
            ticker = sector['us_ticker']
            
            # 加入台股族群信息
            if ticker in SECTOR_MAPPING:
                tw_groups = SECTOR_MAPPING[ticker]['tw_groups']
                sector['tw_groups'] = tw_groups
                print(f"✅ {sector['signal']} {sector['us_sector']:35s} → {', '.join(tw_groups)}")
            else:
                sector['tw_groups'] = []
                print(f"⚠️  {sector['us_sector']:35s} → （無對應台股族群）")
            
            mapped_results.append(sector)
        
        print("=" * 80)
        return mapped_results
    
    def generate_markdown_report(self, data: List[Dict]) -> str:
        """生成 Markdown 報告（保留美股完整信息）"""
        report = f"""# 🌐 美股板塊資金流向 → 台股族群對應報告

    **更新時間:** {self.get_timestamp()} (台北時間)

    ---

    ## 📈 資金流向排名 (TOP 5 - 資金流入)

    """
        
        # TOP 5 資金流入
        for i, data_item in enumerate(data[:5], 1):
            report += f"""### {i}. {data_item['signal']} {data_item['us_sector']}

- **美股代碼:** {data_item['us_ticker']}
- **美股價格:** ${data_item['us_price']}
- **漲跌幅:** {data_item['us_change']:+.2f}%
- **量能比:** {data_item['volume_ratio']:.2f}x
- **資金強度:** {data_item['flow_strength']:.2f}
- **📍 對應台股族群:** {', '.join(data_item.get('tw_groups', []))}

"""
        
        # BOTTOM 3 資金流出
        report += "\n---\n\n## ⚠️ 資金流出警示 (BOTTOM 3)\n\n"
        
        for i, data_item in enumerate(data[-3:], 1):
            report += f"""### {i}. {data_item['signal']} {data_item['us_sector']}

- **美股代碼:** {data_item['us_ticker']}
- **美股價格:** ${data_item['us_price']}
- **跌幅:** {data_item['us_change']:+.2f}%
- **資金強度:** {data_item['flow_strength']:.2f}
- **📍 對應台股族群:** {', '.join(data_item.get('tw_groups', [])) or '（無對應）'}

"""
        
        return report
    
    def save_to_json(self, data: List[Dict], filename: str = 'sector_flow_data.json'):
        """保存為 JSON 格式"""
        output = {
            'update_time': self.get_timestamp(),
            'data': data
        }
        
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 JSON 數據已儲存至 {filepath}")
    
    def save_to_csv(self, data: List[Dict], filename: str = 'sector_flow_quotes.csv'):
        """保存為 CSV 格式"""
        df = pd.DataFrame(data)
        # 重新排序列
        columns = ['us_ticker', 'us_sector', 'us_price', 'us_change', 'volume_ratio', 
                   'flow_strength', 'signal', 'tw_groups']
        df = df[columns]
        
        filepath = self.output_dir / filename
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        print(f"📊 CSV 數據已儲存至 {filepath}")
    
    def save_to_markdown(self, report: str, filename: str = 'SECTOR_REPORT.md'):
        """保存為 Markdown 報告"""
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📝 報告已儲存至 {filepath}")
    
    def run(self):
        """執行完整流程"""
        print("\n" + "=" * 80)
        print("🚀 美股板塊資金流向追蹤系統 (合併版 v2.5)")
        print("=" * 80 + "\n")
        
        # 步驟 1: 抓取美股數據
        us_sectors = self.fetch_sector_data()
        
        # 步驟 2: 對應台股族群
        mapped_data = self.map_to_taiwan_groups(us_sectors)
        
        # 步驟 3: 生成報告
        report = self.generate_markdown_report(mapped_data)
        
        # 步驟 4: 保存所有格式
        self.save_to_json(mapped_data)
        self.save_to_csv(mapped_data)
        self.save_to_markdown(report)
        
        # 步驟 5: 終端輸出報告
        print("\n" + report)
        
        print("=" * 80)
        print("✅ 執行完成！")
        print("=" * 80 + "\n")
        
        return mapped_data


# ============================================================================
# 入口點
# ============================================================================

if __name__ == '__main__':
    tracker = SectorFlowTracker()
    tracker.run()
