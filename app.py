import streamlit as st
import base64
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from brightdata import bdclient  


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BRIGHT_DATA_API_KEY = os.getenv("BRIGHT_DATA_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
bd = bdclient(api_token=BRIGHT_DATA_API_KEY)


st.set_page_config(
    page_title="AI Lead Generation Agent",
    page_icon="🎯",
    layout="wide"
)

with st.sidebar:
    logo_path = "./assets/bright-data-logo.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
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

    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    user_message = st.chat_input("Describe the leads you want...")

    if user_message:
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        ai_response = f"🤖 Got it! I'll look for: **{user_message}**"
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        st.rerun()  


def parse_query_to_filters(query: str):
    """Use OpenAI to turn natural language into structured filters."""
    prompt = f"""
    Convert this lead search request into structured JSON filters:
    "{query}"

    Return only valid JSON in this format:
    {{
      "role": "Marketing Manager",
      "industry": "Fintech",
      "location": "Kenya"
    }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are an expert lead generation assistant. Return only valid JSON."},
                      {"role": "user", "content": prompt}],
            temperature=0
        )
        filters_text = response.choices[0].message.content.strip()
        if filters_text.startswith("```"):
            filters_text = filters_text.split("```")[1]
            if filters_text.startswith("json"):
                filters_text = filters_text[4:]
        filters = json.loads(filters_text)
    except Exception as e:
        st.error(f"Error parsing query: {e}")
        filters = {"query": query}
    return filters


def fetch_leads_from_brightdata(filters: dict):
    """Fetch real leads with Bright Data (example using LinkedIn search)."""
    try:
        keyword = filters.get("role", "") + " " + filters.get("industry", "")
        location = filters.get("location", "")

        result = bd.search_linkedin.jobs(
            keyword=keyword or "Software Engineer",
            location=location or "Kenya",
            country="KE",
            time_range="Past month",
            job_type="Full-time"
        )

        leads = bd.parse_content(result)
        return leads if isinstance(leads, list) else [leads]
    except Exception as e:
        st.error(f"Error fetching leads from Bright Data: {e}")
        return [
            {"title": "Software Engineer", "company": "TechCorp", "location": "Nairobi, Kenya"},
            {"title": "Marketing Manager", "company": "StartupX", "location": "Mombasa, Kenya"},
            {"title": "Data Scientist", "company": "DataFirm", "location": "Kisumu, Kenya"}
        ]


def enrich_leads_with_ai(leads: list):
    """Use OpenAI to enrich, score, and generate outreach strategy."""
    enriched = []
    for lead in leads[:10]:  
        profile_text = f"{lead.get('title', '')} at {lead.get('company', '')}, Location: {lead.get('location', '')}"

        prompt = f"""
        Analyze this lead and return JSON with:
        - summary (1 sentence about their background)
        - score (1-10 relevance score as integer)
        - outreach (best way to contact)

        Lead: {profile_text}

        Return only valid JSON in this format:
        {{
          "summary": "Professional summary here",
          "score": 8,
          "outreach": "Suggested outreach method"
        }}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "You enrich leads for sales teams. Return only valid JSON."},
                          {"role": "user", "content": prompt}],
                temperature=0.5
            )
            
            enriched_text = response.choices[0].message.content.strip()
            if enriched_text.startswith("```"):
                enriched_text = enriched_text.split("```")[1]
                if enriched_text.startswith("json"):
                    enriched_text = enriched_text[4:]
            
            enriched_data = json.loads(enriched_text)
        except Exception as e:
            st.warning(f"Error enriching lead: {e}")
            enriched_data = {
                "summary": "Professional with relevant experience in their field",
                "score": 5,
                "outreach": "Send LinkedIn message with personalized introduction"
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



st.title("🎯 AI-Powered Lead Generation Agent")


debug_mode = st.checkbox("🐛 Enable Debug Mode", value=True)


run_agent = st.button("🚀 Generate Leads", type="primary")

if run_agent and st.session_state.chat_history:
    user_queries = [msg for msg in st.session_state.chat_history if msg["role"] == "user"]
    if user_queries:
        last_query = user_queries[-1]["content"]
        
        if debug_mode:
            st.write("=" * 50)
            st.write("🔧 **DEBUG MODE ENABLED**")
            st.write("=" * 50)
            st.write(f"🎯 **Processing Query:** {last_query}")

        st.info("🤖 Parsing query into filters...")
        filters = parse_query_to_filters(last_query)
        
        if not debug_mode:
            st.json(filters)

        st.info("🔍 Fetching leads from Bright Data...")
        leads = fetch_leads_from_brightdata(filters)

        if not leads or len(leads) == 0:
            st.error("❌ No leads found.")
            if debug_mode:
                st.write("🔍 **Possible reasons:**")
                st.write("- Bright Data API returned empty results")
                st.write("- API credentials might be invalid")
                st.write("- Search parameters too restrictive")
                st.write("- API rate limits exceeded")
        else:
            st.success(f"✅ Found {len(leads)} leads. Enriching with AI...")
            enriched_leads = enrich_leads_with_ai(leads)

            if debug_mode:
                st.write("=" * 50)
                st.write("🎯 **FINAL RESULTS**")
                st.write("=" * 50)

            st.subheader("🎯 AI-Enriched Leads")
            for i, lead in enumerate(enriched_leads, 1):
                if lead['score'] >= 8:
                    border_color = "#28a745"  
                elif lead['score'] >= 6:
                    border_color = "#ffc107"  
                else:
                    border_color = "#dc3545"  
                
                st.markdown(
                    f"""
                    <div style="border:2px solid {border_color}; border-radius:10px; padding:15px; margin-bottom:15px; background-color: #f8f9fa;">
                        <h4 style="color: #2c3e50; margin-bottom: 10px;">#{i} {lead['role']} @ {lead['company']}</h4>
                        <p><b>📍 Location:</b> {lead['location']}</p>
                        <p><b>📝 Summary:</b> {lead['summary']}</p>
                        <p><b>⭐ AI Lead Score:</b> <span style="color: {border_color}; font-weight: bold;">{lead['score']}/10</span></p>
                        <p><b>💡 Suggested Outreach:</b> {lead['outreach']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.warning("Please enter a query in the chat first!")
elif run_agent:
    st.warning("Please enter a query in the chat first!")


st.markdown("---")
st.markdown("### How to use:")
st.markdown("""
1. **Enter your lead requirements** in the chat (e.g., "Find marketing managers in fintech companies in Kenya")
2. **Click 'Generate Leads'** to start the AI agent
3. **Review the AI-enriched results** with scores and outreach suggestions
""")