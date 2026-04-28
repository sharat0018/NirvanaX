"""
NirvanaX — Indian Stock Market Data Service
Dual-source architecture:
  - Groww API: Live quotes, trending stocks, market indices (real-time)
  - Indian Stock Market API (indianapi.in): Historical data, news, financials,
    analyst views, shareholding patterns, corporate actions, IPO data, mutual funds
    Key: sk-live-da2fVvmWowzpXZahuDJunpTn9b6bX168rx749tmC
    Base: https://stock.indianapi.in
"""

import httpx
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── Groww API (live quotes) ───────────────────────────────────────────────────
try:
    from growwapi import GrowwAPI
    _GROWW_AVAILABLE = True
except ImportError:
    _GROWW_AVAILABLE = False

# ── Indian Stock Market API ───────────────────────────────────────────────────
INDIAN_API_KEY = os.getenv("INDIAN_API_KEY", "sk-live-da2fVvmWowzpXZahuDJunpTn9b6bX168rx749tmC")
INDIAN_API_BASE = "https://stock.indianapi.in"
INDIAN_API_HEADERS = {"x-api-key": INDIAN_API_KEY}


# ══════════════════════════════════════════════════════════════════════════════
# INDIAN STOCK MARKET API — Rich data layer
# ══════════════════════════════════════════════════════════════════════════════

async def _indian_api_get(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """Generic GET for Indian Stock Market API with error handling."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{INDIAN_API_BASE}{endpoint}",
                headers=INDIAN_API_HEADERS,
                params=params or {},
            )
            if resp.status_code == 200:
                return resp.json()
            print(f"[IndianAPI] {endpoint} → HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print(f"[IndianAPI] {endpoint} error: {e}")
    return None


async def get_stock_details(symbol: str) -> Optional[Dict]:
    """Full stock details — price, financials, key metrics, analyst views."""
    return await _indian_api_get("/stock", {"name": symbol})


async def get_stock_news(symbol: str) -> Optional[List]:
    """Recent news articles for a stock."""
    data = await _indian_api_get("/news", {"stock_name": symbol})
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data", data.get("news", []))
    return []


async def get_historical_data_indian(symbol: str, period: str = "1m") -> Optional[Dict]:
    """
    Historical OHLCV data.
    period options: 1w, 1m, 3m, 6m, 1y, 3y, 5y
    """
    return await _indian_api_get("/historical_data", {"stock_name": symbol, "filter": period, "period": period})


async def get_stock_forecasts(symbol: str) -> Optional[Dict]:
    """Analyst forecasts and price targets."""
    return await _indian_api_get("/stock_forecasts", {"stock_name": symbol})


async def get_stock_target_price(symbol: str) -> Optional[Dict]:
    """Analyst target prices."""
    return await _indian_api_get("/stock_target_price", {"stock_name": symbol})


async def get_corporate_actions(symbol: str) -> Optional[Dict]:
    """Dividends, splits, bonuses, rights issues."""
    return await _indian_api_get("/corporate_actions", {"stock_name": symbol})


async def get_recent_announcements(symbol: str) -> Optional[Dict]:
    """Recent BSE/NSE announcements."""
    return await _indian_api_get("/recent_announcements", {"stock_name": symbol})


async def get_trending_indian() -> Optional[List]:
    """Trending stocks from Indian API."""
    data = await _indian_api_get("/trending")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data", data.get("trending", []))
    return []


async def get_nse_most_active_indian() -> Optional[List]:
    """NSE most active stocks."""
    data = await _indian_api_get("/NSE_most_active")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data", [])
    return []


async def get_bse_most_active_indian() -> Optional[List]:
    """BSE most active stocks."""
    data = await _indian_api_get("/BSE_most_active")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data", [])
    return []


async def get_mutual_funds_indian(search: Optional[str] = None) -> Optional[List]:
    """Mutual funds data."""
    params = {"search": search} if search else {}
    data = await _indian_api_get("/mutual_funds", params)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data", [])
    return []


async def get_ipo_data() -> Optional[List]:
    """IPO data — upcoming, ongoing, listed."""
    data = await _indian_api_get("/ipo")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data", [])
    return []


async def get_price_shockers() -> Optional[List]:
    """Stocks with significant price movements."""
    data = await _indian_api_get("/price_shockers")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data", [])
    return []


async def get_52_week_high_low(symbol: str) -> Optional[Dict]:
    """52-week high/low data."""
    return await _indian_api_get("/fetch_52_week_high_low_data", {"stock_name": symbol})


async def get_historical_stats(symbol: str) -> Optional[Dict]:
    """Historical statistics."""
    return await _indian_api_get("/historical_stats", {"stock_name": symbol})


# ══════════════════════════════════════════════════════════════════════════════
# COMBINED SERVICE CLASS (backward compatible with existing routes.py)
# ══════════════════════════════════════════════════════════════════════════════

class GrowwAPIService:
    """
    Combined Indian stock data service.
    Groww: live quotes, indices, trending (real-time)
    Indian API: historical, news, financials, analyst views, corporate actions
    """

    def __init__(self):
        self.api_token = os.getenv("GROWW_API_KEY")
        self.instruments_cache = None
        self._groww = None
        if _GROWW_AVAILABLE and self.api_token:
            try:
                from growwapi import GrowwAPI
                self._groww = GrowwAPI(self.api_token)
            except Exception as e:
                print(f"Groww init error: {e}")
        print("Ready to Groww!")

    # ── Live quotes (Groww primary, Indian API fallback) ──────────────────────

    async def get_stock_quote(self, symbol: str) -> Optional[Dict]:
        """Live stock quote — Groww primary."""
        if self._groww:
            try:
                response = self._groww.get_quote(
                    trading_symbol=symbol.upper(),
                    exchange=self._groww.EXCHANGE_NSE,
                    segment=self._groww.SEGMENT_CASH,
                )
                return {
                    "symbol": symbol.upper(),
                    "name": symbol.upper(),
                    "price": float(response.get("last_price", 0)),
                    "change": float(response.get("day_change", 0)),
                    "change_percent": float(response.get("day_change_perc", 0)),
                    "volume": int(response.get("volume", 0)),
                    "high": float(response.get("high", 0)),
                    "low": float(response.get("low", 0)),
                    "open": float(response.get("open", 0)),
                }
            except Exception as e:
                print(f"Groww API Error for {symbol}: {e}")

        # Fallback: Indian API stock details
        data = await get_stock_details(symbol)
        if data:
            price_data = data.get("currentPrice", data.get("price", {}))
            if isinstance(price_data, dict):
                price = float(price_data.get("BSE", price_data.get("NSE", 0)))
            else:
                price = float(price_data or 0)
            return {
                "symbol": symbol.upper(),
                "name": data.get("companyName", symbol.upper()),
                "price": price,
                "change": 0.0,
                "change_percent": float(data.get("percentChange", 0)),
                "volume": 0,
                "source": "indian_api",
            }
        return None

    # ── Historical data (Indian API — Groww doesn't support this tier) ────────

    async def get_historical_data(self, symbol: str, days: int = 30) -> List[Dict]:
        """
        Historical price data via Indian Stock Market API /historical_data endpoint.
        filter param accepts: 'default' (price history), 'pe', 'pb', 'roe', 'roce'
        """
        # Indian API /historical_data requires both period AND filter params
        # period: 1m, 6m, 1yr, 3yr, 5yr, 10yr, max
        # filter: default, price, pe, sm, evebitda, ptb, mcs
        period_map = {7: "1m", 30: "1m", 90: "6m", 180: "6m", 365: "1yr"}
        period = "1m"
        for d_days, p in sorted(period_map.items()):
            if days <= d_days:
                period = p
                break

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    f"{INDIAN_API_BASE}/historical_data",
                    headers=INDIAN_API_HEADERS,
                    params={"stock_name": symbol, "period": period, "filter": "default"}
                )
                if r.status_code == 200:
                    d = r.json()
                    candles = []
                    # Response can be dict with datasets or direct list
                    # Response: {"datasets": [{"metric": "Price", "values": [["date", "price"], ...]}, ...]}
                    # Extract Price dataset only (skip DMA50, DMA200, Volume)
                    datasets = d.get("datasets", []) if isinstance(d, dict) else []
                    for dataset in datasets:
                        if isinstance(dataset, dict) and dataset.get("metric") == "Price":
                            for val in dataset.get("values", []):
                                if isinstance(val, list) and len(val) >= 2:
                                    try:
                                        candles.append({
                                            "date": str(val[0]),
                                            "close": float(str(val[1]).replace(",", "")),
                                        })
                                    except (ValueError, TypeError):
                                        continue
                            break  # Only need Price dataset
                    if candles:
                        return candles
                else:
                    print(f"[IndianAPI/historical] HTTP {r.status_code}: {r.text[:80]}")
        except Exception as e:
            print(f"[IndianAPI/historical] {e}")

        # Fallback: extract from /stock stockTechnicalData
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    f"{INDIAN_API_BASE}/stock",
                    headers=INDIAN_API_HEADERS,
                    params={"name": symbol}
                )
                if r.status_code == 200:
                    d = r.json()
                    tech = d.get("stockTechnicalData", {})
                    if isinstance(tech, dict):
                        # Build synthetic candles from available price points
                        candles = []
                        price_data = d.get("currentPrice", {})
                        if isinstance(price_data, dict):
                            price = float(price_data.get("NSE", price_data.get("BSE", 0)) or 0)
                            if price > 0:
                                candles.append({"date": "current", "close": price})
                        return candles
        except Exception as e:
            print(f"[IndianAPI/historical_fallback] {e}")

        return []

    # ── Rich data methods (Indian API) ────────────────────────────────────────

    async def get_stock_full_details(self, symbol: str) -> Optional[Dict]:
        """Full stock details including financials, metrics, analyst views."""
        return await get_stock_details(symbol)

    async def get_stock_news(self, symbol: str) -> List[Dict]:
        """Recent news for a stock."""
        return await get_stock_news(symbol) or []

    async def get_analyst_views(self, symbol: str) -> Optional[Dict]:
        """Analyst forecasts and target prices."""
        forecasts = await get_stock_forecasts(symbol)
        targets = await get_stock_target_price(symbol)
        return {"forecasts": forecasts, "targets": targets}

    async def get_corporate_actions(self, symbol: str) -> Optional[Dict]:
        """Dividends, splits, bonuses."""
        return await get_corporate_actions(symbol)

    async def get_announcements(self, symbol: str) -> Optional[Dict]:
        """Recent BSE/NSE announcements."""
        return await get_recent_announcements(symbol)

    async def get_52_week_data(self, symbol: str) -> Optional[Dict]:
        """52-week high/low."""
        return await get_52_week_high_low(symbol)

    # ── Market data (Groww primary, Indian API fallback) ─────────────────────

    async def get_market_indices(self) -> List[Dict]:
        """NIFTY, SENSEX indices."""
        indices = []
        if self._groww:
            for symbol, name in [("NIFTY", "NIFTY 50"), ("SENSEX", "SENSEX")]:
                try:
                    r = self._groww.get_quote(
                        trading_symbol=symbol,
                        exchange=self._groww.EXCHANGE_NSE,
                        segment=self._groww.SEGMENT_CASH,
                    )
                    indices.append({
                        "name": name,
                        "value": float(r.get("last_price", 0)),
                        "change": float(r.get("day_change", 0)),
                        "change_percent": float(r.get("day_change_perc", 0)),
                    })
                except Exception as e:
                    print(f"Error fetching {symbol}: {e}")
        return indices

    async def get_trending_stocks(self) -> List[Dict]:
        """Trending stocks — Groww primary, Indian API fallback."""
        # Try Groww first
        if self._groww:
            stocks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
                      "BHARTIARTL", "ITC", "LT", "SBIN", "WIPRO"]
            trending = []
            for symbol in stocks:
                try:
                    r = self._groww.get_quote(
                        trading_symbol=symbol,
                        exchange=self._groww.EXCHANGE_NSE,
                        segment=self._groww.SEGMENT_CASH,
                    )
                    if r:
                        trending.append({
                            "name": symbol, "symbol": symbol,
                            "price": float(r.get("last_price", 0)),
                            "change_percent": float(r.get("day_change_perc", 0)),
                            "volume": int(r.get("volume", 0)),
                        })
                except Exception:
                    continue
            if trending:
                return trending

        # Fallback: Indian API trending
        data = await get_trending_indian()
        if data:
            result = []
            for item in data[:10]:
                if isinstance(item, dict):
                    result.append({
                        "name": item.get("ticker", item.get("symbol", "")),
                        "symbol": item.get("ticker", item.get("symbol", "")),
                        "price": float(item.get("price", item.get("currentPrice", 0))),
                        "change_percent": float(item.get("percentChange", item.get("change", 0))),
                        "volume": int(item.get("volume", 0)),
                    })
            return result
        return []

    async def get_nse_most_active(self) -> List[Dict]:
        """NSE most active stocks."""
        data = await get_nse_most_active_indian()
        if data:
            result = []
            for item in data[:10]:
                if isinstance(item, dict):
                    result.append({
                        "symbol": item.get("ticker", item.get("symbol", "")),
                        "price": float(item.get("price", 0)),
                        "change_percent": float(item.get("percentChange", 0)),
                        "volume": int(item.get("volume", 0)),
                    })
            return result
        return await self.get_trending_stocks()

    async def get_mutual_funds(self, category: Optional[str] = None) -> List[Dict]:
        """Mutual funds — Indian API primary, curated fallback."""
        data = await get_mutual_funds_indian()
        if data and len(data) > 0:
            funds = []
            for item in data[:20]:
                if isinstance(item, dict):
                    funds.append({
                        "id": item.get("schemeCode", item.get("id", "")),
                        "name": item.get("schemeName", item.get("name", "")),
                        "category": item.get("category", "EQUITY"),
                        "returns_1y": float(item.get("returns1yr", item.get("returns_1y", 0)) or 0),
                        "returns_3y": float(item.get("returns3yr", item.get("returns_3y", 0)) or 0),
                        "risk": item.get("riskLevel", item.get("risk", "MEDIUM")),
                        "min_investment": float(item.get("minInvestment", item.get("min_investment", 500)) or 500),
                        "expense_ratio": float(item.get("expenseRatio", item.get("expense_ratio", 1.5)) or 1.5),
                        "aum": item.get("aum", "N/A"),
                    })
            if category:
                funds = [f for f in funds if category.upper() in f["category"].upper()]
            return funds

        # Curated fallback
        funds = [
            {"id": "mf001", "name": "HDFC Equity Fund", "category": "EQUITY", "returns_1y": 12.5, "returns_3y": 15.2, "risk": "HIGH", "min_investment": 500, "expense_ratio": 1.8, "aum": "₹15,000 Cr"},
            {"id": "mf002", "name": "ICICI Liquid Fund", "category": "LIQUID", "returns_1y": 6.8, "returns_3y": 6.5, "risk": "LOW", "min_investment": 100, "expense_ratio": 0.5, "aum": "₹25,000 Cr"},
            {"id": "mf003", "name": "SBI ELSS Tax Saver", "category": "ELSS", "returns_1y": 14.2, "returns_3y": 16.8, "risk": "MEDIUM", "min_investment": 500, "expense_ratio": 1.5, "aum": "₹12,500 Cr"},
            {"id": "mf004", "name": "Axis Bluechip Fund", "category": "EQUITY", "returns_1y": 13.8, "returns_3y": 17.5, "risk": "HIGH", "min_investment": 500, "expense_ratio": 1.9, "aum": "₹18,000 Cr"},
            {"id": "mf005", "name": "Parag Parikh Flexi Cap", "category": "EQUITY", "returns_1y": 15.2, "returns_3y": 19.8, "risk": "HIGH", "min_investment": 1000, "expense_ratio": 2.1, "aum": "₹22,000 Cr"},
            {"id": "mf006", "name": "UTI Nifty Index Fund", "category": "INDEX", "returns_1y": 11.5, "returns_3y": 14.2, "risk": "MEDIUM", "min_investment": 500, "expense_ratio": 0.8, "aum": "₹10,000 Cr"},
        ]
        if category:
            return [f for f in funds if f["category"] == category.upper()]
        return funds

    async def search_stock_symbol(self, company_name: str) -> Optional[str]:
        """Search for stock symbol — Groww instruments list."""
        if not self._groww:
            return company_name.upper().replace(" ", "")
        try:
            search_term = company_name.upper().replace(" ", "")
            result = self._groww.get_instrument_by_exchange_and_trading_symbol(
                exchange=self._groww.EXCHANGE_NSE,
                trading_symbol=search_term,
            )
            if result:
                return search_term
        except Exception:
            pass

        try:
            if self.instruments_cache is None:
                self.instruments_cache = self._groww.get_all_instruments()
            search_lower = company_name.lower().replace(" ", "")
            for _, inst in self.instruments_cache.iterrows():
                if inst.get("exchange") != "NSE" or inst.get("segment") != "CASH":
                    continue
                symbol = str(inst.get("trading_symbol", "")).lower()
                company = str(inst.get("company_name", "")).lower().replace(" ", "")
                if search_lower in symbol or search_lower in company:
                    return inst.get("trading_symbol")
        except Exception as e:
            print(f"Search error: {e}")

        return company_name.upper().replace(" ", "")
