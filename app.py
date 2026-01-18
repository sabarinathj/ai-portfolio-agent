# This is main file. This file will use your existing tools.py for searching and fetching data, but it will wrap the logic in a nice visual interface.
import streamlit as st
import pandas as pd
from tools import search_assets_tool, get_market_data, get_news_for_volatility
from llm_engine import generate_portfolio_report

# --- PAGE CONFIG ---
st.set_page_config(page_title="Agentic Portfolio", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

# --- CALLBACK FUNCTIONS ---
def add_to_portfolio(item):
    # Prevent duplicates
    if not any(d['id'] == item['id'] for d in st.session_state.portfolio):
        st.session_state.portfolio.append(item)
        st.toast(f"Added {item['name']}", icon="✅")
    else:
        st.toast(f"Already in list", icon="⚠️")

def remove_from_portfolio(index):
    item = st.session_state.portfolio.pop(index)
    st.toast(f"Removed {item['name']}", icon="🗑️")

def perform_search():
    query = st.session_state.search_query
    if query:
        # Reset results while searching
        st.session_state.search_results = []
        with st.spinner(f"Searching markets for '{query}'..."):
            results = search_assets_tool(query)
            st.session_state.search_results = results

def clear_search():
    st.session_state.search_query = ""
    st.session_state.search_results = []

# --- MAIN UI ---
st.title("🤖 Agentic Portfolio Analyst")

# 1. SEARCH SECTION
with st.expander("🔎 Add Assets (Stocks & Mutual Funds)", expanded=True):
    # FIX: vertical_alignment="bottom" ensures button aligns with text box
    col1, col2, col3 = st.columns([6, 1, 1], vertical_alignment="bottom")
    
    with col1:
        st.text_input(
            "Search Asset", 
            key="search_query", 
            placeholder="e.g., Motilal Oswal, Tata Motors...", 
            on_change=perform_search
        )
    with col2:
        st.button("Search", on_click=perform_search, use_container_width=True)
    with col3:
        st.button("Clear", on_click=clear_search, use_container_width=True)

    # Scrollable Results Container (Fixed Height)
    if st.session_state.search_results:
        st.caption(f"Found {len(st.session_state.search_results)} results:")
        
        with st.container(height=300):
            for item in st.session_state.search_results:
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.write(f"**{item['name']}**")
                with c2:
                    if item['type'] == "STOCK":
                        st.markdown(":chart: `STOCK`")
                    else:
                        st.markdown(":bank: `MF`")
                with c3:
                    st.button("Add", key=f"add_{item['id']}", on_click=add_to_portfolio, args=(item,))

# 2. WATCHLIST SECTION
st.divider()
st.subheader("📋 Your Watchlist")

if not st.session_state.portfolio:
    st.info("Your watchlist is empty. Search and add assets above.")
else:
    # Header
    h1, h2, h3 = st.columns([3, 1, 1])
    h1.markdown("**Asset Name**")
    h2.markdown("**Type**")
    h3.markdown("**Action**")
    
    for i, item in enumerate(st.session_state.portfolio):
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            st.write(item['name'])
        with c2:
            st.caption(item['type'])
        with c3:
            st.button("❌", key=f"del_{i}", on_click=remove_from_portfolio, args=(i,))

    # 3. ANALYSIS BUTTON
    st.divider()
    if st.button("🚀 Analyze Portfolio Now", type="primary", use_container_width=True):
        
        # Step 1: Fetch Data
        progress_text = "Fetching live market data..."
        my_bar = st.progress(0, text=progress_text)
        
        raw_data = get_market_data(st.session_state.portfolio)
        
        # Step 2: Enrich with News
        enriched_data = []
        total = len(raw_data)
        
        for idx, asset in enumerate(raw_data):
            my_bar.progress(int((idx / total) * 50) + 50, text=f"Analyzing news for {asset['asset']}...")
            
            news = get_news_for_volatility(asset['asset'], asset.get('change', 0))
            asset['news_context'] = news
            enriched_data.append(asset)
            
        my_bar.empty()
        
        # Step 3: LLM Analysis
        with st.spinner("🧠 AI Analyst is writing the report... (This uses GPT-4o)"):
            final_report = generate_portfolio_report(enriched_data)
        
        # --- NEW UI: INTELLIGENCE CARDS ---
        st.subheader("📈 Intelligence Report")
        
        # Check if we have valid data to loop through
        if not final_report or isinstance(final_report, dict) and "error" in final_report:
             st.error("Analysis failed. Please try again.")
        else:
            for item in final_report:
                # Create a card for each asset
                with st.container(border=True):
                    # Header Row: Name | Risk Badge | Outlook
                    c1, c2, c3 = st.columns([3, 1, 2])
                    
                    with c1:
                        st.markdown(f"### {item.get('asset', 'Unknown Asset')}")
                    
                    with c2:
                        # Dynamic Badge Color
                        risk = item.get('danger', 'UNKNOWN').upper()
                        if "SAFE" in risk:
                            st.markdown(":green-background[SAFE]")
                        elif "CAUTION" in risk:
                            st.markdown(":orange-background[CAUTION]")
                        elif "CRITICAL" in risk:
                            st.markdown(":red-background[CRITICAL]")
                        else:
                            st.markdown(f":grey-background[{risk}]")
                            
                    with c3:
                        st.markdown(f"**Outlook:** {item.get('outlook', 'N/A')}")
                    
                    # Detailed Reason Row (Full width, no cropping)
                    st.markdown("**Market Driver:**")
                    st.info(item.get('reason', 'No details provided.'))