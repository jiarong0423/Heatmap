# 美股板塊→台股熱力圖系統使用指南

## 📊 系統概述

這是一個完整的**美股資金流向追蹤系統**，通過美股 ETF 行情變化來預測和推薦台股族群及個股：

```
美股板塊 ETF (16檔)
    ↓
台股族群/主題 (19個)
    ↓
台股個股 (187檔)
```

## 🎯 核心流程

### 1️⃣ 輸入數據源

#### `mappings/us_sector_to_tw_theme.csv`
美股 Sector ETF 與台股族群的對應關係：

| us_sector_ticker | us_sector_name | tw_theme |
|---|---|---|
| XLK | 科技 Technology | IC設計 |
| XLK | 科技 Technology | 光電 |
| XLK | 科技 Technology | 半導體 |
| TAN | 太陽能 Solar Energy | 太陽能 |
| ... | ... | ... |

**覆蓋範圍：**
- 11 檔核心 XL* 系列 ETF (XLK, XLF, XLV, XLE, XLI, XLP, XLY, XLB, XLC, XLRE, XLU)
- 5 檔主題 ETF (TAN 太陽能, SOXX 半導體, CLOU 雲端, CARZ 汽車, LIT 鋰電池)

#### `mappings/tw_theme_to_stocks.csv`
台股族群與個股的完整清單：

| tw_theme | stock_code | stock_name |
|---|---|---|
| 半導體 | 2330 | 台積電 |
| 半導體 | 2454 | 聯發科 |
| IC設計 | 2330 | 台積電 |
| IC設計 | 2454 | 聯發科 |
| ... | ... | ... |

**覆蓋範圍：** 19 個台股族群，187 檔個股

### 2️⃣ 執行主程序

```bash
python3 sector_heatmap.py
```

或使用自定義參數：

```bash
python3 sector_heatmap.py \
  --us2tw mappings/us_sector_to_tw_theme.csv \
  --twlist mappings/tw_theme_to_stocks.csv \
  --outdir out
```

**參數說明：**
- `--us2tw`: 美股→台股族群對應表路徑 (預設: `mappings/us_sector_to_tw_theme.csv`)
- `--twlist`: 台股族群→個股清單路徑 (預設: `mappings/tw_theme_to_stocks.csv`)
- `--outdir`: 輸出目錄 (預設: `out`)

### 3️⃣ 輸出檔案

#### `out/us_sector_quotes.csv`
美股板塊 ETF 即時/延遲報價

```csv
us_sector_ticker,us_sector_name,price,change,change_pct
TAN,太陽能 Solar Energy,57.75,2.16,3.8856
XLB,原物料 Materials,51.605,0.905,1.785
SOXX,納斯達克生技 Nasdaq Biotech,331.06,-13.95,-4.2205
```

**用途：** 查看美股板塊當日表現，判斷哪些板塊資金流入/流出

#### `out/tw_themes_ranked.json`
台股族群熱度排行（按對應美股板塊加權計算）

```json
[
  {
    "tw_theme": "太陽能",
    "score_change_pct": 3.8856,
    "sources": [
      {
        "us_sector_ticker": "TAN",
        "us_sector_name": "太陽能 Solar Energy",
        "change_pct": 3.8856
      },
      {
        "us_sector_ticker": "XLE",
        "us_sector_name": "能源 Energy",
        "change_pct": 1.228
      }
    ],
    "stock_count": 10
  },
  ...
]
```

**排行示例（2024年數據）：**
```
排名  台股族群      熱度    對應美股板塊
1     太陽能       +3.89%  TAN(+3.89%), XLE(+1.23%)
2     鋼鐵         +1.78%  XLB(+1.78%)
...
14    半導體       -2.56%  XLK(-2.56%), SOXX(-4.22%)
```

**解讀方式：**
- ✅ 綠色（正數）：對應美股板塊上漲，台股該族群看好
- ❌ 紅色（負數）：對應美股板塊下跌，台股該族群謹慎
- 多個源頭：該族群對應多個美股板塊時，取最高漲幅

#### `out/us_sector_to_tw_picks.json`
完整的美股→台股→個股三層對應

```json
[
  {
    "us_sector": {
      "ticker": "TAN",
      "name": "太陽能 Solar Energy",
      "price": 57.75,
      "change": 2.16,
      "change_pct": 3.8856
    },
    "tw_themes": [
      {
        "tw_theme": "太陽能",
        "stocks": [
          {"stock_code": "3452", "stock_name": "益通"},
          {"stock_code": "3514", "stock_name": "昱晶"},
          ...
        ]
      }
    ]
  },
  ...
]
```

**用途：** 完整的投資決策鏈
- TAN 上漲 (+3.89%) → 太陽能族群看好 → 選擇 3452、3514、3561 等個股

#### `out/tw_theme_constituents.json`
台股族群→個股清單（供參考）

```json
{
  "太陽能": [
    {"stock_code": "3452", "stock_name": "益通"},
    {"stock_code": "3514", "stock_name": "昱晶"},
    ...
  ],
  "半導體": [
    {"stock_code": "2330", "stock_name": "台積電"},
    {"stock_code": "2454", "stock_name": "聯發科"},
    ...
  ],
  ...
}
```

## 📈 使用案例

### 案例 1：TAN (太陽能 ETF) 上漲 +3.89%

**投資決策流程：**

1. ✅ **識別板塊**：TAN 在美股上漲（+3.89%）
2. ✅ **找到台股族群**：太陽能族群（熱度 +3.89%）
3. ✅ **選擇個股**：
   - 3452 益通
   - 3514 昱晶
   - 3561 昇陽光電
   - 3576 聯合再生
   - 6274 台燿

**投資建議**：買進太陽能族群相關個股，預期跟漲

---

### 案例 2：SOXX (納斯達克生技) 下跌 -4.22%

**投資決策流程：**

1. ❌ **識別板塊**：SOXX 在美股下跌（-4.22%）
2. ❌ **找到台股族群**：半導體族群熱度 -2.56%（同步下跌）
3. ❌ **選擇個股**：
   - 2330 台積電
   - 2454 聯發科
   - 3034 聯詠
   - ...

**投資建議**：減碼或迴避半導體族群，等待反彈信號

## 🔄 運作機制

### 數據流向

```
yfinance 抓取
16 檔美股板塊 ETF
    ↓
計算每檔 ETF 漲跌幅
    ↓
查詢對應的台股族群
（一個台股族群可能對應多個美股 ETF）
    ↓
取「最高漲幅」作為族群熱度分數
（max(change_pct) for all mapped US sectors）
    ↓
排序輸出前 19 個台股族群
    ↓
附上該族群的所有個股清單
```

### 加權計算範例

**太陽能族群對應 2 個美股 ETF：**
- TAN (太陽能 ETF): +3.89%
- XLE (能源 ETF): +1.23%

**族群熱度** = max(3.89%, 1.23%) = **+3.89%**
（取最強信號，代表該族群最有力的上漲動力來自 TAN）

## 📊 台股族群完整清單

| 序號 | 族群 | 個股數 | 對應美股板塊 | 說明 |
|---|---|---|---|---|
| 1 | 半導體 | 10 | XLK, SOXX | 台灣最強產業 |
| 2 | IC設計 | 10 | XLK, SOXX | 聯發科、聯詠等 |
| 3 | 晶圓代工 | 10 | XLK, SOXX | 台積電、聯電等 |
| 4 | 封測 | 8 | XLK, SOXX | 日月光、矽品等 |
| 5 | 光電 | 8 | XLK | 友達、群創等 |
| 6 | 通訊網路 | 10 | CLOU, XLC, XLK | 台灣5G領導廠商 |
| 7 | 金融 | 10 | XLF | 集保、元大、富邦等 |
| 8 | 生技醫療 | 10 | XLV | 台灣生技新興勢力 |
| 9 | 太陽能 | 10 | TAN, XLE | 聯合再生、茂迪等 |
| 10 | 航運 | 10 | XLI | 陽明、長榮、萬海等 |
| 11 | 食品 | 10 | XLP | 台灣食品龍頭 |
| 12 | 汽車 | 10 | XLY, CARZ | 台灣汽車零件商 |
| 13 | 電動車 | 10 | XLY, CARZ | 台灣電動車產業鏈 |
| 14 | 電池 | 10 | LIT | 電池、電芯製造商 |
| 15 | 鋼鐵 | 10 | XLB | 中鋼、高盛等 |
| 16 | 塑膠 | 10 | XLB | 台化、南亞等 |
| 17 | 水泥 | 10 | XLB | 台泥、亞泥等 |
| 18 | 電子零組件 | 10 | CLOU, XLK | 被動元件、連接器等 |
| 19 | 電腦及週邊 | 10 | XLK | 筆電、週邊製造商 |

## ⚡ 快速開始

### 最簡單的方式

```bash
# 1. 執行預設配置
python3 sector_heatmap.py

# 2. 查看結果
head out/tw_themes_ranked.json
```

### 自動化排程

```bash
# 每日北京時間 16:00 (台股開盤末期，美股開市初期)
# 在 crontab 中設定：
0 16 * * 1-5 cd /workspaces/Heatmap && python3 sector_heatmap.py
```

### 與其他系統整合

```python
import json

# 讀取台股族群排行
with open('out/tw_themes_ranked.json') as f:
    ranked_themes = json.load(f)

# 取熱度前 3 名
top_3 = ranked_themes[:3]
for theme in top_3:
    print(f"{theme['tw_theme']}: {theme['score_change_pct']:+.2f}%")
```

## 🔧 技術細節

### 依賴

- `yfinance`: 美股 ETF 報價數據
- `python3.7+`: 標準庫 (csv, json, pathlib, logging, argparse)

### 安裝依賴

```bash
pip install yfinance
```

### 數據更新頻率

- **實時性**：美股開市期間實時更新（延遲 15-20 分鐘）
- **推薦更新**：台股開盤期間每 30 分鐘執行一次
- **夜間**：美股收盤後執行一次，用於隔日台股開盤策略

### 異常處理

- 網路連線問題：自動降級為上次價格
- 掛牌停止：自動標記為 0.0（待驗證）
- 缺失數據：記錄警告，繼續執行

## 📝 更新日誌

### v1.0 (2024-02-04)

- ✅ 完成 16 檔美股板塊 ETF 映射
- ✅ 整合 19 個台股族群，187 檔個股
- ✅ 實現完整的三層映射系統
- ✅ 輸出 4 種格式供多用途使用

## 🚀 未來計劃

- [ ] 實時推播（超過漲跌閾值時通知）
- [ ] Web Dashboard（可視化熱力圖）
- [ ] 機器學習預測（基於歷史相關性）
- [ ] A股映射（延伸至中國股市）
- [ ] 港股映射（香港上市台灣企業）

---

**最後更新**：2024-02-04  
**版本**：1.0  
**維護者**：Copilot Coding Agent
