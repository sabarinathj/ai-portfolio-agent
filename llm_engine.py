# Handles the AI logic separately.
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_portfolio_report(market_data):
    """
    Takes the structured market data and sends it to the LLM for analysis.
    """
    # IMPROVED PROMPT: Asking for depth instead of brevity
    system_prompt = """
    You are a Senior Investment Strategist. 
    Input: JSON list of assets with price, change %, and news context.
    
    Output Format:
    Return a JSON Object with a single key "analysis" containing a list of objects.
    
    Style Guide:
    - **Reason:** Write a detailed 2-3 sentence explanation. Connect the news to the stock price. 
    - **Danger:** Output ONLY one of these labels: "SAFE", "CAUTION", "CRITICAL". 
    - **Outlook:** Provide a specific prediction (e.g., "Expect volatility due to upcoming earnings").
    
    Example JSON Structure:
    {
      "analysis": [
        {
          "asset": "Name",
          "reason": "Detailed explanation here...",
          "danger": "CAUTION",
          "outlook": "Bearish short-term"
        }
      ]
    }
    """
    
    user_data_str = json.dumps(market_data)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_data_str}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        parsed = json.loads(content)
        
        if "analysis" in parsed:
            return parsed["analysis"]
        elif isinstance(parsed, list):
            return parsed
        else:
            return list(parsed.values())[0]
            
    except Exception as e:
        return [{"asset": "Error", "reason": f"AI Generation Failed: {str(e)}", "danger": "ERR", "outlook": "ERR"}]