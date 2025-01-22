from __future__ import annotations as _annotations

from dataclasses import dataclass
from dotenv import load_dotenv
import logfire
import asyncio
import httpx
import os

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI
from supabase import Client
from typing import List

"""
CONFIGURATION GUIDE:

To adapt this agent for a different PDF:

1. First run the crawler (see crawl_pdf.py) with your PDF's:
   - PDF_PATH: Path to your PDF file
   - SOURCE_NAME: A unique identifier for your content source
   
2. Update the filter in retrieve_relevant_documentation() to match your SOURCE_NAME:
   - Change 'renewable_energy_siting_policies' to your chosen SOURCE_NAME in the filter parameter

3. Update the source filter in list_documentation_pages() and get_page_content():
   - Change 'renewable_energy_siting_policies' to your SOURCE_NAME in the .eq() conditions

4. Modify the system_prompt to be specific to your domain

The crawler will populate your Supabase database with the content,
and this agent will then be able to retrieve and search that content.
"""

load_dotenv()

llm = os.getenv('LLM_MODEL', 'gpt-4-turbo-preview')
model = OpenAIModel(llm)

logfire.configure(send_to_logfire='if-token-present')

@dataclass
class PydanticAIDeps:
    supabase: Client
    openai_client: AsyncOpenAI

system_prompt = """
You are an expert on renewable energy siting policies. You have access to comprehensive research and policy documents
to help users understand renewable energy siting regulations, policies and developments.

Your only job is to assist with renewable energy siting policy related questions and you don't answer other questions besides describing what you are able to do.

Don't ask the user before taking an action, just do it. Always make sure you look at the content database with the provided tools before answering the user's question unless you have already.

When you first look at the content, always start with RAG.
Then also always check the list of available pages and retrieve the content of page(s) if it'll help.

Always let the user know when you didn't find the content they're looking for - be honest.
"""

pydantic_ai_expert = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=PydanticAIDeps,
    retries=2
)

async def get_embedding(text: str, openai_client: AsyncOpenAI) -> List[float]:
    """Get embedding vector from OpenAI."""
    try:
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0] * 1536  # Return zero vector on error

@pydantic_ai_expert.tool
async def retrieve_relevant_documentation(ctx: RunContext[PydanticAIDeps], user_query: str) -> str:
    """
    Retrieve relevant renewable energy siting policy content based on the query with RAG.
    
    Args:
        ctx: The context including the Supabase client and OpenAI client
        user_query: The user's question or query
        
    Returns:
        A formatted string containing the top 5 most relevant content chunks
    """
    try:
        # Get the embedding for the query
        query_embedding = await get_embedding(user_query, ctx.deps.openai_client)
        
        # Query Supabase for relevant documents
        result = ctx.deps.supabase.rpc(
            'match_pdf_pages',
            {
                'query_embedding': query_embedding,
                'match_count': 5,
                'filter': {'source': 'renewable_energy_siting_policies'}
            }
        ).execute()
        
        if not result.data:
            return "No relevant content found."
            
        # Format the results
        formatted_chunks = []
        for doc in result.data:
            chunk_text = f"""
# {doc['title']}

{doc['content']}

Page: {doc['page_num']}
"""
            formatted_chunks.append(chunk_text)
            
        # Join all chunks with a separator
        return "\n\n---\n\n".join(formatted_chunks)
        
    except Exception as e:
        print(f"Error retrieving content: {e}")
        return f"Error retrieving content: {str(e)}"

@pydantic_ai_expert.tool
async def list_documentation_pages(ctx: RunContext[PydanticAIDeps]) -> List[int]:
    """
    Retrieve a list of all available pages in the PDF.
    
    Returns:
        List[int]: List of unique page numbers
    """
    try:
        # Query Supabase for unique page numbers where source is renewable_energy_siting_policies
        result = ctx.deps.supabase.from_('pdf_pages') \
            .select('page_num') \
            .eq('metadata->>source', 'renewable_energy_siting_policies') \
            .execute()
        
        if not result.data:
            return []
            
        # Extract unique page numbers
        pages = sorted(set(doc['page_num'] for doc in result.data))
        return pages
        
    except Exception as e:
        print(f"Error retrieving pages: {e}")
        return []

@pydantic_ai_expert.tool
async def get_page_content(ctx: RunContext[PydanticAIDeps], page_num: int) -> str:
    """
    Retrieve the full content of a specific page by combining all its chunks.
    
    Args:
        ctx: The context including the Supabase client
        page_num: The page number to retrieve
        
    Returns:
        str: The complete page content with all chunks combined in order
    """
    try:
        # Query Supabase for all chunks of this page, ordered by chunk_number
        result = ctx.deps.supabase.from_('pdf_pages') \
            .select('title, content, chunk_number') \
            .eq('page_num', page_num) \
            .eq('metadata->>source', 'renewable_energy_siting_policies') \
            .order('chunk_number') \
            .execute()
        
        if not result.data:
            return f"No content found for page: {page_num}"
            
        # Format the page with its title and all chunks
        page_title = result.data[0]['title']
        formatted_content = [f"# {page_title}\n"]
        
        # Add each chunk's content
        for chunk in result.data:
            formatted_content.append(chunk['content'])
            
        # Join everything together
        return "\n\n".join(formatted_content)
        
    except Exception as e:
        print(f"Error retrieving page content: {e}")
        return f"Error retrieving page content: {str(e)}"