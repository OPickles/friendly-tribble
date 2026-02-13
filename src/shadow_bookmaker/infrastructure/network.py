import httpx
from tenacity import retry, wait_exponential, stop_after_attempt
from src.shadow_bookmaker.config import settings

class AsyncNetworkEngine:
    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
    async def fetch_json(self, url: str, headers: dict = None, params: dict = None) -> dict:
        # 🔐 增加 verify=False 绕过本地可能缺乏根证书导致的 SSL 拦截
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT, verify=False) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()