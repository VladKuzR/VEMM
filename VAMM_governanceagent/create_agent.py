import openai
from datetime import datetime
from typing import Dict, Optional
from googlesearch import search

class GovernanceAgent:
    def __init__(self, api_key: str):
        """
        Initialize the Governance Agent with necessary API key
        """
        self.openai_api_key = api_key
        self.client = openai.Client(api_key=self.openai_api_key)
        
    def get_building_department_info(self, location: str) -> Dict:
        """
        Get Department of Buildings contact information for the given location
        """
        try:
            # Use multiple search queries to get better results
            search_queries = [
                f"department of buildings {location} contact information",
                f"building permits {location} government",
                f"{location} building department official website",
                f"{location} construction permits contact",
                f"{location} city hall building department"
            ]
            
            search_results = []
            # Get results from multiple queries
            for query in search_queries:
                for url in search(query, num_results=3):
                    if url not in search_results:  # Avoid duplicates
                        search_results.append(url)
            
            # Extract relevant information using GPT
            system_prompt = """
            You are a governance specialist for renewable energy projects. Your task is to extract 
            and format the Department of Buildings contact information from the provided search results.
            
            If the exact department of buildings information is not available, provide information about:
            1. The city planning department
            2. Building permits division
            3. Construction services
            4. City hall contact information
            
            Always provide the most relevant government contact information for building permits and construction projects.
            If specific information is not available, provide general guidance on how to contact the appropriate department.
            """
            
            user_prompt = f"""
            Location: {location}
            Search Results (Official Websites): {search_results}
            
            Please provide a detailed summary including:
            1. Department Name and Main Contact Information:
               - Phone numbers
               - Email addresses
               - Physical address
               - Website
            
            2. Permit Application Process:
               - Where to apply
               - How to submit applications
               - Online vs in-person options
            
            3. Office Information:
               - Business hours
               - Appointment requirements
               - Walk-in policies
            
            4. Required Documentation:
               - Common permit requirements
               - Application forms
               - Supporting documents needed
            
            5. Additional Information:
               - Fee schedules
               - Processing times
               - Important notices

            Note: If specific information is not available, provide guidance on how to obtain it.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            
            # Check if response is too generic or empty
            if "no available information" in response.choices[0].message.content.lower():
                return {
                    "contact_info": f"""
                    # Building Department Information for {location}
                    
                    ## How to Proceed
                    1. Contact the City Hall of {location} directly
                    2. Visit the city's official website
                    3. Call the general information line for building permits
                    4. Schedule an in-person visit to the planning department
                    
                    ## Next Steps
                    - Search for "{location} City Hall" or "{location} Building Department"
                    - Look for the Planning and Development or Building Permits division
                    - Request a pre-application meeting for your renewable energy project
                    - Ask for specific requirements for solar/wind installations
                    
                    ## General Guidance
                    Most building departments require:
                    - Project plans and specifications
                    - Site surveys or plot plans
                    - Environmental impact assessments
                    - Structural calculations
                    - Electrical diagrams
                    - Permit application forms
                    
                    Please contact your local city hall for specific requirements.
                    """,
                    "timestamp": datetime.now().isoformat(),
                    "location": location,
                    "raw_results": search_results
                }
            
            return {
                "contact_info": response.choices[0].message.content,
                "timestamp": datetime.now().isoformat(),
                "location": location,
                "raw_results": search_results
            }
            
        except Exception as e:
            raise Exception(f"Failed to fetch building department info: {str(e)}")
    
    def get_regulatory_requirements(self, location: str, project_type: str) -> Dict:
        """
        Get specific regulatory requirements for the project type and location
        """
        try:
            search_query = f"{project_type} regulations permits requirements {location} government"
            search_results = []
            
            # Get first 5 search results
            for url in search(search_query, num_results=5):
                search_results.append(url)
            
            system_prompt = """
            You are a governance and compliance specialist for renewable energy projects. 
            Extract and summarize the regulatory requirements and permit processes from 
            the provided search results.
            """
            
            user_prompt = f"""
            Project Type: {project_type}
            Location: {location}
            Search Results: {search_results}
            
            Please provide:
            1. Required permits and licenses
            2. Environmental compliance requirements
            3. Zoning regulations
            4. Construction requirements
            5. Timeline estimates
            6. Associated fees
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            return {
                "requirements": response.choices[0].message.content,
                "timestamp": datetime.now().isoformat(),
                "project_type": project_type,
                "location": location,
                "raw_results": search_results
            }
            
        except Exception as e:
            raise Exception(f"Failed to fetch regulatory requirements: {str(e)}") 