import streamlit as st
import base64
import gc
import os
import sys

# Add parent directory to path so we can import our fix modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Custom fix for ChromaDB SQLite issue on Streamlit Cloud
fix_applied = False
methods_tried = []

try:
    # Method 1: Try to apply our ChromaDB patch
    import chromadb_fix
    fix_applied = chromadb_fix.apply_patch()
    methods_tried.append("ChromaDB patch")
    
    # Method 2: If that fails, try the dummy implementation
    if not fix_applied:
        import chromadb_dummy
        fix_applied = chromadb_dummy.apply_dummy()
        methods_tried.append("Dummy implementation")
        
    if fix_applied:
        st.sidebar.success(f"SQLite compatibility issue fixed using: {methods_tried[-1]}")
    else:
        st.sidebar.warning("Could not fix SQLite compatibility issue. Some features may not work.")
        st.sidebar.info("Tried methods: " + ", ".join(methods_tried))
        
except Exception as e:
    st.sidebar.error(f"Error applying SQLite fixes: {str(e)}")

# Continue with normal imports
try:
    import brand_monitoring_flow.main
    from dotenv import load_dotenv
except Exception as e:
    st.error(f"Error importing required modules: {str(e)}")
    st.code(str(e), language="python")
    st.info("If you're seeing a SQLite error, please check the sidebar for compatibility solutions.")
    raise e

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
    st.session_state.deep_seek_image = base64.b64encode(open("assets/deep-seek.png", "rb").read()).decode()
if "brightdata_image" not in st.session_state:
    st.session_state.brightdata_image = base64.b64encode(open("assets/brightdata.png", "rb").read()).decode()

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
        if hasattr(response, 'instagram_crew_response'):
            st.sidebar.markdown(f"Instagram response: {'Has content' if response.instagram_crew_response else 'Empty'}")
            if response.instagram_crew_response:
                st.sidebar.markdown(f"- Has pydantic attr: {hasattr(response.instagram_crew_response, 'pydantic')}")
                if hasattr(response.instagram_crew_response, 'pydantic'):
                    st.sidebar.markdown(f"- Has content attr: {hasattr(response.instagram_crew_response.pydantic, 'content')}")
                    if hasattr(response.instagram_crew_response.pydantic, 'content'):
                        st.sidebar.markdown(f"- Content length: {len(response.instagram_crew_response.pydantic.content)}")
        if hasattr(response, 'youtube_crew_response'):
            st.sidebar.markdown(f"YouTube response: {'Has content' if response.youtube_crew_response else 'Empty'}")
            if response.youtube_crew_response:
                st.sidebar.markdown(f"- Has pydantic attr: {hasattr(response.youtube_crew_response, 'pydantic')}")
                if hasattr(response.youtube_crew_response, 'pydantic'):
                    st.sidebar.markdown(f"- Has content attr: {hasattr(response.youtube_crew_response.pydantic, 'content')}")
                    if hasattr(response.youtube_crew_response.pydantic, 'content'):
                        st.sidebar.markdown(f"- Content length: {len(response.youtube_crew_response.pydantic.content)}")
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