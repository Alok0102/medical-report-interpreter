import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx

from backend.config import settings
from backend.security import redact_pii
from backend.agents.agent1_extractor import ExtractorAgent
from backend.agents.agent2_analyzer import AnalyzerAgent
from backend.agents.agent3_explainer import ExplainerAgent
from backend.agents.agent4_recommender import RecommenderAgent

app = FastAPI(title="Medical Report Interpreter API")

# Enable CORS for frontend local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate agents
extractor = ExtractorAgent()
analyzer = AnalyzerAgent()
explainer = ExplainerAgent()
recommender = RecommenderAgent()

class AnalysisRequest(BaseModel):
    report_text: str
    active_agents: List[str] = ["extractor", "analyzer", "explainer", "recommender"]

class AnalysisResponse(BaseModel):
    raw_text_length: int
    redacted_text: str
    agents_timeline: List[dict]
    final_analysis: dict
    explanation_markdown: str
    recommendation_markdown: str

@app.get("/api/status")
async def get_status():
    mcp_connected = False
    if settings.MCP_SERVER_URL:
        try:
            # FastMCP status check or basic ping to root SSE url
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{settings.MCP_SERVER_URL.rstrip('/')}/tools")
                if response.status_code == 200:
                    mcp_connected = True
        except Exception:
            pass
            
    return {
        "status": "online",
        "gemini_api_enabled": settings.USE_GEMINI_API,
        "mcp_server_connected": mcp_connected,
        "mcp_server_url": settings.MCP_SERVER_URL
    }

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_report(request: AnalysisRequest):
    if not request.report_text.strip():
        raise HTTPException(status_code=400, detail="Report text cannot be empty.")
        
    timeline = []
    
    # --- PHASE 0: Security & PII Redaction ---
    t_start = time.time()
    redacted_text = redact_pii(request.report_text)
    t_pii = time.time() - t_start
    timeline.append({
        "agent": "Security System",
        "action": "Redacted Patient Identifiable Information (PII)",
        "duration_sec": round(t_pii, 3),
        "status": "completed",
        "details": "Scrubbed names, addresses, DOBs, and phone numbers locally before processing."
    })
    
    # --- PHASE 1: Agent 1 (Extractor) ---
    extracted_data = {}
    if "extractor" in request.active_agents:
        t_start = time.time()
        try:
            extracted_data = extractor.run(redacted_text)
            t_duration = time.time() - t_start
            timeline.append({
                "agent": extractor.name,
                "action": "Extracted numerical parameters and measurement units",
                "duration_sec": round(t_duration, 3),
                "status": "completed",
                "details": f"Successfully parsed {len(extracted_data)} biological markers."
            })
        except Exception as e:
            timeline.append({
                "agent": extractor.name,
                "action": "Failed data extraction",
                "duration_sec": 0,
                "status": "failed",
                "details": str(e)
            })
            raise HTTPException(status_code=500, detail=f"Extraction Agent failed: {str(e)}")

    # --- PHASE 2: Agent 2 (Analyzer with MCP ranges) ---
    analyzed_results = {}
    if "analyzer" in request.active_agents and extracted_data:
        t_start = time.time()
        try:
            analyzed_results = analyzer.run(extracted_data)
            t_duration = time.time() - t_start
            abnormals = sum(1 for item in analyzed_results.values() if item["status"] != "Normal")
            timeline.append({
                "agent": analyzer.name,
                "action": "Queried MCP server for standard reference ranges and evaluated deviations",
                "duration_sec": round(t_duration, 3),
                "status": "completed",
                "details": f"Analyzed {len(analyzed_results)} values. Found {abnormals} out-of-range markers."
            })
        except Exception as e:
            timeline.append({
                "agent": analyzer.name,
                "action": "Failed comparison checks",
                "duration_sec": 0,
                "status": "failed",
                "details": str(e)
            })
            raise HTTPException(status_code=500, detail=f"Analyzer Agent failed: {str(e)}")

    # --- PHASE 3: Agent 3 (Explainer) ---
    explanation = ""
    if "explainer" in request.active_agents and analyzed_results:
        t_start = time.time()
        try:
            explanation = explainer.run(analyzed_results)
            t_duration = time.time() - t_start
            timeline.append({
                "agent": explainer.name,
                "action": "Translated complex medical readings into patient-friendly educational briefs",
                "duration_sec": round(t_duration, 3),
                "status": "completed",
                "details": "Rendered empathetic health summaries in Markdown format."
            })
        except Exception as e:
            timeline.append({
                "agent": explainer.name,
                "action": "Failed explanation generation",
                "duration_sec": 0,
                "status": "failed",
                "details": str(e)
            })
            raise HTTPException(status_code=500, detail=f"Explainer Agent failed: {str(e)}")

    # --- PHASE 4: Agent 4 (Recommender) ---
    recommendations = ""
    if "recommender" in request.active_agents and analyzed_results:
        t_start = time.time()
        try:
            recommendations = recommender.run(analyzed_results)
            t_duration = time.time() - t_start
            timeline.append({
                "agent": recommender.name,
                "action": "Created doctor specialization consultations mapping and dynamic questions guides",
                "duration_sec": round(t_duration, 3),
                "status": "completed",
                "details": "Prepared physician visit checklist."
            })
        except Exception as e:
            timeline.append({
                "agent": recommender.name,
                "action": "Failed recommendation compilation",
                "duration_sec": 0,
                "status": "failed",
                "details": str(e)
            })
            raise HTTPException(status_code=500, detail=f"Recommender Agent failed: {str(e)}")

    return AnalysisResponse(
        raw_text_length=len(request.report_text),
        redacted_text=redacted_text,
        agents_timeline=timeline,
        final_analysis=analyzed_results,
        explanation_markdown=explanation,
        recommendation_markdown=recommendations
    )
