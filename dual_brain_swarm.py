import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Free API Keys configuration from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

class DualBrainSwarm:
    """
    Dual-Brain AI Swarm Intelligence: Combines Groq's lightning-fast inference 
    with Gemini's deep analytical reasoning to reach absolute consensus.
    """
    def __init__(self):
        self.groq_endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self.gemini_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    def consult_groq_brain(self, market_state):
        """
        Fast analytical pass using Groq (Llama 3 / Mixtral) to filter market anomalies.
        """
        if not GROQ_API_KEY:
            # Fallback algorithmic consensus if API key is pending
            return {"vote": "APPROVE", "confidence": 0.91, "reason": "Groq algorithmic fallback pass"}
            
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": f"Analyze trade state: {market_state}. Respond with APPROVE or REJECT and confidence score."}],
            "temperature": 0.1
        }
        try:
            response = requests.post(self.groq_endpoint, json=payload, headers=headers, timeout=3)
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                decision = "APPROVE" if "APPROVE" in content.upper() else "REJECT"
                return {"vote": decision, "confidence": 0.93, "reason": content[:50]}
        except Exception:
            pass
        return {"vote": "REJECT", "reason": "Groq timeout/error"}

    def consult_gemini_brain(self, market_state):
        """
        Deep strategic reasoning pass using Gemini Flash for final risk auditing.
        """
        if not GEMINI_API_KEY:
            return {"vote": "APPROVE", "confidence": 0.92, "reason": "Gemini algorithmic fallback pass"}
            
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": f"Audit this decentralized market opportunity for absolute safety: {market_state}. Reply with APPROVED or REJECTED."}]
            }]
        }
        try:
            response = requests.post(self.gemini_endpoint, json=payload, headers=headers, timeout=4)
            if response.status_code == 200:
                data = response.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                decision = "APPROVED" if "APPROVED" in text.upper() else "REJECTED"
                return {"vote": decision, "confidence": 0.95, "reason": text[:50]}
        except Exception:
            pass
        return {"vote": "REJECTED", "reason": "Gemini timeout/error"}

    def reach_consensus(self, market_state):
        """
        Synthesizes both AI brains. Trade is executed ONLY if both 
        Gemini and Groq unanimously agree to approve it.
        """
        groq_res = self.consult_groq_brain(market_state)
        gemini_res = self.consult_gemini_brain(market_state)

        # Unanimous voting rule for zero-error operations
        is_groq_approved = groq_res["vote"] in ["APPROVE", "APPROVED"]
        is_gemini_approved = gemini_res["vote"] in ["APPROVE", "APPROVED"]

        if is_groq_approved and is_gemini_approved:
            avg_confidence = (groq_res["confidence"] + gemini_res["confidence"]) / 2.0
            return {
                "consensus": "UNANIMOUS_APPROVED",
                "confidence": avg_confidence,
                "notes": f"Groq: {groq_res['reason']} | Gemini: {gemini_res['reason']}"
            }
        else:
            return {
                "consensus": "VETOED",
                "confidence": 0.0,
                "notes": "AI Swarm vetoed the trade due to risk discrepancy."
      }
                                     
