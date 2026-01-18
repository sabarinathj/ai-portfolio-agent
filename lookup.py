import requests
from duckduckgo_search import DDGS

def search_mutual_fund(query):
    """Searches for Mutual Fund Scheme Codes via MFAPI"""
    print(f"\n🔎 Searching for Mutual Fund: '{query}'...")
    try:
        url = f"https://api.mfapi.in/mf/search?q={query}"
        response = requests.get(url).json()
        
        if not response:
            print("❌ No funds found.")
            return

        # Improved UX: Show up to 20 results to capture Direct/Regular/Growth variations
        limit = 20
        funds_to_show = response[:limit]

        print(f"✅ Found {len(response)} matches (Showing top {len(funds_to_show)}):")
        print("-" * 90)
        print(f"{'CODE':<10} | {'SCHEME NAME'}")
        print("-" * 90)
        
        for fund in funds_to_show:
            print(f"{fund['schemeCode']:<10} | {fund['schemeName']}")
            
        if len(response) > limit:
            print(f"... and {len(response) - limit} more. Try a more specific search query.")
            
    except Exception as e:
        print(f"Error: {e}")

def search_stock_symbol(query):
    """
    Uses DuckDuckGo to find the Yahoo Finance ticker.
    This is a 'hack' because yfinance doesn't have a built-in search.
    """
    print(f"\n🔎 Searching for Stock Symbol: '{query}'...")
    search_query = f"yahoo finance ticker symbol {query} india"
    
    try:
        results = DDGS().text(keywords=search_query, region="in-en", max_results=3)
        print("✅ Possible Tickers (Look for .NS or .BO):")
        print("-" * 90)
        for r in results:
            print(f"Title: {r['title']}")
            print(f"Link:  {r['href']}")
            print("-" * 40)
    except Exception as e:
        print(f"Error: {e}")

# --- User Interface ---
if __name__ == "__main__":
    print("="*40)
    print(" FINANCIAL ASSET LOOKUP TOOL")
    print("="*40)
    
    while True:
        print("\nWhat do you want to find?")
        print("1: Mutual Fund Scheme Code")
        print("2: Stock Ticker Symbol (.NS)")
        print("q: Quit")
        
        choice = input("Enter choice: ")
        
        if choice == '1':
            q = input("Enter Mutual Fund Name (e.g., 'Parag Parikh Flexi'): ")
            search_mutual_fund(q)
        elif choice == '2':
            q = input("Enter Stock Name (e.g., 'Tata Motors'): ")
            search_stock_symbol(q)
        elif choice.lower() == 'q':
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again.")