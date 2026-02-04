# 🎯 美股板塊 → 台股族群對應表

## 📊 核心板塊 (11 檔)

| 美股板塊 | 名稱 | 對應台股族群 |
|---------|------|-------------|
| **XLK** | 科技 Technology | 半導體, IC設計, 晶圓代工, 電腦及週邊, 光電, 通訊網路 |
| **XLF** | 金融 Financials | 金融 |
| **XLV** | 醫療保健 Healthcare | 生技醫療 |
| **XLE** | 能源 Energy | 太陽能 |
| **XLI** | 工業 Industrials | 航運 |
| **XLP** | 必需消費 Consumer Staples | 食品 |
| **XLY** | 非必需消費 Consumer Discretionary | 汽車, 電動車 |
| **XLB** | 原物料 Materials | 鋼鐵, 塑膠, 水泥 |
| **XLC** | 通訊服務 Communication Services | 通訊網路 |
| **XLRE** | 房地產 Real Estate | （無對應台股族群） |
| **XLU** | 公用事業 Utilities | （無對應台股族群） |

## 🚀 主題板塊 (5 檔)

| 美股板塊 | 名稱 | 對應台股族群 |
|---------|------|-------------|
| **TAN** | 太陽能 Solar Energy | 太陽能 |
| **SOXX** | 半導體 Semiconductors | 半導體, IC設計, 晶圓代工 |
| **CLOU** | 雲端運算 Cloud Computing | 電子零組件, 通訊網路 |
| **CARZ** | 電動車 EV | 汽車, 電動車 |
| **LIT** | 鋰電池 Lithium Battery | 電池 |

## 📈 台股族群清單 (19 個)

| # | 族群名稱 | 對應美股板塊 |
|---|---------|------------|
| 1 | 半導體 | XLK, SOXX |
| 2 | IC設計 | XLK, SOXX |
| 3 | 晶圓代工 | XLK, SOXX |
| 4 | 封測 | XLK |
| 5 | 光電 | XLK |
| 6 | 通訊網路 | XLK, XLC, CLOU |
| 7 | 電子零組件 | CLOU |
| 8 | 電腦及週邊 | XLK |
| 9 | 金融 | XLF |
| 10 | 生技醫療 | XLV |
| 11 | 太陽能 | TAN, XLE |
| 12 | 航運 | XLI |
| 13 | 食品 | XLP |
| 14 | 汽車 | XLY, CARZ |
| 15 | 電動車 | XLY, CARZ |
| 16 | 電池 | LIT |
| 17 | 鋼鐵 | XLB |
| 18 | 塑膠 | XLB |
| 19 | 水泥 | XLB |

## 🔗 使用說明

### 投資決策流程

1. **監控美股板塊**: 觀察 16 檔美股板塊 ETF 的漲跌幅
2. **找出對應族群**: 查表確認該板塊對應的台股族群
3. **進行操作**: 根據美股走勢決定是否買進或賣出台股該族群的相關個股

### 快速查詢

- **TAN 上漲** → 買進太陽能族群相關個股
- **SOXX 下跌** → 回避或減碼半導體、IC設計、晶圓代工族群
- **XLB 上漲** → 關注鋼鐵、塑膠、水泥族群

## 📊 實時熱力圖

執行以下命令生成最新的台股族群熱度排行：

```bash
python3 sector_heatmap.py
```

輸出文件：
- `out/us_sector_quotes.csv` - 美股板塊實時報價
- `out/tw_themes_ranked.json` - 台股族群熱度排行（按美股推動力加權）
- `out/us_sector_to_tw_picks.json` - 完整美股→台股→個股映射

## 📚 更多資訊

詳見 [HEATMAP_GUIDE.md](HEATMAP_GUIDE.md) 了解系統的完整使用說明。
