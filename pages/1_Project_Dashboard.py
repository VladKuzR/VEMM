import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import openai
from dotenv import load_dotenv
from Home import stream_llm_response


# Load environment variables
load_dotenv()

# Configure OpenAI API
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    st.error("OpenAI API key not found. Please check your .env file.")
    st.stop()

openai.api_key = api_key

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
    # Create three columns for project cards
    cols = st.columns(3)
    
    # Distribute projects across columns
    for idx, project in enumerate(st.session_state.projects):
        with cols[idx % 3]:
            # Create a card for each project
            with st.container():
                st.markdown(f"""
                <div class="project-card">
                    <h3>{project['project_name']}</h3>
                    <p>{project['type']} in {project['location']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Expandable section for project details
                with st.expander("View Details"):
                    # Project Overview
                    st.subheader("Project Overview")
                    st.markdown(f"""
                    - **Location:** {project['location']}
                    - **Type:** {project['type']}
                    - **Size:** {project['size']} MW
                    - **Budget:** ${project['budget']}M
                    - **Date Added:** {project['date_added']}
                    """)
                    
                    # ESG Score Visualization
                    st.subheader("ESG Score")
                    score_color = "green" if project['esg_score'] >= 70 else "orange" if project['esg_score'] >= 50 else "red"
                    st.progress(project['esg_score']/100)
                    st.markdown(f"""
                    <div style='text-align: center; margin: 10px 0;'>
                        <span class='score-badge' style='background-color: {score_color}; color: white;'>
                            {int(project['esg_score'])}/100
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Improvement Agents Section
                    st.markdown("---")
                    st.header("💡 Impact Improvement Agents")
                    
                    # Environmental Agent Tab
                    env_tab, social_tab = st.tabs(["🌿 Environmental Agent", "🤝 Social Media Agent"])
                    
                    with env_tab:
                        st.subheader("🌿 Environmental Impact Optimization")
                        st.markdown("""
                        Generate a comprehensive environmental strategy to improve your project's environmental score. 
                        This will include ecosystem impact analysis, resource efficiency planning, and mitigation strategies.
                        """)
                        
                        if st.button("Generate Environmental Strategy", key=f"env_strategy_{idx}"):
                            with st.spinner("Analyzing environmental impact and generating recommendations..."):
                                strategy = get_environmental_strategy(project)
                                st.markdown("### 🌍 Environmental Improvement Strategy")
                                st.markdown(strategy)
                                
                                # Add improvement potential note
                                st.markdown("""
                                <div class="eco-improvement-section">
                                    <h4>🌱 Potential Environmental Score Improvement</h4>
                                    <p>Implementing these environmental strategies could improve your environmental score by 8-15 points 
                                    through enhanced ecosystem protection, resource efficiency, and carbon footprint reduction.</p>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    with social_tab:
                        st.subheader("🚀 Social Impact Improvement")
                        if st.button("Generate Social Media Strategy", key=f"strategy_{idx}"):
                            with st.spinner("Generating social media marketing strategy..."):
                                strategy = get_social_media_strategy(project)
                                st.markdown("### 📱 Social Media Marketing Strategy")
                                st.markdown(strategy)
                                
                                # Add improvement potential note
                                st.markdown("""
                                <div class="improvement-section">
                                    <h4>💡 Potential Social Score Improvement</h4>
                                    <p>Implementing this social media strategy could improve your social impact score by 5-10 points 
                                    through increased community engagement, transparency, and public support.</p>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # Action Buttons
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Delete Project", key=f"delete_{idx}"):
                            st.session_state.projects.remove(project)
                            st.rerun()
                    with col2:
                        # Export individual project data
                        project_df = pd.DataFrame([project])
                        csv = project_df.to_csv(index=False)
                        st.download_button(
                            label="Export Data",
                            data=csv,
                            file_name=f"{project['project_name']}_data.csv",
                            mime="text/csv",
                            key=f"export_{idx}"
                        )

                    st.markdown("### Ask about this project")
                    question = st.text_input("Your question:", key=f"q_{project['project_name']}")
                    if st.button("Ask", key=f"btn_{project['project_name']}"):
                        if question:
                            with st.spinner("Getting response..."):
                                response = get_project_specific_response(project, question)
                                st.markdown("#### Response:")
                                st.markdown(response)
                        else:
                            st.warning("Please enter a question.")

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