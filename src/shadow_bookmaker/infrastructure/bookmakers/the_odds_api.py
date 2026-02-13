from typing import List
from src.shadow_bookmaker.infrastructure.bookmakers.base import BaseBookmaker
from src.shadow_bookmaker.infrastructure.network import AsyncNetworkEngine
from src.shadow_bookmaker.domain.models import OddsDTO
from src.shadow_bookmaker.config import settings

class TheOddsAPIBookmaker(BaseBookmaker):
    def __init__(self, mapper):
        super().__init__(mapper)
        self.network = AsyncNetworkEngine()

    @property
    def name(self) -> str: return "TheOddsAPI"
    
    async def fetch_odds(self) -> List[OddsDTO]:
        if not settings.ODDS_API_KEY:
            return []
            
        # 🎯 核心修复 1：改为官方节点 'upcoming'，跨越所有体育类型，抓取全球即刻开打的赛事
        url = "https://api.the-odds-api.com/v4/sports/upcoming/odds"
        params = {
            "apiKey": settings.ODDS_API_KEY,
            "regions": "eu,uk", # 🎯 核心修复 2：扩大侦测区域，包含欧洲和英国大盘
            "markets": "h2h"
        }
        
        try:
            print("\n📡 [系统日志] 正在向外网大盘发射穿透请求...")
            data = await self.network.fetch_json(url, params=params)
        except Exception as e:
            print(f"🚨 [网络层拦截] 抓取失败 (请查看这里打印的报错原因): {e}")
            return []

        results = []
        for match in data:
            home_raw = match.get("home_team", "")
            away_raw = match.get("away_team", "")
            if not home_raw or not away_raw: continue
            
            home_team = self.mapper.standardize(home_raw)
            away_team = self.mapper.standardize(away_raw)
            
            # 让 UI 显示体育类别（如 [basketball_nba] 湖人 vs 勇士）
            sport_title = match.get("sport_title", "Unknown")
            match_id = f"[{sport_title}] {home_team} vs {away_team}"

            bookmakers = match.get("bookmakers", [])
            if not bookmakers: continue
            
            # 🎯 核心修复 3：智能降级替补！优先找平博，如果平博未开盘，抓取第一家顶级大庄兜底
            target_bookie = next((b for b in bookmakers if b["key"] == "pinnacle"), bookmakers[0])
            bookie_title = target_bookie.get("title", "Unknown Bookie")

            for market in target_bookie.get("markets", []):
                if market["key"] == "h2h":
                    h_odds = a_odds = d_odds = 0.0
                    for outcome in market["outcomes"]:
                        if outcome["name"] == home_raw: h_odds = outcome["price"]
                        elif outcome["name"] == away_raw: a_odds = outcome["price"]
                        elif outcome["name"].lower() == "draw": d_odds = outcome["price"]
                        
                    if h_odds > 1.0 and a_odds > 1.0:
                        results.append(OddsDTO(
                            bookmaker=bookie_title, match_id=match_id,
                            home_team=home_team, away_team=away_team,
                            home_odds=h_odds, away_odds=a_odds, 
                            draw_odds=d_odds if d_odds > 1.0 else None
                        ))
        print(f"✅ [情报解密成功] 成功截获 {len(results)} 场真实比赛数据！\n")
        return results