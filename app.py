import streamlit as st
import base64
import os
import time
from dotenv import load_dotenv
from openai import OpenAI
from brightdata import bdclient  # Bright Data Python SDK

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BRIGHT_DATA_API_KEY = os.getenv("BRIGHT_DATA_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
bd = bdclient(api_token=BRIGHT_DATA_API_KEY)

# --- UI CONFIG ---
st.set_page_config(
    page_title="AI Lead Generation Agent",
    page_icon="D",
    layout="wide"
)

with st.sidebar:
    with open("./assets/bright-data-logo.png", "rb") as f:
        bright_logo = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <div style="text-align: center;">
            <img src="data:image/png;base64,{bright_logo}" style="height: 100px;"/>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### AI Assistant")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_message = st.chat_input("Describe the leads you want...")

    if user_message:
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        ai_response = f"🤖 Got it! I’ll look for: **{user_message}**"
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})

    run_agent = st.button("Run AI Agent 🚀")


# --- FUNCTIONS ---
def parse_query_to_filters(query: str):
    """Use OpenAI to turn natural language into structured filters."""
    prompt = f"""
    Convert this lead search request into structured JSON filters:
    "{query}"

    Example output:
    {{
      "role": "Marketing Manager",
      "industry": "Fintech",
      "location": "Kenya"
    }}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are an expert lead generation assistant."},
                  {"role": "user", "content": prompt}],
        temperature=0
    )
    filters_text = response.choices[0].message.content.strip()
    try:
        filters = eval(filters_text)  
    except:
        filters = {"query": query}
    return filters


def fetch_leads_from_brightdata(filters: dict):
    """Fetch real leads with Bright Data (example using LinkedIn search)."""
    keyword = filters.get("role", "") + " " + filters.get("industry", "")
    location = filters.get("location", "")

    # Use LinkedIn Jobs scraper
    result = bd.search_linkedin.jobs(
        keyword=keyword or "Software Engineer",
        location=location or "Kenya",
        country="KE",
        time_range="Past month",
        job_type="Full-time"
    )

    leads = bd.parse_content(result)
    return leads if isinstance(leads, list) else [leads]


def enrich_leads_with_ai(leads: list):
    """Use OpenAI to enrich, score, and generate outreach strategy."""
    enriched = []
    for lead in leads[:10]:  
        profile_text = f"{lead.get('title', '')} at {lead.get('company', '')}, Location: {lead.get('location', '')}"

        prompt = f"""
        Analyze this lead and return JSON with:
        - summary (1 sentence about their background)
        - score (1-10 relevance score)
        - outreach (best way to contact)

        Lead: {profile_text}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You enrich leads for sales teams."},
                      {"role": "user", "content": prompt}],
            temperature=0.5
        )

        try:
            enriched_data = eval(response.choices[0].message.content.strip())
        except:
            enriched_data = {
                "summary": "No summary",
                "score": 5,
                "outreach": "Send LinkedIn message"
            }

        enriched.append({
            "role": lead.get("title", "Unknown"),
            "company": lead.get("company", "Unknown"),
            "location": lead.get("location", "Unknown"),
            "summary": enriched_data["summary"],
            "score": enriched_data["score"],
            "outreach": enriched_data["outreach"],
        })
    return enriched


# --- MAIN APP ---
st.title("AI-Powered Lead Generation Agent")

if run_agent and st.session_state.chat_history:
    last_query = st.session_state.chat_history[-2]["content"] if len(st.session_state.chat_history) >= 2 else st.session_state.chat_history[-1]["content"]

    st.info("🤖 Parsing query into filters...")
    filters = parse_query_to_filters(last_query)
    st.json(filters)

    st.info("🔍 Fetching leads from Bright Data...")
    leads = fetch_leads_from_brightdata(filters)

    if not leads:
        st.error("No leads found.")
    else:
        st.success(f"Found {len(leads)} leads. Enriching with AI...")
        enriched_leads = enrich_leads_with_ai(leads)

        st.subheader("AI-Enriched Leads")
        for lead in enriched_leads:
            st.markdown(
                f"""
                <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                    <h4>{lead['role']} @ {lead['company']}</h4>
                    <p><b>Location:</b> {lead['location']}</p>
                    <p><b>Summary:</b> {lead['summary']}</p>
                    <p><b>AI Lead Score:</b> {lead['score']}/10</p>
                    <p><b>Suggested Outreach:</b> {lead['outreach']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
