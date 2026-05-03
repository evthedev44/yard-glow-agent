import os
import anthropic
from dotenv import load_dotenv
from tools import TOOLS, run_tool

# Load keys from .env file
load_dotenv()

def run_agent(address):
    """Run the property research agent for a given address"""
    
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Load the system prompt from our markdown file
    with open("prompts/system.md", "r") as f:
        system_prompt = f.read()
    
    # Start the conversation with the user's address
    messages = [
        {
            "role": "user",
            "content": f"Please research this property and generate a Yard Glow property brief: {address}"
        }
    ]
    
    print(f"\n🔍 Researching: {address}")
    print("━" * 50)
    
    # The agent loop
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            system=system_prompt,
            tools=TOOLS,
            messages=messages
        )
        
        # Did Claude want to use a tool?
        if response.stop_reason == "tool_use":
            
            # Add Claude's response to history
            messages.append({
                "role": "assistant",
                "content": response.content
            })
            
            # Find and run each tool Claude requested
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"→ Searching: {block.input.get('query', block.input.get('url', ''))}")
                    result = run_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            
            # Feed results back to Claude
            messages.append({
                "role": "user",
                "content": tool_results
            })
        
        else:
            # Claude is done — extract the final brief
            final = next(
                block.text for block in response.content 
                if hasattr(block, "text")
            )
            print("✓ Research complete\n")
            return final