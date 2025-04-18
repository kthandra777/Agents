#!/usr/bin/env python
from pydantic import BaseModel

from crewai.flow import Flow, listen, start
import requests
import asyncio
import time
import os

from brand_monitoring_flow.crews.youtube_crew.youtube_crew import YoutubeCrew, YoutubeReport, YoutubeWriterReport
from brand_monitoring_flow.crews.instagram_crew.instagram_crew import InstagramCrew, InstagramReport, InstagramWriterReport
from brand_monitoring_flow.crews.linkedin_crew.linkedin_crew import LinkedInCrew, LinkedInReport, LinkedInWriterReport
from brand_monitoring_flow.crews.X_crew.X_crew import XCrew, XReport, XWriterReport
# Commented out web crew import as we're disabling web scraping
# from brand_monitoring_flow.crews.web_crew.web_crew import WebCrew, WebReport, WebWriterReport

from brand_monitoring_flow.tools.custom_tool import BrightDataWebSearchTool, scrape_urls

class BrandMonitoringState(BaseModel):
    """
    State model for the Brand Monitoring flow.
    
    Attributes:
        total_results: Number of search results to retrieve per platform
        brand_name: Name of the brand to monitor
        llm_provider: LLM provider to use (groq or ollama)
        search_response: Raw search results
        *_search_response: Platform-specific search results
        *_scrape_response: Raw scraping results
        *_filtered_scrape_response: Filtered scraping results
        *_crew_response: AI-analyzed results for each platform
    """
    total_results: int = 5  # Limiting to max 5 results
    brand_name: str = "Browserbase"
    llm_provider: str = "ollama"  # Default to ollama, can be set to "groq"
    search_response: list[dict] = []

    # Platform-specific search results
    linkedin_search_response: list[dict] = []
    instagram_search_response: list[dict] = []
    youtube_search_response: list[dict] = []
    x_search_response: list[dict] = []
    # Commented out web search fields
    # web_search_response: list[dict] = []

    # Raw scraping results
    linkedin_scrape_response: list[dict] = []
    instagram_scrape_response: list[dict] = []
    youtube_scrape_response: list[dict] = []
    x_scrape_response: list[dict] = []
    # Commented out web scrape fields
    # web_scrape_response: list[dict] = []

    # Filtered scraping results
    linkedin_filtered_scrape_response: list[dict] = []
    instagram_filtered_scrape_response: list[dict] = []
    youtube_filtered_scrape_response: list[dict] = []
    x_filtered_scrape_response: list[dict] = []
    # Commented out web filtered fields
    # web_filtered_scrape_response: list[dict] = []
    
    # AI-analyzed results
    linkedin_crew_response: LinkedInReport = None
    instagram_crew_response: InstagramReport = None
    youtube_crew_response: YoutubeReport = None
    x_crew_response: XReport = None
    # Commented out web crew response
    # web_crew_response: WebReport = None

class BrandMonitoringFlow(Flow[BrandMonitoringState]):
    """
    Main flow orchestrating the brand monitoring process.
    
    This flow handles:
    1. Searching for brand mentions across platforms
    2. Scraping the content from found URLs
    3. Analyzing the content using AI
    4. Generating reports for each platform
    """

    @start()
    def scrape_data(self):
        """
        Start the flow by searching for brand mentions and categorizing by platform.
        """
        print(f"Initiating brand monitoring for: {self.state.brand_name}")
        
        # Set environment variable for LLM provider right at the start
        os.environ["LLM_PROVIDER"] = self.state.llm_provider
        print(f"Using LLM provider: {self.state.llm_provider}")
        
        if self.state.llm_provider == "groq":
            os.environ["GROQ_MODEL"] = "llama3-70b-8192"
        else:
            os.environ["OLLAMA_MODEL"] = "deepseek-r1"
        
        # Search for brand mentions
        web_search_tool = BrightDataWebSearchTool()
        self.state.search_response = web_search_tool._run(self.state.brand_name, total_results=self.state.total_results)
        
        # Categorize results by platform
        if not self.state.search_response:
            print("No search results found. Check Bright Data credentials.")
            return
            
        # Process based on site type
        for r in self.state.search_response:
            url = r.get('link', '').lower()
            
            # LinkedIn - match any linkedin.com URL
            if "linkedin.com" in url:
                if len(self.state.linkedin_search_response) < 5:
                    print(f"Found LinkedIn result: {url}")
                    self.state.linkedin_search_response.append(r)
            
            # Instagram - match any instagram.com URL
            elif "instagram.com" in url:
                if len(self.state.instagram_search_response) < 5:
                    print(f"Found Instagram result: {url}")
                    self.state.instagram_search_response.append(r)
            
            # YouTube - match any youtube.com URL
            elif "youtube.com" in url or "youtu.be" in url:
                if len(self.state.youtube_search_response) < 5:
                    print(f"Found YouTube result: {url}")
                    self.state.youtube_search_response.append(r)
            
            # X/Twitter - more flexible matching for twitter URLs
            elif ("x.com" in url or "twitter.com" in url):
                if len(self.state.x_search_response) < 5:
                    print(f"Found X/Twitter result: {url}")
                    self.state.x_search_response.append(r)
            
        # Print counts of each platform's results
        print(f"Search results found - LinkedIn: {len(self.state.linkedin_search_response)}, " +
              f"Instagram: {len(self.state.instagram_search_response)}, " +
              f"YouTube: {len(self.state.youtube_search_response)}, " +
              f"X/Twitter: {len(self.state.x_search_response)}")

    @listen(scrape_data)
    async def scrape_data_and_analyse(self):
        """
        Scrape content from found URLs and analyze with AI for each platform.
        """
        print(f"Using LLM provider: {os.environ.get('LLM_PROVIDER')}")
        
        # Check if we have any results to process
        if (len(self.state.linkedin_search_response) == 0 and 
            len(self.state.instagram_search_response) == 0 and
            len(self.state.youtube_search_response) == 0 and
            len(self.state.x_search_response) == 0):
            print("No search results found for any platform. No analysis will be performed.")
        
        async def linkedin_analysis():
            """Scrape and analyze LinkedIn content"""
            if not self.state.linkedin_search_response:
                print("No LinkedIn URLs found in search results.")
                return
                
            linkedin_urls = [r['link'] for r in self.state.linkedin_search_response]
            linkedin_params = {"dataset_id": "gd_lyy3tktm25m4avu764"}

            # Scrape LinkedIn content
            try:
                self.state.linkedin_scrape_response = scrape_urls(linkedin_urls, linkedin_params, "linkedin")
                if not self.state.linkedin_scrape_response:
                    print("No LinkedIn content found after scraping.")
                    return
            except Exception as e:
                print(f"LinkedIn scraping error: {str(e)}")
                return

            # Filter and process the content
            for i in self.state.linkedin_scrape_response:
                self.state.linkedin_filtered_scrape_response.append({
                    "url": i["url"],
                    "headline": i.get("headline", "No headline"),
                    "post_text": i.get("post_text", "No post text available"),
                    "hashtags": i.get("hashtags", []),
                    "tagged_companies": i.get("tagged_companies", []),
                    "tagged_people": i.get("tagged_people", []),
                    "original_poster": i.get("user_id", "Unknown user")
                })

            if not self.state.linkedin_filtered_scrape_response:
                print("No LinkedIn content to analyze after filtering.")
                return
            
            # Analyze with AI
            try:
                linkedin_crew = LinkedInCrew()
                self.state.linkedin_crew_response = linkedin_crew.crew().kickoff(inputs={
                    "linkedin_data": self.state.linkedin_filtered_scrape_response, 
                    "brand_name": self.state.brand_name
                })
                if self.state.linkedin_crew_response:
                    print(f"LinkedIn analysis complete with {len(self.state.linkedin_crew_response.pydantic.content)} items")
                else:
                    print("LinkedIn analysis returned no results.")
            except Exception as e:
                print(f"LinkedIn analysis error: {str(e)}")
        
        async def instagram_analysis():
            """Scrape and analyze Instagram content"""
            if not self.state.instagram_search_response:
                print("No Instagram URLs found in search results.")
                return
                
            instagram_urls = [r['link'] for r in self.state.instagram_search_response]
            insta_params = {
                "dataset_id": "gd_lk5ns7kz21pck8jpis",
                "include_errors": "true",
            }

            # Scrape Instagram content
            try:
                self.state.instagram_scrape_response = scrape_urls(instagram_urls, insta_params, "instagram")
                if not self.state.instagram_scrape_response:
                    print("No Instagram content found after scraping.")
                    return
            except Exception as e:
                print(f"Instagram scraping error: {str(e)}")
                return

            # Filter and process the content
            for i in self.state.instagram_scrape_response:
                self.state.instagram_filtered_scrape_response.append({
                    "url": i["url"],
                    "description": i.get("description", "No description available"),
                    "likes": i.get("likes", "0"),
                    "num_comments": i.get("num_comments", "0"),
                    "is_paid_partnership": i.get("is_paid_partnership", False),
                    "followers": i.get("followers", "0"),
                    "original_poster": i.get("user_posted", "Unknown user")
                })

            if not self.state.instagram_filtered_scrape_response:
                print("No Instagram content to analyze after filtering.")
                return
            
            # Analyze with AI
            try:
                instagram_crew = InstagramCrew()
                self.state.instagram_crew_response = instagram_crew.crew().kickoff(inputs={
                    "instagram_data": self.state.instagram_filtered_scrape_response,
                    "brand_name": self.state.brand_name
                })
                if self.state.instagram_crew_response:
                    print(f"Instagram analysis complete with {len(self.state.instagram_crew_response.pydantic.content)} items")
                else:
                    print("Instagram analysis returned no results.")
            except Exception as e:
                print(f"Instagram analysis error: {str(e)}")

        async def youtube_analysis():
            """Scrape and analyze YouTube content"""
            if not self.state.youtube_search_response:
                print("No YouTube URLs found in search results.")
                return
                
            youtube_urls = [r['link'] for r in self.state.youtube_search_response]
            youtube_params = {"dataset_id": "gd_lk56epmy2i5g7lzu0k", "include_errors": "true"} 
            
            # Scrape YouTube content
            try:
                self.state.youtube_scrape_response = scrape_urls(youtube_urls, youtube_params, "youtube")
                if not self.state.youtube_scrape_response:
                    print("No YouTube content found after scraping.")
                    return
            except Exception as e:
                print(f"YouTube scraping error: {str(e)}")
                return

            # Filter and process the content
            for i in self.state.youtube_scrape_response:
                self.state.youtube_filtered_scrape_response.append({
                    "url": i["url"],
                    "title": i.get("title", "No Title"),
                    "description": i.get("description", "No description available"),
                    "original_poster": i.get("youtuber", "Unknown creator"),
                    "verified": i.get("verified", False),
                    "views": i.get("views", "0"),
                    "likes": i.get("likes", "0"),
                    "hashtags": i.get("hashtags", []),
                    "transcript": i.get("transcript", "No transcript available")
                })

            if not self.state.youtube_filtered_scrape_response:
                print("No YouTube content to analyze after filtering.")
                return
            
            # Analyze with AI
            try:
                youtube_crew = YoutubeCrew()
                self.state.youtube_crew_response = youtube_crew.crew().kickoff(inputs={
                    "youtube_data": self.state.youtube_filtered_scrape_response, 
                    "brand_name": self.state.brand_name
                })
                if self.state.youtube_crew_response:
                    print(f"YouTube analysis complete with {len(self.state.youtube_crew_response.pydantic.content)} items")
                else:
                    print("YouTube analysis returned no results.")
            except Exception as e:
                print(f"YouTube analysis error: {str(e)}")

        async def x_analysis():
            """Scrape and analyze X/Twitter content"""
            if not self.state.x_search_response:
                print("No X/Twitter URLs found in search results.")
                return
                
            x_urls = [r['link'] for r in self.state.x_search_response]
            x_params = {
                "dataset_id": "gd_lwxkxvnf1cynvib9co",
                "include_errors": "true",
            }

            # Scrape X/Twitter content
            try:
                self.state.x_scrape_response = scrape_urls(x_urls, x_params, "twitter")
                if not self.state.x_scrape_response:
                    print("No X/Twitter content found after scraping.")
                    return
            except Exception as e:
                print(f"X/Twitter scraping error: {str(e)}")
                return

            # Filter and process the content
            for i in self.state.x_scrape_response:
                self.state.x_filtered_scrape_response.append({
                    "url": i["url"],
                    "views": i.get("views", "0"),
                    "likes": i.get("likes", "0"),
                    "replies": i.get("replies", "0"),
                    "reposts": i.get("reposts", "0"),
                    "hashtags": i.get("hashtags", []),
                    "quotes": i.get("quotes", "0"),
                    "bookmarks": i.get("bookmarks", "0"),
                    "description": i.get("description", "No description available"),
                    "tagged_users": i.get("tagged_users", []),
                    "original_poster": i.get("user_posted", "Unknown user")
                })

            if not self.state.x_filtered_scrape_response:
                print("No X/Twitter content to analyze after filtering.")
                return
            
            # Analyze with AI
            try:
                x_crew = XCrew()
                self.state.x_crew_response = x_crew.crew().kickoff(inputs={
                    "x_data": self.state.x_filtered_scrape_response,
                    "brand_name": self.state.brand_name
                })
                if self.state.x_crew_response:
                    print(f"X/Twitter analysis complete with {len(self.state.x_crew_response.pydantic.content)} items")
                else:
                    print("X/Twitter analysis returned no results.")
            except Exception as e:
                print(f"X/Twitter analysis error: {str(e)}")

        # Commented out web analysis function
        # async def web_analysis():
        #     if self.state.web_search_response:
        #         web_urls = [r['link'] for r in self.state.web_search_response]
        #
        #         print(web_urls)
        #
        #         web_params = {
        #             "dataset_id": "gd_m6gjtfmeh43we6cqc",
        #             "include_errors": "false",
        #             "custom_output_fields": "markdown",
        #         }
        #
        #         self.state.web_scrape_response = scrape_urls(web_urls, web_params, "web")
        #
        #         print(self.state.web_scrape_response)
        #         print(type(self.state.web_scrape_response))
        #
        #         for i in self.state.web_scrape_response:
        #             self.state.web_filtered_scrape_response.append({
        #                 "url": i["url"],
        #                 "markdown": i["markdown"]
        #             })
        #
        #         web_crew = WebCrew()
        #         self.state.web_crew_response = web_crew.crew().kickoff(inputs={"web_data": self.state.web_filtered_scrape_response,
        #                                                                        "brand_name": self.state.brand_name})

        # Create tasks for each platform's analysis
        tasks = [
            asyncio.create_task(linkedin_analysis()),
            asyncio.create_task(instagram_analysis()),
            asyncio.create_task(youtube_analysis()),
            asyncio.create_task(x_analysis()),
            # Removed web_analysis from tasks
        ]

        try:
            # Use gather with return_exceptions=True to prevent one failed task from stopping all others
            await asyncio.gather(*tasks, return_exceptions=True)
            print("Analysis completed for all platforms")
        except Exception as e:
            print(f"Error during task execution: {str(e)}")
            import traceback
            print(traceback.format_exc())
        
        print("Brand monitoring analysis complete")

        if self.state.linkedin_crew_response:   
            for r in self.state.linkedin_crew_response.pydantic.content:
                print(r.post_title)
                print(r.post_link)
                for c in r.content_lines:
                    print("- " + c)
                print("\n")

        if self.state.instagram_crew_response:  
            for r in self.state.instagram_crew_response.pydantic.content:
                print(r.post_title)
                print(r.post_link)
                for c in r.content_lines:
                    print("- " + c)
                print("\n")

        if self.state.youtube_crew_response:
            for r in self.state.youtube_crew_response.pydantic.content:
                print(r.video_title)
                print(r.video_link)
                for c in r.content_lines:
                    print("- " + c)
                print("\n")
        
        if self.state.x_crew_response:
            for r in self.state.x_crew_response.pydantic.content:
                print(r.post_title)
                print(r.post_link)
                for c in r.content_lines:
                    print("- " + c)
                print("\n")

        # Commented out web crew response printing
        # if self.state.web_crew_response:
        #     for r in self.state.web_crew_response.pydantic.content:
        #         print(r.page_title)
        #         print(r.page_link)
        #         for c in r.content_lines:
        #             print("- " + c)
        #         print("\n")


def kickoff():
    """Start the brand monitoring flow"""
    brand_monitoring_flow = BrandMonitoringFlow()
    brand_monitoring_flow.kickoff()


def plot():
    """Plot the flow for visualization"""
    brand_monitoring_flow = BrandMonitoringFlow()
    brand_monitoring_flow.plot()


if __name__ == "__main__":
    kickoff()
