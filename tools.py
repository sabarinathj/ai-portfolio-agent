# This file defines what your agent can do. We will give it three specific skills: checking stocks (yfinance), checking mutual funds (using the free Indian mfapi.in public API), and searching the web for news (DuckDuckGo).
import requests
import yfinance as yf
from duckduckgo_search import DDGS

def search_assets_tool(query):
    """
    Searches for Stocks (via Yahoo Finance/DDG) and Mutual Funds (via MFAPI).
    Returns a combined list of results.
    """
    results = []
    
    # --- 1. SEARCH STOCKS & ETFs (Improved Logic) ---
    # We search specifically for the Yahoo Finance URL patterns
    try:
        # Broader search query to catch ETFs and Stocks
        search_query = f"site:in.finance.yahoo.com/quote {query}"
        ddg_results = DDGS().text(keywords=search_query, region="in-en", max_results=8)
        
        for r in ddg_results:
            # URL format usually: https://in.finance.yahoo.com/quote/RELIANCE.NS/
            url = r.get('href', '')
            title = r.get('title', '')
            
            if '/quote/' in url:
                parts = url.split('/quote/')
                if len(parts) > 1:
                    # Ticker is usually the part after quote/ and before /
                    ticker = parts[1].split('/')[0]
                    
                    # Only accept Indian tickers (.NS or .BO)
                    if ".NS" in ticker or ".BO" in ticker:
                        # Clean up title for display (Remove " - Yahoo Finance" etc)
                        clean_title = title.split("Price")[0].strip().replace(" - Yahoo Finance", "")
                        
                        # Avoid duplicates
                        if not any(x['id'] == ticker for x in results):
                            results.append({
                                "name": clean_title if clean_title else ticker,
                                "id": ticker,
                                "type": "STOCK"
                            })
    except Exception as e:
        print(f"Stock search error: {e}")

    # --- 2. SEARCH MUTUAL FUNDS ---
    try:
        url = f"https://api.mfapi.in/mf/search?q={query}"
        mf_res = requests.get(url).json()
        
        # Take top 5 MF results
        for mf in mf_res[:5]:
             results.append({
                "name": mf['schemeName'],
                "id": mf['schemeCode'],
                "type": "MF"
            })
    except Exception as e:
        print(f"MF search error: {e}")
        
    return results

def get_market_data(portfolio_list):
    """
    Fetches live data for a list of assets.
    """
    gathered_data = []
    
    for item in portfolio_list:
        try:
            if item['type'] == "MF":
                # Mutual Fund Logic
                url = f"https://api.mfapi.in/mf/{item['id']}"
                resp = requests.get(url).json()
                nav_data = resp.get('data', [])
                
                if nav_data:
                    latest = float(nav_data[0]['nav'])
                    prev = float(nav_data[1]['nav'])
                    change = ((latest - prev) / prev) * 100
                    
                    gathered_data.append({
                        "asset": resp['meta']['scheme_name'],
                        "price": round(latest, 4),
                        "change": round(change, 2),
                        "id": item['id'],
                        "type": "MF"
                    })
                    
            else:
                # Stock Logic
                ticker = yf.Ticker(item['id'])
                # Get 5 days to ensure we have a previous close even after weekends/holidays
                hist = ticker.history(period="5d")
                
                if not hist.empty:
                    close_today = hist['Close'].iloc[-1]
                    close_prev = hist['Close'].iloc[-2]
                    change = ((close_today - close_prev) / close_prev) * 100
                    
                    gathered_data.append({
                        "asset": item['name'], # Use the friendly name
                        "price": round(close_today, 2),
                        "change": round(change, 2),
                        "id": item['id'],
                        "type": "STOCK"
                    })
        except Exception as e:
            gathered_data.append({"asset": item['name'], "error": str(e)})
            
    return gathered_data

def get_news_for_volatility(asset_name, change_pct):
    """
    Only searches news if volatility is high enough.
    """
    if abs(change_pct) < 0.5:
        return "Market sentiment tracking."
        
    try:
        # Clean ticker for better search (remove .NS)
        clean_name = asset_name.replace(".NS", "").replace(".BO", "")
        q = f"{clean_name} share price news reason today"
        
        results = DDGS().text(keywords=q, region="in-en", max_results=2)
        if results:
            return f"News found: {str(results)}"
        return "No specific news found."
    except:
        return "News search failed."