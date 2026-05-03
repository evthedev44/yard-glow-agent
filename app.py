import os
from flask import Flask, render_template, request, jsonify
from agent import run_agent
from tools import get_street_view_url, get_aerial_url
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/research", methods=["POST"])
def research():
    data = request.get_json()
    address = data.get("address", "").strip()
    
    if not address:
        return jsonify({"error": "Please enter an address"}), 400
    
    try:
        # Run the agent
        brief = run_agent(address)
        
        # Get photo URLs
        street_view = get_street_view_url(address)
        aerial = get_aerial_url(address)
        
        return jsonify({
            "brief": brief,
            "street_view": street_view,
            "aerial": aerial
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)