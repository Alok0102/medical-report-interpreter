try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

from backend.config import settings

class BaseAgent:
    def __init__(self, name: str, role: str, system_instruction: str):
        self.name = name
        self.role = role
        self.system_instruction = system_instruction
        self.client = None
        
        if settings.USE_GEMINI_API and settings.GEMINI_API_KEY and HAS_GENAI:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=system_instruction
                )
            except Exception as e:
                print(f"[{self.name}] Error configuring Gemini API: {e}. Falling back to simulation mode.")
                self.model = None
        else:
            self.model = None

    def query_gemini(self, prompt: str) -> str:
        """Sends a query to Gemini if API is enabled, otherwise returns None."""
        if self.model:
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"[{self.name}] Gemini call failed: {e}. Falling back to simulation.")
        return None
