"""
llm_judge.py
────────────
LLM fallback layer for uncertain-zone messages.
Uses Gemini API for high-confidence decisions.
"""

import os
import json
import hashlib
import time
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

_gemini_available = False
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    _gemini_available = True
    print("[llm_judge] Gemini API key found. LLM fallback enabled.")
else:
    print("[llm_judge] GEMINI_API_KEY not found in .env file. LLM fallback disabled.")

# ── PROMPT ────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a strict cybersecurity AI. Your only job is to classify SMS/chat messages as SAFE, SUSPICIOUS, or SCAM.

Classification rules (apply ALL):
- Any request for OTP, PIN, password, or verification code → SCAM
- Any request for bank/account/card details → SCAM
- Urgency + action request → SCAM
- Promises of money, prizes, rewards requiring action → SCAM
- Social engineering ("don't tell anyone", "only you can help") → SUSPICIOUS or SCAM
- Spelling variations to hide intent (0tp, s3nd, acc0unt) → treat same as real words
- Emotional manipulation to force quick action → SUSPICIOUS or SCAM
- Normal casual conversation → SAFE

You MUST output ONLY valid JSON — no extra text before or after.
Format: {"label": "SAFE"|"SUSPICIOUS"|"SCAM", "confidence": <float 0.0-1.0>, "reason": "<short sentence>"}
"""

# ── CACHING ───────────────────────────────────────────────────────────

MAX_CACHE_SIZE   = 512
_cache: dict[str, dict] = {}

def _cache_key(text: str) -> str:
    return hashlib.md5(text.strip().lower().encode()).hexdigest()

# ── CORE CALL ─────────────────────────────────────────────────────────

def _call_gemini_raw(message: str) -> dict | None:
    if not _gemini_available:
        return None

    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=_SYSTEM_PROMPT,
            generation_config={"response_mime_type": "application/json"}
        )
        
        prompt = f'Classify this message:\n\n"{message}"'
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        # Extract JSON
        start = raw_text.find("{")
        end   = raw_text.rfind("}") + 1
        if start == -1 or end == 0:
            return None

        parsed = json.loads(raw_text[start:end])
        
        label = parsed.get("label", "").upper().strip()
        if label not in ("SAFE", "SUSPICIOUS", "SCAM"):
            label = "SUSPICIOUS"

        return {
            "label":      label,
            "confidence": float(parsed.get("confidence", 0.5)),
            "reason":     parsed.get("reason", "LLM analysis")
        }
    except Exception as e:
        print(f"[llm_judge] Error calling Gemini: {e}")
        return None

# ── PUBLIC API ────────────────────────────────────────────────────────

def is_available() -> bool:
    return _gemini_available

def judge(message: str) -> dict:
    FALLBACK = {
        "label":      "SUSPICIOUS",
        "confidence": 0.5,
        "reason":     "LLM unavailable — defaulting to Suspicious",
        "source":     "fallback"
    }

    if not is_available():
        return FALLBACK

    key = _cache_key(message)
    if key in _cache:
        result = dict(_cache[key])
        result["source"] = "cache"
        return result

    t0     = time.time()
    result = _call_gemini_raw(message)
    elapsed = time.time() - t0

    if result is None:
        return FALLBACK

    result["source"] = "llm"
    result["latency_ms"] = round(elapsed * 1000)

    if len(_cache) >= MAX_CACHE_SIZE:
        oldest_key = next(iter(_cache))
        del _cache[oldest_key]
    _cache[key] = result

    return result

def label_to_prob(label: str, confidence: float) -> float:
    base = {"SAFE": 0.1, "SUSPICIOUS": 0.5, "SCAM": 0.9}[label]
    return base * confidence + 0.5 * (1 - confidence)
