# Usage example
def main():
    # Initialize the agent
    agent = SocialMarketingAgent(
        api_key="your-openai-api-key",
        census_api_key="your-census-api-key"
    )
    
    # Fetch demographic data
    demographics = agent.fetch_census_data(
        location="36061",  # Example: New York County FIPS code
        metrics=["B01001_001E", "B19013_001E"]  # Population and median income
    )
    
    # Generate campaign strategy
    campaign = agent.generate_campaign_strategy(
        prompt="Create a campaign to promote financial literacy in underserved communities",
        target_audience="Young adults 18-35 in urban areas",
        campaign_goals=[
            "Increase financial literacy awareness by 30%",
            "Engage 10,000 community members in workshops",
            "Partner with 20 local organizations"
        ],
        budget=100000.0
    )
    
    print(campaign["campaign_strategy"])

if __name__ == "__main__":
    main()