import streamlit as st
import openai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

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

# Function to get AI response
def get_ai_response(user_input):
try:
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0].message.content
except Exception as e:
    return f"An error occurred: {str(e)}"

def extract_esg_score(response):
try:
    score_section = response.split("[ESG_SCORE]")[1].split("[/ESG_SCORE]")[0].strip()
    total_score = float(score_section.split("Total Score: ")[1].split("/100")[0])
    return total_score, score_section
except:
    return None, None

# Generate analysis button
if st.button("Generate Analysis"):
if location and project_type:
    user_prompt = f"""
    Please provide a comprehensive analysis for a {project_type} project in {location}.
    Project Size: {project_size} MW
    Budget: ${project_budget} million
    
    Please include:
    1. ESG Guidelines compliance analysis
    2. Community sentiment assessment
    3. Biodiversity impact analysis
    4. Sustainability recommendations
    5. Potential challenges and solutions
    
    End with an ESG score breakdown using the specified format.
    """
    
    with st.spinner("Generating analysis..."):
        response = get_ai_response(user_prompt)
        
        # Extract and display ESG score
        score, score_details = extract_esg_score(response)
        if score is not None:
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
        # Remove the ESG score section from the main response
        cleaned_response = response.split("[ESG_SCORE]")[0]
        st.markdown(cleaned_response)
else:
    st.warning("Please enter a location and select a project type.")

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