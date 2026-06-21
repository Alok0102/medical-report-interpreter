from backend.agents.base import BaseAgent

class ExplainerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Explainer Agent",
            role="Patient Communication Specialist",
            system_instruction=(
                "You are an empathetic medical communicator. Explain lab test results and abnormal values "
                "in warm, clear, jargon-free layman's terms. Never diagnose directly; describe possible conditions "
                "or reasons in an informative, reassuring manner."
            )
        )

    def run(self, analysis_results: dict) -> str:
        print(f"[{self.name}] Generating explanation...")
        
        # 1. Try Live Gemini if configured
        if self.model:
            prompt = (
                f"Explain the following analyzed lab results to a patient in simple language. "
                f"Provide details on what the abnormal levels might indicate, but maintain a reassuring, non-diagnostic tone:\n\n"
                f"{analysis_results}"
            )
            explanation = self.query_gemini(prompt)
            if explanation:
                return explanation

        # 2. Local fallback / simulation explanation builder
        explanation_parts = []
        abnormalities = [f for f in analysis_results.values() if f["status"] != "Normal"]
        
        if not abnormalities:
            explanation_parts.append(
                "## Overall Status: All Inspected Levels Normal\n\n"
                "Great news! All of the test values analyzed from your report fall within the standard healthy "
                "reference ranges. This suggests that the measured markers are currently balanced and within expected parameters."
            )
        else:
            explanation_parts.append(
                f"## Overview of Findings\n\n"
                f"We reviewed the report and noted that **{len(abnormalities)}** marker(s) fall outside the standard reference ranges. "
                "Below is a breakdown of what these findings mean in plain language:\n"
            )
            
            for item in abnormalities:
                test_name = item["name"]
                val = item["value"]
                unit = item["unit"]
                status = item["status"]
                ref = item["reference_range"]
                
                explanation_parts.append(f"### 🔍 {test_name}: **{status}**")
                explanation_parts.append(f"- **Your Level:** {val} {unit} (Normal range is {ref})")
                
                # Medical insights matching common laboratory results
                key = test_name.lower()
                insight = "This marker is slightly outside standard ranges."
                if "hemoglobin" in key or "red blood" in key:
                    if status == "Low":
                        insight = ("Hemoglobin is the protein in red blood cells that carries oxygen to your organs. "
                                   "A low level (anemia) can lead to feelings of fatigue, coldness, or low energy, "
                                   "often linked to iron levels, vitamin intake, or temporary stress.")
                    else:
                        insight = ("Elevated hemoglobin means a higher density of red blood cells. "
                                   "This can be due to dehydration, living at a high altitude, or high cellular production.")
                elif "wbc" in key or "white blood" in key:
                    if status == "Low":
                        insight = ("White blood cells form the core of your immune system. A low count suggests "
                                   "a temporarily weakened immune defense, sometimes caused by viral infections, medications, or stress.")
                    else:
                        insight = ("An elevated white blood cell count typically indicates your body is actively fighting off "
                                   "an infection, inflammation, or physical stress. It is a sign of immune response activation.")
                elif "platelet" in key:
                    if status == "Low":
                        insight = ("Platelets are critical for blood clotting. A low count (thrombocytopenia) means your body "
                                   "might bruise or bleed more easily, occasionally linked to immune factors, nutritional gaps, or infections.")
                    else:
                        insight = ("A high platelet count can indicate inflammation, tissue recovery, or a bone marrow response.")
                elif "glucose" in key:
                    if status == "High":
                        insight = ("Elevated fasting glucose indicates high sugar levels in your blood. "
                                   "This is common in prediabetes or diabetes, and can be influenced by diet, stress, or insulin resistance.")
                    else:
                        insight = ("Low blood glucose (hypoglycemia) can trigger shakiness, dizziness, or sweatiness, often due to missed meals.")
                elif "potassium" in key:
                    insight = ("Potassium regulates muscle contractions and heart rhythm. Levels outside the normal range "
                               "require careful attention as they can affect muscle strength and cardiovascular health.")
                elif "creatinine" in key:
                    if status == "High":
                        insight = ("Creatinine is a waste product filtered by the kidneys. High levels suggest your kidneys "
                                   "might be working harder than usual or filtering less efficiently. This can happen with dehydration.")
                
                explanation_parts.append(f"- **What this means:** {insight}\n")
                
        explanation_parts.append(
            "\n*Note: These explanations are for educational purposes. Your doctor will interpret these values in the context of your complete health profile.*"
        )
        return "\n".join(explanation_parts)
