from crewai import LLM
import os

def get_llm(provider=None, model=None):
    """
    Get the appropriate LLM based on provider and model
    
    Args:
        provider (str): The LLM provider ('groq' or 'ollama')
        model (str): The specific model to use
    
    Returns:
        LLM instance configured for use with CrewAI
    """
    # Default to environment variable or 'ollama' if not specified
    provider = provider or os.getenv("LLM_PROVIDER", "ollama")
    
    if provider.lower() == "groq":
        # Get API key from environment
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable must be set to use Groq")
        
        # Default model for Groq is llama3-70b-8192
        base_model = model or os.getenv("GROQ_MODEL", "llama3-70b-8192")
        
        # For Groq, use groq/model_name format for LiteLLM
        groq_model = f"groq/{base_model}"
        print(f"Using Groq model: {groq_model}")
        
        return LLM(
            model=groq_model,  # Using the format groq/model_name
            api_key=api_key,
            temperature=0.2
        )
    else:
        # Default to Ollama with deepseek-r1 model
        model = model or os.getenv("OLLAMA_MODEL", "deepseek-r1")
        
        # For Ollama, we need to use ollama/model_name format to work with LiteLLM
        ollama_model = f"ollama/{model}"
        print(f"Using Ollama model: {ollama_model}")
        
        return LLM(
            model=ollama_model,  # Using the format ollama/model_name
            temperature=0.2
        ) 