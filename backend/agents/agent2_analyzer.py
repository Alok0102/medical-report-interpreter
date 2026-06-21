import httpx
import json
from backend.agents.base import BaseAgent
from backend.config import settings

class AnalyzerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Analyzer Agent",
            role="Pathology Comparison Specialist",
            system_instruction=(
                "You are an expert clinical laboratory scientist. Your job is to compare a patient's "
                "actual test values with standard reference ranges and flag high, low, or normal status. "
                "Output a clean structure listing each test, actual value, normal range, status, and description."
            )
        )

    def run(self, extracted_data: dict) -> dict:
        print(f"[{self.name}] Comparing values with reference ranges...")
        analysis_results = {}
        
        for test_name, info in extracted_data.items():
            value = info.get("value")
            unit = info.get("unit", "")
            
            # Default reference range values to fall back to if MCP server is offline
            ref_min = 0.0
            ref_max = 999.0
            ref_unit = unit
            description = "Laboratory measurement."
            test_display_name = test_name.capitalize()
            
            # Query the MCP server
            mcp_success = False
            if settings.MCP_SERVER_URL:
                try:
                    # Under the FastMCP HTTP/SSE server, we can query tools directly.
                    # FastMCP exposes a standard tool-call POST endpoint when running in SSE/HTTP mode.
                    # Typically: POST http://localhost:8001/tools/lookup_test_range/call
                    # with JSON body: {"arguments": {"test_key": test_name}}
                    url = f"{settings.MCP_SERVER_URL.rstrip('/')}/tools/lookup_test_range/call"
                    response = httpx.post(url, json={"arguments": {"test_key": test_name}}, timeout=2.0)
                    
                    if response.status_code == 200:
                        mcp_result = response.json()
                        # Extract the text content from the MCP tool output
                        content_list = mcp_result.get("content", [])
                        if content_list and content_list[0].get("type") == "text":
                            text_data = content_list[0].get("text", "")
                            
                            # Parse JSON inside tool result
                            if not text_data.startswith("Test key"): # checks for 'Test key not found' error string
                                data = json.loads(text_data)
                                test_display_name = data.get("name", test_display_name)
                                ref_min = float(data.get("range_min", ref_min))
                                ref_max = float(data.get("range_max", ref_max))
                                ref_unit = data.get("unit", ref_unit)
                                description = data.get("description", description)
                                mcp_success = True
                except Exception as e:
                    # Fail silently and fall back to local comparison
                    print(f"[{self.name}] MCP lookup failed for '{test_name}': {e}. Using local reference data.")
            
            # If MCP was offline or test wasn't in MCP, use local fallback logic
            if not mcp_success:
                fallback_database = {
                    "hemoglobin": {"name": "Hemoglobin", "min": 12.0, "max": 17.2, "unit": "g/dL", "desc": "Oxygen-carrying protein in red blood cells."},
                    "wbc": {"name": "White Blood Cells", "min": 4.5, "max": 11.0, "unit": "x10^3 cells/mcL", "desc": "Cells that combat infections and foreign organisms."},
                    "platelets": {"name": "Platelet Count", "min": 150.0, "max": 450.0, "unit": "x10^3 cells/mcL", "desc": "Blood fragments responsible for proper clotting."},
                    "rbc": {"name": "Red Blood Cells", "min": 4.2, "max": 6.1, "unit": "x10^6 cells/mcL", "desc": "Cells responsible for transporting oxygen throughout the body."},
                    "hematocrit": {"name": "Hematocrit", "min": 36.0, "max": 50.0, "unit": "%", "desc": "Volume percentage of red cells in blood."},
                    "sodium": {"name": "Sodium", "min": 135.0, "max": 145.0, "unit": "mEq/L", "desc": "Essential electrolyte for body fluid balancing."},
                    "potassium": {"name": "Potassium", "min": 3.5, "max": 5.2, "unit": "mEq/L", "desc": "Electrolyte vital for muscular and nerve cell activity."},
                    "glucose": {"name": "Glucose", "min": 70.0, "max": 99.0, "unit": "mg/dL", "desc": "Fasting blood sugar level."},
                    "creatinine": {"name": "Creatinine", "min": 0.6, "max": 1.2, "unit": "mg/dL", "desc": "Kidney filtration metabolic byproduct."}
                }
                
                lookup_key = test_name.lower().strip()
                if lookup_key in fallback_database:
                    db_info = fallback_database[lookup_key]
                    test_display_name = db_info["name"]
                    ref_min = db_info["min"]
                    ref_max = db_info["max"]
                    ref_unit = db_info["unit"]
                    description = db_info["desc"]

            # Perform comparison
            status = "Normal"
            if value < ref_min:
                status = "Low"
            elif value > ref_max:
                status = "High"
                
            analysis_results[test_name] = {
                "name": test_display_name,
                "value": value,
                "unit": ref_unit,
                "reference_range": f"{ref_min} - {ref_max} {ref_unit}",
                "status": status,
                "description": description
            }
            
        return analysis_results
