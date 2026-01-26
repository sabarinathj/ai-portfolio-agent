import requests
import yfinance as yf
from duckduckgo_search import DDGS

def search_assets_tool(query):
    """
    Searches for Stocks (via Yahoo Finance API) and Mutual Funds (via MFAPI).
    """
    results = []
    
    # --- 1. SEARCH STOCKS (Fixed: Using Yahoo Typeahead API) ---
    # This is the official-ish endpoint Yahoo uses for its own search bar.
    # It returns structured JSON, so no more brittle scraping.
    try:
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        headers = {'User-Agent': 'Mozilla/5.0'} # Required to avoid 403 error
        params = {
            'q': query,
            'quotesCount': 10,
            'newsCount': 0,
            'enableFuzzyQuery': 'false',
            'quotesQueryId': 'tss_match_phrase_query'
        }
        
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        
        if 'quotes' in data:
            for item in data['quotes']:
                # Filter strictly for Indian Exchanges (NSE/BSE)
                # 'exchDisp' usually contains 'NSE' or 'BSE'
                exchange = item.get('exchDisp', '').upper()
                symbol = item.get('symbol', '')
                
                # Check if it is an Indian Equity
                if (exchange in ['NSE', 'BSE'] or symbol.endswith('.NS') or symbol.endswith('.BO')) and item.get('quoteType') == 'EQUITY':
                    results.append({
                        "name": item.get('shortname', symbol),
                        "id": symbol, # This will be something like 'RELIANCE.NS'
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