import xml.etree.ElementTree as ET
import json

def parse_tool_calls(root):
    tool_calls = []
    
    for tool_call in root.findall('tool_call'):
        json_content = tool_call.text.strip()
        
        tool_call_data = json.loads(json_content)
        
        tool_calls.append({
            "name": tool_call_data["name"],
            "arguments": tool_call_data["arguments"]
        })
    
    return tool_calls

def extract_tool_cals(xml: str):
    full_string = f"<root>{xml}</root>"

    root = ET.fromstring(full_string)

    return parse_tool_calls(root)