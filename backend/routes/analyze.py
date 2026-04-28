from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pickle, os, sys
import numpy as np
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.preprocessing import preprocess_text
from utils.scoring import get_rule_features, get_matched_categories, get_explanations, check_critical_override
from utils.database import save_analysis
from utils import llm_judge

router = APIRouter()

SAFE_THRESHOLD = 0.40
SCAM_THRESHOLD = 0.72

base_dir   = os.path.dirname(os.path.dirname(__file__))
models_dir = os.path.join(base_dir, 'models')

# ── Load TF-IDF + LSA + LightGBM artifacts ────────────────────────────
word_vec = char_vec = lsa_model = model = feature_names = shap_importance = None
try:
    with open(os.path.join(models_dir, 'word_vectorizer.pkl'), 'rb') as f: word_vec = pickle.load(f)
    with open(os.path.join(models_dir, 'char_vectorizer.pkl'), 'rb') as f: char_vec = pickle.load(f)
    with open(os.path.join(models_dir, 'lsa.pkl'),             'rb') as f: lsa_model = pickle.load(f)
    with open(os.path.join(models_dir, 'model.pkl'),           'rb') as f: model    = pickle.load(f)
    with open(os.path.join(models_dir, 'feature_names.pkl'),   'rb') as f: feature_names = pickle.load(f)
    with open(os.path.join(models_dir, 'shap_importance.pkl'), 'rb') as f: shap_importance = pickle.load(f)
    print("[analyze] Loaded LightGBM + TF-IDF + LSA artifacts.")
except Exception as e:
    print(f"[analyze] Warning: {e}")

# ── No MiniLM — using LSA (TruncatedSVD) as semantic layer ────────────

# ── Load DistilBERT (optional) ────────────────────────────────────────
bert_tok = bert_mdl = None
try:
    bert_dir = os.path.join(models_dir, 'scam_model')
    bert_tok = DistilBertTokenizer.from_pretrained(bert_dir)
    bert_mdl = DistilBertForSequenceClassification.from_pretrained(bert_dir)
    bert_mdl.eval()
    print("[analyze] Loaded DistilBERT model.")
except Exception as e:
    print(f"[analyze] DistilBERT not active: {e}")


def _build_features(clean_text: str, raw_text: str) -> np.ndarray:
    X_word  = word_vec.transform([clean_text]).toarray()
    X_char  = char_vec.transform([clean_text]).toarray()
    X_lsa   = lsa_model.transform(word_vec.transform([clean_text]))
    X_rules = np.array([get_rule_features(raw_text)])
    return np.hstack([X_word, X_char, X_lsa, X_rules])


def _get_top_words(clean_text: str, n: int = 5) -> list:
    try:
        tfidf_arr = word_vec.transform([clean_text]).toarray()[0]
        vocab = word_vec.get_feature_names_out()
        contrib = []
        for i, val in enumerate(tfidf_arr):
            if val > 0:
                word = vocab[i]
                shap_w = shap_importance.get(word, 0.0) if shap_importance else 0.0
                contrib.append((word, val * shap_w))
        contrib.sort(key=lambda x: x[1], reverse=True)
        return [w for w, _ in contrib[:n] if w]
    except Exception:
        return []


def _classify(prob: float) -> str:
    if prob < SAFE_THRESHOLD:  return "Safe"
    if prob < SCAM_THRESHOLD:  return "Suspicious"
    return "Scam"


class AnalyzeRequest(BaseModel):
    message: str
    unknown_sender: bool = False


@router.post("/analyze")
async def analyze_message(req: AnalyzeRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if not model or not lsa_model:
        raise HTTPException(status_code=500, detail="Models not loaded. Run train.py first.")

    clean = preprocess_text(req.message)

    # ── 1. Rule score (0.0 – 1.0) ─────────────────────────────────────
    matched_cats = get_matched_categories(req.message)
    rule_score   = min(len(matched_cats) / 4.0, 1.0)   # 4+ cats → 1.0

    # ── 2. LightGBM + TF-IDF + LSA (lexical signal) ───────────────────
    feat    = _build_features(clean, req.message)
    ml_prob = model.predict_proba(feat)[0][1]

    # ── 3. DistilBERT semantic layer (optional) ────────────────────────
    bert_prob = None
    if bert_mdl and bert_tok:
        inputs = bert_tok(req.message, return_tensors="pt",
                          padding=True, truncation=True, max_length=128)
        with torch.no_grad():
            probs = torch.nn.functional.softmax(bert_mdl(**inputs).logits, dim=-1)[0]
            bert_prob = probs[2].item() + probs[1].item() * 0.5

    # ── 4. WEIGHTED FUSION ────────────────────────────────────────────
    # BERT understands meaning  → dominates (60%)
    # ML catches lexical patterns → supporting role (20%)
    # Rules catch known fraud patterns → safety guard (20%)
    if bert_prob is not None:
        final_prob = 0.6 * bert_prob + 0.2 * ml_prob + 0.2 * rule_score
    else:
        # No BERT: ML is primary (70%), rules as strong safety net (30%)
        final_prob = 0.7 * ml_prob + 0.3 * rule_score

    if req.unknown_sender:
        final_prob = min(1.0, final_prob + 0.05)

    # ── 5. CRITICAL OVERRIDE ────────────────────────────────────────────
    # Known high-risk pattern (OTP+tell, password+send, etc.) → force SCAM
    if check_critical_override(req.message):
        final_prob = max(final_prob, 0.92)

    # ── 6. LLM FALLBACK (uncertain zone only) ──────────────────────────
    # Triggered ONLY when the system is not confident enough:
    #   A) final_prob in uncertain band 0.40–0.72
    #   B) ML and BERT strongly disagree (gap > 0.40)
    #   C) Suspicious keywords + borderline score
    # High-confidence decisions (< 0.40 or > 0.72) SKIP the LLM entirely.
    llm_result    = None
    llm_triggered = False

    _in_uncertain_zone = SAFE_THRESHOLD <= final_prob < SCAM_THRESHOLD
    _ml_bert_conflict  = (bert_prob is not None
                          and abs(bert_prob - ml_prob) > 0.40)
    _suspicious_kw     = any(kw in req.message.lower()
                             for kw in ["otp", "verify", "urgent", "account",
                                        "password", "bank", "win", "prize",
                                        "otp", "kyc", "blocked", "suspended"])

    if llm_judge.is_available() and (
        _in_uncertain_zone
        or _ml_bert_conflict
        or (_suspicious_kw and final_prob > 0.25)
    ):
        llm_result    = llm_judge.judge(req.message)
        llm_triggered = True
        llm_prob      = llm_judge.label_to_prob(
                            llm_result["label"], llm_result["confidence"])

        # Blend: existing signals = 70%, LLM = 30%
        # LLM only nudges — it cannot override a high-confidence ML+BERT decision
        final_prob = 0.70 * final_prob + 0.30 * llm_prob
        final_prob = min(1.0, final_prob)

    # ── 7. Label ───────────────────────────────────────────────────────
    label = _classify(final_prob)

    # ── 8. Explainability ──────────────────────────────────────────────
    top_words    = _get_top_words(clean)
    explanations = get_explanations(req.message, matched_cats, top_words)

    # Add LLM reasoning to explanations if it was triggered
    if llm_triggered and llm_result and llm_result.get("reason"):
        src = "LLM" if llm_result.get("source") == "llm" else "LLM (cached)"
        explanations.insert(0, f"{src} [{llm_result['label']} @ {llm_result['confidence']:.0%}]: {llm_result['reason']}")

    # ── 9. Save & Return ───────────────────────────────────────────────
    risk_score = round(final_prob * 100)
    save_analysis(req.message, risk_score, label)

    return {
        "final_score": risk_score,
        "label": label,
        "breakdown": {
            "ml_probability":    round(ml_prob, 4),
            "bert_probability":  round(bert_prob, 4) if bert_prob else None,
            "rule_score":        round(rule_score, 4),
            "final_probability": round(final_prob, 4),
            "llm_triggered":     llm_triggered,
            "llm_result":        llm_result,
            "rule_categories":   matched_cats,
            "top_signal_words":  top_words,
            "shap_top_features": list(shap_importance.keys())[:5] if shap_importance else []
        },
        "explanation": explanations
    }
