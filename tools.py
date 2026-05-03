import os
import requests

# ─── Tool Definitions ───────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "get_property_data",
        "description": "Get detailed property data including value, owner, last sale, lot size, and structure details from a property address.",
        "input_schema": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Full property address e.g. '123 Main St, Austin, TX 78701'"
                }
            },
            "required": ["address"]
        }
    },
    {
        "name": "get_property_owner",
        "description": "Get owner information and sale history for a property.",
        "input_schema": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Full property address"
                }
            },
            "required": ["address"]
        }
    },
    {
        "name": "search_web",
        "description": "Search the web for additional property information such as permits, HOA details, or neighborhood info.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    }
]


# ─── Tool Executor ───────────────────────────────────────────────────────────

def run_tool(tool_name, tool_input):
    if tool_name == "get_property_data":
        return get_property_data(tool_input["address"])
    elif tool_name == "get_property_owner":
        return get_property_owner(tool_input["address"])
    elif tool_name == "search_web":
        return search_web(tool_input["query"])
    else:
        return f"Unknown tool: {tool_name}"


# ─── Rentcast API Functions ──────────────────────────────────────────────────

def get_property_data(address):
    """Get property details from Rentcast API"""
    api_key = os.getenv("RENTCAST_API_KEY")
    
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    params = {"address": address}
    
    try:
        # Get property details
        response = requests.get(
            "https://api.rentcast.io/v1/properties",
            headers=headers,
            params=params
        )
        
        if response.status_code != 200:
            return f"Error fetching property data: {response.status_code} - {response.text}"
        
        data = response.json()
        
        if not data:
            return "No property data found for this address."
        
        # Handle both list and dict responses
        prop = data[0] if isinstance(data, list) else data
        
        # Format the data cleanly for Claude
        result = f"""
PROPERTY DATA FROM RENTCAST:
Address: {prop.get('formattedAddress', 'N/A')}
Property Type: {prop.get('propertyType', 'N/A')}
Bedrooms: {prop.get('bedrooms', 'N/A')}
Bathrooms: {prop.get('bathrooms', 'N/A')}
Square Footage: {prop.get('squareFootage', 'N/A')} sqft
Lot Size: {prop.get('lotSize', 'N/A')} sqft
Year Built: {prop.get('yearBuilt', 'N/A')}
Last Sale Price: ${prop.get('lastSalePrice', 'N/A'):,} if isinstance(prop.get('lastSalePrice'), int) else {prop.get('lastSalePrice', 'N/A')}
Last Sale Date: {prop.get('lastSaleDate', 'N/A')}
HOA Fee: {prop.get('hoaFee', 'None')}
County: {prop.get('county', 'N/A')}
APN: {prop.get('assessorParcelNumber', 'N/A')}
"""
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"


def get_property_owner(address):
    """Get owner and valuation data from Rentcast"""
    api_key = os.getenv("RENTCAST_API_KEY")
    
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        # Get valuation
        val_response = requests.get(
            "https://api.rentcast.io/v1/avm/value",
            headers=headers,
            params={"address": address}
        )
        
        result = "VALUATION DATA:\n"
        
        if val_response.status_code == 200:
            val = val_response.json()
            price = val.get('price', 'N/A')
            price_low = val.get('priceLow', 'N/A')
            price_high = val.get('priceHigh', 'N/A')
            result += f"""
Estimated Value: ${price:,} if isinstance(price, int) else {price}
Value Range: ${price_low:,} - ${price_high:,} if isinstance(price_low, int) else {price_low} - {price_high}
"""
        else:
            result += f"Valuation not available: {val_response.status_code}\n"
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"


def search_web(query):
    """Search the web using Google Custom Search API"""
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CX")
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": 5
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if "items" not in data:
            return "No results found."
        
        results = []
        for item in data["items"]:
            results.append(f"Title: {item['title']}\nURL: {item['link']}\nSnippet: {item['snippet']}\n")
        
        return "\n---\n".join(results)
        
    except Exception as e:
        return f"Search error: {str(e)}"


# ─── Google Photo URLs ───────────────────────────────────────────────────────

def get_street_view_url(address):
    api_key = os.getenv("GOOGLE_API_KEY")
    encoded = requests.utils.quote(address)
    return f"https://maps.googleapis.com/maps/api/streetview?size=800x400&location={encoded}&key={api_key}"


def get_aerial_url(address):
    api_key = os.getenv("GOOGLE_API_KEY")
    encoded = requests.utils.quote(address)
    return f"https://maps.googleapis.com/maps/api/staticmap?center={encoded}&zoom=18&size=800x400&maptype=satellite&key={api_key}"