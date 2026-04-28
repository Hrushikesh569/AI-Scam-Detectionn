import re

# ─────────────────────────────────────────────────────────────────────
# PHRASE LISTS — used to extract numeric rule features fed into ML model
# These are NO LONGER overrides or score adders.
# They return 0/1 feature values that the ML model has learned to weight.
# ─────────────────────────────────────────────────────────────────────

URGENCY_PHRASES = [
    "act now", "immediately", "last warning", "action required",
    "immediate action", "limited time", "don't miss", "right now",
    "final warning", "within 24 hours", "expires today",
    "respond immediately", "time is running out"
]

FEAR_PHRASES = [
    "blocked", "suspended", "locked", "permanently closed",
    "restricted", "disconnected", "disabled", "terminated",
    "unusual activity", "unauthorized", "compromised",
    "legal action", "face legal"
]

AUTHORITY_PHRASES = [
    "rbi mandate", "bank account", "tax refund", "apple id",
    "customer service", "account verification", "kyc",
    "debit card", "credit card", "sim card"
]

GREED_PHRASES = [
    "you won", "you have won", "prize", "jackpot", "lottery",
    "cash prize", "gift card", "reward", "earn money",
    "part time job", "work from home", "selected for",
    "pre-approved", "processing fee", "double your money"
]

ACTION_PHRASES = [
    "click here", "click this link", "call this number",
    "share otp", "share your otp", "send your bank",
    "send bank details", "verify your", "update your",
    "confirm your identity", "provide documentation",
    "confirm your delivery", "download this app",
    "send me the otp", "tell me the otp", "tell me your otp",
    "give me the otp", "give me your otp",
    "what is your otp", "enter your otp"
]

SOCIAL_ENGINEERING_PHRASES = [
    "changed my number", "don't tell anyone",
    "i'll explain later", "this is confidential",
    "i trust you", "don't ask questions",
    "just follow what i say", "save this number",
    "text me on whatsapp only"
]

EMOTIONAL_PHRASES = [
    "i'm in trouble", "please don't ignore",
    "can't call anyone else", "help me urgently",
    "i'm stuck", "please return it",
    "accidentally sent money", "transfer a small amount"
]
# ─────────────────────────────────────────────────────────────────────
# CRITICAL OVERRIDE PATTERNS
# These patterns are so high-risk they force SCAM classification
# regardless of ML probability. The rule engine acts as a hard guard.
# ─────────────────────────────────────────────────────────────────────

CRITICAL_PATTERNS = [
    # OTP fraud (any combination of otp + request verb)
    ("otp", ["send", "tell", "share", "give", "what is", "enter"]),
    # Password request
    ("password", ["share", "send", "tell", "give", "what is"]),
    # Bank details
    ("account number", ["share", "send", "tell", "give"]),
    ("card number",    ["share", "send", "tell", "give"]),
    # Processing fee scam
    ("processing fee", ["pay", "send", "transfer", "deposit"]),
    # Double money scam
    ("double",         ["transfer", "send", "deposit", "invest"]),
]


def check_critical_override(text: str) -> bool:
    """
    Returns True if the message contains a critical high-confidence
    fraud pattern that should force SCAM classification.
    E.g. 'tell me your otp', 'send your password'
    """
    lower = text.lower()
    for keyword, verbs in CRITICAL_PATTERNS:
        if keyword in lower:
            for verb in verbs:
                if verb in lower:
                    return True
    return False


ALL_CATEGORIES = [
    ("urgency",   URGENCY_PHRASES),
    ("fear",      FEAR_PHRASES),
    ("authority", AUTHORITY_PHRASES),
    ("greed",     GREED_PHRASES),
    ("action",    ACTION_PHRASES),
    ("social",    SOCIAL_ENGINEERING_PHRASES),
    ("emotional", EMOTIONAL_PHRASES),
]


def _has_match(text: str, phrases: list) -> int:
    """Return 1 if ANY phrase from the list appears in text, else 0."""
    lower = text.lower()
    for phrase in phrases:
        if phrase in lower:
            return 1
    return 0


def get_rule_features(text: str) -> list:
    """
    Extract rule-based binary features for ML input.
    Returns a list of 7 floats (0.0 or 1.0) — one per manipulation category.
    These are fed as extra columns alongside TF-IDF into the classifier.
    """
    return [float(_has_match(text, phrases)) for _, phrases in ALL_CATEGORIES]


def get_matched_categories(text: str) -> list:
    """Return human-readable names of all matched rule categories."""
    return [name for name, phrases in ALL_CATEGORIES if _has_match(text, phrases)]


def get_explanations(text: str, matched_categories: list, top_words: list) -> list:
    """
    Generate human-readable explanations combining:
    - Which manipulation categories were triggered
    - Top ML-weighted words from the message
    """
    exps = []

    label_map = {
        "urgency":   "Urgency pressure detected",
        "fear":      "Fear-based manipulation detected",
        "authority": "Authority impersonation detected",
        "greed":     "Reward/money lure detected",
        "action":    "Suspicious action demand detected",
        "social":    "Social engineering pattern detected",
        "emotional": "Emotional manipulation detected",
    }

    for cat in matched_categories:
        if cat in label_map:
            # Find specific matching phrase for detail
            _, phrases = next(p for p in ALL_CATEGORIES if p[0] == cat)
            lower = text.lower()
            matched = [p for p in phrases if p in lower]
            detail = f": '{matched[0]}'" if matched else ""
            exps.append(f"{label_map[cat]}{detail}")

    if top_words:
        exps.append(f"High-risk terms in message: {', '.join(top_words)}")

    if not exps:
        exps.append("No significant threat patterns detected")

    return exps


def calculate_behavior_score(unknown_sender: bool) -> float:
    """
    Kept for backward compatibility.
    Returns a 0/1 feature value for unknown sender status.
    """
    return 1.0 if unknown_sender else 0.0
