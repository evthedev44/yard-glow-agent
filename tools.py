import os
import requests

# ─── Tool Definitions ───────────────────────────────────────────────────────
# These tell Claude what tools exist and when to use them

TOOLS = [
    {
        "name": "search_web",
        "description": "Search the web for property information, owner details, tax records, permits, and any other public data about a property or address.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Be specific — include the full address and what you're looking for. Example: '4821 Barton Creek Blvd Austin TX owner history tax record'"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "fetch_page",
        "description": "Fetch the full content of a webpage to extract property details, tax records, or permit information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL of the page to fetch"
                }
            },
            "required": ["url"]
        }
    }
]


# ─── Tool Executor ───────────────────────────────────────────────────────────
# This actually runs the tool when Claude asks for it

def run_tool(tool_name, tool_input):
    if tool_name == "search_web":
        return search_web(tool_input["query"])
    elif tool_name == "fetch_page":
        return fetch_page(tool_input["url"])
    else:
        return f"Unknown tool: {tool_name}"


# ─── Individual Tool Functions ───────────────────────────────────────────────

def search_web(query):
    """Search the web using Google Custom Search API"""
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CX")  # Custom Search Engine ID

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": 5  # return top 5 results
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if "items" not in data:
            return "No results found for this search."

        results = []
        for item in data["items"]:
            results.append(f"Title: {item['title']}\nURL: {item['link']}\nSnippet: {item['snippet']}\n")

        return "\n---\n".join(results)

    except Exception as e:
        return f"Search error: {str(e)}"


def fetch_page(url):
    """Fetch the text content of a webpage"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        
        # Very basic HTML stripping — just get the text
        text = response.text
        
        # Remove script and style blocks
        import re
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Return first 3000 characters — enough for Claude to extract what it needs
        return text[:3000]

    except Exception as e:
        return f"Error fetching page: {str(e)}"


def get_street_view_url(address):
    """Generate a Google Street View image URL for the property"""
    api_key = os.getenv("GOOGLE_API_KEY")
    encoded = requests.utils.quote(address)
    return f"https://maps.googleapis.com/maps/api/streetview?size=800x400&location={encoded}&key={api_key}"


def get_aerial_url(address):
    """Generate a Google Maps Static aerial image URL for the property"""
    api_key = os.getenv("GOOGLE_API_KEY")
    encoded = requests.utils.quote(address)
    return f"https://maps.googleapis.com/maps/api/staticmap?center={encoded}&zoom=18&size=800x400&maptype=satellite&key={api_key}"