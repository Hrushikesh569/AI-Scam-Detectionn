import streamlit as st
import requests
import pickle
import os

st.set_page_config(
    page_title="ScamGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
shap_importance = {}
try:
    with open(os.path.join(models_dir, 'shap_importance.pkl'), 'rb') as f:
        shap_importance = pickle.load(f)
except Exception:
    pass

API_URL = "http://localhost:8000/analyze"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1117 50%, #0a0e1a 100%);
}

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

.hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 4px 0;
    line-height: 1.1;
}

.hero-sub {
    color: #6b7280;
    font-size: 0.95rem;
    margin-bottom: 32px;
    font-weight: 400;
    letter-spacing: 0.02em;
}

.result-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01));
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 28px;
    margin: 12px 0;
    backdrop-filter: blur(10px);
}

.label-safe       { color: #34d399; font-size: 2.2rem; font-weight: 700; }
.label-suspicious { color: #fbbf24; font-size: 2.2rem; font-weight: 700; }
.label-scam       { color: #f87171; font-size: 2.2rem; font-weight: 700; }

.risk-bar-wrap {
    background: rgba(255,255,255,0.06);
    border-radius: 999px;
    height: 10px;
    margin: 16px 0 6px;
    overflow: hidden;
}

.badge {
    display: inline-block;
    padding: 5px 14px;
    margin: 4px 4px 4px 0;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.badge-rule { background: rgba(99,102,241,0.2); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.3); }
.badge-word { background: rgba(167,139,250,0.2); color: #c4b5fd; border: 1px solid rgba(167,139,250,0.3); }

.example-pill {
    cursor: pointer;
    padding: 8px 14px;
    border-radius: 999px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    color: #9ca3af;
    font-size: 0.78rem;
    margin: 4px 4px 4px 0;
    transition: all 0.2s;
}

.shap-bar {
    height: 5px;
    border-radius: 999px;
    margin-bottom: 2px;
}

.metric-mini {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 16px;
    text-align: center;
}
.metric-mini .val { font-size: 1.5rem; font-weight: 700; color: #e2e8f0; }
.metric-mini .lbl { font-size: 0.7rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 2px; }

div[data-testid="stTextArea"] textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 14px !important;
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
    resize: vertical !important;
}
div[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(99,102,241,0.5) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}

div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 20px rgba(99,102,241,0.3) !important;
}

div[data-testid="stButton"] button[kind="secondary"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #9ca3af !important;
    font-size: 0.78rem !important;
}

section[data-testid="stSidebar"] {
    background: rgba(10,14,26,0.95) !important;
    border-right: 1px solid rgba(255,255,255,0.05) !important;
}

.divider { border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='padding:8px 0 24px'><span style='font-size:1.5rem'>🛡️</span> <span style='font-size:1.1rem;font-weight:700;color:#e2e8f0;'>ScamGuard</span></div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#6b7280;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;'>SHAP Feature Importance</p>", unsafe_allow_html=True)
    st.caption("Signals the model relies on most")

    if shap_importance:
        max_val = max(shap_importance.values()) or 1
        items = sorted(shap_importance.items(), key=lambda x: x[1], reverse=True)
        shown = 0
        for feat, val in items:
            # Skip unreadable LSA/semantic dimensions
            if feat.startswith("bert_") or feat.strip() in ("", " "):
                continue
            if shown >= 12:
                break
            pct = int((val / max_val) * 100)
            if feat.startswith("rule:"):
                color, label = "#6366f1", feat.replace("rule:", "")
            else:
                color, label = "#06b6d4", feat.strip()
            st.markdown(f"""
            <div style='margin:8px 0'>
              <div style='display:flex;justify-content:space-between;align-items:center'>
                <span style='font-size:0.72rem;color:#9ca3af;'>{label}</span>
                <span style='font-size:0.68rem;color:#6b7280'>{val:.3f}</span>
              </div>
              <div class='shap-bar' style='background:{color};width:{pct}%;opacity:0.7;'></div>
            </div>""", unsafe_allow_html=True)
            shown += 1
    else:
        st.info("Run train.py to see SHAP analysis.")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown("<p style='color:#6b7280;font-size:0.72rem;'>Model: LightGBM + LSA + TF-IDF<br>Trained on 5,988 real messages</p>", unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────────────
st.markdown("<h1 class='hero-title'>ScamGuard AI</h1>", unsafe_allow_html=True)
st.markdown("<p class='hero-sub'>Real-time intelligent scam & fraud detection</p>", unsafe_allow_html=True)

# ── LAYOUT ────────────────────────────────────────────────────────────
left, right = st.columns([1, 1], gap="large")

with left:
    message = st.text_area("", height=140, placeholder="Paste any message to analyze...")
    unknown_sender = st.checkbox("Unknown / unsaved sender", value=False)
    analyze_btn = st.button("Analyze Message →", type="primary", use_container_width=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown("<p style='color:#6b7280;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;'>Try an example</p>", unsafe_allow_html=True)

    examples = {
        "✅  Call me when you reach": "Call me when you reach home bro",
        "⚠️  Small favor request":    "Don't tell anyone, I need a small favor",
        "🚨  OTP scam":               "Send me the OTP you just received to verify my account",
        "🚨  Account freeze threat":  "Your account will be blocked. Verify KYC immediately.",
        "🚨  Prize money lure":       "You won Rs 50000! Pay processing fee to claim prize.",
    }
    for ex_label, ex_msg in examples.items():
        if st.button(ex_label, use_container_width=True, key=ex_label):
            message = ex_msg

with right:
    if analyze_btn and message and message.strip():
        with st.spinner(""):
            try:
                resp = requests.post(API_URL, json={
                    "message": message,
                    "unknown_sender": unknown_sender
                }, timeout=30)
                data = resp.json()

                label     = data["label"]
                score     = data["final_score"]
                breakdown = data["breakdown"]

                label_cls  = {"Safe": "label-safe", "Suspicious": "label-suspicious", "Scam": "label-scam"}[label]
                label_icon = {"Safe": "✅", "Suspicious": "⚠️", "Scam": "🚨"}[label]
                bar_color  = {"Safe": "#34d399",    "Suspicious": "#fbbf24",         "Scam": "#f87171"}[label]

                st.markdown(f"""
                <div class='result-card'>
                  <div class='{ label_cls }'>{label_icon} {label}</div>
                  <div style='color:#6b7280;font-size:0.82rem;margin:4px 0 16px;'>Risk Score: {score}/100</div>
                  <div class='risk-bar-wrap'>
                    <div style='background:{bar_color};width:{score}%;height:100%;border-radius:999px;
                                box-shadow:0 0 12px {bar_color}55;transition:width 0.5s;'></div>
                  </div>
                  <div style='display:flex;justify-content:space-between;font-size:0.7rem;color:#4b5563;'>
                    <span>Safe</span><span>Suspicious</span><span>Scam</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Metrics row
                c1, c2, c3 = st.columns(3)
                for col, val, lbl in [
                    (c1, f"{breakdown['ml_probability']:.0%}", "ML Score"),
                    (c2, f"{breakdown['final_probability']:.0%}", "Final Risk"),
                    (c3, f"{breakdown['bert_probability']:.0%}" if breakdown['bert_probability'] else "N/A", "BERT Layer"),
                ]:
                    with col:
                        st.markdown(f"""
                        <div class='metric-mini'>
                          <div class='val'>{val}</div>
                          <div class='lbl'>{lbl}</div>
                        </div>""", unsafe_allow_html=True)

                st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

                # Rule categories
                cats = breakdown.get("rule_categories", [])
                if cats:
                    st.markdown("<p style='color:#9ca3af;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin:12px 0 6px;'>Patterns Detected</p>", unsafe_allow_html=True)
                    badges = " ".join([f"<span class='badge badge-rule'>{c}</span>" for c in cats])
                    st.markdown(badges, unsafe_allow_html=True)

                # Top risk words
                words = breakdown.get("top_signal_words", [])
                if words:
                    st.markdown("<p style='color:#9ca3af;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin:12px 0 6px;'>Risk Keywords</p>", unsafe_allow_html=True)
                    badges = " ".join([f"<span class='badge badge-word'>{w}</span>" for w in words])
                    st.markdown(badges, unsafe_allow_html=True)

                if not cats and not words:
                    st.markdown("<p style='color:#4b5563;font-size:0.85rem;margin-top:12px;'>No significant threat patterns detected.</p>", unsafe_allow_html=True)

            except requests.exceptions.ConnectionError:
                st.error("Backend offline — run `python main.py` first.")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.markdown("""
        <div style='height:340px;display:flex;flex-direction:column;align-items:center;
                    justify-content:center;border:1px dashed rgba(255,255,255,0.07);
                    border-radius:20px;color:#374151;text-align:center;'>
          <div style='font-size:3rem;margin-bottom:12px;opacity:0.4;'>🛡️</div>
          <div style='font-size:0.9rem;'>Results will appear here</div>
        </div>
        """, unsafe_allow_html=True)
