import streamlit as st
import base64
import gc
import os
import sys

# Attempt to patch the sqlite3 issue with the minimal approach
try:
    import sqlite3
    print(f"Current SQLite version: {sqlite3.sqlite_version}")
    
    # Try to replace sqlite3 with pysqlite3
    try:
        import pysqlite3
        print("Successfully imported pysqlite3, replacing sqlite3")
        sys.modules["sqlite3"] = pysqlite3
        print("Replaced sqlite3 with pysqlite3")
    except ImportError:
        print("Could not import pysqlite3")
except Exception as e:
    print(f"Error checking SQLite: {str(e)}")

# Try to patch chromadb directly
try:
    # Monkey patch chromadb's SQLite version check before importing
    import importlib.util
    spec = importlib.util.find_spec('chromadb')
    if spec:
        module_path = spec.origin
        if os.path.isfile(module_path):
            with open(module_path, 'r') as f:
                content = f.read()
            
            # Replace the version check
            patched_content = content.replace(
                "if not has_pysqlite and not sqlite_version_info >= (3, 35, 0):",
                "if False:  # Patched by Streamlit app"
            )
            
            # Write back
            try:
                with open(module_path, 'w') as f:
                    f.write(patched_content)
                print("Successfully patched chromadb module")
            except Exception as e:
                print(f"Failed to write to {module_path}: {str(e)}")
except Exception as e:
    print(f"Error patching chromadb: {str(e)}")

# Create a special error handler that will show a friendly message
def special_import():
    try:
        import brand_monitoring_flow.main
        from dotenv import load_dotenv
        return True, None, brand_monitoring_flow.main
    except RuntimeError as e:
        if "Your system has an unsupported version of sqlite3" in str(e):
            return False, "SQLite version issue. Using simplified mode.", None
        else:
            return False, str(e), None
    except Exception as e:
        return False, str(e), None

# Try to import with our error handler
success, error_message, brand_monitoring_flow_main = special_import()

if not success:
    # Show a simplified version of the app if we can't load the main package
    st.title("Brand Monitoring - Simplified Mode")
    st.warning(f"The app is running in simplified mode due to environment limitations: {error_message}")
    
    st.markdown("""
    ## Welcome to Brand Monitoring
    
    This application is designed to monitor brand mentions across social media platforms.
    
    ### How it works:
    1. The app searches for mentions of your brand across LinkedIn, Instagram, X/Twitter and YouTube
    2. It uses AI to analyze sentiment and summarize the findings
    3. Results are presented in an easy-to-digest format
    
    ### Deployment Issue:
    There's currently a technical issue with the SQLite database version on Streamlit Cloud.
    Please try running this app locally for full functionality.
    
    ### Local Setup:
    ```bash
    git clone https://github.com/kthandra777/Agents.git
    cd Agents
    pip install -r requirements.txt
    streamlit run brand-monitoring/brand_monitoring_flow/src/brand_monitoring_app.py
    ```
    """)
    
    st.sidebar.title("About")
    st.sidebar.info("This is a simplified version of the Brand Monitoring app due to deployment constraints.")
    
else:
    # If we've successfully imported everything, run the normal app
    import brand_monitoring_flow.main
    from dotenv import load_dotenv
    
    # Load environment variables from .env file if available
    load_dotenv()
    
    # ===========================
    #   Streamlit Setup
    # ===========================
    
    if "response" not in st.session_state:
        st.session_state.response = None
    
    if "flow" not in st.session_state:
        st.session_state.flow = None
    
    if "api_keys" not in st.session_state:
        st.session_state.api_keys = {
            "groq_api_key": os.getenv("GROQ_API_KEY", ""),
            "bright_data_username": os.getenv("BRIGHT_DATA_USERNAME", ""),
            "bright_data_password": os.getenv("BRIGHT_DATA_PASSWORD", ""),
            "bright_data_api_key": os.getenv("BRIGHT_DATA_API_KEY", "")
        }
    
    # Load images for UI
    if "deep_seek_image" not in st.session_state:
        try:
            st.session_state.deep_seek_image = base64.b64encode(open("assets/deep-seek.png", "rb").read()).decode()
        except:
            st.session_state.deep_seek_image = ""
    
    if "brightdata_image" not in st.session_state:
        try:
            st.session_state.brightdata_image = base64.b64encode(open("assets/brightdata.png", "rb").read()).decode()
        except:
            st.session_state.brightdata_image = ""
    
    def reset_analysis():
        """Reset the analysis state and clear memory"""
        st.session_state.response = None
        st.session_state.flow = None
        gc.collect()
    
    
    def start_analysis():
        """Start the brand monitoring analysis process"""
        # Validate API keys
        if not st.session_state.api_keys["groq_api_key"]:
            st.error("Groq API key is required")
            return
        
        if (not st.session_state.api_keys["bright_data_username"] or 
            not st.session_state.api_keys["bright_data_password"] or 
            not st.session_state.api_keys["bright_data_api_key"]):
            st.error("All Bright Data credentials are required")
            return
        
        # Set environment variables for the API keys
        os.environ["GROQ_API_KEY"] = st.session_state.api_keys["groq_api_key"]
        os.environ["BRIGHT_DATA_USERNAME"] = st.session_state.api_keys["bright_data_username"]
        os.environ["BRIGHT_DATA_PASSWORD"] = st.session_state.api_keys["bright_data_password"]
        os.environ["BRIGHT_DATA_API_KEY"] = st.session_state.api_keys["bright_data_api_key"]
        
        # Display header
        st.markdown("""
                # Brand Monitoring powered by Groq & <img src="data:image/png;base64,{}" width="180" style="vertical-align: -10px;">
            """.format(
                st.session_state.brightdata_image
            ), unsafe_allow_html=True)
        
        # Create a placeholder for status updates
        status_placeholder = st.empty()
        
        with status_placeholder.container():
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            try:
                # Step 1: Initialize flow
                progress_text.text("Initializing brand monitoring flow...")
                progress_bar.progress(10)
                
                st.session_state.flow = brand_monitoring_flow.main.BrandMonitoringFlow()
            
                st.session_state.flow.state.brand_name = st.session_state.brand_name
                st.session_state.flow.state.total_results = st.session_state.total_results
                st.session_state.flow.state.llm_provider = "groq"  # Specify to use Groq
                
                # Step 2: Web search
                progress_text.text(f"Searching for mentions of {st.session_state.brand_name}...")
                progress_bar.progress(30)
                
                # Step 3: Analyzing results
                progress_text.text(f"Analyzing mentions with Groq LLM...")
                progress_bar.progress(50)
                
                # Kick off the flow
                st.session_state.flow.kickoff()
                
                # Step 4: Processing results
                progress_text.text("Processing analysis results...")
                progress_bar.progress(80)
                
                # Store the results
                st.session_state.response = st.session_state.flow.state
                
                # Step 5: Completed
                progress_bar.progress(100)
                progress_text.text("Analysis complete!")
                
                # Check if we actually got any results
                has_results = False
                if st.session_state.response:
                    if (hasattr(st.session_state.response, 'linkedin_crew_response') and st.session_state.response.linkedin_crew_response or 
                        hasattr(st.session_state.response, 'instagram_crew_response') and st.session_state.response.instagram_crew_response or 
                        hasattr(st.session_state.response, 'youtube_crew_response') and st.session_state.response.youtube_crew_response or 
                        hasattr(st.session_state.response, 'x_crew_response') and st.session_state.response.x_crew_response):
                        has_results = True
                
                if not has_results:
                    st.warning('No analysis results available. The search found some content, but the AI analysis failed. Try a different brand or check console logs.')
                    
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(error_details)
                st.error(f"An error occurred: {str(e)}")
                st.code(error_details, language="python")
    
    # ===========================
    #   Sidebar
    # ===========================
    with st.sidebar:
        st.header("Brand Monitoring Settings")
        
        # API Keys section
        st.subheader("API Keys")
        
        # Groq API Key
        groq_api_key = st.text_input(
            "Groq API Key",
            value=st.session_state.api_keys["groq_api_key"],
            type="password",
            help="Get your API key from https://console.groq.com/keys"
        )
        
        # Bright Data credentials
        bright_data_username = st.text_input(
            "Bright Data Username",
            value=st.session_state.api_keys["bright_data_username"],
            help="Your Bright Data account username"
        )
        
        bright_data_password = st.text_input(
            "Bright Data Password",
            value=st.session_state.api_keys["bright_data_password"],
            type="password"
        )
        
        bright_data_api_key = st.text_input(
            "Bright Data API Key",
            value=st.session_state.api_keys["bright_data_api_key"],
            type="password",
            help="Get your API key from Bright Data dashboard"
        )
        
        # Update session state with the entered API keys
        st.session_state.api_keys["groq_api_key"] = groq_api_key
        st.session_state.api_keys["bright_data_username"] = bright_data_username
        st.session_state.api_keys["bright_data_password"] = bright_data_password
        st.session_state.api_keys["bright_data_api_key"] = bright_data_api_key
        
        st.divider()
        
        # Brand name input
        st.markdown("### Enter Any Brand Name")
        st.session_state.brand_name = st.text_input(
            "Type any company or brand name",
            value="Hugging Face" if "brand_name" not in st.session_state else st.session_state.brand_name,
            help="Enter any brand name you want to monitor. This can be any company, product, or service."
        )
        
        # Example brands for easy testing
        st.write("Or try one of these popular brands:")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Microsoft"):
                st.session_state.brand_name = "Microsoft"
        with col2:
            if st.button("Tesla"):
                st.session_state.brand_name = "Tesla"
        with col3:
            if st.button("Apple"):
                st.session_state.brand_name = "Apple"
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Google"):
                st.session_state.brand_name = "Google"
        with col2:
            if st.button("Netflix"):
                st.session_state.brand_name = "Netflix"
        with col3:
            if st.button("Spotify"):
                st.session_state.brand_name = "Spotify"
        
        st.divider()
        
        # Number of search results
        st.session_state.total_results = st.number_input(
            "Total Search Results (max 5 per platform)",
            min_value=1,
            max_value=5,
            value=5,
            step=1,
            help="Maximum number of results to search for each platform"
        )
    
        st.divider()
        
        # Analysis buttons
        col1, col2 = st.columns(2)
        with col1:
            st.button("Start Analysis 🚀", type="primary", on_click=start_analysis)
        with col2:
            st.button("Reset", on_click=reset_analysis)
    
    # ===========================
    #   Main Content Area
    # ===========================
    
    # Move the header inside a container to ensure it stays at the top
    if st.session_state.response is None:
        header_container = st.container()
        with header_container:
            st.markdown("""
                # Brand Monitoring powered by Groq & <img src="data:image/png;base64,{}" width="180" style="vertical-align: -10px;">
            """.format(
                st.session_state.brightdata_image
            ), unsafe_allow_html=True)
    
    # Display results if available
    if st.session_state.response:
        try:
            response = st.session_state.response
            
            # Debug: Print out what's in each response
            st.sidebar.markdown("### Debug Info")
            if hasattr(response, 'linkedin_crew_response'):
                st.sidebar.markdown(f"LinkedIn response: {'Has content' if response.linkedin_crew_response else 'Empty'}")
                if response.linkedin_crew_response:
                    st.sidebar.markdown(f"- Has pydantic attr: {hasattr(response.linkedin_crew_response, 'pydantic')}")
                    if hasattr(response.linkedin_crew_response, 'pydantic'):
                        st.sidebar.markdown(f"- Has content attr: {hasattr(response.linkedin_crew_response.pydantic, 'content')}")
                        if hasattr(response.linkedin_crew_response.pydantic, 'content'):
                            st.sidebar.markdown(f"- Content length: {len(response.linkedin_crew_response.pydantic.content)}")
            if hasattr(response, 'youtube_crew_response'):
                st.sidebar.markdown(f"YouTube response: {'Has content' if response.youtube_crew_response else 'Empty'}")
                if response.youtube_crew_response:
                    st.sidebar.markdown(f"- Has pydantic attr: {hasattr(response.youtube_crew_response, 'pydantic')}")
                    if hasattr(response.youtube_crew_response, 'pydantic'):
                        st.sidebar.markdown(f"- Has content attr: {hasattr(response.youtube_crew_response.pydantic, 'content')}")
                        if hasattr(response.youtube_crew_response.pydantic, 'content'):
                            st.sidebar.markdown(f"- Content length: {len(response.youtube_crew_response.pydantic.content)}")
            if hasattr(response, 'instagram_crew_response'):
                st.sidebar.markdown(f"Instagram response: {'Has content' if response.instagram_crew_response else 'Empty'}")
                if response.instagram_crew_response:
                    st.sidebar.markdown(f"- Has pydantic attr: {hasattr(response.instagram_crew_response, 'pydantic')}")
                    if hasattr(response.instagram_crew_response, 'pydantic'):
                        st.sidebar.markdown(f"- Has content attr: {hasattr(response.instagram_crew_response.pydantic, 'content')}")
                        if hasattr(response.instagram_crew_response.pydantic, 'content'):
                            st.sidebar.markdown(f"- Content length: {len(response.instagram_crew_response.pydantic.content)}")
            if hasattr(response, 'x_crew_response'):
                st.sidebar.markdown(f"X/Twitter response: {'Has content' if response.x_crew_response else 'Empty'}")
                if response.x_crew_response:
                    st.sidebar.markdown(f"- Has pydantic attr: {hasattr(response.x_crew_response, 'pydantic')}")
                    if hasattr(response.x_crew_response, 'pydantic'):
                        st.sidebar.markdown(f"- Has content attr: {hasattr(response.x_crew_response.pydantic, 'content')}")
                        if hasattr(response.x_crew_response.pydantic, 'content'):
                            st.sidebar.markdown(f"- Content length: {len(response.x_crew_response.pydantic.content)}")
            
            # Check if we have any actual results
            has_results = False
            
            # LinkedIn Results
            if response.linkedin_crew_response:
                has_results = True
                st.markdown("## 💼 LinkedIn Mentions")
                for post in response.linkedin_crew_response.pydantic.content:
                    with st.expander(f"📝 {post.post_title}"):
                        st.markdown(f"**Source:** [{post.post_link}]({post.post_link})")
                        for line in post.content_lines:
                            st.markdown(f"- {line}")
            
            # Instagram Results
            if response.instagram_crew_response:
                has_results = True
                st.markdown("## 📸 Instagram Mentions")
                for post in response.instagram_crew_response.pydantic.content:
                    with st.expander(f"📝 {post.post_title}"):
                        st.markdown(f"**Source:** [{post.post_link}]({post.post_link})")
                        for line in post.content_lines:
                            st.markdown(f"- {line}")
            
            # YouTube Results
            if response.youtube_crew_response:
                has_results = True
                st.markdown("## 🎥 YouTube Mentions")
                for video in response.youtube_crew_response.pydantic.content:
                    with st.expander(f"📝 {video.video_title}"):
                        st.markdown(f"**Source:** [{video.video_link}]({video.video_link})")
                        for line in video.content_lines:
                            st.markdown(f"- {line}")
            
            # X/Twitter Results
            if response.x_crew_response:
                has_results = True
                st.markdown("## 🐦 X/Twitter Mentions")
                for post in response.x_crew_response.pydantic.content:
                    with st.expander(f"📝 {post.post_title}"):
                        st.markdown(f"**Source:** [{post.post_link}]({post.post_link})")
                        for line in post.content_lines:
                            st.markdown(f"- {line}")
            
            # Always show raw URLs section regardless of AI processing success
            st.markdown("---")
            st.markdown("## 🔍 Raw Search Results")
            st.markdown("Below are all URLs found before AI processing")
            
            if hasattr(response, 'linkedin_search_response') and response.linkedin_search_response:
                st.markdown("### 💼 LinkedIn URLs Found")
                for item in response.linkedin_search_response:
                    st.markdown(f"- [{item.get('title', 'LinkedIn post')}]({item.get('link', '#')})")
            
            if hasattr(response, 'instagram_search_response') and response.instagram_search_response:
                st.markdown("### 📸 Instagram URLs Found")
                for item in response.instagram_search_response:
                    st.markdown(f"- [{item.get('title', 'Instagram post')}]({item.get('link', '#')})")
            
            if hasattr(response, 'youtube_search_response') and response.youtube_search_response:
                st.markdown("### 🎥 YouTube URLs Found")
                for item in response.youtube_search_response:
                    st.markdown(f"- [{item.get('title', 'YouTube video')}]({item.get('link', '#')})")
            
            if hasattr(response, 'x_search_response') and response.x_search_response:
                st.markdown("### 🐦 X/Twitter URLs Found")
                for item in response.x_search_response:
                    st.markdown(f"- [{item.get('title', 'X/Twitter post')}]({item.get('link', '#')})")
                    
            # If no AI-processed results, keep the existing warning
            if not has_results:
                st.warning("The AI analysis couldn't process the results properly. Please see the raw URLs above.")
    
        except Exception as e:
            st.error(f"An error occurred while displaying results: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown("Built with CrewAI, Groq, Bright Data and Streamlit") 