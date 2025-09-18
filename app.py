import base64
import json
import streamlit as st
from openai import OpenAI
import requests 

st.set_page_config(
    page_title="Deep Research Agent",
    page_icon="🎯",
    layout="wide"
)

with open("./assets/bright-data-logo.png", "rb") as brightdata_logo:
    brightdata_logo = base64.b64encode(brightdata_logo.read()).decode()
    title_hmtl = f""" 
    <div>
        <img src="data:image/png;base64,{brightdata_logo}" style="height: 60px; width:150px;"/>
        <h1 style="margin: 0; padding: 0; font-size: 2.5rem; font-weight: bold;">
            <span style="font-size:2.5rem;">🔎</span> AI-Powered Lead Generation Agent with
            <span style="color: #0000FF;">Bright Data</span> & 
            <span style="color: #8564ff;">OpenAI</span>
        </h1>
    </div>
    """
    st.markdown(title_hmtl, unsafe_allow_html=True)

with st.sidebar:
    bright_data_api_key = st.text_input("Enter your Bright Data API key", type="password")
    st.divider()

    st.subheader("Enter OpenAI API key")
    open_ai_api_key = st.text_input("Enter OpenAI API key", type="password")
    st.divider()

    st.header("How it Works")
    st.markdown("""
    1. **Enter your API keys above and lead requirements** in the chat (e.g., "Find marketing managers in fintech companies in the world")
    2. **Click 'Enter Button'** to start the AI agent
    3. **Review the AI-enriched results** with scores and outreach suggestions
    """)
    st.markdown("---")


if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Describe the Leads you want....")

def extract_search_parameters(user_input):
    """Use OpenAI to extract search parameters from natural language input"""
    if not open_ai_api_key:
        st.error("OpenAI API key is required")
        return None
    
    try:
        client = OpenAI(api_key=open_ai_api_key)
        
        prompt = f"""
        Extract the following information from the user query for lead generation:
        - Role/Job Title
        - Industry
        - Location
        - Any other specific requirements
        
        User query: {user_input}
        
        Return a JSON object with keys: role, industry, location, other_requirements.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts search parameters from natural language queries. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
    
        result = response.choices[0].message.content
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]
            
        return json.loads(result)
    
    except Exception as e:
        st.error(f"Error extracting search parameters: {e}")
        return {
            "role": "marketing manager" if "marketing" in user_input.lower() else "professional",
            "industry": "fintech" if "fintech" in user_input.lower() else "technology",
            "location": "United States" if "us" in user_input.lower() or "usa" in user_input.lower() else "Worldwide",
            "other_requirements": user_input
        }

def fetch_leads_from_brightdata(filters):
    """Fetch real leads with Bright Data"""
    if not bright_data_api_key:
        st.error("Bright Data API key is required")
        return []
    
    try:
        headers = {
            "Authorization": f"Bearer {bright_data_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": f"{filters.get('role', '')} {filters.get('industry', '')}",
            "location": filters.get("location", ""),
            "country": "US",  
            "limit": 10  
        }
        
        response = requests.post(
            "https://api.brightdata.com/datasets/v1/search",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            st.error(f"Bright Data API error: {response.status_code} - {response.text}")
            return [
            ]
            
    except Exception as e:
        st.error(f"Error fetching leads from Bright Data: {e}")
        return [
        ]

def enrich_leads_with_ai(leads, original_query):
    """Use OpenAI to enrich leads with scores and outreach suggestions"""
    if not open_ai_api_key:
        st.error("OpenAI API key is required")
        return leads
    
    try:
        client = OpenAI(api_key=open_ai_api_key)
        
        enriched_leads = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, lead in enumerate(leads):
            status_text.text(f"Analyzing lead {i+1} of {len(leads)}...")
            progress_bar.progress((i + 1) / len(leads))
            
            prompt = f"""
            Based on the original query "{original_query}" and the following lead information:
            {json.dumps(lead, indent=2)}
            
            Please provide:
            1. A relevance score from 1-100 (how well this lead matches the query)
            2. A brief analysis of why this lead is a good fit
            3. A personalized outreach suggestion
            
            Return your response as a JSON object with keys: score, analysis, outreach_suggestion.
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a lead generation expert. Analyze leads and provide scores and outreach suggestions. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
                
            ai_analysis = json.loads(result)
            
            enriched_lead = {**lead, **ai_analysis}
            enriched_leads.append(enriched_lead)
        
        progress_bar.empty()
        status_text.empty()
        return enriched_leads
        
    except Exception as e:
        st.error(f"Error enriching leads with AI: {e}")
        return leads

def display_results(leads):
    """Display the enriched leads in a nice format"""
    st.subheader("AI-Enriched Leads")
    
    for i, lead in enumerate(leads):
        with st.expander(f"Lead #{i+1}: {lead.get('name', 'N/A')} - {lead.get('title', 'N/A')} at {lead.get('company', 'N/A')}"):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                score = lead.get('score', 0)
                if score >= 80:
                    score_color = "green"
                elif score >= 60:
                    score_color = "orange"
                else:
                    score_color = "red"
                
                st.markdown(f"**Relevance Score:** <span style='color:{score_color}; font-size: 1.5rem;'>{score}/100</span>", unsafe_allow_html=True)
                st.markdown(f"**Company:** {lead.get('company', 'N/A')}")
                st.markdown(f"**Title:** {lead.get('title', 'N/A')}")
                st.markdown(f"**Location:** {lead.get('location', 'N/A')}")
                if 'linkedin' in lead:
                    st.markdown(f"**LinkedIn:** [Profile Link]({lead.get('linkedin')})")
            
            with col2:
                st.markdown("**AI Analysis:**")
                st.info(lead.get('analysis', 'No analysis available'))
                st.markdown("**Outreach Suggestion:**")
                st.success(lead.get('outreach_suggestion', 'No suggestion available'))


if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("⏳ Analyzing your request...")
        

        message_placeholder.markdown("🔍 Extracting search parameters...")
        filters = extract_search_parameters(user_input)

        message_placeholder.markdown("📊 Fetching leads from Bright Data...")
        leads = fetch_leads_from_brightdata(filters)
        
        message_placeholder.markdown("🧠 Enriching leads with AI analysis...")
        enriched_leads = enrich_leads_with_ai(leads, user_input)
        

        message_placeholder.markdown("✅ Lead generation complete!")
        display_results(enriched_leads)
        
        st.session_state.messages.append({"role": "assistant", "content": f"Found {len(enriched_leads)} leads for your query: {user_input}"})