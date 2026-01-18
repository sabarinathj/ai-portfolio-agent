# This is the main file. We will use OpenAI's "Function Calling" capability. This allows the LLM to decide which tool to call and when.
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from tools import get_stock_price, get_mf_nav, search_market_news

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MY_PORTFOLIO = {
    "stocks": ["RELIANCE.NS", "TATAELXSI.NS", "HDFCBANK.NS"],
    "mutual_funds": ["122639", "118989"] 
}

# LOWERED threshold to ensure we see it working even for small moves
NEWS_TRIGGER_THRESHOLD = 0.5 

def gather_data():
    print("📊 Fetching Portfolio Data...")
    gathered_data = []

    for ticker in MY_PORTFOLIO["stocks"]:
        print(f"   > Checking {ticker}...")
        price_info = get_stock_price(ticker)
        
        if "error" in price_info:
            gathered_data.append({"asset": ticker, "error": price_info["error"]})
            continue

        change = price_info.get("change_pct", 0)
        news_summary = "Market movement is minimal; no specific news triggered."
        
        if abs(change) >= NEWS_TRIGGER_THRESHOLD:
            print(f"     ! Volatility detected ({change}%). Searching news...")
            
            # --- FIX: Clean the Ticker Name for better search results ---
            clean_name = ticker.replace(".NS", "").replace(".BO", "")
            
            # We try a very specific query first
            query = f"{clean_name} share price news reason today"
            news_raw = search_market_news(query)
            news_summary = f"News Search Results: {news_raw}"
        
        gathered_data.append({
            "type": "Stock",
            "name": ticker,
            "price": price_info["price"],
            "change": f"{change}%",
            "news_context": news_summary
        })

    for scheme_code in MY_PORTFOLIO["mutual_funds"]:
        print(f"   > Checking Fund {scheme_code}...")
        nav_info = get_mf_nav(scheme_code)
        
        if "error" in nav_info:
            gathered_data.append({"asset": scheme_code, "error": nav_info["error"]})
            continue

        gathered_data.append({
            "type": "MF",
            "name": nav_info["scheme"],
            "price": nav_info["nav"],
            "change": f"{nav_info['change_pct']}%",
            "news_context": "Mutual Funds reflect underlying portfolio changes."
        })

    return gathered_data

def generate_analysis(data):
    print("\n🧠 Agent is thinking (Synthesizing Report)...")
    
    system_instruction = """
    You are a Senior Investment Risk Analyst. 
    
    CRITICAL INSTRUCTION:
    If the 'news_context' contains actual news (e.g., earnings, government policy, contracts), 
    you MUST explicitly mention it in the 'Reason' and 'Outlook'.
    
    If the news context is empty or irrelevant, ONLY THEN use 'General market sentiment'.
    
    Output Format for each asset:
    ---
    ### [Asset Name]
    * **Rate:** [Price]
    * **Day Change:** [Percentage]
    * **Reason:** [Specific news causing the move. Be detailed.]
    * **Danger Bell:** [GREEN/ORANGE/RED. Explain why.]
    * **Outlook:** [Short term prediction based on the specific news.]
    ---
    """

    user_prompt = f"Here is the daily market data for my portfolio: {json.dumps(data)}"

    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.5
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    # Run the main flow
    data = gather_data()
    report = generate_analysis(data)
    
    print("\n" + "="*50)
    print(" DAILY PORTFOLIO INTELLIGENCE REPORT ")
    print("="*50)
    print(report)