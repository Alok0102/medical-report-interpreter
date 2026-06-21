import os
from dotenv import load_dotenv

# Load local environment file
load_dotenv()

class Settings:
    USE_GEMINI_API: bool = os.getenv("USE_GEMINI_API", "false").lower() == "true"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MCP_SERVER_URL: str = os.getenv("MCP_SERVER_URL", "http://localhost:8001/mcp")
    
settings = Settings()
