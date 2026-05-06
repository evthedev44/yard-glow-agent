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
        "name": "get_property_valuation",
        "description": "Get estimated market value for a property.",
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
    },
    {
        "name": "get_permits",
        "description": "Get City of Austin building permit history for a property. Shows pools, landscaping, remodels, additions and other permits pulled at the address.",
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
    }
]


# ─── Tool Executor ───────────────────────────────────────────────────────────

def run_tool(tool_name, tool_input):
    if tool_name == "get_property_data":
        return get_property_data(tool_input["address"])
    elif tool_name == "get_property_valuation":
        return get_property_valuation(tool_input["address"])
    elif tool_name == "search_web":
        return search_web(tool_input["query"])
    elif tool_name == "get_permits":
        return get_permits(tool_input["address"])
    else:
        return f"Unknown tool: {tool_name}"


# ─── Rentcast API Functions ──────────────────────────────────────────────────

def get_property_data(address):
    """Get property details from Rentcast API"""
    api_key = os.getenv("RENTCAST_API_KEY")

    if not api_key:
        return "Error: RENTCAST_API_KEY not found in environment variables."

    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(
            "https://api.rentcast.io/v1/properties",
            headers=headers,
            params={"address": address}
        )

        if response.status_code != 200:
            return f"Error fetching property data: {response.status_code} - {response.text}"

        data = response.json()

        if not data:
            return "No property data found for this address."

        prop = data[0] if isinstance(data, list) else data

        # Extract owner info
        owner = prop.get('owner', {})
        owner_names = ', '.join(owner.get('names', ['N/A']))

        # Extract last sale price
        last_sale_price = prop.get('lastSalePrice', 'N/A')
        last_sale_price_fmt = f"${last_sale_price:,}" if isinstance(last_sale_price, (int, float)) else last_sale_price

        # Extract tax assessed value
        tax_assessments = prop.get('taxAssessments', {})
        if tax_assessments:
            latest_year = max(tax_assessments.keys())
            tax_assessed = tax_assessments[latest_year].get('value', 'N/A')
            tax_assessed_fmt = f"${tax_assessed:,}" if isinstance(tax_assessed, (int, float)) else tax_assessed
        else:
            tax_assessed_fmt = 'N/A'

        # Extract property taxes
        property_taxes = prop.get('propertyTaxes', {})
        if property_taxes:
            latest_tax_year = max(property_taxes.keys())
            annual_tax = property_taxes[latest_tax_year].get('total', 'N/A')
            annual_tax_fmt = f"${annual_tax:,}" if isinstance(annual_tax, (int, float)) else annual_tax
        else:
            annual_tax_fmt = 'N/A'

        # Extract features
        features = prop.get('features', {})
        garage = features.get('garage', False)
        fireplace = features.get('fireplace', False)
        pool = features.get('pool', False)
        floor_count = features.get('floorCount', 'N/A')

        # Format lot size in acres
        lot_size_sqft = prop.get('lotSize', 'N/A')
        if isinstance(lot_size_sqft, (int, float)):
            lot_size_acres = round(lot_size_sqft / 43560, 2)
            lot_size_fmt = f"{lot_size_sqft:,} sqft ({lot_size_acres} acres)"
        else:
            lot_size_fmt = lot_size_sqft

        result = f"""
PROPERTY DATA FROM RENTCAST:
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Address:          {prop.get('formattedAddress', 'N/A')}
Owner:            {owner_names}
Owner Occupied:   {prop.get('ownerOccupied', 'N/A')}
Property Type:    {prop.get('propertyType', 'N/A')}
Bedrooms:         {prop.get('bedrooms', 'N/A')}
Bathrooms:        {prop.get('bathrooms', 'N/A')}
Square Footage:   {prop.get('squareFootage', 'N/A'):,} sqft
Lot Size:         {lot_size_fmt}
Year Built:       {prop.get('yearBuilt', 'N/A')}
Stories:          {floor_count}
Garage:           {'Yes' if garage else 'No'}
Fireplace:        {'Yes' if fireplace else 'No'}
Pool:             {'Yes' if pool else 'No'}
Last Sale Price:  {last_sale_price_fmt}
Last Sale Date:   {prop.get('lastSaleDate', 'N/A')}
Tax Assessed:     {tax_assessed_fmt}
Annual Tax:       {annual_tax_fmt}
County:           {prop.get('county', 'N/A')}
Subdivision:      {prop.get('subdivision', 'N/A')}
Legal:            {prop.get('legalDescription', 'N/A')}
"""
        return result

    except Exception as e:
        return f"Error: {str(e)}"


def get_property_valuation(address):
    """Get estimated market value from Rentcast AVM"""
    api_key = os.getenv("RENTCAST_API_KEY")

    if not api_key:
        return "Error: RENTCAST_API_KEY not found in environment variables."

    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(
            "https://api.rentcast.io/v1/avm/value",
            headers=headers,
            params={"address": address}
        )

        if response.status_code != 200:
            return f"Valuation not available: {response.status_code} - {response.text}"

        val = response.json()

        price = val.get('price', 'N/A')
        price_low = val.get('priceLow', 'N/A')
        price_high = val.get('priceHigh', 'N/A')

        price_fmt = f"${price:,}" if isinstance(price, (int, float)) else price
        price_low_fmt = f"${price_low:,}" if isinstance(price_low, (int, float)) else price_low
        price_high_fmt = f"${price_high:,}" if isinstance(price_high, (int, float)) else price_high

        result = f"""
MARKET VALUATION FROM RENTCAST:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Estimated Value:  {price_fmt}
Value Range Low:  {price_low_fmt}
Value Range High: {price_high_fmt}
"""
        return result

    except Exception as e:
        return f"Error: {str(e)}"


# ─── City of Austin Permits ──────────────────────────────────────────────────

def get_permits(address):
    """Get City of Austin permit history for a property"""
    try:
        # Extract street number and name only e.g. "1610 VIRGINIA AVE"
        street = address.split(",")[0].strip().upper()
        encoded = requests.utils.quote(f"{street}%")

        url = f"https://data.austintexas.gov/resource/3syk-w9eu.json?$where=original_address1+like+%27{encoded}%27&$limit=20&$order=issue_date+DESC"

        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return "Permit data not available."

        data = response.json()

        if not data:
            return "No permits found for this address."

        result = f"CITY OF AUSTIN PERMIT HISTORY ({len(data)} permits found):\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        for permit in data:
            issue_date = permit.get('issue_date', 'N/A')[:10] if permit.get('issue_date') else 'N/A'
            result += f"\n[{issue_date}] {permit.get('permit_type_desc', 'N/A')} — {permit.get('work_class', 'N/A')}\n"
            result += f"  Description: {permit.get('description', 'N/A')}\n"
            result += f"  Status: {permit.get('status_current', 'N/A')}\n"
            if permit.get('total_job_valuation'):
                result += f"  Valuation: ${int(float(permit.get('total_job_valuation', 0))):,}\n"

        return result

    except Exception as e:
        return f"Error fetching permits: {str(e)}"


# ─── Google Search ───────────────────────────────────────────────────────────

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