# Brand Monitoring

A powerful brand monitoring application that analyzes brand mentions across multiple social media platforms including LinkedIn, Instagram, X/Twitter, and YouTube.

## Features

- **Multi-Platform Monitoring**: Track brand mentions across LinkedIn, Instagram, X/Twitter, and YouTube
- **AI-Powered Analysis**: Uses Groq LLM for analyzing and summarizing brand mentions
- **Interactive UI**: Built with Streamlit for easy navigation and visualization
- **Real-time Data**: Fetches real-time data using Bright Data web scraping services

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your API keys (see `.env.example`)
4. Run the application: `streamlit run src/brand_monitoring_app.py`

## Required API Keys

- Groq API Key (for LLM processing)
- Bright Data credentials (username, password, API key for web scraping)

## Built With

- [CrewAI](https://github.com/joaomdmoura/crewAI) - Multi-agent framework
- [Groq](https://groq.com/) - Fast LLM API
- [Bright Data](https://brightdata.com/) - Web scraping services
- [Streamlit](https://streamlit.io/) - UI framework 