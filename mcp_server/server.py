import os
import json
from mcp.server.fastmcp import FastMCP

# Create FastMCP server instance
mcp = FastMCP("MedicalReferenceRanges")

# Path to the reference ranges JSON file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(CURRENT_DIR, "data", "reference_ranges.json")

def load_ranges():
    try:
        with open(DATA_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        # Fallback database if file read fails
        return {
            "CBC": {
                "hemoglobin": {"name": "Hemoglobin", "range_min": 12.0, "range_max": 17.2, "unit": "g/dL", "description": "Carries oxygen."},
                "wbc": {"name": "White Blood Cell Count (WBC)", "range_min": 4.5, "range_max": 11.0, "unit": "x10^3 cells/mcL", "description": "Fights infection."},
                "platelets": {"name": "Platelets", "range_min": 150.0, "range_max": 450.0, "unit": "x10^3 cells/mcL", "description": "Blood clotting."}
            }
        }

@mcp.tool()
def get_reference_ranges(panel_name: str) -> str:
    """
    Get the complete list of standard normal reference ranges for a lab panel (e.g., 'CBC' or 'BMP').
    """
    ranges = load_ranges()
    panel = panel_name.upper().strip()
    if panel in ranges:
        return json.dumps(ranges[panel], indent=2)
    return f"Panel '{panel_name}' not found. Available panels: {', '.join(ranges.keys())}"

@mcp.tool()
def lookup_test_range(test_key: str) -> str:
    """
    Look up normal reference range limits for a specific lab test (e.g. 'hemoglobin', 'wbc', 'potassium', 'glucose').
    """
    ranges = load_ranges()
    test_key_clean = test_key.lower().strip()
    
    for panel, tests in ranges.items():
        if test_key_clean in tests:
            return json.dumps(tests[test_key_clean], indent=2)
            
    # Try fuzzy matching
    matches = []
    for panel, tests in ranges.items():
        for key, val in tests.items():
            if test_key_clean in val["name"].lower() or test_key_clean in key:
                matches.append(val)
                
    if matches:
        return json.dumps(matches, indent=2)
        
    return f"Test key '{test_key}' not found in reference database."

@mcp.resource("reference:ranges")
def get_all_ranges_resource() -> str:
    """
    Exposes the entire standard reference range dictionary as a static resource.
    """
    return json.dumps(load_ranges(), indent=2)

if __name__ == "__main__":
    mcp.settings.port = 8001
    mcp.settings.host = "127.0.0.1"
    mcp.run(transport="sse")
