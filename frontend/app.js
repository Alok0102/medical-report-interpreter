// AetherMed - Frontend Dashboard Controller

const BACKEND_URL = "http://localhost:8000";

// Preset medical report texts
const PRESETS = {
    healthy: `PATIENT RECORD
Patient Name: Alexander Vance
DOB: May 12, 1985
Phone: +1 (555) 304-9988
Address: 4820 Birchwood Lane, Seattle, WA

COMPLETE BLOOD COUNT (CBC):
Hemoglobin: 15.4 g/dL
White Blood Cell Count (WBC): 6.8 x10^3 cells/mcL
Platelets: 280 x10^3 cells/mcL
Red Blood Cell Count (RBC): 4.9 x10^6 cells/mcL
Hematocrit: 44.5 %`,

    anemia: `CLINICAL LAB REPORT
Patient: Emily R. Harrison
Date of Birth: 10/24/1992
Contact: emily.harrison@email.com
ID: 492-20-4820

LAB TEST RESULTS:
Hemoglobin: 10.1 g/dL
White Blood Cell Count (WBC): 12.4 x10^3 cells/mcL
Platelets: 135 x10^3 cells/mcL
Hematocrit: 32.8 %`,

    diabetes: `METABOLIC PROFILE DATA
Client Name: Richard K. Miller
Address: 882 Pine Avenue, Chicago, IL
DOB: 03/15/1971

BASIC METABOLIC PANEL (BMP):
Glucose (Fasting): 142.0 mg/dL
Sodium: 141.0 mEq/L
Potassium: 3.9 mEq/L
Creatinine: 1.6 mg/dL`
};

document.addEventListener("DOMContentLoaded", () => {
    // Icons
    lucide.createIcons();

    // DOM Elements
    const txtReport = document.getElementById("report-input");
    const btnAnalyze = document.getElementById("btn-analyze");
    const welcomePanel = document.getElementById("welcome-panel");
    const timelinePanel = document.getElementById("timeline-panel");
    const resultsPanel = document.getElementById("results-panel");
    const timelineList = document.getElementById("timeline-list");
    const redactedTextDisplay = document.getElementById("redacted-text-display");
    const metricsTableBody = document.getElementById("metrics-table-body");
    const explanationDisplay = document.getElementById("explanation-display");
    const recommendationsDisplay = document.getElementById("recommendations-display");

    // Status Dots
    const dotBackend = document.querySelector("#status-backend .status-dot");
    const txtBackend = document.querySelector("#status-backend .status-text");
    const dotMcp = document.querySelector("#status-mcp .status-dot");
    const txtMcp = document.querySelector("#status-mcp .status-text");
    const dotGemini = document.querySelector("#status-gemini .status-dot");
    const txtGemini = document.querySelector("#status-gemini .status-text");

    // Presets
    document.getElementById("btn-load-healthy").addEventListener("click", () => txtReport.value = PRESETS.healthy);
    document.getElementById("btn-load-anemia").addEventListener("click", () => txtReport.value = PRESETS.anemia);
    document.getElementById("btn-load-diabetes").addEventListener("click", () => txtReport.value = PRESETS.diabetes);

    // Set Initial Preset
    txtReport.value = PRESETS.anemia;

    // Tabs control
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            const tabId = btn.getAttribute("data-tab");
            document.getElementById(tabId).classList.add("active");
        });
    });

    // Connect and Check API Status
    async function checkStatus() {
        try {
            const res = await fetch(`${BACKEND_URL}/api/status`);
            if (res.ok) {
                const data = await res.json();
                
                // Backend Status
                dotBackend.className = "status-dot online";
                txtBackend.textContent = "Backend: Connected";

                // MCP Server Status
                if (data.mcp_server_connected) {
                    dotMcp.className = "status-dot online";
                    txtMcp.textContent = "MCP Server: Active";
                } else {
                    dotMcp.className = "status-dot offline";
                    txtMcp.textContent = "MCP Server: Offline (Using Local Fallbacks)";
                }

                // Gemini Status
                if (data.gemini_api_enabled) {
                    dotGemini.className = "status-dot online";
                    txtGemini.textContent = "Gemini LLM: Live API";
                } else {
                    dotGemini.className = "status-dot online";
                    txtGemini.textContent = "Gemini LLM: Local Simulator Mode";
                }
            }
        } catch (e) {
            dotBackend.className = "status-dot offline";
            txtBackend.textContent = "Backend: Disconnected";
            dotMcp.className = "status-dot offline";
            txtMcp.textContent = "MCP Server: Offline";
            dotGemini.className = "status-dot offline";
            txtGemini.textContent = "Gemini LLM: Offline";
        }
    }

    // Run status check immediately
    checkStatus();
    // Poll status check every 5 seconds
    setInterval(checkStatus, 5000);

    // Run Agent Analysis
    btnAnalyze.addEventListener("click", async () => {
        const text = txtReport.value.trim();
        if (!text) {
            alert("Please paste or write a medical report first.");
            return;
        }

        // Adjust UI visibility
        welcomePanel.classList.add("hidden");
        timelinePanel.classList.remove("hidden");
        resultsPanel.classList.add("hidden"); // Hide results panel while processing

        // Render loading/processing state for timeline
        renderInitialTimeline();

        btnAnalyze.disabled = true;
        btnAnalyze.querySelector("span").textContent = "Agents Collaborating...";

        try {
            const res = await fetch(`${BACKEND_URL}/api/analyze`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ report_text: text })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Server analysis error");
            }

            const data = await res.json();
            
            // Animate each timeline step sequentially to give a premium coordinated-agents feel
            await animateTimelineCompletion(data.agents_timeline);
            
            // Populate actual results
            populateResults(data);

            // Display results panel
            resultsPanel.classList.remove("hidden");
            
            // Auto click the metrics/analysis tab
            document.querySelector("[data-tab='tab-metrics']").click();

        } catch (error) {
            console.error(error);
            alert(`Analysis failed: ${error.message}`);
            // Reset state
            welcomePanel.classList.remove("hidden");
            timelinePanel.classList.add("hidden");
        } finally {
            btnAnalyze.disabled = false;
            btnAnalyze.querySelector("span").textContent = "Execute Agent Pipeline";
        }
    });

    const pipelineSteps = [
        { key: "security", title: "PII Security Scrubber", action: "Redacting patient private information locally..." },
        { key: "extractor", title: "Extractor Agent", action: "Extracting blood counts and data from report text..." },
        { key: "analyzer", title: "Analyzer Agent", action: "Querying MCP range tables and flagging out-of-range metrics..." },
        { key: "explainer", title: "Explainer Agent", action: "Synthesizing educational explanations in simple language..." },
        { key: "recommender", title: "Recommender Agent", action: "Formulating consultation roadmap and doctor questions list..." }
    ];

    function renderInitialTimeline() {
        timelineList.innerHTML = "";
        pipelineSteps.forEach((step, idx) => {
            const stepDiv = document.createElement("div");
            stepDiv.id = `step-${step.key}`;
            stepDiv.className = "timeline-step pending";
            stepDiv.innerHTML = `
                <div class="timeline-node">${idx + 1}</div>
                <div class="timeline-info">
                    <div class="timeline-header-row">
                        <div class="timeline-agent-name">${step.title}</div>
                        <div class="timeline-time" id="time-${step.key}">Pending</div>
                    </div>
                    <div class="timeline-action">${step.action}</div>
                    <div class="timeline-details" id="details-${step.key}">Awaiting preceding task completion...</div>
                </div>
            `;
            timelineList.appendChild(stepDiv);
        });
        lucide.createIcons();
    }

    async function animateTimelineCompletion(realTimeline) {
        // Map backend agent responses to our steps
        const stepKeys = ["security", "extractor", "analyzer", "explainer", "recommender"];
        
        for (let i = 0; i < stepKeys.length; i++) {
            const key = stepKeys[i];
            const element = document.getElementById(`step-${key}`);
            const timeLabel = document.getElementById(`time-${key}`);
            const detailsLabel = document.getElementById(`details-${key}`);
            
            // Set current step to processing
            element.className = "timeline-step active-processing";
            timeLabel.textContent = "Processing...";
            detailsLabel.textContent = "Performing analysis using specialized context...";
            
            // Artificial small delay for visual elegance (e.g. 800ms)
            await new Promise(resolve => setTimeout(resolve, 800));
            
            // Get backend real execution details
            const serverInfo = realTimeline[i] || { duration_sec: 0.1, details: "Completed task." };
            
            element.className = "timeline-step completed";
            timeLabel.textContent = `${serverInfo.duration_sec}s`;
            detailsLabel.textContent = serverInfo.details;
        }
    }

    function populateResults(data) {
        // Redacted Text Display
        redactedTextDisplay.textContent = data.redacted_text;

        // Metrics Table Body
        metricsTableBody.innerHTML = "";
        const analysis = data.final_analysis;
        
        if (Object.keys(analysis).length === 0) {
            metricsTableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No lab parameters could be extracted. Please paste a clean CBC/BMP report.</td></tr>`;
        } else {
            for (const [key, item] of Object.entries(analysis)) {
                const tr = document.createElement("tr");
                
                // Status Badge class
                const statusClass = item.status.toLowerCase();
                
                tr.innerHTML = `
                    <td style="font-weight: 600;">${item.name}</td>
                    <td><strong style="color: var(--text-main); font-size: 14px;">${item.value}</strong> ${item.unit}</td>
                    <td style="color: var(--text-muted);">${item.reference_range}</td>
                    <td><span class="badge ${statusClass}">${item.status}</span></td>
                    <td style="color: var(--text-muted); font-size: 12px; max-width: 250px;">${item.description}</td>
                `;
                metricsTableBody.appendChild(tr);
            }
        }

        // Markdown Explanation
        explanationDisplay.innerHTML = marked.parse(data.explanation_markdown || "No explanation generated.");
        
        // Markdown Recommendations
        recommendationsDisplay.innerHTML = marked.parse(data.recommendation_markdown || "No recommendations generated.");
        
        lucide.createIcons();
    }
});
