from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
import ssl
import time
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Disable SSL verification for Bright Data proxy
ssl._create_default_https_context = ssl._create_unverified_context

class BrightDataWebSearchToolInput(BaseModel):
    """Input schema for BrightDataWebSearchTool."""
    title: str = Field(..., description="Brand name to monitor")

class BrightDataWebSearchTool(BaseTool):
    """
    A tool for searching the web via Bright Data's proxy.
    
    This tool performs searches for a given brand name across multiple platforms:
    - LinkedIn
    - Instagram
    - YouTube
    - X/Twitter
    """
    name: str = "Web Search Tool"
    description: str = "Use this tool to search Google and retrieve the top search results."
    args_schema: Type[BaseModel] = BrightDataWebSearchToolInput

    def _run(self, title: str, total_results: int = 50) -> str:
        """
        Run the search for a brand name across multiple platforms.
        
        Args:
            title: The brand name to search for
            total_results: Maximum number of results to retrieve
            
        Returns:
            List of search results as dictionaries
        """
        # Set up Bright Data proxy
        host = 'brd.superproxy.io'
        port = 33335

        username = os.getenv("BRIGHT_DATA_USERNAME")
        password = os.getenv("BRIGHT_DATA_PASSWORD")
        
        proxy_url = f'http://{username}:{password}@{host}:{port}'

        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }

        # Run multiple searches to target specific platforms
        all_results = []
        
        # Search queries targeting different platforms
        search_queries = [
            f'"{title}" site:linkedin.com',
            f'"{title}" site:instagram.com',
            f'"{title}" site:youtube.com OR site:youtu.be',
            f'"{title}" site:twitter.com OR site:x.com OR tweet {title}'
        ]
        
        print(f"Searching for brand mentions: {title}")
        
        for query in search_queries:
            formatted_query = "+".join(query.split(" "))
            url = f"https://www.google.com/search?q={formatted_query}&tbs=qdr:w&brd_json=1&num={total_results//4}"
            try:
                response = requests.get(url, proxies=proxies, verify=False)
                if response.status_code == 200 and 'organic' in response.json():
                    results_count = len(response.json()['organic'])
                    all_results.extend(response.json()['organic'])
                    print(f"Found {results_count} results for {query.split(' site:')[1] if 'site:' in query else 'general search'}")
                else:
                    print(f"No results found for {query}")
            except Exception as e:
                print(f"Search error: {str(e)}")
                
        print(f"Total results found: {len(all_results)}")
        return all_results


def scrape_urls(input_urls: list[str], initial_params: dict, scraping_type: str):
    """
    Scrape content from a list of URLs using Bright Data's API.
    
    Args:
        input_urls: List of URLs to scrape
        initial_params: Parameters for the Bright Data API
        scraping_type: Type of content being scraped (linkedin, instagram, etc.)
        
    Returns:
        List of scraped content as dictionaries
    """
    print(f"Scraping {len(input_urls)} {scraping_type} URLs")
    
    # If no URLs provided, return empty list
    if not input_urls:
        print(f"No {scraping_type} URLs to scrape.")
        return []
        
    url = "https://api.brightdata.com/datasets/v3/trigger"
    headers = {
        "Authorization": f"Bearer {os.getenv('BRIGHT_DATA_API_KEY')}",
        "Content-Type": "application/json",
    }
    data = [{"url":url} for url in input_urls]

    try:
        # Trigger the scraping job
        scraping_response = requests.post(url, headers=headers, params=initial_params, json=data)
        
        # Check for successful response
        if scraping_response.status_code != 200:
            print(f"API error: Status code {scraping_response.status_code}")
            return []
            
        # Try to parse JSON response
        try:
            response_json = scraping_response.json()
        except ValueError:
            print(f"Invalid JSON response from API")
            return []
            
        if 'snapshot_id' not in response_json:
            print(f"No snapshot_id in response")
            return []
            
        snapshot_id = response_json['snapshot_id']
        
        # Track progress
        tacking_url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
        status_response = requests.get(tacking_url, headers=headers)
        
        # Add timeout to prevent infinite waiting
        start_time = time.time()
        timeout = 60  # seconds
        
        while status_response.json()['status'] != "ready":
            if time.time() - start_time > timeout:
                print(f"Timeout waiting for scraping to complete after {timeout} seconds")
                return []
                
            time.sleep(10)
            status_response = requests.get(tacking_url, headers=headers)
            print(f"Scraping progress: {status_response.json().get('progress', 'N/A')}%")

        print(f"Scraping {scraping_type} completed successfully")

        # Get results
        output_url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}"
        params = {"format": "json"}
        output_response = requests.get(output_url, headers=headers, params=params)
        
        try:
            return output_response.json()
        except ValueError:
            print(f"Invalid JSON in results")
            return []
            
    except Exception as e:
        print(f"Scraping error: {str(e)}")
        return []