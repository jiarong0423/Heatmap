#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股板塊熱力圖（以 Sector ETFs 代表）-> 對應台股族群 -> 列出台股個股

Inputs:
  mappings/us_sector_to_tw_theme.csv      (美股板塊->台股族群對應)
  mappings/tw_theme_to_stocks.csv         (台股族群->個股)

Outputs:
  out/us_sector_quotes.csv                 (美股板塊ETF報價/漲跌)
  out/tw_themes_ranked.json                (台股族群：依對應美股板塊漲跌加權後排序)
  out/tw_theme_constituents.json           (台股族群 -> 個股清單)
  out/us_sector_to_tw_picks.json           (美股板塊 -> 台股族群 -> 台股個股)
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
import logging

import yfinance as yf

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SectorQuote:
    ticker: str
    name: str
    price: float
    change: float
    change_pct: float


def read_csv(path: Path, encoding: str = "utf-8-sig") -> List[dict]:
    """讀取 CSV 檔案"""
    with path.open("r", encoding=encoding, newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, header: List[str], rows: List[dict]) -> None:
    """寫入 CSV 檔案"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in header})
    logger.info(f"✅ 已儲存: {path}")


def write_json(path: Path, obj) -> None:
    """寫入 JSON 檔案"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"✅ 已儲存: {path}")


def fetch_sector_quotes(sector_tickers: List[str]) -> Dict[str, SectorQuote]:
    """
    用 yfinance 抓 ticker 的即時/延遲報價資訊。
    
    Args:
        sector_tickers: 美股板塊 ETF 代碼列表
        
    Returns:
        {ticker: SectorQuote} 的字典
    """
    quotes: Dict[str, SectorQuote] = {}
    
    logger.info(f"🔍 正在抓取 {len(sector_tickers)} 檔美股板塊 ETF 報價...")

    # 用 fast_info 方法取得快速報價 (更穩定)
    for t in sector_tickers:
        try:
            ticker_obj = yf.Ticker(t)
            info = ticker_obj.fast_info
            
            price = float(info.get("last_price", 0.0) or 0.0)
            prev = float(info.get("previous_close", 0.0) or 0.0)
            
            # 如果 fast_info 無資料，嘗試 history
            if price == 0.0:
                hist = ticker_obj.history(period='5d', interval='1d')
                if not hist.empty:
                    price = float(hist['Close'].iloc[-1])
                    prev = float(hist['Close'].iloc[-2]) if len(hist) >= 2 else price
            
            change = price - prev
            change_pct = (change / prev * 100.0) if prev else 0.0
            
            name = info.get("longName") or info.get("shortName") or t
            
            quotes[t] = SectorQuote(
                ticker=t,
                name=name,
                price=round(price, 4),
                change=round(change, 4),
                change_pct=round(change_pct, 4),
            )
            logger.info(f"  ✓ {t:6s} {name:30s} {price:8.2f} {change_pct:+7.2f}%")
        except Exception as e:
            logger.warning(f"  ⚠️  {t} 抓取失敗: {e}")
            # 最弱容錯：至少不讓整支程式掛掉
            quotes[t] = SectorQuote(ticker=t, name=t, price=0.0, change=0.0, change_pct=0.0)

    return quotes


def main() -> int:
    p = argparse.ArgumentParser(description="美股板塊 -> 台股族群/個股熱力圖產生器")
    p.add_argument("--us2tw", default="mappings/us_sector_to_tw_theme.csv", 
                   help="美股板塊->台股族群對應表")
    p.add_argument("--twlist", default="mappings/tw_theme_to_stocks.csv",
                   help="台股族群->個股對應表")
    p.add_argument("--outdir", default="out",
                   help="輸出目錄")
    args = p.parse_args()

    logger.info(f"📁 輸入檔案:")
    logger.info(f"   美股->台股: {args.us2tw}")
    logger.info(f"   台股族群->個股: {args.twlist}")
    
    us2tw = read_csv(Path(args.us2tw))
    twlist = read_csv(Path(args.twlist))
    outdir = Path(args.outdir)

    # 1) 建立 mapping：us_sector_ticker -> list(tw_theme)
    us_to_tw: Dict[str, List[str]] = {}
    us_sector_name: Dict[str, str] = {}
    for r in us2tw:
        us_t = (r.get("us_sector_ticker") or "").strip().upper()
        us_n = (r.get("us_sector_name") or "").strip()
        tw   = (r.get("tw_theme") or "").strip()
        if not us_t:
            continue
        us_to_tw.setdefault(us_t, [])
        if tw and tw not in us_to_tw[us_t]:
            us_to_tw[us_t].append(tw)
        if us_n:
            us_sector_name[us_t] = us_n

    sector_tickers = sorted(us_to_tw.keys())
    if not sector_tickers:
        raise SystemExit("❌ 未找到美股板塊代碼，請檢查 us_sector_to_tw_theme.csv")

    logger.info(f"📊 已載入 {len(sector_tickers)} 檔美股板塊 ETF")

    # 2) 抓美股板塊ETF報價
    logger.info(f"\n🔄 抓取美股板塊行情...")
    quotes = fetch_sector_quotes(sector_tickers)

    # 輸出美股板塊行情
    us_rows = []
    for t in sector_tickers:
        q = quotes[t]
        us_rows.append({
            "us_sector_ticker": q.ticker,
            "us_sector_name": us_sector_name.get(t, q.name),
            "price": q.price,
            "change": q.change,
            "change_pct": q.change_pct,
        })
    us_rows.sort(key=lambda r: float(r["change_pct"]), reverse=True)
    write_csv(outdir / "us_sector_quotes.csv",
              ["us_sector_ticker", "us_sector_name", "price", "change", "change_pct"],
              us_rows)

    # 3) 台股族群 -> 個股
    logger.info(f"\n📋 載入台股族群->個股對應...")
    tw_theme_to_stocks: Dict[str, List[dict]] = {}
    for r in twlist:
        theme = (r.get("tw_theme") or r.get("產業分類") or "").strip()
        code  = (r.get("stock_code") or r.get("股票代碼") or "").strip()
        name  = (r.get("stock_name") or r.get("股票名稱") or "").strip()
        if not theme or not code:
            continue
        tw_theme_to_stocks.setdefault(theme, [])
        tw_theme_to_stocks[theme].append({"stock_code": code, "stock_name": name})

    logger.info(f"   已載入 {len(tw_theme_to_stocks)} 個台股族群，共 {sum(len(s) for s in tw_theme_to_stocks.values())} 檔個股")
    
    write_json(outdir / "tw_theme_constituents.json", tw_theme_to_stocks)

    # 4) 美股板塊 -> 台股族群 -> 台股個股（最終輸出）
    logger.info(f"\n🔗 建立美股板塊 -> 台股族群 -> 個股對應...")
    us_to_tw_picks = []
    for t in sector_tickers:
        q = quotes[t]
        themes = us_to_tw.get(t, [])
        us_to_tw_picks.append({
            "us_sector": {
                "ticker": t,
                "name": us_sector_name.get(t, q.name),
                "price": q.price,
                "change": q.change,
                "change_pct": q.change_pct,
            },
            "tw_themes": [
                {
                    "tw_theme": theme,
                    "stocks": tw_theme_to_stocks.get(theme, [])
                }
                for theme in themes
            ]
        })

    # 5) 族群熱度排行（用對應到的美股板塊漲跌來給分）
    # 一個族群可能被多個板塊指到，這裡用「max change_pct」當族群熱度分數
    logger.info(f"\n🔥 計算台股族群熱度排行...")
    theme_score: Dict[str, float] = {}
    theme_sources: Dict[str, List[dict]] = {}
    for item in us_to_tw_picks:
        us = item["us_sector"]
        for tw in item["tw_themes"]:
            theme = tw["tw_theme"]
            score = float(us["change_pct"])
            theme_score[theme] = max(theme_score.get(theme, -1e9), score)
            theme_sources.setdefault(theme, []).append({
                "us_sector_ticker": us["ticker"],
                "us_sector_name": us["name"],
                "change_pct": score
            })

    ranked = []
    for theme, score in sorted(theme_score.items(), key=lambda x: x[1], reverse=True):
        ranked.append({
            "tw_theme": theme,
            "score_change_pct": round(score, 4),
            "sources": sorted(theme_sources.get(theme, []), key=lambda r: r["change_pct"], reverse=True),
            "stock_count": len(tw_theme_to_stocks.get(theme, [])),
        })

    write_json(outdir / "us_sector_to_tw_picks.json", us_to_tw_picks)
    write_json(outdir / "tw_themes_ranked.json", ranked)

    # 6) 輸出摘要
    logger.info(f"\n" + "="*70)
    logger.info(f"✅ 熱力圖生成完成！")
    logger.info(f"="*70)
    logger.info(f"📊 統計:")
    logger.info(f"   美股板塊 ETF: {len(sector_tickers)} 檔")
    logger.info(f"   台股族群: {len(tw_theme_to_stocks)} 個")
    logger.info(f"   台股個股: {sum(len(s) for s in tw_theme_to_stocks.values())} 檔")
    logger.info(f"\n📁 輸出檔案位置: {outdir.resolve()}")
    logger.info(f"   - us_sector_quotes.csv (美股板塊行情)")
    logger.info(f"   - us_sector_to_tw_picks.json (美股->台股完整對應)")
    logger.info(f"   - tw_themes_ranked.json (台股族群熱度排行)")
    logger.info(f"   - tw_theme_constituents.json (台股族群->個股清單)")
    logger.info(f"="*70)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
