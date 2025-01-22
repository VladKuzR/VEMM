import streamlit as st
import json
import requests
from create_agent import SocialMarketingAgent
from typing import List, Dict

# Set page config
st.set_page_config(
    page_title="Social Marketing Campaign Generator",
    page_icon="🎯",
    layout="wide"
)

# Initialize session state variables
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'location' not in st.session_state:
    st.session_state.location = None
if 'census_data' not in st.session_state:
    st.session_state.census_data = None

def initialize_agent():
    """Initialize the agent with API keys"""
    try:
        agent = SocialMarketingAgent(
            api_key=st.secrets["OPENAI_API_KEY"],
            census_api_key=st.secrets["CENSUS_API_KEY"]
        )
        st.session_state.agent = agent
        return True
    except Exception as e:
        st.error(f"Failed to initialize agent: {str(e)}")
        return False

def get_place_fips(city: str, state: str) -> str:
    """Convert city and state to FIPS place code"""
    city = city.strip().title()
    state = state.strip().upper()
    
    # Use ACS5 endpoint with proper variables
    url = "https://api.census.gov/data/2020/acs/acs5"
    
    try:
        # First get the state FIPS code
        state_fips = state_codes.get(state, '')
        
        # Query with NAME to get place information
        response = requests.get(
            url,
            params={
                "key": st.secrets["CENSUS_API_KEY"],
                "get": "NAME",
                "for": "place:*",
                "in": f"state:{state_fips}",
            }
        )
        
        if response.status_code != 200:
            st.error(f"Census API error: {response.status_code}")
            return None
            
        data = response.json()
        
        # Find the matching place
        for row in data[1:]:  # Skip header row
            if city.lower() in row[0].lower():
                place_fips = row[-1]  # Get place FIPS code
                st.write(f"Debug - Found place: {row[0]} with FIPS: {place_fips}")
                return place_fips
        
        st.error(f"Could not find FIPS code for {city}, {state}")
        return None
        
    except Exception as e:
        st.error(f"Error looking up place code: {str(e)}")
        return None

def fetch_census_data(location: str, state: str, metrics: List[str]) -> Dict:
    """
    Fetch demographic data from Census API
    """
    base_url = "https://api.census.gov/data/2020/acs/acs5"
    
    try:
        state_fips = state_codes.get(state, '')
        response = requests.get(
            base_url,
            params={
                "key": st.secrets["CENSUS_API_KEY"],
                "get": ",".join(["NAME"] + metrics),
                "for": f"place:{location}",
                "in": f"state:{state_fips}"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Census API returned status code {response.status_code}")
            
        data = response.json()
        if len(data) < 2:  # No data found
            raise Exception("No data found for this location")
            
        # Convert to dictionary
        headers = data[0]
        values = data[1]
        return dict(zip(headers, values))
        
    except Exception as e:
        raise Exception(f"Failed to fetch census data: {str(e)}")

# Dictionary of state abbreviations to FIPS codes
state_codes = {
    'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06', 'CO': '08', 
    'CT': '09', 'DE': '10', 'FL': '12', 'GA': '13', 'HI': '15', 'ID': '16',
    'IL': '17', 'IN': '18', 'IA': '19', 'KS': '20', 'KY': '21', 'LA': '22',
    'ME': '23', 'MD': '24', 'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28',
    'MO': '29', 'MT': '30', 'NE': '31', 'NV': '32', 'NH': '33', 'NJ': '34',
    'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38', 'OH': '39', 'OK': '40',
    'OR': '41', 'PA': '42', 'RI': '44', 'SC': '45', 'SD': '46', 'TN': '47',
    'TX': '48', 'UT': '49', 'VT': '50', 'VA': '51', 'WA': '53', 'WV': '54',
    'WI': '55', 'WY': '56'
}

# Main app layout
st.title("🎯 Social Marketing Campaign Generator")

# Sidebar for API setup
with st.sidebar:
    st.header("Setup")
    if st.button("Initialize Agent", key="init_agent"):
        if initialize_agent():
            st.success("Agent initialized successfully!")

# Main content
if st.session_state.agent is not None:
    # Create two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Campaign Parameters")
        
        # Business Details
        st.subheader("Business Details")
        business_name = st.text_input("Business Name", key="business_name_input")
        business_type = st.text_input("Business Type", key="business_type_input")
        target_audience = st.text_input("Target Audience", key="target_audience_input")
        goals = st.text_area("Business Goals (one per line)", key="goals_input")
        budget = st.number_input("Budget ($)", min_value=0, key="budget_input")
        
        # Store the inputs in session state
        st.session_state.business_name = business_name
        st.session_state.business_type = business_type
        st.session_state.target_audience = target_audience
        st.session_state.goals = [g.strip() for g in goals.split('\n') if g.strip()]
        st.session_state.budget = budget if budget > 0 else None
        
        # City and State inputs
        col_city, col_state = st.columns([2, 1])
        with col_city:
            city = st.text_input("City", placeholder="Enter city name", key="city_input")
        with col_state:
            state = st.selectbox("State", options=sorted(state_codes.keys()), key="state_select")
        
        # FIPS code lookup
        if city and state:
            place_code = get_place_fips(city, state)
            if place_code:
                st.session_state.location = place_code
                st.session_state.state = state
                st.success(f"Found FIPS code: {place_code}")
                
                # Census Metrics
                st.subheader("Census Metrics")
                metric_options = [
                    ("B01003_001E", "Total Population"),
                    ("B19013_001E", "Median Household Income"),
                    ("B01002_001E", "Median Age"),
                    ("B15003_001E", "Educational Attainment")
                ]
                
                metrics = st.multiselect(
                    "Select Metrics",
                    options=metric_options,
                    default=[metric_options[0]],
                    format_func=lambda x: x[1],
                    help="Select demographic metrics to fetch",
                    key="metrics_select"
                )
                
                metric_codes = [m[0] for m in metrics]
                
                if st.button("Fetch Census Data", key="fetch_census"):
                    try:
                        census_data = fetch_census_data(
                            st.session_state.location, 
                            st.session_state.state, 
                            metric_codes
                        )
                        # Store census data in both session state and agent
                        st.session_state.census_data = census_data
                        st.session_state.agent.demographic_data = census_data
                        
                        st.success("Census data fetched successfully!")
                        
                        # Display census data results
                        st.subheader("Census Data Results")
                        for metric in metrics:
                            metric_code = metric[0]
                            metric_name = metric[1]
                            if metric_code in census_data:
                                value = census_data[metric_code]
                                if "income" in metric_name.lower():
                                    formatted_value = f"${int(float(value)):,}"
                                else:
                                    formatted_value = f"{int(float(value)):,}"
                                st.metric(metric_name, formatted_value)
                    except Exception as e:
                        st.error(f"Error fetching census data: {str(e)}")
            else:
                st.session_state.location = None
                st.session_state.state = None
                st.warning("Please enter a valid city and state")
    
    with col2:
        st.subheader("Generated Strategy")
        if st.button("Generate Campaign Strategy", key="generate_strategy"):
            if st.session_state.census_data is None:
                st.error("Please fetch census data first!")
            else:
                with st.spinner("Generating marketing strategy..."):
                    try:
                        # Debug output
                        st.write("Debug - Census Data:", st.session_state.agent.demographic_data)
                        st.write("Debug - Goals:", st.session_state.goals)
                        
                        strategy = st.session_state.agent.generate_campaign_strategy(
                            prompt=f"Generate a strategy for {business_name} ({business_type}) in {city}, {state}",
                            target_audience=target_audience,
                            campaign_goals=st.session_state.goals,
                            budget=st.session_state.budget
                        )
                        
                        if strategy:
                            st.markdown("### Campaign Strategy")
                            st.write(strategy['campaign_strategy'])
                            
                            st.markdown("### Generated At")
                            st.write(strategy['timestamp'])
                            
                            st.markdown("### Demographic Data Used")
                            st.write(strategy['demographic_data_used'])
                    except Exception as e:
                        st.error(f"Error generating strategy: {str(e)}")

else:
    st.info("Please initialize the agent using the sidebar button first.")

# Footer
st.markdown("---")
st.markdown("*Powered by OpenAI GPT-4 and US Census Data*")