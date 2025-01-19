import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import openai
from dotenv import load_dotenv
from Home import stream_llm_response
import sys
from VAMM_governanceagent.create_agent import GovernanceAgent
from VAMM_socialagent_master.create_agent import SocialMarketingAgent
from VAMM_governanceagent.Expert_Agent import pydantic_ai_expert, PydanticAIDeps
from openai import AsyncOpenAI
from supabase import create_client, Client

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import using the folder name with underscores
from VAMM_socialagent_master.create_agent import SocialMarketingAgent

# Load environment variables
load_dotenv()

# Configure OpenAI API
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    st.error("OpenAI API key not found. Please check your .env file.")
    st.stop()

openai.api_key = api_key

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    st.error("Supabase credentials not found. Please check your .env file.")
    st.stop()

supabase_client = create_client(supabase_url, supabase_key)

# Set page config
st.set_page_config(
    page_title="Project Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for cards and detailed view
st.markdown("""
<style>
    .project-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        width: 100%;  /* Make card take full width */
        box-sizing: border-box;  /* Include padding in width calculation */
    }
    .project-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .metric-container {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #e9ecef;
    }
    .score-badge {
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 10px 0;
    }
    /* Social Media Section Styles */
    .social-media-section {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border: 1px solid #e9ecef;
    }
    .improvement-section {
        background-color: #f0f9ff;
        border-left: 4px solid #0d6efd;
        padding: 15px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
    }
    /* Environmental Section Styles */
    .environmental-section {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border: 1px solid #e9ecef;
    }
    .eco-improvement-section {
        background-color: #f0fff4;
        border-left: 4px solid #38a169;
        padding: 15px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
    }
    .metric-highlight {
        background-color: #e6ffec;
        padding: 8px;
        border-radius: 4px;
        margin: 5px 0;
    }
    .agent-box {
        background-color: #f8f9fa;
        border: 2px solid #e9ecef;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .agent-box h4 {
        color: #1a73e8;
        margin-bottom: 15px;
    }
    /* Make expander take full width */
    .streamlit-expanderHeader {
        width: 100%;
        display: block;
    }
    
    /* Style for the expander content */
    .streamlit-expanderContent {
        width: 100%;
        box-sizing: border-box;
    }
    
    /* Container for the expander */
    div[data-testid="stExpander"] {
        width: 100%;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for projects if it doesn't exist
if 'projects' not in st.session_state:
    st.session_state.projects = []

# Function to get social media marketing strategy
def get_social_media_strategy(project):
    try:
        prompt = f"""
        As a social media marketing expert for renewable energy projects, create a comprehensive social media strategy to improve 
        the social impact score for this project:
        
        Project Details:
        - Name: {project['project_name']}
        - Type: {project['type']}
        - Location: {project['location']}
        - Size: {project['size']} MW
        - Budget: ${project['budget']}M
        
        Please provide:
        1. Key messaging themes and hashtags
        2. Platform-specific strategies (Twitter, LinkedIn, Facebook, Instagram)
        3. Community engagement tactics
        4. Content calendar suggestions
        5. KPIs and success metrics
        
        Format your response in clear sections with actionable items.
        """
        
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert social media marketing strategist specializing in renewable energy projects and ESG improvement."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500,
            stream=True  # Enable streaming
        )
        return stream_llm_response(response)
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Function to get environmental improvement strategy
def get_environmental_strategy(project):
    try:
        prompt = f"""
        As an environmental impact specialist for renewable energy projects, create a comprehensive environmental improvement strategy for this project:
        
        Project Details:
        - Name: {project['project_name']}
        - Type: {project['type']}
        - Location: {project['location']}
        - Size: {project['size']} MW
        - Budget: ${project['budget']}M
        
        Please provide:
        1. Ecosystem Impact Analysis
           - Local wildlife assessment
           - Habitat protection measures
           - Biodiversity conservation strategies
        
        2. Resource Efficiency Plan
           - Water usage optimization
           - Land use efficiency
           - Material sustainability
        
        3. Carbon Footprint Reduction
           - Construction phase emissions
           - Operational emissions
           - Supply chain optimization
        
        4. Environmental Monitoring Plan
           - Key metrics to track
           - Monitoring frequency
           - Reporting framework
        
        5. Mitigation Strategies
           - Short-term actions
           - Long-term sustainability measures
           - Emergency response protocols
        
        Format your response in clear sections with specific, actionable recommendations.
        Include estimated environmental impact improvements for each measure.
        """
        
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert environmental specialist focusing on renewable energy projects and ESG improvement. Provide detailed, technical, yet actionable recommendations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500,
            stream=True  # Enable streaming
        )
        return stream_llm_response(response)
    except Exception as e:
        return f"An error occurred: {str(e)}"

def get_project_specific_response(project, question):
    try:
        prompt = f"""
        Regarding the {project['type']} project named "{project['project_name']}" in {project['location']},
        with a size of {project['size']} MW and budget of ${project['budget']}M,
        please answer the following question:
        {question}
        """
        
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert consultant on renewable energy projects."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
            stream=True  # Enable streaming
        )
        return stream_llm_response(response)
    except Exception as e:
        return f"An error occurred: {str(e)}"

def stream_llm_response(response):
    placeholder = st.empty()
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            full_response += chunk.choices[0].delta.content
            placeholder.markdown(full_response + "▌")
    placeholder.markdown(full_response)
    return full_response

# Update the async helper functions
async def get_expert_response(prompt, deps):
    response = await pydantic_ai_expert.run(
        prompt,
        deps=deps
    )
    # Extract the data field from the response which contains the formatted text
    return response.data if hasattr(response, 'data') else str(response)

def run_async_response(prompt, deps):
    import asyncio
    return asyncio.run(get_expert_response(prompt, deps))

async def handle_project_chat():
    # Initialize OpenAI client
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Initialize dependencies
    deps = PydanticAIDeps(
        supabase=supabase_client,
        openai_client=openai_client
    )
    
    if "project_messages" not in st.session_state:
        st.session_state.project_messages = []

    for message in st.session_state.project_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What would you like to know about your renewable energy project?"):
        st.session_state.project_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = await pydantic_ai_expert.run(
                prompt,
                deps=deps
            )
            st.markdown(response)
            st.session_state.project_messages.append({"role": "assistant", "content": response})

# Title
st.title("Project Dashboard 📊")
st.markdown("Manage and track all your renewable energy projects in one place.")

# Quick Stats at the top
if st.session_state.projects:
    total_projects = len(st.session_state.projects)
    avg_esg_score = sum(p['esg_score'] for p in st.session_state.projects) / total_projects
    total_capacity = sum(p['size'] for p in st.session_state.projects)
    total_budget = sum(p['budget'] for p in st.session_state.projects)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Projects", total_projects)
    with col2:
        st.metric("Average ESG Score", f"{avg_esg_score:.1f}")
    with col3:
        st.metric("Total Capacity", f"{total_capacity:.1f} MW")
    with col4:
        st.metric("Total Budget", f"${total_budget:.1f}M")

# Project Cards
st.header("Your Projects")

if not st.session_state.projects:
    st.info("No projects added yet. Start by analyzing a project on the home page!")
else:
    # Use a single column layout for full width
    for idx, project in enumerate(st.session_state.projects):
        # Create container for each project
        with st.container():
            # Project card header
            st.markdown(f"""
            <div class="project-card">
                <h3>{project['project_name']}</h3>
                <p>{project['type']} in {project['location']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Project details in expander
            with st.expander("View Details"):
                # Create tabs for different sections
                overview_tab, social_tab, environmental_tab, governance_tab = st.tabs([
                    "Overview", "Social", "Environmental", "Governance"
                ])
                
                with overview_tab:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Size", f"{project['size']} MW")
                        st.metric("Budget", f"${project['budget']}M")
                    with col2:
                        st.metric("ESG Score", project['esg_score'])
                        st.metric("Location", project['location'])
                
                with social_tab:
                    st.markdown("""
                    <div class="agent-box">
                        <h4>🤖 Social Media Impact Agent</h4>
                        <p>Chat with your AI social media strategist to improve your project's social impact.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    user_message = st.text_input("Ask your social media agent:", key=f"social_input_{idx}")
                    
                    if st.button("Send", key=f"social_send_{idx}"):
                        if user_message:
                            with st.spinner("Processing your request..."):
                                # Get project context
                                project_context = f"""
                                Project: {project['project_name']}
                                Type: {project['type']}
                                Location: {project['location']}
                                Size: {project['size']} MW
                                Budget: ${project['budget']}M
                                """
                                
                                # Get response from social agent
                                response = st.session_state.social_agent.get_response(
                                    user_message, 
                                    context=project_context
                                )
                                
                                # Display response
                                st.markdown("### 🤖 Agent Response:")
                                st.markdown(response)
                        else:
                            st.warning("Please enter a message for the agent.")
                    
                    # Add strategy generator
                    st.markdown("---")
                    if st.button("Generate Full Social Media Strategy", key=f"strategy_{idx}"):
                        with st.spinner("Generating social media marketing strategy..."):
                            strategy = get_social_media_strategy(project)
                            st.markdown("### 📱 Social Media Marketing Strategy")
                            st.markdown(strategy)
                
                with environmental_tab:
                    if st.button("Generate Environmental Strategy", key=f"env_strategy_{idx}"):
                        with st.spinner("Generating environmental strategy..."):
                            strategy = get_environmental_strategy(project)
                            st.markdown("### 🌿 Environmental Strategy")
                            st.markdown(strategy)
                
                with governance_tab:
                    st.markdown("""
                    <div class="agent-box">
                        <h4>🏛️ Governance & Compliance Agent</h4>
                        <p>Get information about building departments, permits, and regulatory requirements.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if 'project_messages' not in st.session_state:
                        st.session_state.project_messages = []

                    # Display chat history
                    for message in st.session_state.project_messages:
                        with st.chat_message(message["role"]):
                            st.write(message["content"])

                    # Chat input
                    if prompt := st.chat_input("Ask about governance, permits, or regulatory requirements"):
                        st.session_state.project_messages.append({"role": "user", "content": prompt})
                        with st.chat_message("user"):
                            st.write(prompt)

                        with st.chat_message("assistant"):
                            with st.spinner("Processing your request..."):
                                # Initialize OpenAI client
                                openai_client = AsyncOpenAI(api_key=api_key)
                                
                                # Initialize dependencies
                                deps = PydanticAIDeps(
                                    supabase=supabase_client,
                                    openai_client=openai_client
                                )
                                
                                # Get response from expert agent
                                response = run_async_response(prompt, deps)
                                st.write(response)
                                st.session_state.project_messages.append({"role": "assistant", "content": response})

# Export All Projects functionality
if st.session_state.projects:
    st.sidebar.header("Bulk Actions")
    if st.sidebar.button("Export All Projects"):
        df = pd.DataFrame(st.session_state.projects)
        csv = df.to_csv(index=False)
        st.sidebar.download_button(
            label="Download CSV",
            data=csv,
            file_name="all_renewable_energy_projects.csv",
            mime="text/csv"
        )