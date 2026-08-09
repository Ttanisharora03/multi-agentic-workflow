from tavily import TavilyClient # type: ignore[import-untyped]
import os

def search_dubai_info(query: str) -> str:
    """
    Uses the Tavily Search API to find live information about Dubai, such as 
    events, opening hours, or reviews.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return f"Web search skipped: TAVILY_API_KEY not configured. Mocking search for: {query}"
        
    client = TavilyClient(api_key=api_key)
    try:
        response = client.search(
            query=f"Dubai: {query}",
            search_depth="basic",
            max_results=3
        )
        results = response.get("results", [])
        if not results:
            return "No recent search results found."
            
        formatted_results = [
            f"- {res['title']}: {res['content']}" for res in results
        ]
        return "\n".join(formatted_results)
    except Exception as e:
        return f"Web search failed: {str(e)}"
