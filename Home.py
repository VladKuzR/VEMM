import streamlit as st
import openai
from dotenv import load_dotenv
import os
from datetime import datetime
import requests
from geopy.geocoders import Nominatim

# Load environment variables
load_dotenv()

# Configure OpenAI API
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    st.error("OpenAI API key not found. Please check your .env file.")
    st.stop()

openai.api_key = api_key

# Initialize session state for projects if it doesn't exist
if 'projects' not in st.session_state:
    st.session_state.projects = []

# Add to your session state initialization
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None

# Set page config
st.set_page_config(
    page_title="Renewable Energy Project Consultant",
    page_icon="🌱",
    layout="wide"
)

# Title and description
st.title("Renewable Energy Project Consultant 🌱")
st.markdown("""
This AI consultant will help you evaluate and plan your renewable energy projects
in accordance with ESG guidelines and local regulations.
""")

# Project name input
project_name = st.text_input("Project Name:", "")

# Location input
location = st.text_input("Enter the project location (City, State):", "")

# Project type selection
project_type = st.selectbox(
    "Select your renewable energy project type:",
    ["Solar Farm", "Wind Farm", "Hydroelectric", "Biomass", "Geothermal"]
)

# Additional information
project_size = st.number_input("Estimated project size (in MW):", min_value=0.0, value=1.0)
project_budget = st.number_input("Estimated budget (in USD millions):", min_value=0.0, value=1.0)

system_prompt = """You are an agent consultant, perfectly trained on consulting for contractors 
to start renewable energy projects in the United States. The user is a contractor looking to 
build a new project and they want to be sure that they are up to standards with the ESG 
guidelines of local areas. You will advise them on optimal areas, based on their selected 
geographic destination. You will provide community sentiment, biodiversity analysis, and sustainability.

For each analysis, you will also provide an ESG score from 0-100 based on the following criteria:
- Environmental (40 points): Impact on local ecosystem, carbon footprint, resource efficiency
- Social (30 points): Community benefits, job creation, social impact
- Governance (30 points): Regulatory compliance, transparency, risk management

Format the score section of your response as: 
[ESG_SCORE]
Environmental: X/40
Social: X/30
Governance: X/30
Total Score: X/100
[/ESG_SCORE]"""

def stream_llm_response(response):
    placeholder = st.empty()
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            full_response += chunk.choices[0].delta.content
            placeholder.markdown(full_response + "▌")
    placeholder.markdown(full_response)
    return full_response

# Function to get AI response
def get_ai_response(user_input, is_followup=False):
    try:
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        # If it's a follow-up question, include previous context
        if is_followup and st.session_state.messages:
            messages.extend(st.session_state.messages)
        
        messages.append({"role": "user", "content": user_input})
        
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=1500,
            stream=True  # Enable streaming
        )
        
        full_response = stream_llm_response(response)
        
        # Store the interaction in session state
        if not is_followup:
            st.session_state.messages = messages + [
                {"role": "assistant", "content": full_response}
            ]
        else:
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )
            
        return full_response
    except Exception as e:
        return f"An error occurred: {str(e)}"

def extract_esg_score(response):
    try:
        score_section = response.split("[ESG_SCORE]")[1].split("[/ESG_SCORE]")[0].strip()
        total_score = float(score_section.split("Total Score: ")[1].split("/100")[0])
        return total_score, score_section
    except:
        return None, None

def get_fema_risks(lat, lon):
    """Get comprehensive FEMA risk data for the location"""
    if lat is None or lon is None:
        return None, None
    
    # Get disaster declarations
    disasters_url = "https://www.fema.gov/api/open/v1/DisasterDeclarationsSummaries"
    disaster_params = {
        "$filter": f"latitude gt {lat-1} and latitude lt {lat+1} and longitude gt {lon-1} and longitude lt {lon+1}",
        "$orderby": "declarationDate desc",
        "$top": 5
    }
    
    # Get National Risk Index data
    nri_url = "https://hazards.fema.gov/nri/public/api/data/county"
    nri_params = {
        "latitude": lat,
        "longitude": lon
    }
    
    try:
        disasters_response = requests.get(disasters_url, params=disaster_params)
        nri_response = requests.get(nri_url, params=nri_params)
        
        disasters = None
        risk_data = None
        
        if disasters_response.status_code == 200:
            disasters = disasters_response.json().get('DisasterDeclarationsSummaries', [])
        
        if nri_response.status_code == 200:
            risk_data = nri_response.json()
            
        return disasters, risk_data
    except Exception as e:
        print(f"Error fetching FEMA data: {str(e)}")
        return None, None

def format_risk_context(disasters, risk_data):
    """Format FEMA risk data into a readable context string"""
    context = "\nFEMA Risk Analysis:\n"
    
    if disasters:
        context += "\nRecent Disaster Declarations:\n"
        for disaster in disasters:
            context += f"- {disaster.get('declarationTitle')} ({disaster.get('declarationDate')})\n"
    
    if risk_data:
        context += "\nNational Risk Index Data:\n"
        try:
            risk_factors = risk_data.get('riskFactors', {})
            for risk_type, risk_info in risk_factors.items():
                if isinstance(risk_info, dict):
                    risk_score = risk_info.get('score', 'N/A')
                    risk_rating = risk_info.get('rating', 'N/A')
                    context += f"- {risk_type}: Score {risk_score} ({risk_rating})\n"
            
            # Add overall risk scores
            overall = risk_data.get('overall', {})
            context += "\nOverall Risk Metrics:\n"
            context += f"- Risk Score: {overall.get('riskScore', 'N/A')}\n"
            context += f"- Risk Rating: {overall.get('riskRating', 'N/A')}\n"
            context += f"- Resilience Score: {overall.get('resilienceScore', 'N/A')}\n"
            
        except Exception as e:
            context += f"Error parsing risk data: {str(e)}\n"
    
    return context

def get_coordinates(location):
    """Convert location string to coordinates using Nominatim"""
    try:
        geolocator = Nominatim(user_agent="renewable_energy_consultant")
        location_data = geolocator.geocode(location)
        if location_data:
            return location_data.latitude, location_data.longitude
        return None, None
    except Exception as e:
        print(f"Error getting coordinates: {str(e)}")
        return None, None

# Generate analysis button
if st.button("Generate Analysis"):
    if location and project_type and project_name:
        # Get location coordinates and FEMA data
        lat, lon = get_coordinates(location)
        disasters, risk_data = get_fema_risks(lat, lon) if lat and lon else (None, None)
        
        # Format FEMA risk context
        fema_context = format_risk_context(disasters, risk_data) if disasters or risk_data else ""
        
        user_prompt = f"""
        Please provide a comprehensive analysis for a {project_type} project in {location}.
        Project Size: {project_size} MW
        Budget: ${project_budget} million
        {fema_context}
        
        Please include:
        1. ESG Guidelines compliance analysis
        2. Community sentiment assessment
        3. Biodiversity impact analysis
        4. Sustainability recommendations
        5. Risk assessment and mitigation strategies:
           - Natural disaster risks
           - Environmental hazards
           - Community resilience factors
           - Infrastructure vulnerabilities
        
        End with an ESG score breakdown using the specified format.
        """
        
        with st.spinner("Generating analysis..."):
            response = get_ai_response(user_prompt)
            st.session_state.current_analysis = response
            
            # Extract and display ESG score
            score, score_details = extract_esg_score(response)
            if score is not None:
                # Store project data in session state
                project_data = {
                    "project_name": project_name,
                    "location": location,
                    "type": project_type,
                    "size": project_size,
                    "budget": project_budget,
                    "esg_score": score,
                    "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.projects.append(project_data)
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown("### ESG Score")
                    # Create a progress bar for the total score
                    st.progress(score/100)
                    st.markdown(f"### {int(score)}/100")
                with col2:
                    st.markdown("### Score Breakdown")
                    st.text(score_details)
            
            st.markdown("### Detailed Analysis")
            cleaned_response = response.split("[ESG_SCORE]")[0]
            st.markdown(cleaned_response)
            
            # Add a success message
            st.success("Project analysis complete! You can ask follow-up questions below.")
    else:
        st.warning("Please enter a project name, location, and select a project type.")

# Add follow-up interaction section
if st.session_state.current_analysis:
    st.markdown("---")
    st.markdown("### Follow-up Questions")
    st.markdown("Ask any questions about the analysis or request additional details.")
    
    # Text input for follow-up questions
    follow_up = st.text_input("Your question:", key="follow_up")
    
    # Button to submit follow-up question
    if st.button("Ask Question"):
        if follow_up:
            with st.spinner("Getting response..."):
                # Create context-aware prompt
                context_prompt = f"""
                Regarding the previous analysis about the {project_type} project in {location},
                please answer the following question:
                {follow_up}
                """
                
                follow_up_response = get_ai_response(context_prompt, is_followup=True)
                
                # Display the response in a new container
                with st.container():
                    st.markdown("#### Response:")
                    st.markdown(follow_up_response)
        else:
            st.warning("Please enter a question.")

    # Display conversation history
    if st.session_state.messages:
        st.markdown("### Conversation History")
        for msg in st.session_state.messages[1:]:  # Skip the system prompt
            if msg["role"] == "user":
                st.markdown(f"**You:** {msg['content']}")
            else:
                st.markdown(f"**Assistant:** {msg['content']}")

# Sidebar with additional information
with st.sidebar:
    st.header("About")
    st.markdown("""
    This tool helps renewable energy contractors:
    - Assess ESG compliance
    - Analyze community impact
    - Evaluate biodiversity concerns
    - Plan sustainable projects
    """) 