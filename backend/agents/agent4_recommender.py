from backend.agents.base import BaseAgent

class RecommenderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Recommender Agent",
            role="Healthcare Navigation Consultant",
            system_instruction=(
                "You are an expert healthcare navigator. Based on laboratory anomalies, recommend the appropriate "
                "medical specialization (e.g., General Practitioner, Hematologist, Nephrologist, Endocrinologist) "
                "the patient should consult. Provide a structured, highly actionable bullet-pointed list of "
                "critical questions the patient should ask during their doctor visit. Output in clean Markdown."
            )
        )

    def run(self, analysis_results: dict) -> str:
        print(f"[{self.name}] Creating recommendations and question guide...")
        
        # 1. Try Live Gemini if configured
        if self.model:
            prompt = (
                f"Suggest medical specialists and key questions to ask a doctor based on these lab findings:\n\n"
                f"{analysis_results}"
            )
            recommendations = self.query_gemini(prompt)
            if recommendations:
                return recommendations

        # 2. Local fallback / simulation recommendation builder
        specialists = set()
        questions = []
        
        has_abnormalities = False
        
        for test_name, item in analysis_results.items():
            if item["status"] != "Normal":
                has_abnormalities = True
                key = test_name.lower()
                status = item["status"]
                
                if "hemoglobin" in key or "rbc" in key or "platelet" in key:
                    specialists.add("Hematologist (Blood Specialist)")
                    if status == "Low":
                        questions.append("Could my low hemoglobin/red blood count indicate iron-deficiency anemia or a vitamin deficiency?")
                        questions.append("Should we perform additional tests (like Ferritin or Vitamin B12 checks) to find the root cause?")
                        questions.append("Would dietary changes or iron supplements help resolve this?")
                    else:
                        questions.append("What could be causing elevated hemoglobin or red blood cells in my case?")
                elif "wbc" in key:
                    specialists.add("Infectious Disease Specialist or Hematologist")
                    if status == "High":
                        questions.append("Does my elevated white blood cell count indicate an active infection or localized inflammation?")
                        questions.append("Is a follow-up test needed to see if the count returns to normal on its own?")
                    else:
                        questions.append("Could my low white blood cell count make me more vulnerable to catching infections, and how can I protect myself?")
                elif "glucose" in key:
                    specialists.add("Endocrinologist (Hormone & Metabolism Specialist)")
                    if status == "High":
                        questions.append("Does this fasting glucose result put me in the range for prediabetes or diabetes?")
                        questions.append("Would you recommend an HbA1c test to look at my average blood sugar over the last 3 months?")
                        questions.append("What lifestyle modifications (diet, exercise) do you suggest starting with?")
                elif "creatinine" in key:
                    specialists.add("Nephrologist (Kidney Specialist)")
                    questions.append("Does this elevated creatinine indicate any decline in my kidney function?")
                    questions.append("Could this result be due to simple dehydration or muscle exercise, and should we re-test?")
                    questions.append("Are there any medications or supplements I should avoid to protect my kidneys?")
                elif "sodium" in key or "potassium" in key:
                    specialists.add("Nephrologist or General Physician")
                    questions.append("What is causing this electrolyte imbalance, and could it affect my heart or hydration levels?")

        # Add general physician as primary contact
        specialists.add("Primary Care Physician / General Practitioner (First point of contact)")
        
        # Build Markdown guide
        output_parts = [
            "## Recommended Consultations\n",
            "Based on the analyzed values, we recommend starting with your **Primary Care Physician**, who may refer you to one of these specialists if needed:\n"
        ]
        
        for spec in sorted(specialists):
            output_parts.append(f"- **{spec}**")
            
        output_parts.append("\n## Questions to Ask Your Doctor\n")
        output_parts.append("We recommend printing or saving this list of questions for your next appointment:\n")
        
        # Add basic standard questions
        if not has_abnormalities:
            questions.append("Are there any preventive health measures or lifestyle habits you recommend based on these normal results?")
            questions.append("When should I schedule my next routine blood panel check?")
        else:
            # Insert standard patient advocacy questions at the beginning
            questions.insert(0, "How do these results compare with my previous blood tests?")
            questions.insert(1, "What are the most likely causes for these out-of-range values in my specific health profile?")
            questions.append("What symptoms or signs should I watch out for that would require immediate attention?")
            
        for q in questions:
            output_parts.append(f"- [ ] \"{q}\"")
            
        output_parts.append("\n*Remember to bring a copy of your complete lab report to your consultation.*")
        return "\n".join(output_parts)
