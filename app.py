import streamlit as st
import base64
import time

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
        ai_response = f"🤖 Okay, I’ll search Bright Data for: **{user_message}**"
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})

    run_agent = st.button("Run AI Agent 🚀")



def parse_query_to_filters(query: str, attempt: int):
    """Use AI to parse natural language into filters."""
    filters = {
        "role": "Marketing Manager",
        "industry": "Fintech",
        "location": "Kenya",
        "experience": "5+ years"
    }
    if attempt == 2:
        filters["location"] = "East Africa"
    if attempt == 3:
        filters["industry"] = "Finance"
    return filters


def fetch_leads_from_brightdata(filters: dict):
    """Fetch leads (mocked). Replace with Bright Data API call."""
    if filters["location"] == "Kenya":
        return []  
    elif filters["location"] == "East Africa":
        return [
            {"name": "John Doe", "role": "Marketing Manager", "company": "FinBank", "experience": "8 years"},
        ]
    else:
        return [
            {"name": "Jane Smith", "role": "Marketing Director", "company": "PayWave", "experience": "10 years"},
            {"name": "Ali Kamau", "role": "Marketing Lead", "company": "Equity Digital", "experience": "7 years"},
        ]


def enrich_leads_with_ai(leads: list):
    """Add AI summaries, scores, and outreach suggestions."""
    enriched = []
    for lead in leads:
        lead["summary"] = f"{lead['experience']} in {lead['company']} driving growth."
        lead["score"] = 9 if "Director" in lead["role"] else 8
        lead["outreach"] = "Suggest highlighting fintech success stories."
        enriched.append(lead)
    return enriched



def run_ai_agent(user_query: str, max_attempts=3):
    """Agent retries with different filters until it finds leads."""
    for attempt in range(1, max_attempts + 1):
        st.info(f"🤖 Attempt {attempt}: reasoning about filters...")
        time.sleep(1)

        filters = parse_query_to_filters(user_query, attempt)
        st.json(filters)

        leads = fetch_leads_from_brightdata(filters)
        if leads:
            st.success(f"✅ Found {len(leads)} leads on attempt {attempt}")
            return enrich_leads_with_ai(leads)

        st.warning("⚠️ No leads found, refining search...")
        time.sleep(1)

    st.error("❌ Could not find leads after multiple attempts.")
    return []



st.title("AI-Powered Lead Generation Agent")

if run_agent and st.session_state.chat_history:
    last_query = st.session_state.chat_history[-2]["content"] if len(st.session_state.chat_history) >= 2 else st.session_state.chat_history[-1]["content"]

    leads = run_ai_agent(last_query)

    if leads:
        st.subheader("AI-Enriched Leads")
        for lead in leads:
            st.markdown(
                f"""
                <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                    <h4>{lead['name']} — {lead['role']} @ {lead['company']}</h4>
                    <p><b>Summary:</b> {lead['summary']}</p>
                    <p><b>AI Lead Score:</b> {lead['score']}/10</p>
                    <p><b>Suggested Outreach:</b> {lead['outreach']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
